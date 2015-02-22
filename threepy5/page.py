# -*- coding: utf-8 -*-
"""
A `Page` is a window that holds both a `Board` and a `Canvas` to draw over that `Board`.
It also has facilities for closer inspection of individual objects.
"""

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
    """A `Page` holds all the main items to create, edit and visualize a collection of `Card`s.
    The window that takes center stage in a `Page` by default is a `Board`. Associated to it is
    a `Canvas`, and one can toggle between the two with a button in the tool bar. `Page` also
    handles the sidebars (`TagsInspect`), the "minimap" (`BoardInspect`), and the `Card` inspection
    view (`CardInspect`).

    The `Board`, `Canvas` and `CardInspect` (and possibly others) seemingly hold the same position
    in the `Page`. This is achieved by having a sizer for them (`content_sizer`) and constantly
    adding and deleting these objects from it. All the objects that can be shown in this main sizer
    are stored in the attribute `contents`.
    """
    
    CARD_PADDING = Board.CARD_PADDING
    PIXELS_PER_SCROLL = 20
    DEFAULT_SZ = (20, 20)
    ZOOM_CHOICES = ["50%", "100%", "150%", "200%"]
    VIEW_CH_DEF = "View"
    VIEW_CHOICES = ("All", KindButton.CONCEPT_LBL_LONG, KindButton.ASSUMPTION_LBL_LONG, KindButton.RESEARCH_LBL_LONG, KindButton.FACT_LBL_LONG)

    InspectEvent, EVT_PAGE_INSPECT = ne.NewEvent()
    CancelInspectEvent, EVT_PAGE_CANCEL_INSPECT = ne.NewEvent()
    DeleteEvent, EVT_PAGE_DEL_CARD = ne.NewEvent()

    def __init__(self, parent, pos=wx.DefaultPosition, size = wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Book`.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(Page, self).__init__(parent, pos=pos, size=size)

        # members
        self.contents = []
        self.sidebars = []
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
        """Get the class of the object currently residing in `content_sizer`.

        `returns: ` the __class__ attribute of the object.
        """
        return self.content_sizer.GetChildren()[0].GetWindow().__class__

    def ShowContent(self, ctrl):
        """Assings the object to show inside `content_sizer`.

        * `ctrl: ` any element of self.contents.
        """
        # remove all children and add only ctrl in the content area
        # ctrl should be a member of self.contents
        self.content_sizer.Clear()
        self.content_sizer.Add(ctrl, proportion=1, flag=wx.EXPAND, border=1)
        
        for c in self.contents: c.Hide()
        ctrl.Show()
        self.Layout()
        self.GetTopLevelParent().SetFocus()

    def InspectCards(self, cards):
        """Set up the children to show the `CardInspect` inspecting `cards`.
        Raises `Page.EVT_PAGE_INSPECT`.

        * `cards: ` a list of `Card`s.
        """
        toinspect = cards[:]

        # make sure to first SetCards() and then Deactivate()
        self.ShowContent(self.view_card)
        self.view_card.SetCards(toinspect)

        # clean up
        self.board.UnselectAll()
        self.board.selec.Deactivate()
        self.inspect.SetLabel("Save and return")
        
        # raise the event
        number = len(toinspect)
        title = ""
        if number == 1:
            title = toinspect[0].GetTitle()
        event = self.InspectEvent(id=wx.ID_ANY, number=number, title=title)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def CancelInspect(self):
        """Cleans up after a `Card` inspection. Raises `Page.EVT_PAGE_CANCEL_INSPECT`."""
        # raise the event
        cards = self.view_card.GetCards()
        number = len(cards)
        if number == 1:
            title = cards[0].GetTitle()
        else:
            title = ""
        event = self.CancelInspectEvent(id=wx.ID_ANY, number=number, title=title)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        # clean up
        self.ShowBoard()
        self.inspect.SetLabel("Inspect")

    def ShowBoard(self):
        """Show the `Board` in the `content_sizer`."""
        # remember that self.board is a Board
        # but we added the parent Board object to our Sizer
        self.ShowContent(self.board)
        cards = self.board.GetCards()
        if cards:
            cards[0].SetFocus()

    def ShowCanvas(self):
        """Show the `Canvas` in the `content_sizer`."""
        self.ShowContent(self.canvas)
        view = self.board.GetViewStart()
        self.canvas.Scroll(view)

    def ShowMinimap(self):
        """Show the `BoardInspect`. Note that the minimap is not in `self.contents`, so it
        isn't added to `content_sizer`. Be sure to use this method and not self.minimap.Show(),
        as we also calculate the position before showing.
        """
        self.minimap.Show()

    def HideMinimap(self):
        """Hide the `BoardInspect` minimap. Note that the minimap is not in `self.contents`."""
        self.minimap.Hide()

    def ToggleMinimap(self):
        """Hide/Show the `BoardInspect` minimap. Note that the minimap is not in `self.contents`."""
        mp = self.minimap
        if mp.IsShown(): self.HideMinimap()
        else:            self.ShowMinimap()

    def ShowToolBar(self, show=True):
        """Show the button bar at the bottom of the `Page`."""
        self.GetSizer().Show(self.GetToolBarSizer(), show=show, recursive=True)
        self.Layout()

    def GetToolBarSizer(self):
        """Get the button bar sizer.

        `returns: ` a `wx.Sizer`.
        """
        return self.toolbar

    def GetBoardBmp(self):
        """Get the currently visible part of the `Board` as a wx.Bitmap.

        `returns: ` a `wx.Bitmap`.
        """
        # get the current board as a bitmap
        sz = self.board.GetClientSize()
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
        """Setup the `Canvas` background. Always call before showing the `Canvas`."""
        # set sizes
        self.canvas.SetSize(self.board.GetSize())
        sz = self.board.content_sz
        self.canvas.SetVirtualSize(sz)
        self.canvas.content_sz = sz

        # pass the bitmap to canvas
        self.canvas.SetOffset(self.board.GetViewStartPixels())
        self.canvas.SetBackground(self.GetBoardBmp())

    def ShowSidebar(self, show=True):
        """Show/Hide the sidebar.

        * `show: ` if `False`, hide the sidebar.
        """
        self.sidebar_sizer.Clear()
        for c in self.sidebars: c.Hide()

        if show:
            self.sidebar_sizer.Add(self.tags_sb, proportion=1, flag=wx.EXPAND, border=1)            
            self.tags_sb.Show()
            
        self.Layout()

    def HideSidebar(self):
        """Same as ShowSidebar(False)."""
        self.ShowSidebar(False)

                        
    ### Auxiliary functions
    
    def Dump(self):
        """Returns a `dict` with all the info contained in this `Page`.

        `returns: ` a `dict` of the form {"board": Board.Dump(), "canvas": Canvas.Dump()}.
        """
        # get the board dump dict and process it
        board_di = self.board.Dump()
        
        # if we're inspecting, restore the cards, dump and then return to the inspection view
        inspecting = []
        if self.GetCurrentContent() == CardInspect:
            inspecting = self.view_card.GetCards()
            self.view_card.Restore()

        # dump the real coordinates
        for id, card in board_di.iteritems():
            if "pos" in card.keys():
                card["pos"] = tuple([int(k / self.scale) for k in card["pos"]])
            if "width" in card.keys():
                card["width"] = int(card["width"] / self.scale)
            if "height" in card.keys():
                card["height"] = int(card["height"] / self.scale)

        # restore inspect view
        if inspecting:
            self.InspectCards(inspecting)

        # get the canvas dump dict
        canvas_di = self.canvas.Dump()

        # join the two
        di = {"board": board_di, "canvas": canvas_di}

        return di

    def Load(self, di):
        """Read a `dict` and load all its data.

        * `di: ` a `dict` in the format returned by `Dump`.
        """
        self.board.Load(di["board"])
        self.canvas.Load(di["canvas"])

    def CleanUpUI(self):
        """Helper function for `InitUI`. Resets all control members.

        `returns: ` the previous `Board` size.
        """
        sz = self.board.GetParent().GetSize()
        self.board.Hide() # important!
        self.board = None
        self.board_box = None
        self.bmp_ctrl = None
        self.bmp_box = None
        self.SetSizer(None)

        return sz
    
    def InitUI(self):
        """Initialize this `Page`'s GUI and controls."""
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
        """Initializes the `wx.AcceleratorTable`."""
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
        """Initializes `sidebar_sizer` and `content_sizer`."""
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
        """Initializes `Board`."""
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
        """Initializes `Canvas`."""
        cv = Canvas(self, size=size)
        self.canvas = cv
        self.canvas.Hide()
        self.contents.append(cv)

    def InitInspect(self, size=wx.DefaultSize):
        """Initializes `CardInspect`."""
        vw = CardInspect(self, size=size)
        self.view_card = vw
        self.view_card.Hide()
        self.contents.append(vw)

        # bindings
        vw.Bind(Card.EVT_CARD_CANCEL_INSPECT, self.OnCancelInspect)

    def InitSidebar(self, size=wx.DefaultSize):
        """Initializes `TagsInspect`."""
        tg = TagsInspect(self, self.board)
        self.tags_sb = tg
        self.tags_sb.Hide()
        # doesn't go in contents since it can be shown
        # alongside board and inspect
        # self.contents.append(tg)
        self.sidebar_sizer.Add(tg, proportion=1, flag=wx.EXPAND)
        self.sidebars.append(tg)

    def InitButtonBar(self):
        """Initializes the tool bar."""
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
        """Listens to `F9`."""
        self.ShowSidebar(not self.tags_sb.IsShown())

    def OnRequestInspect(self, ev):
        """Listens to `Card.EVT_CARD_REQUEST_INSPECT` from `Board`."""
        card = ev.GetEventObject()
        self.board.SelectCard(card, True)
        self.InspectCards([card])

    def OnCancelInspect(self, ev):
        """Listens to `Card.EVT_CARD_CANCEL_INSPECT` from `Card`s that are being inspected."""
        self.CancelInspect()
        ev.GetEventObject().SetFocus()
        
    def OnDelete(self, ev):
        """Listens to `Board.EVT_BOARD_DEL_CARD`."""
        event = self.DeleteEvent(id=wx.ID_ANY, number=ev.number)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def OnSize(self, ev):
        """Listens to `wx.EVT_SIZE`."""
        # important to skip the event for Sizers to work correctly
        ev.Skip()

    def OnInspect(self, ev):
        """Listens to `wx.EVT_BUTTON` from the inspect button in the button bar."""
        content = self.GetCurrentContent()
        if content == Board:
            sel = self.board.GetSelection()
            if sel:
                self.InspectCards(sel)
        elif content == CardInspect:
            # don't call self.CancelInspect()
            # instead, tell the inspected cards that they should request
            # a cancelation
            self.view_card.GetCards()[-1].CancelInspect()

    def OnToggle(self, ev):
        """Listents to `wx.EVT_BUTTON` from the `Board`/`Canvas` button in the button bar"""
        if self.GetCurrentContent() == Board:
            self.SetupCanvas()
            self.ShowCanvas()
        else:
            self.ShowBoard()

        # never forget to Layout after Sizer operations            
        self.Layout()

    def GetScaleFromStr(self, s):
        """Parses a string to extract a scale.
        
        * `s: ` is be a string of the type "\d\d\d?%?" (eg, "100%" or "75").
        
        `returns: `the float corresponding to the scale.
        """
        scale = 1.0
        if isnumber(s):
            scale = float(s)/100
        elif isnumber(s[:-1]) and s[-1] == "%":
            scale = float(s[:-1])/100
        return scale
        
    def OnZoomCombo(self, ev):
        """Listens to `wx.EVT_COMBOBOX` from the zoom combo box in the button bar."""
        self.Zoom(self.GetScaleFromStr(ev.GetString()))

    def OnZoomEnter(self, ev):
        """Listens to `wx.EVT_TEXT_ENTER` from the zoom combo box in the button bar."""
        self.Zoom(self.GetScaleFromStr(ev.GetString()))

    def Zoom(self, new_scale):
        """Zoom in or out the current `Board`. Effectively changes the scale of all
        relevant coordinates.

        * `new_scale: ` the new scale for all `Card`s.
        """
        # save the scroll position and go to origin
        # so that all the cards' coordinates are absolute
        scroll_pos = self.board.GetViewStart()
        self.board.Scroll(0, 0)

        # scale cards
        for c in self.board.GetCards():
            c.Stretch(new_scale / self.scale)

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
        """Zoom in to the next greater scale in `self.ZOOM_CHOICES`."""
        chs = self.ZOOM_CHOICES
        new = chs.index(self.zoom.GetValue()) - 1
        if new > -1 and new < len(chs):
            self.Zoom(self.GetScaleFromStr(chs[new]))

    def ZoomOut(self):
        """Zoom out to the next smaller scale in `self.ZOOM_CHOICES`."""
        chs = self.ZOOM_CHOICES
        new = chs.index(self.zoom.GetValue()) + 1
        if new > -1 and new < len(chs):
            self.Zoom(self.GetScaleFromStr(chs[new]))

    def OnView(self, ev):
        """Listens to `wx.EVT_CHOICE` from the view contents by kind combo box in the button bar."""
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
    """
    A `Book` holds various `Page`s, and is the equivalent of a file at
    application level: every `Book` is stored in one file and every file loads
    one `Book`.
    """

    NewPageEvent, EVT_BK_NEW_PAGE = ne.NewEvent()

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `ThreePyFiveFrame`.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(Book, self).__init__(parent, pos=pos, size=size)
        self.InitMenu()

        
    ### Behavior functions

    def NewPage(self):
        """Creates a new `Page`, by asking the user for the `Page` name.

        `returns: ` `True` if a new `Page` was succesfully created.
        """
        dlg = wx.TextEntryDialog(self, "New page title: ")
        if dlg.ShowModal() == wx.ID_OK:
            pg = Page(self)
            self.AddPage(pg, dlg.GetValue(), select=True)
            pg.SetFocus()
            return True
        else:
            return False

    def AddPage(self, page, text, select=False, imageId=wx.Notebook.NO_IMAGE):
        """Overridden from `wx.Book`. Raises the `Bool.EVT_NB_NEW_PAGE` event."""
        super(Book, self).AddPage(page, text, select, imageId)
        
        event = self.NewPageEvent(id=wx.ID_ANY, page=page, title=text)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        
    ### Auxiliary functions

    def InitMenu(self):
        """Initialize this `Book`'s context menu."""
        # make menu items
        menu = wx.Menu()
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        
        # change page name
        name = wx.MenuItem(menu, wx.ID_ANY, "Change current page name")
        self.Bind(wx.EVT_MENU, self.OnNameChange, name)

        # page close
        close = wx.MenuItem(menu, wx.ID_CLOSE, "Close page")
        self.Bind(wx.EVT_MENU, self.OnClose, close)

        # page ordering
        pg_forward = wx.MenuItem(menu, wx.ID_ANY, "Move page forward")
        self.Bind(wx.EVT_MENU, self.OnPageForward, pg_forward)

        # setup (order matters)
        menu.AppendItem(name)
        menu.AppendItem(pg_forward)
        menu.AppendItem(close)

        # setup accelerators        
        accels = []
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("W"), close.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))
        self.close_item = close
        self.menu = menu
        
    def Dump(self):
        """Return a `dict` holding all this `Book`'s data.
        
        `returns: ` a `dict` of the form `{"page title 1": data1, "page title 2": data2, ...}`,
        where `data*` are the objects returned by each `Page`'s `Dump`.
        """
        di = {}
        for i in range(self.GetPageCount()):
            pg = self.GetPage(i)
            di[self.GetPageText(i)] = pg.Dump()
        return di

    def Load(self, di):
        """Read data from a `dict` and load it into this `Book` for displaying.

        * `di: ` must be a `dict`in the format returned by `Dump`.
        """
        for title, page in di.iteritems():
            pg = Page(self)
            pg.Hide()        # hide while all data is loaded
            pg.Load(page)
            pg.Show()        # then show everything at the same time
            self.AddPage(pg, title, select=False)
        self.SetSelection(0)


    ### Callbacks

    def OnPageForward(self, ev):
        """Listens to `wx.EVT_MENU` from "Move page forward" from the context menu."""
        # if we're already on the last page, don't do anything
        index = self.GetSelection()
        if index == self.GetPageCount()-1:
            return
        
        pg = self.GetCurrentPage()
        print pg
        self.DeletePage(index)
        print pg
        self.InsertPage(index + 1, pg, self.GetPageText(index), select=True)
        print "OnPageForward: ", pg

    def OnClose(self, ev):
        """Listens to `wx.EVT_MENU` from "Close page" from the context menu."""
        cur = self.GetSelection()
        title = self.GetPageText(cur)
        dlg = wx.MessageDialog(self, "Are you sure you want to delete " + title + " page?", style=wx.YES_NO)
        if dlg.ShowModal() == wx.ID_YES:
            self.DeletePage(cur)

    def OnNameChange(self, ev):
        """Listens to `wx.EVT_MENU` from "Change current page name" from the context menu."""
        dlg = wx.TextEntryDialog(self, "New page title: ")
        if dlg.ShowModal() == wx.ID_OK:
            cur = self.GetSelection()
            self.SetPageText(cur, dlg.GetValue())            
            
    def OnRightDown(self, ev):
        """Listens to `wx.wx.EVT_RIGHT_DOWN`."""
        self.menu_position = ev.GetPosition()
        self.PopupMenu(self.menu, ev.GetPosition())


        
###########################
# pdoc documentation setup
###########################
# __pdoc__ is the special variable from the automatic
# documentation generator pdoc.
# By setting pdoc[class.method] to None, we are telling
# pdoc to not generate documentation for said method.
__pdoc__ = {}
__pdoc__["field"] = None

# Since we only want to generate documentation for our own
# mehods, and not the ones coming from the base classes,
# we first set to None every method in the base class.
for field in dir(wx.Panel):
    __pdoc__['Page.%s' % field] = None
for field in dir(wx.Notebook):
    __pdoc__['Book.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in Page.__dict__.keys():
    if 'Page.%s' % field in __pdoc__.keys():
        del __pdoc__['Page.%s' % field]
for field in Book.__dict__.keys():
    if 'Book.%s' % field in __pdoc__.keys():
        del __pdoc__['Book.%s' % field]
        
