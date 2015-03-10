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

        dbg = wx.Button(self, label="debug")
        dbg.Bind(wx.EVT_BUTTON, self.OnDebug)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(dbg, flag=wx.ALIGN_BOTTOM)

        box.Add(hbox, proportion=0)

        menu = wx.Menu()
        dbg_it = wx.MenuItem(menu, wx.ID_ANY, "Debug")
        self.Bind(wx.EVT_MENU, self.OnDebug, dbg_it)
        accels = [wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D") , dbg_it.GetId())]
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def OnDebug(self, ev):
        print "------DEBUG-----"
        print "work size:  ", self.ctrl.Size
        print "board size: ", self.ctrl.Board.Size
        print "children: ", len(self.ctrl.Board.Selectables)
        print "cards: ", self.ctrl.Deck.cards


if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame(None)

    ####################
    # write code here
    ####################

    ctrl = newgui.workspace.Workspace(frame)
    frame.Sizer.Add(ctrl, proportion=1, flag=wx.EXPAND)
    frame.ctrl = ctrl

    # frame.ctrl.Deck.NewCard("Content", pos=(15,15))

    w = newgui.board.ImagePlaceHolder(ctrl.Board)

    # lis = utils.listener(topics=[utils.pub.ALL_TOPICS])

    ####################
    # end code here
    ####################

    frame.Show()
    app.MainLoop()


