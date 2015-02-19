#!/usr/bin/python
# -*- coding: utf-8 -*-

# canvas.py
# drawing area class for notes.py
# some code copied from wxPython demo code app doodle.py:
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
        dc = wx.MemoryDC(self.GetBitmap())
        dc.BeginDrawing()

        for colour, thickness, line in self.lines:
            pen = wx.Pen(colour, thickness, wx.SOLID)
            dc.SetPen(pen)
            for coords in line:
                x1, y1, x2, y2 = coords
                # draw the lines relative to the current offset
                dc.DrawLine(x1 - self.offset.x, y1 - self.offset.y,
                            x2 - self.offset.x, y2 - self.offset.y)
        
        dc.EndDrawing()
        self.SetBitmap(dc.GetAsBitmap())

        
    ### Auxiliary functions
    
    def InitBuffer(self):
        """Initialize the bitmap used for buffering the display."""
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
        self.curLine = []
        self.pos = ev.GetPosition()

    def OnLeftUp(self, ev):
        """Called when the left mouse button is released"""
        "CanvasBase.LeftUp"
        self.lines.append((self.colour, self.thickness, self.curLine))
        self.curLine = []
            
    def OnMotion(self, ev):
        if ev.Dragging() and ev.LeftIsDown():
            # BufferedDC will paint first over self.GetBitmap()
            # and then copy everything to ClientDC(self)
            dc = wx.BufferedDC(wx.ClientDC(self), self.GetBitmap())
            dc.BeginDrawing()
            
            dc.SetPen(self.pen)
            new_pos = ev.GetPosition()
            
            # store the lines with absolute coordinates
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
        self.Bind(wx.EVT_SHOW, self.OnShow)

        # finish up        
        self.ctrl = ctrl

                
    ### Behavior functions

    def SetOffset(self, pt):
        self.ctrl.SetOffset(pt)

    def GetOffset(self):
        return self.ctrl.GetOffset()

    def SetBackground(self, bmp):
        """Call to show the part that will be seen."""
        if bmp:
            self.ctrl.SetBitmap(bmp)
            self.FitToChildren()

    ### Auxiliary functions

    def Dump(self):
        """Unlike many other controls that dump a dict, we are dumping a list."""
        return self.ctrl.lines

    def Load(self, li):
        """Load from a list got from Canvas.Dump()"""
        self.ctrl.lines = li


    ### Callbacks

    def OnShow(self, ev):
        if ev.IsShown():
            self.ctrl.DrawLines()
