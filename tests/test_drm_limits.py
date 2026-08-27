import io
import zipfile

import pytest

from kobo_book_downloader.errors import KoboException
from kobo_book_downloader.kobo_drm_remover import KoboDrmRemover


def make_zip( entries ) -> io.BytesIO:
	zipContents = io.BytesIO()
	with zipfile.ZipFile( zipContents, "w", zipfile.ZIP_DEFLATED ) as outputZip:
		for filename, contents in entries:
			outputZip.writestr( filename, contents )
	zipContents.seek( 0 )
	return zipContents


def remove_drm( inputFile: io.BytesIO, outputFile: io.BytesIO ) -> None:
	KoboDrmRemover( "device-id", "user-id" ).RemoveDrm( inputFile, outputFile, {} )


def test_zip_entry_count_cap_is_enforced_before_reading( monkeypatch ):
	monkeypatch.setattr( KoboDrmRemover, "MaxEntryCount", 1 )
	inputFile = make_zip( [ ( "one", b"1" ), ( "two", b"2" ) ] )
	outputFile = io.BytesIO()

	with pytest.raises( KoboException, match = "exceeds the 1-entry limit" ):
		remove_drm( inputFile, outputFile )

	assert outputFile.getvalue() == b""


def test_zip_individual_entry_size_cap_is_enforced_before_reading( monkeypatch ):
	monkeypatch.setattr( KoboDrmRemover, "MaxEntryUncompressedBytes", 3 )
	inputFile = make_zip( [ ( "large", b"1234" ) ] )
	outputFile = io.BytesIO()

	with pytest.raises( KoboException, match = "exceeds the 3-byte per-entry limit" ):
		remove_drm( inputFile, outputFile )

	assert outputFile.getvalue() == b""


def test_zip_total_uncompressed_size_cap_is_enforced_before_reading( monkeypatch ):
	monkeypatch.setattr( KoboDrmRemover, "MaxTotalUncompressedBytes", 5 )
	inputFile = make_zip( [ ( "one", b"123" ), ( "two", b"456" ) ] )
	outputFile = io.BytesIO()

	with pytest.raises( KoboException, match = "exceeds the 5-byte total limit" ):
		remove_drm( inputFile, outputFile )

	assert outputFile.getvalue() == b""
