#!/usr/bin/python
import wx
import sys
from os import getcwd as cwd
sys.path.append(cwd())
import threepy5
import classfactory
import gui

__all__ = ["threepy5", "classfactory", "gui"]

if __name__ == "__main__":
    app = wx.App()
    frame = gui.threepy5GUI.ThreePyFiveFrame(None)
    app.MainLoop()
