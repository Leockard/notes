#!/usr/bin/python
import wx
import gui
import threepy5

__all__ = ["threepy5", "gui"]

if __name__ == "__main__":
    print dir(gui)
    app = wx.App()
    frame = gui.threepy5GUI.ThreePyFiveFrame(None)
    app.MainLoop()
