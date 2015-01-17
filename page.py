#!/usr/bin/python

# page.py
# Page class: contains a Board and a canvas, plus functionality to switch between the two

import wx
from board import Board
from canvas import Canvas



######################
# Page class
######################

class Page(wx.Panel):
    DEFAULT_SZ = (20, 20)
    CARD_PADDING = Board.CARD_PADDING

    def __init__(self, parent, id = wx.ID_ANY, pos = (0, 0), size = DEFAULT_SZ):
        super(Page, self).__init__(parent, wx.ID_ANY, pos, size = size)

        self.ui_ready = False
        self.InitUI()

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
        # self.InitCanvas()

        # execute only the first time
        if not self.ui_ready:
            self.zoom = wx.Choice(self, wx.ID_ANY, choices=["100%", "50%", "150%", "200%"])
            self.zoom.Bind(wx.EVT_CHOICE, self.OnZoom)            
            self.toggle_but = wx.Button(self, label = "Toggle")
            self.toggle_but.Bind(wx.EVT_BUTTON, self.OnToggle)
            
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.toggle_but, proportion=1, flag=wx.LEFT|wx.EXPAND, border=1)
        hbox.Add(self.zoom,       proportion=1, flag=wx.LEFT|wx.EXPAND, border=1)
        vbox.Add(hbox, proportion=0, flag=wx.LEFT, border=1)

        self.ui_ready = True

    def InitBoard(self, size = DEFAULT_SZ):
        # make new
        bd = Board(self, size = size)
        # bd.SetBackgroundColour(Page.BACKGROUND_CL)

        # # UI setup
        vbox = self.GetSizer()
        if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
        bd_box = wx.BoxSizer(wx.HORIZONTAL)
        bd_box.Add(bd,   proportion=1, flag=wx.LEFT|wx.EXPAND, border=1)
        vbox.Add(bd_box, proportion=1, flag=wx.LEFT|wx.EXPAND, border=1)
        
        # set members
        self.board = bd.board
        self.board_box = bd_box
        
        self.board.Show()        

    # def InitCanvas(self):
    #     # make new
    #     ctrl = Canvas(self, wx.ID_ANY)
        
    #     # UI setup
    #     vbox = self.GetSizer()
    #     if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
    #     bmp_box = wx.BoxSizer(wx.HORIZONTAL)
    #     bmp_box.Add(ctrl, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

    #     # Set members
    #     self.bmp_ctrl = ctrl
    #     self.bmp_box = bmp_box
        
    #     self.bmp_ctrl.Hide()


    ### Callbacks

    def OnToggle(self, ev):
        print "Page.OnToggle"
        
    def OnZoom(self, ev):
        print "Page.OnZoom"
    
    def OnSize(self, ev):
        self.SetSize(ev.GetSize())
