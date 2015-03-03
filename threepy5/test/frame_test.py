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

        dbg = wx.Button(self, label="debug")
        dbg.Bind(wx.EVT_BUTTON, self.OnDebug)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dbg, flag=wx.ALIGN_BOTTOM)

        box.Add(hbox, proportion=0)


    def OnDebug(self, ev):
        print "------DEBUG-----"
        
        self.ctrl.Selector.DeleteSelection()


if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame(None)

    ####################
    # write code here
    ####################

    ctrl = newgui.Board(frame)
    frame.Sizer.Add(ctrl, proportion=1, flag=wx.EXPAND)
    frame.ctrl = ctrl

    frame.ctrl.Deck.NewCard("Content", pos=(15,15))
    frame.ctrl.Deck.NewCard("Content", pos=(15,200))
    frame.ctrl.Deck.NewCard("Content", pos=(300,15))
    frame.ctrl.Deck.NewCard("Content", pos=(300,200))
    c1, c2, c3, c3 = ctrl.Cards    

    ctrl.Selector.Select(c1)

    ####################
    # end code here
    ####################
    
    frame.Show()
    app.MainLoop()


