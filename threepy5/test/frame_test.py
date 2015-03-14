"""This is NOT a unit test, just a file I use to try out things quickly."""

import wx
import threepy5.threepy5 as py5
import threepy5
import threepy5.utils as utils
import threepy5.gui.wxutils as wxutils
import threepy5.gui as newgui


class TestFrame(wx.Frame):
    def __init__(self, parent):
        super(TestFrame, self).__init__(parent)
        box = wx.BoxSizer(wx.VERTICAL)
        self.Sizer = box
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(hbox, proportion=0)


if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame(None)
    app.MainLoop()


