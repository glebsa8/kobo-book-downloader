from logging import Logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .kobo import Kobo
	from .settings import Settings

class Globals:
	Logger = None # type: Logger | None
	Kobo = None # type: Kobo | None
	Settings = None # type: Settings | None
