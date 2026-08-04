"""ForgeCAD graphical workbench initialization."""

import FreeCADGui

from workbench import ForgeCADWorkbench


FreeCADGui.addWorkbench(ForgeCADWorkbench())
