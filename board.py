#!/usr/bin/python

# board.py
# note taking class for notes.py

import wx
from boardbase import BoardBase
from card import *


######################
# Board Class
######################

class Board(wx.Panel):
    CARD_PADDING = BoardBase.CARD_PADDING

    def __init__(self, parent, id = wx.ID_ANY, pos = (0, 0), size = (20, 20)):
        super(Board, self).__init__(parent, size=size)

        self.menu_position = (0, 0)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # UI steup
        # self.InitBar()
        self.InitBoard(pos=pos, size=size)
        self.InitMenu()

        # Bindings
        self.board.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)


    ### Auxiliary functions

    def InitBoard(self, pos, size):
        hbox = self.GetSizer()
        if not hbox: hbox = wx.BoxSizer(wx.HORIZONTAL)
            
        board = BoardBase(self, pos=pos, size=size)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(board, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        hbox.Add(vbox,  proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        
        # set members
        self.board = board

    def InitMenu(self):
        menu = wx.Menu()
        
        # insert actions
        cont_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Content")
        self.Bind(wx.EVT_MENU, self.OnInsertContent, cont_it)

        head_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Header")
        self.Bind(wx.EVT_MENU, self.OnInsertHeader, head_it)
        
        img_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Image")
        self.Bind(wx.EVT_MENU, self.OnInsertImg, img_it)
        
        # window actions
        min_it = wx.MenuItem(menu, wx.ID_ANY, "Minimize")
        self.Bind(wx.EVT_MENU, self.OnMinimize, min_it)
        
        close_it = wx.MenuItem(menu, wx.ID_ANY, "Close")
        self.Bind(wx.EVT_MENU, self.OnClose, close_it)

        menu.AppendItem(cont_it)
        menu.AppendItem(head_it)
        menu.AppendItem(img_it)
        menu.AppendSeparator()
        menu.AppendItem(min_it)
        menu.AppendItem(close_it)        

        self.menu = menu
        
    ### Callbacks

    def OnRightDown(self, ev):
        self.menu_position = ev.GetPosition()
        self.PopupMenu(self.menu, ev.GetPosition())

    def OnInsertContent(self, ev):
        self.board.PlaceNewCard("Content", pos=self.menu_position)

    def OnInsertHeader(self, ev):
        self.board.PlaceNewCard("Header", pos=self.menu_position)

    def OnInsertImg(self, ev):
        self.board.PlaceNewCard("Image", pos=self.menu_position)

    def OnMinimize(self, ev):
        pass

    def OnClose(self, ev):
        print "close"
