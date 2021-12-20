from .base import *  # noqa
from .htmltags import *  # noqa
from .lazy import *  # noqa
from .safestring import mark_safe  # noqa

__version__ = "1.2.5"


DEBUG: bool = False
"Turning on this flag will add html attributes with information "
"about the source of the generated html output",
# not sure whether this is a smart idea, but environment variables
# do not really seem better...
