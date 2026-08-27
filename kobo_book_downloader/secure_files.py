import os
import stat
import tempfile


class OwnedTemporaryFile:
	"""A random temporary file whose identity is tracked for safe cleanup."""

	def __init__( self, directory: str ):
		fileDescriptor, self.Path = tempfile.mkstemp(
			dir = directory,
			prefix = ".kobo-book-downloader-",
			suffix = ".tmp",
		)
		fileStat = os.fstat( fileDescriptor )
		self.__Identity = ( fileStat.st_dev, fileStat.st_ino )
		try:
			self.File = os.fdopen( fileDescriptor, "w+b" )
		except Exception:
			os.close( fileDescriptor )
			os.unlink( self.Path )
			raise

	def FlushAndSync( self ) -> None:
		self.File.flush()
		os.fsync( self.File.fileno() )

	def Close( self ) -> None:
		if not self.File.closed:
			self.File.close()

	def PublishWithoutOverwrite( self, outputPath: str ) -> None:
		self.FlushAndSync()
		self.Close()
		if not self.__PathStillBelongsToOperation():
			raise RuntimeError( "The temporary output file was replaced before publication." )

		# Hard-link creation is atomic and fails if any file or symlink already exists at outputPath.
		os.link( self.Path, outputPath )

	def Cleanup( self ) -> None:
		self.Close()
		if not self.__PathStillBelongsToOperation():
			return

		os.unlink( self.Path )

	def __PathStillBelongsToOperation( self ) -> bool:
		try:
			pathStat = os.lstat( self.Path )
		except FileNotFoundError:
			return False

		return stat.S_ISREG( pathStat.st_mode ) and \
			( pathStat.st_dev, pathStat.st_ino ) == self.__Identity
