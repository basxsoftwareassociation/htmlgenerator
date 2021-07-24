import cython
from htmlgenerator.base import *  # noqa
from htmlgenerator.htmltags import *  # noqa
from htmlgenerator.lazy import *  # noqa
from htmlgenerator.safestring import mark_safe  # noqa

__version__ = "2.0.0"


DEBUG: bool = False
"Turning on this flag will add html attributes with information about the source of the generated html output",
# not sure whether this is a smart idea, but environment variables do not really seem better...
