#!/usr/bin/python

# page.py
# Page class: contains a Board and a canvas, plus functionality to switch between the two

import wx
from utilities import AutoSize
from utilities import isnumber
from board import *
from canvas import Canvas



######################
# Page class
######################

class Page(wx.Panel):
    CARD_PADDING = Board.CARD_PADDING
    PIXELS_PER_SCROLL = 20

    VIEW_CH_DEF = "View"
    VIEW_CH_C = "Concepts"
    VIEW_CH_A = "Assumptions"
    VIEW_CH_R = "Research"
    VIEW_CH_F = "Facts"
    VIEW_CHOICES = (VIEW_CH_DEF, VIEW_CH_C, VIEW_CH_A, VIEW_CH_R, VIEW_CH_F)

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size = wx.DefaultSize):
        super(Page, self).__init__(parent, id=id, pos=pos, size=size)

        self.resizing = False
        self.scale = 1.0
        self.content_size = wx.Size(size[0], size[1])
        self.ui_ready = False
        self.InitUI()

        self.Bind(wx.EVT_SIZE, self.OnSize)


    ### Behavior functions


    ### Behavior functions

    def SetupCanvas(self):
        """Setsup the canvas background. Call before showing the Canvas."""
        rect = self.board.GetRect()                
        self.canvas.SetSize((rect.width, rect.height))

        bmp = wx.EmptyBitmap(rect.width, rect.height)
        dc = wx.MemoryDC()
        dc.SelectObject(bmp)
        
        # off = self.board.GetClientAreaOrigin()
        dc.Blit(0, 0,                         # pos
                sz.width, sz.height,          # size
                wx.ClientDC(self.board),      # src
                0, 0)                         # offset
        dc.SelectObject(wx.NullBitmap)

        # let the canvas handle its own scrollbars
        self.canvas.FitToChildren()

        self.canvas.buffer = bmp
        self.canvas.Refresh()

                
    ### Auxiliary functions

    def InitUI(self):
        sz = (20, 20)
        # cleanup the previous UI, if any
        if self.ui_ready:
            sz = self.board.GetSize()
            self.board.Hide() # important!
            self.board = None
            self.board_box = None
            self.bmp_ctrl = None
            self.bmp_box = None
            self.SetSizer(None)

        # make new UI
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)
        self.InitBoard(sz)
        self.InitCanvas()

        # execute only the first time
        if not self.ui_ready:
            self.toggle = wx.Button(self, label = "Toggle")
            self.toggle.Bind(wx.EVT_BUTTON, self.OnToggle)

            self.view = wx.Choice(self, choices=Page.VIEW_CHOICES)
            self.view.SetSelection(0)
            self.view.Bind(wx.EVT_CHOICE, self.OnView)
                        
            chs = ["50%", "100%", "150%", "200%"]
            self.zoom = wx.ComboBox(self, value=chs[1], choices=chs, style=wx.TE_PROCESS_ENTER)
            self.zoom.SetSelection(1)
            self.zoom.Bind(wx.EVT_COMBOBOX, self.OnZoomCombo)
            self.zoom.Bind(wx.EVT_TEXT_ENTER, self.OnZoomEnter)
            
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.toggle, proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)
        hbox.Add(self.view,   proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)

        zbox = wx.BoxSizer(wx.VERTICAL) # must be vertical so that ALIGN_RIGHT works
        zbox.Add(self.zoom, proportion=1, flag=wx.ALIGN_RIGHT, border=1)
        hbox.Add(zbox,      proportion=1, flag=wx.ALIGN_RIGHT|wx.EXPAND, border=1)
        
        vbox.Add(hbox, proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)

        self.ui_ready = True

    def InitBoard(self, id=wx.ID_ANY, size=wx.DefaultSize):
        # make new
        bd = Board(self, size=size)

        # # UI setup
        vbox = self.GetSizer()
        if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(bd,   proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        vbox.Add(box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        
        # set members
        self.board = bd.board
        self.board.Show()        

    def InitCanvas(self, id=wx.ID_ANY, size=wx.DefaultSize):
        # make new
        ctrl = Canvas(self, size=size)
        
        # UI setup
        vbox = self.GetSizer()
        if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(ctrl, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        vbox.Add(box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # Set members
        self.canvas = ctrl
        self.canvas.Hide()


    ### Callbacks

    def OnSize(self, ev):
        self.board.UpdateContentSize(ev.GetSize())
        self.canvas.UpdateContentSize(ev.GetSize())
        # important to skip the event for Sizers to work correctly
        ev.Skip()

    def OnToggle(self, ev):
        if self.board.IsShown():
            self.SetupCanvas()
            self.board.Hide()
            self.canvas.Show()
        else:
            self.board.Show()
            self.canvas.Hide()

    def OnZoomCombo(self, ev):
        """Called when an item in the zoom combo box is selected."""
        self.Zoom(float(ev.GetString()[:-1])/100)

    def OnZoomEnter(self, ev):
        s = ev.GetString()
        if isnumber(s):
            self.Zoom(float(s)/100)
        elif isnumber(s[:-1]) and s[-1] == "%":
            self.Zoom(float(s[:-1])/100)
        
    def Zoom(self, new_scale):
        for c in self.board.GetCards():
            rect = c.GetRect()
            # revert to original coordinates
            # and then calculate the actual new one
            left = (rect.left / self.scale) * new_scale
            right = (rect.right / self.scale) * new_scale
            top = (rect.top / self.scale) * new_scale
            bottom = (rect.bottom / self.scale) * new_scale
            c.SetRect(wx.Rect(left, top, right - left, bottom - top))
        self.scale = new_scale
        self.board.scale = new_scale
        self.canvas.scale = new_scale

    def OnView(self, ev):
        s = ev.GetString()
        if   s == Page.VIEW_CH_C: show = self.board.GetContentsByKind(Content.CONCEPT_LBL)
        elif s == Page.VIEW_CH_A: show = self.board.GetContentsByKind(Content.ASSUMPTION_LBL)
        elif s == Page.VIEW_CH_R: show = self.board.GetContentsByKind(Content.RESEARCH_LBL)
        elif s == Page.VIEW_CH_F: show = self.board.GetContentsByKind(Content.FACT_LBL)
        else: show = self.board.GetCards()
            
        show = list(set(show) | set(self.board.GetHeaders()))
        hide = list(set(self.board.GetCards()) - set(show))
        for c in show: c.Show()
        for c in hide: c.Hide()
