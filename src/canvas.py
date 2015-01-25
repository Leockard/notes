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
        super(CanvasBase, self).__init__(parent, bitmap=bitmap, style=wx.BORDER_NONE)
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

        
    ### Behavior functions
    
    def SetOffset(self, pt):
        self.offset = pt

    def GetOffset(self):
        return self.offset

    def DrawLines(self):
        """Redraws all the lines that have been drawn already."""
        print "CanvasBase.DrawLines: ", len(self.lines)
        dc = wx.MemoryDC(self.GetBitmap())
        dc.BeginDrawing()
        
        for colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for coords in line:
                dc.DrawLine(*coords)
        
        dc.EndDrawing()
        self.SetBitmap(dc.GetAsBitmap())

        
    ### Auxiliary functions
    
    def InitBuffer(self):
        """Initialize the bitmap used for buffering the display."""
        print "CanvasBase.InitBuffer"
        size = self.GetClientSize()
        buf = wx.EmptyBitmap(max(1, size.width), max(1, size.height))
        dc = wx.BufferedDC(None, buf)

        # clear everything by painting over with bg colour        
        dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
        dc.Clear()

        self.DrawLines()
        self.buffer = buf

        
    ### Callbacks

    def OnLeftDown(self, ev):
        """Called when the left mouse button is pressed"""
        print "CanvasBase.LeftDown"
        self.curLine = []
        self.pos = ev.GetPosition()

    def OnLeftUp(self, ev):
        """Called when the left mouse button is released"""
        "CanvasBase.LeftUp"
        self.lines.append((self.colour, self.thickness, self.curLine))
        self.curLine = []
            
    def OnMotion(self, ev):
        if ev.Dragging() and ev.LeftIsDown():
            print "CanvasBase.Motion"
            # BufferedDC will paint first over self.GetBitmap()
            # and then copy everything to ClientDC(self)
            dc = wx.BufferedDC(wx.ClientDC(self), self.GetBitmap())
            dc.BeginDrawing()
            
            dc.SetPen(self.pen)
            new_pos = ev.GetPosition()
            coords = (self.pos.x + self.offset.x, self.pos.y + self.offset.y,
                      new_pos.x  + self.offset.x,  new_pos.y + self.offset.y)
            self.curLine.append(coords)
            dc.DrawLine(*coords)
            self.pos = new_pos
            
            dc.EndDrawing()
            self.SetBitmap(dc.GetAsBitmap())

        
        
######################
# Canvas Class
######################

class Canvas(AutoSize):
    def __init__(self, parent, size=wx.DefaultSize, pos=wx.DefaultPosition):
        super(Canvas, self).__init__(parent)

        # controls        
        ctrl = CanvasBase(self, bitmap=wx.NullBitmap)

        # boxes
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)
        box.Add(ctrl, proportion=1)

        # bindings
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        self.Bind(wx.EVT_SHOW, self.OnShow)

        # finish up        
        self.ctrl = ctrl

                
    ### Behavior functions

    def SetBackground(self, bmp):
        """Call to show the part that will be seen."""
        print "Canvas.SetBackground"
        if bmp:
            print "setting bmp of size: ", bmp.GetSize()
            self.ctrl.SetBitmap(bmp)
            self.FitToChildren()


    ### Callbacks

    def OnShow(self, ev):
        print "Canvas.OnShow"        
        if ev.IsShown():
            self.ctrl.DrawLines()

    def OnScroll(self, ev):
        pos = ev.GetPosition() * self.SCROLL_STEP
        if ev.GetOrientation() == wx.VERTICAL:
            self.ctrl.SetOffset(wx.Point(0, pos))
            pt = wx.Point(0, pos)
        elif ev.GetOrientation() == wx.HORIZONTAL:
            self.ctrl.SetOffset(wx.Point(pos, 0))
            pt = wx.Point(pos, 0)
