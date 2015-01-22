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

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # UI steup
        # self.InitBar()
        self.InitBoard(pos=pos, size=size)

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

    ### Callbacks

    def OnRightDown(self, ev):
        self.PopupMenu(BoardMenu(self.GetParent()), ev.GetPosition())

        

######################
# Auxiliary classes
######################            

class BoardMenu(wx.Menu):
    def __init__(self, parent):
        super(BoardMenu, self).__init__()

        min_item = wx.MenuItem(self, wx.NewId(), "Minimize")
        self.AppendItem(min_item)
        close_item = wx.MenuItem(self, wx.NewId(), "Close")
        self.AppendItem(close_item)

        self.Bind(wx.EVT_MENU, self.OnMinimize, min_item)
        self.Bind(wx.EVT_MENU, self.OnClose, close_item)


    ### Callbacks
    
    def OnMinimize(self, ev):
        self.GetParent().Iconize()

    def OnClose(self, ev):
        self.GetParent().Close()
