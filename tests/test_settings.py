import json
import stat

from kobo_book_downloader.settings import Settings


def test_settings_use_xdg_config_home_and_round_trip(tmp_path, monkeypatch):
	config_home = tmp_path / "nested" / "config"
	monkeypatch.setenv( "XDG_CONFIG_HOME", str( config_home ) )

	settings = Settings()
	settings.AccessToken = "access-token"
	settings.RefreshToken = "refresh-token"
	settings.DeviceId = "device-id"
	settings.Save()

	settings_path = config_home / "kobo-book-downloader.json"
	assert settings_path.is_file()
	assert json.loads( settings_path.read_text() )[ "AccessToken" ] == "access-token"
	assert stat.S_IMODE( settings_path.stat().st_mode ) == 0o600

	reloaded = Settings()
	assert reloaded.AccessToken == "access-token"
	assert reloaded.RefreshToken == "refresh-token"
	assert reloaded.DeviceId == "device-id"


def test_settings_use_standard_config_directory_by_default(tmp_path, monkeypatch):
	monkeypatch.delenv( "XDG_CONFIG_HOME", raising = False )
	monkeypatch.setenv( "HOME", str( tmp_path ) )

	settings = Settings()

	assert settings.SettingsFilePath == str( tmp_path / ".config" / "kobo-book-downloader.json" )


def test_settings_keep_using_an_existing_legacy_file(tmp_path, monkeypatch):
	monkeypatch.delenv( "XDG_CONFIG_HOME", raising = False )
	monkeypatch.setenv( "HOME", str( tmp_path ) )
	legacy_path = tmp_path / "kobo-book-downloader.json"
	legacy_path.write_text( "{}" )

	settings = Settings()

	assert settings.SettingsFilePath == str( legacy_path )
