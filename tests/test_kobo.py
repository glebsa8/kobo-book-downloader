import pytest

from kobo_book_downloader.kobo import DownloadUrlListEmptyKoboException, Kobo


def test_download_info_rejects_an_empty_url_list():
	with pytest.raises( DownloadUrlListEmptyKoboException ):
		Kobo._Kobo__GetDownloadInfo( "book-id", { "ContentUrls": [] } )


def test_download_info_selects_epub_and_removes_problem_query_parameter():
	response = {
		"ContentUrls": [
			{
				"DRMType": "KDRM",
				"UrlFormat": "EPUB3",
				"DownloadUrl": "https://example.com/book.epub?b=bad&token=good",
			}
		]
	}

	url, has_drm = Kobo._Kobo__GetDownloadInfo( "book-id", response )

	assert url == "https://example.com/book.epub?token=good"
	assert has_drm is True
