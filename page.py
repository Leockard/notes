#!/usr/bin/python

# page.py
# Page class: contains a Board and a canvas, plus functionality to switch between the two

import wx
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
                rect.width, rect.height,      # size
                wx.ClientDC(self.board),      # src
                rect.x, rect.y)               # offset
        dc.SelectObject(wx.NullBitmap)

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

            # self.view = wx.Choice(self, choices=["Normal", "Research"])
            self.view = wx.Choice(self, choices=Page.VIEW_CHOICES)
            self.view.SetSelection(0)
            self.view.Bind(wx.EVT_CHOICE, self.OnView)
                        
            self.zoom = wx.Choice(self, choices=["100%", "50%", "150%", "200%"])
            self.zoom.SetSelection(0)
            self.zoom.Bind(wx.EVT_CHOICE, self.OnZoom)
            
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

    def OnToggle(self, ev):
        if self.board.IsShown():
            self.SetupCanvas()
            self.board.Hide()
            self.canvas.Show()
        else:
            self.board.Show()
            self.canvas.Hide()
        
    def OnZoom(self, ev):
        scale = float(ev.GetString()[:-1]) / 100
        self.scale = scale
        self.Refresh()

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
