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
    VIEW_CHOICES = ("All", Content.CONCEPT_LBL_LONG, Content.ASSUMPTION_LBL_LONG, Content.RESEARCH_LBL_LONG, Content.FACT_LBL_LONG)

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size = wx.DefaultSize):
        super(Page, self).__init__(parent, id=id, pos=pos, size=size)

        # members
        self.resizing = False
        self.scale = 1.0
        self.content_size = wx.Size(size[0], size[1])

        # GUI
        self.ui_ready = False        
        self.InitUI()

        self.Bind(wx.EVT_SIZE, self.OnSize)


    ### Behavior functions

    def GetBoardBmp(self):
        # get the current board as a bitmap
        sz = self.board.content_sz

        if sz.width > -1 and sz.height > -1:
            bmp = wx.EmptyBitmap(sz.x, sz.y)
            dc = wx.MemoryDC()
            
            dc.SelectObject(bmp)
            dc.Blit(0, 0,                         # pos
                    sz.x, sz.y,                   # size
                    wx.ClientDC(self.board),      # src
                    0, 0)                         # offset
            bmp = dc.GetAsBitmap()
            dc.SelectObject(wx.NullBitmap)

            return bmp
        
        else:
            return None

    def SetupCanvas(self):
        """Setup the canvas background. Call before showing the Canvas."""
        # set sizes
        self.canvas.SetSize(self.board.GetSize())
        sz = self.board.content_sz
        self.canvas.SetVirtualSize(sz)
        self.canvas.content_sz = sz

        # pass the bitmap to canvas        
        self.canvas.SetBackground(self.GetBoardBmp())

                        
    ### Auxiliary functions
    
    def Dump(self):
        di = self.board.Dump()
        for id, card in di.iteritems():
            if "pos" in card.keys():
                card["pos"] = tuple([int(k / self.scale) for k in card["pos"]])
            if "width" in card.keys():
                card["width"] = int(card["width"] / self.scale)
            if "height" in card.keys():
                card["height"] = int(card["height"] / self.scale)
        return di
    
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

        # boxing
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
        # bd = CardView(self, size=size)

        # # UI setup
        vbox = self.GetSizer()
        vbox.Add(bd, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        
        # set members
        self.board = bd.board
        self.board.Show()        

    def InitCanvas(self, id=wx.ID_ANY, size=wx.DefaultSize):
        # make new
        cv = Canvas(self, size=size)
        
        # UI setup
        vbox = self.GetSizer()

        # we don't add it yet:
        # only board will be visible first
        # also see, OnToggling
        # vbox.Add(box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # Set members
        self.canvas = cv
        self.canvas.Hide()


    ### Callbacks

    def OnSize(self, ev):
        # important to skip the event for Sizers to work correctly
        ev.Skip()

    def OnToggle(self, ev):
        # EXTREMELY important!
        # remember that self.board is a BoardBase
        # but we added the parent Board object to our Sizer
        bd = self.board.GetParent()

        # now do the actual toggling replacing bd with self.canvas
        if self.board.IsShown():
            self.SetupCanvas()
            self.board.Hide()
            self.canvas.Show()
            
            val = self.GetSizer().Replace(bd, self.canvas)
        else:
            self.board.Show()
            self.canvas.Hide()
            val = self.GetSizer().Replace(self.canvas, bd)

        # never forget to Layout after Sizer operations            
        self.Layout()

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
        """Zoom is actually a change of scale of all relevant coordinates."""
        # save the scroll position and go to origin
        # so that all the cards' coordinates are absolute
        scroll_pos = self.board.GetViewStart()
        self.board.Scroll(0, 0)

        # scale cards
        for c in self.board.GetCards():
            rect = c.GetRect()
            # revert to original coordinates
            # and then calculate the actual new one
            left   = int((float(rect.left) / self.scale)   * new_scale)
            right  = int((float(rect.right) / self.scale)  * new_scale)
            top    = int((float(rect.top) / self.scale)    * new_scale)
            bottom = int((float(rect.bottom) / self.scale) * new_scale)
            c.SetRect(wx.Rect(left, top, right - left + 1, bottom - top + 1))

        # scale content size
        self.board.content_sz  = wx.Size(*[i / self.scale * new_scale for i in self.board.content_sz])
        self.board.SetVirtualSize(self.board.content_sz)

        # return to previous scroll position
        self.board.Scroll(*scroll_pos)

        self.board.scale = new_scale
        self.canvas.scale = new_scale
        self.scale = new_scale            

    def OnView(self, ev):
        s = ev.GetString()
        if s == "All":
            show = self.board.GetCards()
        else:
            show = self.board.GetContentsByKind(s)
            
        show = list(set(show) | set(self.board.GetHeaders()))
        hide = list(set(self.board.GetCards()) - set(show))
        for c in show: c.Show()
        for c in hide: c.Hide()
