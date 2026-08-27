import io
import logging
from types import SimpleNamespace
import zipfile

import pytest

from kobo_book_downloader.errors import KoboException
from kobo_book_downloader.globals import Globals
from kobo_book_downloader.kobo import Kobo
from kobo_book_downloader.kobo_drm_remover import KoboDrmRemover


class FakeResponse:
	def __init__( self, chunks, headers = None, on_iterate = None ):
		self.Chunks = chunks
		self.headers = headers or {}
		self.OnIterate = on_iterate
		self.Closed = False

	def raise_for_status( self ) -> None:
		pass

	def iter_content( self, chunk_size ):
		if self.OnIterate is not None:
			self.OnIterate()
		for chunk in self.Chunks:
			if isinstance( chunk, Exception ):
				raise chunk
			yield chunk

	def close( self ) -> None:
		self.Closed = True


class FakeSession:
	def __init__( self, response ):
		self.Response = response

	def get( self, url, stream = False ):
		return self.Response


@pytest.fixture
def kobo_client():
	Globals.Logger = logging.getLogger( "kobo-book-downloader-tests" )
	Globals.Settings = SimpleNamespace( DeviceId = "device-id", UserId = "user-id" )
	return Kobo()


def configure_download( monkeypatch, koboClient, response, hasDrm = False ) -> None:
	drmType = "KDRM" if hasDrm else "SignedNoDrm"
	contentAccessResponse = {
		"ContentKeys": [],
		"ContentUrls": [
			{
				"DRMType": drmType,
				"UrlFormat": "EPUB3",
				"DownloadUrl": "https://example.com/book.epub",
			}
		],
	}
	monkeypatch.setattr(
		koboClient,
		"_Kobo__GetContentAccessBook",
		lambda productId, displayProfile: contentAccessResponse,
	)
	koboClient.Session = FakeSession( response )


def test_existing_destination_is_preserved_without_contacting_kobo( tmp_path, monkeypatch, kobo_client ):
	outputPath = tmp_path / "book.epub"
	outputPath.write_bytes( b"original" )
	monkeypatch.setattr(
		kobo_client,
		"_Kobo__GetContentAccessBook",
		lambda productId, displayProfile: pytest.fail( "Kobo should not be contacted" ),
	)

	with pytest.raises( KoboException, match = "already exists" ):
		kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	assert outputPath.read_bytes() == b"original"


def test_existing_destination_symlink_is_not_followed( tmp_path, monkeypatch, kobo_client ):
	outputPath = tmp_path / "book.epub"
	victimPath = tmp_path / "victim.txt"
	victimPath.write_bytes( b"victim" )
	try:
		outputPath.symlink_to( victimPath )
	except ( NotImplementedError, OSError ):
		pytest.skip( "This platform cannot create a test symlink" )

	monkeypatch.setattr(
		kobo_client,
		"_Kobo__GetContentAccessBook",
		lambda productId, displayProfile: pytest.fail( "Kobo should not be contacted" ),
	)

	with pytest.raises( KoboException, match = "already exists" ):
		kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	assert outputPath.is_symlink()
	assert victimPath.read_bytes() == b"victim"


def test_operation_temporaries_are_cleaned_after_drm_failure( tmp_path, monkeypatch, kobo_client ):
	outputPath = tmp_path / "book.epub"
	response = FakeResponse( [ b"encrypted book" ] )
	configure_download( monkeypatch, kobo_client, response, hasDrm = True )

	def fail_drm_removal( self, inputFile, outputFile, contentKeys ) -> None:
		outputFile.write( b"partial" )
		raise KoboException( "DRM failed" )

	monkeypatch.setattr( KoboDrmRemover, "RemoveDrm", fail_drm_removal )

	with pytest.raises( KoboException, match = "DRM failed" ):
		kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	assert not outputPath.exists()
	assert list( tmp_path.iterdir() ) == []
	assert response.Closed is True


def test_old_predictable_temporary_name_cannot_redirect_download( tmp_path, monkeypatch, kobo_client ):
	outputPath = tmp_path / "book.epub"
	predictablePath = tmp_path / "book.epub.downloading"
	victimPath = tmp_path / "victim.txt"
	victimPath.write_bytes( b"victim" )

	try:
		predictablePath.symlink_to( victimPath )
	except ( NotImplementedError, OSError ):
		predictablePath.write_bytes( b"predictable" )

	response = FakeResponse( [ b"completed book" ] )
	configure_download( monkeypatch, kobo_client, response )
	kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	assert outputPath.read_bytes() == b"completed book"
	assert victimPath.read_bytes() == b"victim"
	assert predictablePath.exists() or predictablePath.is_symlink()


def test_drm_download_publishes_completed_zip_and_removes_temporaries( tmp_path, monkeypatch, kobo_client ):
	encryptedBook = io.BytesIO()
	with zipfile.ZipFile( encryptedBook, "w", zipfile.ZIP_DEFLATED ) as bookZip:
		bookZip.writestr( "chapter.txt", b"chapter contents" )

	outputPath = tmp_path / "book.epub"
	response = FakeResponse( [ encryptedBook.getvalue() ] )
	configure_download( monkeypatch, kobo_client, response, hasDrm = True )
	kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	with zipfile.ZipFile( outputPath, "r" ) as completedBook:
		assert completedBook.read( "chapter.txt" ) == b"chapter contents"
	assert sorted( path.name for path in tmp_path.iterdir() ) == [ "book.epub" ]


def test_destination_created_during_download_is_preserved( tmp_path, monkeypatch, kobo_client ):
	outputPath = tmp_path / "book.epub"
	response = FakeResponse(
		[ b"downloaded book" ],
		on_iterate = lambda: outputPath.write_bytes( b"racing writer" ),
	)
	configure_download( monkeypatch, kobo_client, response )

	with pytest.raises( KoboException, match = "created during the download" ):
		kobo_client.Download( "book-id", Kobo.DisplayProfile, str( outputPath ) )

	assert outputPath.read_bytes() == b"racing writer"
	assert sorted( path.name for path in tmp_path.iterdir() ) == [ "book.epub" ]


def test_content_length_over_download_cap_is_rejected( monkeypatch, kobo_client ):
	response = FakeResponse( [ b"unused" ], headers = { "Content-Length": "6" } )
	kobo_client.Session = FakeSession( response )
	monkeypatch.setattr( Kobo, "MaxDownloadBytes", 5 )
	outputFile = io.BytesIO()

	with pytest.raises( KoboException, match = "exceeds the 5-byte limit" ):
		kobo_client._Kobo__DownloadToFile( "https://example.com/book", outputFile )

	assert outputFile.getvalue() == b""
	assert response.Closed is True


def test_streaming_download_over_cap_is_rejected( monkeypatch, kobo_client ):
	response = FakeResponse( [ b"123", b"456" ] )
	kobo_client.Session = FakeSession( response )
	monkeypatch.setattr( Kobo, "MaxDownloadBytes", 5 )
	outputFile = io.BytesIO()

	with pytest.raises( KoboException, match = "exceeded the 5-byte limit while streaming" ):
		kobo_client._Kobo__DownloadToFile( "https://example.com/book", outputFile )

	assert outputFile.getvalue() == b"123"
	assert response.Closed is True
