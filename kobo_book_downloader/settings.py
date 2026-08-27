import json
import os

class Settings:
	def __init__( self ):
		self.DeviceId = ""
		self.SerialNumber = ""
		self.AccessToken = ""
		self.RefreshToken = ""
		self.UserId = ""
		self.UserKey = ""
		self.SettingsFilePath = Settings.__GetCacheFilePath()

		self.Load()

	def AreAuthenticationSettingsSet( self ) -> bool:
		return len( self.DeviceId ) > 0 and len( self.AccessToken ) > 0 and len( self.RefreshToken ) > 0

	def IsLoggedIn( self ) -> bool:
		return len( self.UserId ) > 0 and len( self.UserKey ) > 0

	def Load( self ) -> None:
		if not os.path.isfile( self.SettingsFilePath ):
			return

		Settings.__EnsureOwnerOnlyPermissions( self.SettingsFilePath )
		with open( self.SettingsFilePath, "r" ) as f:
			jsonText = f.read()
			jsonObject = json.loads( jsonText )
			self.__LoadFromJson( jsonObject )

	def Save( self ) -> None:
		settingsDirectory = os.path.dirname( self.SettingsFilePath )
		os.makedirs( settingsDirectory, exist_ok = True )
		if os.path.isfile( self.SettingsFilePath ):
			Settings.__EnsureOwnerOnlyPermissions( self.SettingsFilePath )

		fileDescriptor = os.open( self.SettingsFilePath, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600 )
		with os.fdopen( fileDescriptor, "w" ) as f:
			jsonObject = self.__SaveToJson()
			f.write( json.dumps( jsonObject, indent = 4 ) )
		Settings.__EnsureOwnerOnlyPermissions( self.SettingsFilePath )

	@staticmethod
	def __EnsureOwnerOnlyPermissions( settingsFilePath: str ) -> None:
		if os.name == "posix":
			os.chmod( settingsFilePath, 0o600 )

	def __SaveToJson( self ) -> dict:
		return {
			"AccessToken": self.AccessToken,
			"DeviceId": self.DeviceId,
			"RefreshToken": self.RefreshToken,
			"SerialNumber": self.SerialNumber,
			"UserId": self.UserId,
			"UserKey": self.UserKey
		}

	def __LoadFromJson( self, jsonMap: dict ) -> None:
		self.AccessToken = jsonMap.get( "AccessToken", self.AccessToken )
		self.DeviceId = jsonMap.get( "DeviceId", self.DeviceId )
		self.RefreshToken = jsonMap.get( "RefreshToken", self.RefreshToken )
		self.SerialNumber = jsonMap.get( "SerialNumber", self.SerialNumber )
		self.UserId = jsonMap.get( "UserId", self.UserId )
		self.UserKey = jsonMap.get( "UserKey", self.UserKey )

	@staticmethod
	def __GetCacheFilePath() -> str:
		cacheHome = os.environ.get( "XDG_CONFIG_HOME" )
		if cacheHome is not None:
			return os.path.join( cacheHome, "kobo-book-downloader.json" )

		home = os.path.expanduser( "~" )
		cacheHome = os.path.join( home, ".config" )
		settingsFilePath = os.path.join( cacheHome, "kobo-book-downloader.json" )

		# Keep using the pre-XDG location when an existing installation has credentials there.
		legacySettingsFilePath = os.path.join( home, "kobo-book-downloader.json" )
		if os.path.isfile( legacySettingsFilePath ) and not os.path.isfile( settingsFilePath ):
			return legacySettingsFilePath

		return settingsFilePath
