#!/usr/bin/python

# canvas.py
# drawing area class for notes.py
# most code copied from wxPython demo code app doodle.py:
# http://www.wxpython.org/download.php

import wx


######################
# Canvas Class
######################

class Canvas(wx.Control):
    def __init__(self, parent, id=wx.ID_ANY, size=wx.DefaultSize):
        wx.Control.__init__(self, parent, id=id, size=size, style=wx.NO_FULL_REPAINT_ON_RESIZE|wx.BORDER_NONE)

        # print "__init__"
        self.SetBackgroundColour("WHITE")
        self.thickness = 1
        self.colour = "BLACK"
        self.pen = wx.Pen(self.colour, self.thickness, wx.SOLID)
        self.lines = []
        self.pos = wx.Point(0,0)
        self.buffer = wx.EmptyBitmap(1, 1)
        
        self.InitBuffer()

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SHOW, self.OnShow) # or hide
        # self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)


    ### Behavior functions
    def DrawLines(self, dc):
        """Redraws all the lines that have been drawn already."""
        # print "DrawLines"
        dc.BeginDrawing()
        for colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for coords in line:
                dc.DrawLine(*coords)
        dc.EndDrawing()

    def SetBackground(self, bg):
        # print "SetBackground"
        dest = wx.ClientDC(self)
        # dest = wx.MemoryDC()
        # print "selecting self.buffer of size: " + str(self.buffer.GetSize())
        # dest.SelectObject(self.buffer)
        # print "drawing bg: " + str(bg.GetSize())
        dest.DrawBitmap(bg, 0, 0)
        # dest.SelectObject(wx.NullBitmap)

                
    ### Auxiliary functions
    
    def InitBuffer(self):
        """Initialize the bitmap used for buffering the display."""
        # print "InitBuffer"
        size = self.GetClientSize()
        # print "making new buffer"
        buf = wx.EmptyBitmap(max(1, size.width), max(1, size.height))
        dc = wx.BufferedDC(None, buf)
        
        if hasattr(self, "buffer"):
            # print "copying what we had before"
            dc.DrawBitmap(self.buffer, 0, 0)
                
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.DrawLines(dc)
        self.reInitBuffer = False
        self.buffer = buf


    ### Callbacks

    def OnShow(self, ev):
        if ev.IsShown():
            self.DrawLines(wx.BufferedDC(None, self.buffer))
    
    def OnLeftDown(self, ev):
        """called when the left mouse button is pressed"""
        self.curLine = []
        self.pos = ev.GetPosition()
        self.CaptureMouse()

    def OnLeftUp(self, ev):
        """called when the left mouse button is released"""
        if self.HasCapture():
            self.lines.append((self.colour, self.thickness, self.curLine))
            self.curLine = []
            self.ReleaseMouse()
            
    def OnMotion(self, ev):
        """
        Called when the mouse is in motion.  If the left button is
        dragging then draw a line from the last event position to the
        current one.  Save the coordinates for redraws.
        """
        if ev.Dragging() and ev.LeftIsDown():
            # all drawings over dc will not be saved in self.buffer...
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
            dc.BeginDrawing()
            dc.SetPen(self.pen)
            pos = ev.GetPosition()
            coords = (self.pos.x, self.pos.y, pos.x, pos.y)
            self.curLine.append(coords)
            dc.DrawLine(*coords)
            self.pos = pos
            dc.EndDrawing()

    def OnSize(self, ev):
        # print "OnSize" + str(ev.GetSize())
        self.SetSize(ev.GetSize())
        self.reInitBuffer = True

    def OnIdle(self, ev):
        """
        If the size was changed then resize the bitmap used for double
        buffering to match the window size.  We do it in Idle time so
        there is only one refresh after resizing is done, not lots while
        it is happening.
        """
        if self.reInitBuffer:
            # print "OnIdle: reInitBuffer = True"
            self.InitBuffer()
            self.Refresh(False)

    def OnPaint(self, ev):
        """Called when the window is exposed."""
        # Create a buffered paint DC.  It will create the real wx.PaintDC and then blit
        # the bitmap to it when dc is deleted.
        # print "OnPaint"
        dc = wx.BufferedPaintDC(self, self.buffer)

    def OnEraseBackground(self, evt):
        #  http://www.blog.pythonlibrary.org/2010/03/18/wxpython-putting-a-background-image-on-a-panel/
        # print "OnErase"
        dc = evt.GetDC()
    
        if not dc:
            dc = wx.ClientDC(self)
            rect = self.GetUpdateRegion().GetBox()
            dc.SetClippingRect(rect)
        dc.Clear()
        # print "onerase"

