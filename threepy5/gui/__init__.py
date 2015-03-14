"""
Modules in gui hold the view/controller classes for `threepy5`.
"""
import board
import workspace
import frame



if __name__ == "__main__":
    import wx
    app = wx.App()
    frame = frame.ThreePyFiveFrame()
    app.MainLoop()
