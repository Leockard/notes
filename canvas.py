#!/usr/bin/python

# canvas.py
# drawing area class for notes.py
# most code copied from wxPython demo code app doodle.py:
# http://www.wxpython.org/download.php

import wx
from utilities import AutoSize


######################
# CanvasBase Class
######################

class CanvasBase(wx.StaticBitmap):
    def __init__(self, parent, bitmap=wx.NullBitmap):
        super(CanvasBase, self).__init__(parent, bitmap=bitmap, style=wx.NO_FULL_REPAINT_ON_RESIZE|wx.BORDER_NONE)
        self.thickness = 1
        self.colour = "BLACK"
        self.pen = wx.Pen(self.colour, self.thickness, wx.SOLID)
        self.lines = []
        self.pos = wx.Point(0,0)
        self.buffer = wx.EmptyBitmap(1, 1)
        self.offset = wx.Point(0, 0)
        
        self.InitBuffer()

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        
    ### Behavior functions

    def SetBuffer(self, bmp):
        self.buffer = bmp
    
    def SetOffset(self, pt):
        self.offset = pt

    def GetOffset(self):
        return self.offset

    def DrawLines(self, dc):
        """Redraws all the lines that have been drawn already."""
        dc.BeginDrawing()
        for colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for coords in line:
                dc.DrawLine(*coords)
        dc.EndDrawing()

        
    ### Auxiliary functions
    
    def InitBuffer(self):
        """Initialize the bitmap used for buffering the display."""
        size = self.GetClientSize()
        buf = wx.EmptyBitmap(max(1, size.width), max(1, size.height))
        dc = wx.BufferedDC(None, buf)
        
        if hasattr(self, "buffer"):
            dc.DrawBitmap(self.buffer, 0, 0)
                
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()
        self.DrawLines(dc)
        self.reInitBuffer = False
        self.buffer = buf

        
    ### Callbacks
    
    def OnLeftDown(self, ev):
        """Called when the left mouse button is pressed"""
        self.curLine = []
        self.pos = ev.GetPosition()

    def OnLeftUp(self, ev):
        """Called when the left mouse button is released"""
        self.lines.append((self.colour, self.thickness, self.curLine))
        self.curLine = []
            
    def OnMotion(self, ev):
        if ev.Dragging() and ev.LeftIsDown():
            # all drawings over dc will not be saved in self.buffer...
            dc = wx.BufferedDC(wx.ClientDC(self), self.GetBitmap())
            dc.BeginDrawing()
            dc.SetPen(self.pen)
            pos = ev.GetPosition()
            coords = (self.pos.x + self.offset.x, self.pos.y + self.offset.y,
                      pos.x + self.offset.x, pos.y + self.offset.y)
            self.curLine.append(coords)
            dc.DrawLine(*coords)
            self.pos = pos
            dc.EndDrawing()
            self.SetBitmap(dc.GetAsBitmap())

    def OnIdle(self, ev):
        """
        If the size was changed then resize the bitmap used for double
        buffering to match the window size.  We do it in Idle time so
        there is only one refresh after resizing is done, not lots while
        it is happening.
        """
        if self.reInitBuffer:
            self.InitBuffer()
            self.Refresh(False)

    def OnPaint(self, ev):
        """Called when the window is exposed."""
        print "Canvas.OnPaint"
        dc = wx.PaintDC(self)
        src = wx.MemoryDC()
        src.SelectObject(self.buffer)

        sz = self.GetVirtualSize()
        pos = self.GetViewStart()
        sc = self.GetScrollPixelsPerUnit()
        print sz, pos
        dc.Blit(0, 0,
                sz.x, sz.y,
                src,
                pos.x * sc[0], pos.y * sc[1])
        src.SelectObject(wx.NullBitmap)


        
######################
# CanvasBase Class
######################

class Canvas(AutoSize):
    def __init__(self, parent, size=wx.DefaultSize, pos=wx.DefaultPosition):
        super(Canvas, self).__init__(parent)
        self.buffer = None
        
        ctrl = CanvasBase(self, bitmap=wx.NullBitmap)

        box = wx.BoxSizer(wx.VERTICAL)
        # self.SetSizer(box)
        box.Add(ctrl, proportion=1, flag=wx.EXPAND)
        
        self.FitToChildren()
        self.ctrl = ctrl
        self.Bind(wx.EVT_SHOW, self.OnShow)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)

        
    ### Behavior functions

    def SetBuffer(self, bmp):
        """Call to set the whole of the content."""
        self.buffer = bmp

    def SetBackground(self, bmp):
        """Call to show the part that will be seen."""
        print "setting bmp of size: ", bmp.GetSize()
        self.ctrl.SetBuffer(bmp)
        self.ctrl.SetBitmap(bmp)
        self.ctrl.SetSize(bmp.GetSize())
        # self.SetSize(bmp.GetSize())


    ### Callbacks

    def OnShow(self, ev):
        print "show"
        print self.GetSize()
        print self.GetViewStart()
        
    def OnScroll(self, ev):
        print "scroll"
        pos = ev.GetPosition() * self.SCROLL_STEP
        if ev.GetOrientation() == wx.VERTICAL:
            # self.ctrl.SetOffset(wx.Point(0, pos))
            pt = wx.Point(0, pos)
        elif ev.GetOrientation() == wx.HORIZONTAL:
            # self.ctrl.SetOffset(wx.Point(pos, 0))
            pt = wx.Point(pos, 0)
        print pt
            
