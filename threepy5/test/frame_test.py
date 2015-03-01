"""This is NOT a unit test, just a file I use to try out things quickly."""

import wx
import threepy5.threepy5 as py5
import threepy5
from threepy5.gui import board as newgui


class TestFrame(wx.Frame):
    def __init__(self, parent):
        super(TestFrame, self).__init__(parent)
        box = wx.BoxSizer(wx.VERTICAL)
        self.Sizer = box

        ####################
        # write code here
        ####################

        ctrl = newgui.Board(self)
        box.Add(ctrl, proportion=1, flag=wx.EXPAND)
        self.ctrl = ctrl

        c1 = self.ctrl.AddCard("Content", pos=(15,15))
        c2 = self.ctrl.AddCard("Content", pos=(15,200))
        c3 = self.ctrl.AddCard("Content", pos=(300,15))
        c4 = self.ctrl.AddCard("Content", pos=(300,200))

        self.ctrl.Selector.Select(c2)


        ####################
        # end code here
        ####################

        dbg = wx.Button(self, label="debug")
        dbg.Bind(wx.EVT_BUTTON, self.OnDebug)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dbg, flag=wx.ALIGN_BOTTOM)

        box.Add(hbox, proportion=0)


    def OnDebug(self, ev):
        print "------DEBUG-----"
        
        self.ctrl.Selector.SelectNearest(wx.WXK_UP)


if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame(None)
    frame.Show()
    app.MainLoop()
