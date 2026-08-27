from .errors import KoboException

from Crypto.Cipher import AES
from Crypto.Util import Padding

from typing import BinaryIO, Dict
import base64
import binascii
import hashlib
import zipfile

# Based on obok.py by Physisticated.
class KoboDrmRemover:
	MaxEntryCount = 10_000
	MaxEntryUncompressedBytes = 512 * 1024 * 1024
	MaxTotalUncompressedBytes = 2 * 1024 * 1024 * 1024

	def __init__( self, deviceId: str, userId: str ):
		self.DeviceIdUserIdKey = KoboDrmRemover.__MakeDeviceIdUserIdKey( deviceId, userId )

	@staticmethod
	def __MakeDeviceIdUserIdKey( deviceId: str, userId: str ) -> bytes:
		deviceIdUserId = ( deviceId + userId ).encode()
		key = hashlib.sha256( deviceIdUserId ).hexdigest()
		return binascii.a2b_hex( key[ 32: ] )

	def __DecryptContents( self, contents: bytes, contentKeyBase64: str ) -> bytes:
		contentKey = base64.b64decode( contentKeyBase64 )
		keyAes = AES.new( self.DeviceIdUserIdKey, AES.MODE_ECB )
		decryptedContentKey = keyAes.decrypt( contentKey )

		contentAes = AES.new( decryptedContentKey, AES.MODE_ECB )
		decryptedContents = contentAes.decrypt( contents )
		return Padding.unpad( decryptedContents, AES.block_size, "pkcs7" )

	@staticmethod
	def __ValidateZipLimits( entries: list ) -> None:
		if len( entries ) > KoboDrmRemover.MaxEntryCount:
			raise KoboException(
				"The EPUB ZIP contains %d entries, which exceeds the %d-entry limit."
				% ( len( entries ), KoboDrmRemover.MaxEntryCount )
			)

		totalUncompressedBytes = 0
		for entry in entries:
			if entry.file_size > KoboDrmRemover.MaxEntryUncompressedBytes:
				raise KoboException(
					"The EPUB ZIP entry '%s' expands to %d bytes, which exceeds the %d-byte per-entry limit."
					% ( entry.filename, entry.file_size, KoboDrmRemover.MaxEntryUncompressedBytes )
				)

			totalUncompressedBytes += entry.file_size
			if totalUncompressedBytes > KoboDrmRemover.MaxTotalUncompressedBytes:
				raise KoboException(
					"The EPUB ZIP expands to %d bytes, which exceeds the %d-byte total limit."
					% ( totalUncompressedBytes, KoboDrmRemover.MaxTotalUncompressedBytes )
				)

	def RemoveDrm( self, inputPath: BinaryIO | str, outputPath: BinaryIO | str, contentKeys: Dict[ str, str ] ) -> None:
		with zipfile.ZipFile( inputPath, "r" ) as inputZip:
			entries = inputZip.infolist()
			KoboDrmRemover.__ValidateZipLimits( entries )

			with zipfile.ZipFile( outputPath, "w", zipfile.ZIP_DEFLATED ) as outputZip:
				for entry in entries:
					contents = inputZip.read( entry )
					contentKeyBase64 = contentKeys.get( entry.filename, None )
					if contentKeyBase64 is not None:
						contents = self.__DecryptContents( contents, contentKeyBase64 )
					outputZip.writestr( entry.filename, contents )
