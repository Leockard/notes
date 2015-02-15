#!/usr/bin/python
# -*- coding: utf-8 -*-

# page.py
# Page class: contains a Board and a canvas, plus functionality to switch between the two

import wx
from utilities import AutoSize
from utilities import *
from board import *
from cardinspect import *
from canvas import Canvas
import wx.lib.agw.flatnotebook as fnb



######################
# Page class
######################

class Page(wx.Panel):
    CARD_PADDING = Board.CARD_PADDING
    PIXELS_PER_SCROLL = 20
    DEFAULT_SZ = (20, 20)
    ZOOM_CHOICES = ["50%", "100%", "150%", "200%"]
    VIEW_CH_DEF = "View"
    VIEW_CHOICES = ("All", KindButton.CONCEPT_LBL_LONG, KindButton.ASSUMPTION_LBL_LONG, KindButton.RESEARCH_LBL_LONG, KindButton.FACT_LBL_LONG)

    InspectEvent, EVT_PAGE_INSPECT = ne.NewEvent()
    CancelInspectEvent, EVT_PAGE_CANCEL_INSPECT = ne.NewEvent()
    DeleteEvent, EVT_PAGE_DEL_CARD = ne.NewEvent()

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size = wx.DefaultSize):
        super(Page, self).__init__(parent, id=id, pos=pos, size=size)

        # members
        self.contents = []
        self.sidebars = []
        self.inspecting = None
        self.scale = 1.0
        self.content_size = wx.Size(size[0], size[1])

        # GUI
        self.ui_ready = False        
        self.InitUI()
        self.InitAccels()

        # bindings
        self.Bind(wx.EVT_SIZE, self.OnSize)

        
    ### Behavior functions

    def GetCurrentContent(self):
        """Returns the class of content currently showing in conten_sizer."""
        return self.content_sizer.GetChildren()[0].GetWindow().__class__

    def ShowContent(self, ctrl):
        """Shows the ctrl inside content_sizer."""
        # remove all children and add only ctrl in the content area
        # ctrl should be a member of self.contents
        self.content_sizer.Clear()
        self.content_sizer.Add(ctrl, proportion=1, flag=wx.EXPAND, border=1)
        
        for c in self.contents: c.Hide()
        ctrl.Show()
        self.Layout()

    def InspectCards(self, cards):
        self.inspecting = cards
        self.inspect.SetLabel("Save and return")
        
        self.ShowContent(self.view_card)
        self.view_card.SetCards(cards)
        # SetCard copies its argument, so we have to use Get now
        self.view_card.GetCards()[0].content.SetFocus()

        # raise the event
        number = len(self.inspecting)
        title = ""
        if number == 1:
            title = self.inspecting[0].GetTitle()
        event = self.InspectEvent(id=wx.ID_ANY, number=number, title=title)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def SaveFromInspect(self):
        """
        If inspecting a card, copy the inspected card's state to the
        original. This includes caret position within the card, which
        effectively unselects the original card.
        """
        if self.GetCurrentContent() == CardInspect:
            # copy state
            for card, ins in self.view_card.GetPairs().iteritems():
                ins.SetTitle(card.GetTitle())
                ins.SetContent(card.GetContent())
                ins.SetKind(card.GetKind())
                ins.SetCaretPos(*card.GetCaretPos())

    def CancelInspect(self):
        # save modifications
        self.SaveFromInspect()

        # raise the event
        number = len(self.inspecting)
        if number == 1:
            title = self.inspecting[0].GetTitle()
        else:
            title = ""
        event = self.CancelInspectEvent(id=wx.ID_ANY, number=number, title=title)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        # clean up
        for c in self.inspecting:
            c.SetInspecting(False)
        self.inspecting = None
        self.inspect.SetLabel("Inspect")
        self.ShowBoard()

    def ShowBoard(self):
        # remember that self.board is a BoardBase
        # but we added the parent Board object to our Sizer
        self.ShowContent(self.board)

    def ShowCanvas(self):
        self.ShowContent(self.canvas)
        view = self.board.GetViewStart()
        self.canvas.Scroll(view)

    def ShowMinimap(self):
        """
        Show the minimap. Note that the minimap is not considered
        a "content".  Be sure to use this method and not inspect.Show(),
        as we also calculate the position before showing.
        """
        self.minimap.Show()

    def HideMinimap(self):
        """Hide the minimap. Note that the minimap is not considered a "content"."""
        self.minimap.Hide()

    def ToggleMinimap(self):
        mp = self.minimap
        if mp.IsShown(): self.HideMinimap()
        else:            self.ShowMinimap()

    def ShowToolBar(self, show=True):
        self.GetSizer().Show(self.GetToolBarSizer(), show=show, recursive=True)
        self.Layout()

    def GetToolBarSizer(self):
        return self.toolbar

    def GetBoardBmp(self):
        # get the current board as a bitmap
        sz = self.board.content_sz
        bmp = None

        if sz.width > -1 and sz.height > -1:
            bmp = wx.EmptyBitmap(sz.width, sz.height)
            dc = wx.MemoryDC()
            
            dc.SelectObject(bmp)
            dc.Blit(0, 0,                         # pos
                    sz.x, sz.y,                   # size
                    wx.ClientDC(self.board),      # src
                    0, 0)                         # offset
            bmp = dc.GetAsBitmap()
            dc.SelectObject(wx.NullBitmap)

        return bmp

    def SetupCanvas(self):
        """Setup the canvas background. Call before showing the Canvas."""
        # set sizes
        self.canvas.SetSize(self.board.GetSize())
        sz = self.board.content_sz
        self.canvas.SetVirtualSize(sz)
        self.canvas.content_sz = sz

        # pass the bitmap to canvas        
        self.canvas.SetBackground(self.GetBoardBmp())

    def ShowSidebar(self, show=True):
        self.sidebar_sizer.Clear()
        for c in self.sidebars: c.Hide()

        if show:
            self.sidebar_sizer.Add(self.tags_sb, proportion=1, flag=wx.EXPAND, border=1)            
            self.tags_sb.Show()
            
        self.Layout()

    def HideSidebar(self):
        self.ShowSidebar(False)

                        
    ### Auxiliary functions
    
    def Dump(self):
        # if we're inspecting, first save those changes and then dump
        if self.GetCurrentContent() == CardInspect:
            self.SaveFromInspect()
            
        di = self.board.Dump()
        for id, card in di.iteritems():
            if "pos" in card.keys():
                card["pos"] = tuple([int(k / self.scale) for k in card["pos"]])
            if "width" in card.keys():
                card["width"] = int(card["width"] / self.scale)
            if "height" in card.keys():
                card["height"] = int(card["height"] / self.scale)
        return di

    def Load(self, di):
        self.board.Load(di)

    def CleanUpUI(self):
        """Resets all control member values. Returns previous Board size."""
        sz = self.board.GetParent().GetSize()
        self.board.Hide() # important!
        self.board = None
        self.board_box = None
        self.bmp_ctrl = None
        self.bmp_box = None
        self.SetSizer(None)

        return sz
    
    def InitUI(self):
        # cleanup the previous UI, if any
        if self.ui_ready:
            sz = self.CleanUpUI()
        else:
            sz = self.DEFAULT_SZ

        # make new UI
        self.InitSizers()
        self.InitBoard(sz)
        self.InitCanvas()
        self.InitInspect()
        self.InitSidebar()
        # execute only the first time
        if not self.ui_ready: self.InitButtonBar()

        # content sizer takes all available space for content
        # always use the individual ShowXXX() controls
        self.ShowBoard()
        self.Layout()
        self.ui_ready = True

    def InitAccels(self):
        # we create ghost menus so that we can
        # bind its items to some accelerators
        accels = []
        ghost = wx.Menu()

        # show/hide sidebar        
        sbar = wx.MenuItem(ghost, wx.ID_ANY, "View sidebar", kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.OnToggleSidebar, sbar)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F9, sbar.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def InitSizers(self):
        # main sizer, with two main regions: data (dbox) and buttons (bbox)
        vbox = wx.BoxSizer(wx.VERTICAL)
        dbox = wx.BoxSizer(wx.HORIZONTAL)
        bbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(dbox, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        vbox.Add(bbox, proportion=0, flag=wx.ALL|wx.EXPAND, border=1)
        self.SetSizer(vbox)
        self.toolbar = bbox

        # the data sizer contains the sidebar (sbox) and the
        # contents sizer (cbox), which in turn contains the board/canvas/inspect views.
        # the contents sizer takes all available space for content
        # always use the individual ShowXXX() methods
        sbox = wx.BoxSizer(wx.VERTICAL)
        cbox = wx.BoxSizer(wx.HORIZONTAL)
        dbox.Add(sbox, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        dbox.Add(cbox, proportion=4, flag=wx.ALL|wx.EXPAND, border=1)        
        self.sidebar_sizer = sbox
        self.content_sizer = cbox

    def InitBoard(self, size=wx.DefaultSize):
        # make board
        bd = Board(self, size=size)
        
        # bindings
        bd.Bind(Card.EVT_CARD_REQUEST_INSPECT, self.OnRequestInspect)
        bd.Bind(bd.EVT_BOARD_DEL_CARD, self.OnDelete)

        # init also the inspection view
        ins = BoardInspect(self, bd)
        ins.Hide()
        self.minimap = ins

        # finish up
        self.board = bd
        bd.Hide()
        self.contents.append(bd)        

    def InitCanvas(self, size=wx.DefaultSize):
        cv = Canvas(self, size=size)
        self.canvas = cv
        self.canvas.Hide()
        self.contents.append(cv)

    def InitInspect(self, size=wx.DefaultSize):
        vw = CardInspect(self, size=size)
        self.view_card = vw
        self.view_card.Hide()
        self.contents.append(vw)

        # bindings
        vw.Bind(Card.EVT_CARD_CANCEL_INSPECT, self.OnCancelInspect)

    def InitSidebar(self, size=wx.DefaultSize):
        tg = TagsInspect(self, self.board)
        self.tags_sb = tg
        self.tags_sb.Hide()
        # doesn't go in contents since it can be shown
        # alongside board and inspect
        # self.contents.append(tg)
        self.sidebar_sizer.Add(tg, proportion=1, flag=wx.EXPAND)
        self.sidebars.append(tg)

    def InitButtonBar(self):
        # controls
        self.inspect = wx.Button(self, label = "Inspect")
        self.inspect.Bind(wx.EVT_BUTTON, self.OnInspect)

        self.toggle = wx.Button(self, label = "Toggle")
        self.toggle.Bind(wx.EVT_BUTTON, self.OnToggle)

        self.view = wx.Choice(self, choices=Page.VIEW_CHOICES)
        self.view.SetSelection(0)
        self.view.Bind(wx.EVT_CHOICE, self.OnView)
                    
        # chs = ["50%", "100%", "150%", "200%"]
        chs = self.ZOOM_CHOICES
        self.zoom = wx.ComboBox(self, value=chs[1], choices=chs, style=wx.TE_PROCESS_ENTER)
        self.zoom.SetSelection(1)
        self.zoom.Bind(wx.EVT_COMBOBOX, self.OnZoomCombo)
        self.zoom.Bind(wx.EVT_TEXT_ENTER, self.OnZoomEnter)
        zbox = wx.BoxSizer(wx.VERTICAL) # must be vertical so that ALIGN_RIGHT works
        zbox.Add(self.zoom, proportion=1, flag=wx.ALIGN_RIGHT, border=1)        

        # boxing
        # box = wx.BoxSizer(wx.HORIZONTAL)
        box = self.toolbar
        box.Add(self.inspect, proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)
        box.Add(self.toggle,  proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)
        box.Add(self.view,    proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)
        box.Add(zbox,      proportion=1, flag=wx.ALIGN_RIGHT|wx.EXPAND, border=1)        

        # self.GetSizer().Add(box, proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)
        # self.toolbar = box


    ### Callbacks

    def OnToggleSidebar(self, ev):
        self.ShowSidebar(not self.tags_sb.IsShown())

    def OnRequestInspect(self, ev):
        card = ev.GetEventObject()
        self.board.SelectCard(card, True)
        self.InspectCards([card])

    def OnCancelInspect(self, ev):
        self.CancelInspect()
        
    def OnDelete(self, ev):
        event = self.DeleteEvent(id=wx.ID_ANY, number=ev.number)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def OnSize(self, ev):
        # important to skip the event for Sizers to work correctly
        ev.Skip()

    def OnInspect(self, ev):
        if self.board.GetParent().IsShown():
            # inspect selected card
            sel = self.board.GetSelection()
            if len(sel) == 1:
                self.InspectCard(sel[0])
        elif self.view_card.IsShown():
            # save modifications
            self.SaveFromInspect()
            self.ShowBoard()

    def OnToggle(self, ev):
        # now do the actual toggling replacing bd with self.canvas
        if self.GetCurrentContent() == Board:
            self.SetupCanvas()
            self.ShowCanvas()
        else:
            self.ShowBoard()

        # never forget to Layout after Sizer operations            
        self.Layout()

    def GetScaleFromStr(self, s):
        """s should be a string of the type \d\d\d%?. Returns the float corresponding to the scale s."""
        scale = 1.0
        if isnumber(s):
            scale = float(s)/100
        elif isnumber(s[:-1]) and s[-1] == "%":
            scale = float(s[:-1])/100
        return scale
        
    def OnZoomCombo(self, ev):
        """Called when an item in the zoom combo box is selected."""
        self.Zoom(self.GetScaleFromStr(ev.GetString()))

    def OnZoomEnter(self, ev):
        self.Zoom(self.GetScaleFromStr(ev.GetString()))

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
            c.Scale(new_scale / self.scale)

        # scale content size
        self.board.content_sz  = wx.Size(*[i / self.scale * new_scale for i in self.board.content_sz])
        self.board.SetVirtualSize(self.board.content_sz)

        # return to previous scroll position
        self.board.Scroll(*scroll_pos)

        # make sure the combo text matches the new scale
        self.zoom.SetValue(str(int(new_scale * 100)) + "%")

        # setup members
        self.board.scale = new_scale
        self.canvas.scale = new_scale
        self.scale = new_scale            

    def ZoomIn(self):
        chs = self.ZOOM_CHOICES
        new = chs.index(self.zoom.GetValue()) - 1
        if new > -1 and new < len(chs):
            self.Zoom(self.GetScaleFromStr(chs[new]))

    def ZoomOut(self):
        chs = self.ZOOM_CHOICES
        new = chs.index(self.zoom.GetValue()) + 1
        if new > -1 and new < len(chs):
            self.Zoom(self.GetScaleFromStr(chs[new]))

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



######################
# Book class
######################            

class Book(wx.Notebook):
    NewPageEvent, EVT_BK_NEW_PAGE = ne.NewEvent()

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(Book, self).__init__(parent, pos=pos, size=size)
        self.InitMenu()
        self.ShowWelcomePage()        

        
    ### Behavior functions

    def NewPage(self):
        dlg = wx.TextEntryDialog(self, "New page title: ")
        if dlg.ShowModal() == wx.ID_OK:
            # erase the welcome page
            if self.GetPageCount() == 1 and self.GetPage(0).__class__ == WelcomePage:
                self.DeletePage(0)
            
            # create the new one
            pg = Page(self)
            self.AddPage(pg, dlg.GetValue(), select=True)
            pg.SetFocus()

    def AddPage(self, page, text, select=False, imageId=wx.Notebook.NO_IMAGE):
        """Call the usual wx.Notebook.AddPage, and also raise the EVT_NB_NEW_PAGE event."""
        super(Book, self).AddPage(page, text, select, imageId)
        
        event = self.NewPageEvent(id=wx.ID_ANY, page=page, title=text)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def ShowWelcomePage(self):
        # use the ancertor's method since we don't want
        # to raise EVT_NB_NEW_PAGE
        super(Book, self).AddPage(WelcomePage(self), WelcomePage.DEFAULT_TITLE, True)


    ### Auxiliary functions

    def InitMenu(self):
        # make menu items
        menu = wx.Menu()
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        
        # change page name
        name = wx.MenuItem(menu, wx.ID_ANY, "Change current page name")
        self.Bind(wx.EVT_MENU, self.OnNameChange, name)

        # page close
        close = wx.MenuItem(menu, wx.ID_CLOSE, "Close page")
        self.Bind(wx.EVT_MENU, self.OnClose, close)

        # setup (order matters)
        menu.AppendItem(name)
        # don't append close yet, check OnRightDown()
        # menu.AppendItem(close)

        # setup accelerators        
        accels = []
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("W"), close.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))
        self.close_item = close
        self.menu = menu
        
    def Dump(self):
        di = {}
        for i in range(self.GetPageCount()):
            pg = self.GetPage(i)
            di[self.GetPageText(i)] = pg.Dump()
        return di

    def Load(self, di):
        for title, page in di.iteritems():
            pg = Page(self)
            pg.Hide()        # hide while all data is loaded
            pg.Load(page)
            pg.Show()        # then show everything at the same time
            self.AddPage(pg, title, select=False)
        self.SetSelection(0)


    ### Callbacks

    def OnClose(self, ev):
        # don't do anything for the welcome page
        if self.GetPageCount() == 1 and self.GetPage(0).__class__ == WelcomePage:
            ev.Skip()
            return

        # for any other page, confirm closing
        cur = self.GetSelection()
        title = self.GetPageText(cur)
        dlg = wx.MessageDialog(self, "Are you sure you want to delete " + title + " page?", style=wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            self.DeletePage(cur)

    def OnNameChange(self, ev):
        dlg = wx.TextEntryDialog(self, "New page title: ")
        if dlg.ShowModal() == wx.ID_OK:
            cur = self.GetSelection()
            self.SetPageText(cur, dlg.GetValue())            
            
    def OnRightDown(self, ev):
        if not(self.GetPageCount() == 1 and self.GetPage(0).__class__ == WelcomePage):
            self.menu.AppendItem(self.close_item)
        self.menu_position = ev.GetPosition()
        self.PopupMenu(self.menu, ev.GetPosition())

        

######################
# WelcomePage class
######################            

class WelcomePage(wx.Panel):
    DEFAULT_TITLE = "Welcome"
    
    def __init__(self, parent):
        super(WelcomePage, self).__init__(parent)
        self.InitUI()
        

    ### Auxiliary functions

    def InitUI(self):
        # controls
        newb  = wx.Button(self, label="New book")
        loadb = wx.Button(self, label="Load book")

        # boxing
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)
        box.Add(newb, proportion=0)
        box.Add(loadb, proportion=0)
        
        # bindings
        newb.Bind(wx.EVT_BUTTON, self.OnNewBook)
        loadb.Bind(wx.EVT_BUTTON, self.OnLoadBook)


    ### Callbacks

    def OnNewBook(self, ev):
        self.GetParent().NewPage()

    def OnLoadBook(self, ev):
        self.GetTopLevelParent().OnOpen(None)
