import sys
sys.path.append('../lib')
try:
    import xbmc
except ImportError:
    #kodi stubs directory
    sys.path.append(sys.argv[1])
import boogie
import core
import helper
from core import api
boogie.api = api
boogie.listitem = core.listitem
boogie.__all__ = ["container", "dispatch", "navigator", "resolver", "player", "api", "lisitem"]

import pydocmd
modules = [boogie, helper]
pages = ["introduction.md", "quickstart.md"]
pydocmd.create(modules, pages, "../README.md")
