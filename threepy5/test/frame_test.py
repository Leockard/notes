"""This is NOT a unit test, just a file I use to try out things quickly."""

import wx
import threepy5.threepy5 as py5
import threepy5
from threepy5.gui import threepy5GUI_new as newgui


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
        for c in self.ctrl.Cards:
            print c.Position
 
        

if __name__ == "__main__":
    app = wx.App()
    frame = TestFrame(None)
    frame.Show()
    app.MainLoop()
