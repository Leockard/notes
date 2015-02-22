# -*- coding: utf-8 -*-
"""
Main frame object for note taking application `threepy5`.
"""

import wx
import os
import pickle
from page import *
from card import *
from canvas import *
from board import *
from cardinspect import *
import wx.richtext as rt
import json
import re


class ThreePyFiveFrame(wx.Frame):
    """
    A `ThreePyFiveFrame` holds a `WelcomePage` at startup, until a `Book` is loaded.
    """
    
    DEFAULT_SZ = (800, 600)
    DEFAULT_PAGE_NAME = "Untitled Notes"
    CLEAN_STATUS_BAR_AFTER_MS = 5000

    def __init__(self, parent, title="3py5", size=DEFAULT_SZ, style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE):
        """Constructor.

        * `parent: ` the parent `Book`.
        * `title: ` the title of this `ThreePyFiveFrame`.
        * `size: ` by default, is `ThreePyFiveFrame.DEFAULT_SZ`.
        * `style: ` by default, is `wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE`.
        """
        super(ThreePyFiveFrame, self).__init__(parent, title=title, size=size, style=style)

        self.SetTitle(self.DEFAULT_PAGE_NAME)
        self.cur_file = ""
        self.search_find = []
        self.search_str = ""
        self.notebook = None
        self.welcome = None
        self.search_head = None    # contains the current search index
                                   # when not searching, set to None
        self.ui_ready = False
        self.InitUI()              # sets up the sizer and the buttons' bindings

        # Done.
        self.Show()

        
    ### Behavior Functions

    def GetCurrentPage(self):
        """Get the `Page` currently selected in the loaded `Book`.

        `returns: ` a `Page` or `None`.
        """
        result = None
        if self.notebook:
            result = self.notebook.GetCurrentPage()
        return result

    def GetCurrentBoard(self):
        """Get the `Board` from the `Page` currently selected.

        `returns: ` a `Board`, or `None`."""
        result = None
        pg = self.GetCurrentPage()
        if pg and hasattr(pg, "board"):
            result = pg.board
        return result

    def Search(self, ev):
        """Listens to `wx.EVT_TEXT` in the search bar. Search the current text in
        the search bar in all of the Cards' texts. Cycle through finds
        with (SHUFT+)CTRL+G.
        """
        # search string in lower case
        s = self.search_ctrl.GetValue().lower()
        
        # if we were already searching, clear up highlighting
        if self.search_find:
            for c, i in self.search_find:
                c.SetStyle(i, i + len(self.search_str), c.GetDefaultStyle())

        # if no search string, reset variables and quit
        if not s:
            self.search_ctrl.SetBackgroundColour(wx.WHITE)
            self.search_find = []
            self.search_str = ""
            self.search_head = None
            return
                
        # where are we searching?
        cards = []
        content = self.GetCurrentPage().GetCurrentContent()
        if content == Board:
            cards = self.GetCurrentBoard().GetCards()
        elif content == CardInspect:
            cards = self.GetCurrentPage().view_card.GetCards()

        # gather all (lower case) values in which to search
        # including the control they appear in
        txt_ctrls = []
        for c in cards:
            if isinstance(c, Content):
                txt_ctrls.append((c.GetTitle().lower(),   c.title))
                txt_ctrls.append((c.GetContent().lower(), c.content))
            if isinstance(c, Header):
                txt_ctrls.append((c.GetHeader().lower(),  c.header))

        # do the actual searching
        finds = []
        for txt, ctrl in txt_ctrls:
            pos = [m.start() for m in re.finditer(s, txt)]
            for p in pos:
                finds.append((ctrl, p))

        # if success: highlight and setup vars for cycling
        if finds:
            self.search_ctrl.SetBackgroundColour(wx.YELLOW)
            for c, i in finds:
                c.SetStyle(i, i + len(s), wx.TextAttr(wx.NullColour, wx.YELLOW))

            self.search_find = finds
            self.search_str = s
            self.search_head = 0    # when done, set to None

        # if not found: make sure variables are setup correctly too
        else:
            self.search_ctrl.SetBackgroundColour(wx.RED)
            self.search_find = []
            self.search_str = ""
            self.search_head = None

    def OnCancelSearch(self, ev):
        """Listens to `wx.EVT_SEARCHCTRL_CANCEL_BTN` from the search bar."""
        self.CancelSearch()

    def CancelSearch(self):
        """Cancel the current search. Restores highliting  and hides the search bar."""
        if self.search_find:
            # erase all highlight
            for c, i in self.search_find:
                s = self.search_ctrl.GetValue()
                c.SetStyle(i, i + len(s), c.GetDefaultStyle())

            # set focus on last result
            ctrl = self.search_find[self.search_head - 1][0]
            pos = self.search_find[self.search_head - 1][1]
            ctrl.SetFocus()
            ctrl.SetSelection(pos, pos + len(self.search_str))

            # clear up variables
            self.search_find = []
            self.search_head = None
            self.search_str = ""
        else:
            # return the focus to the last selected card or to the board
            bd = self.GetCurrentBoard()
            sel = bd.GetSelection()
            if sel:
                sel[-1].SetFocus()
            else:
                bd.SetFocusIgnoringChildren()

        self.search_ctrl.Hide()

    def PrevSearchResult(self):
        """Highlights the previous search result."""
        if self.search_head != None:
            old = i = self.search_head
            new = i - 1
            if new < 0: new = len(self.search_find) - 1
            self.JumpSearchResults(old, new)
            self.search_head = new

    def NextSearchResult(self):
        """Highlights the next search result with a strong highlight and scrolls it into view."""
        if self.search_head != None:
            old = i = self.search_head
            new = i + 1
            if new >= len(self.search_find): new = 0
            self.JumpSearchResults(old, new)
            self.search_head = new

    def JumpSearchResults(self, old, new):
        """Unhighlights the `old` search result and highlights the `new` one. Don't use this
        method directly, instead use `PrevSearchResult` and `NextSearchResult`.

        * `old: ` a valid index in the internal search result list (`self.search_find`).
        * `new: ` idem.
        """
        s = self.search_ctrl.GetValue()

        # erase strong highlight on previous search find
        # even if this is the first one, nothing bad will happen
        # we'd just painting yellow again over the last one
        ctrl = self.search_find[old][0]
        pos = self.search_find[old][1]
        ctrl.SetStyle(pos, pos + len(s), wx.TextAttr(None, wx.YELLOW))

        # selection and strong hightlight on current search find
        ctrl = self.search_find[new][0]
        pos = self.search_find[new][1]
        ctrl.SetStyle(pos, pos + len(s), wx.TextAttr(None, wx.RED))

        # make sure the find is visible            
        card = GetCardAncestor(ctrl)
        if card:
            self.GetCurrentBoard().ScrollToCard(card)
            if isinstance(card, Content):
                if card.IsCollapsed():
                    card.Uncollapse()
                card.ScrollToChar(pos)

                                
    ### Auxiliary functions

    def InitMenuBar(self):
        """Initialize the menu bar and also sets the `wx.AcceleratorTable`."""
        bar = wx.MenuBar()

        ## file menu
        file_menu = wx.Menu()
        newt_it = wx.MenuItem(file_menu, wx.ID_NEW,  "&New")
        open_it = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open")
        save_it = wx.MenuItem(file_menu, wx.ID_SAVE, "&Save")
        quit_it = wx.MenuItem(file_menu, wx.ID_EXIT, "&Quit")

        file_menu.AppendItem(newt_it)
        file_menu.AppendItem(open_it)
        file_menu.AppendItem(save_it)
        file_menu.AppendSeparator()
        file_menu.AppendItem(quit_it)

        ## edit menu
        edit_menu = wx.Menu()
        copy_it = wx.MenuItem(edit_menu, wx.ID_COPY, "Copy")
        past_it = wx.MenuItem(edit_menu, wx.ID_PASTE, "Paste")
        delt_it = wx.MenuItem(edit_menu, wx.ID_DELETE, "Delete")

        edit_menu.AppendItem(copy_it)
        edit_menu.AppendItem(past_it)
        edit_menu.AppendItem(delt_it)

        ## insert menu
        insert_menu = wx.Menu()
        contr_it = wx.MenuItem(insert_menu, wx.ID_ANY, "New Card: Right")
        contb_it = wx.MenuItem(insert_menu, wx.ID_ANY, "New Card: Below")
        headr_it = wx.MenuItem(insert_menu, wx.ID_ANY, "New Header: Right")
        headb_it = wx.MenuItem(insert_menu, wx.ID_ANY, "New Header: Below")
        img_it   = wx.MenuItem(insert_menu, wx.ID_ANY, "Insert image")

        insert_menu.AppendItem(contr_it)
        insert_menu.AppendItem(contb_it)
        insert_menu.AppendItem(headr_it)
        insert_menu.AppendItem(headb_it)        
        insert_menu.AppendItem(img_it)
        
        ## selection menu
        selection_menu = wx.Menu()
        sela_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Select All")
        selc_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Select Current")
        seln_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Select None")
        harr_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Arrange &Horizontally")
        varr_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Arrange &Vertically")
        group_it = wx.MenuItem(selection_menu, wx.ID_ANY, "Group selection")
                
        selection_menu.AppendItem(sela_it)
        selection_menu.AppendItem(selc_it)
        selection_menu.AppendItem(seln_it)
        selection_menu.AppendItem(harr_it)
        selection_menu.AppendItem(varr_it)
        selection_menu.AppendSeparator()
        selection_menu.AppendItem(group_it)

        ## view menu
        view_menu = wx.Menu()
        collp_it = wx.MenuItem(view_menu, wx.ID_ANY, "(Un)Collapse card")
        inspc_it = wx.MenuItem(view_menu, wx.ID_ANY, "Inspect card")
        tgmap_it = wx.MenuItem(view_menu, wx.ID_ANY, "Show map")
        zoomi_it = wx.MenuItem(view_menu, wx.ID_ANY, "Zoom in")
        zoomo_it = wx.MenuItem(view_menu, wx.ID_ANY, "Zoom out")
        hideb_it = wx.MenuItem(view_menu, wx.ID_ANY, "Hide Page tool bar", kind=wx.ITEM_CHECK)

        view_menu.AppendItem(collp_it)
        view_menu.AppendItem(inspc_it)
        view_menu.AppendItem(tgmap_it)
        view_menu.AppendItem(zoomi_it)
        view_menu.AppendItem(zoomo_it)
        view_menu.AppendSeparator()
        view_menu.AppendItem(hideb_it)
        
        view_menu.Check(hideb_it.GetId(), True)        

        ## debug menu
        debug_menu = wx.Menu()                
        debug_it = wx.MenuItem(debug_menu, wx.ID_ANY, "&Debug")
        debug_menu.AppendItem(debug_it)
    
        ## search menu. ghost
        search_menu = wx.Menu()
        search_it = wx.MenuItem(search_menu, wx.ID_ANY, "Search")
        next_it   = wx.MenuItem(search_menu, wx.ID_ANY, "Next")
        prev_it   = wx.MenuItem(search_menu, wx.ID_ANY, "Previous")

        ## bindings
        self.Bind(wx.EVT_MENU, self.OnQuit       , quit_it)
        self.Bind(wx.EVT_MENU, self.OnCopy       , copy_it)
        self.Bind(wx.EVT_MENU, self.OnPaste      , past_it)
        self.Bind(wx.EVT_MENU, self.OnDelete     , delt_it)
        
        self.Bind(wx.EVT_MENU, self.OnSelectAll     , sela_it)
        self.Bind(wx.EVT_MENU, self.OnSelectCurrent , selc_it)
        self.Bind(wx.EVT_MENU, self.OnSelectNone    , seln_it)
        self.Bind(wx.EVT_MENU, self.OnGroupSelection, group_it)

        self.Bind(wx.EVT_MENU, self.OnSave       , save_it)
        self.Bind(wx.EVT_MENU, self.OnOpen       , open_it)

        self.Bind(wx.EVT_MENU, self.OnZoomIn  , zoomi_it)
        self.Bind(wx.EVT_MENU, self.OnZoomOut , zoomo_it)
        
        self.Bind(wx.EVT_MENU, self.OnViewPageBar , hideb_it)

        self.Bind(wx.EVT_MENU, self.OnToggleCollapse  , collp_it)
        self.Bind(wx.EVT_MENU, self.OnMenuInspectCard , inspc_it)
        self.Bind(wx.EVT_MENU, self.OnToggleMinimap   , tgmap_it)

        self.Bind(wx.EVT_MENU, self.OnInsertContentRight , contr_it)
        self.Bind(wx.EVT_MENU, self.OnInsertContentBelow , contb_it)        
        self.Bind(wx.EVT_MENU, self.OnInsertHeaderRight  , headr_it)
        self.Bind(wx.EVT_MENU, self.OnInsertHeaderBelow  , headb_it)        
        self.Bind(wx.EVT_MENU, self.OnInsertImage   , img_it)

        self.Bind(wx.EVT_MENU, self.OnCtrlF      , search_it)
        # self.Bind(wx.EVT_MENU, self.OnCtrlG      , next_it)     # ctrl+g is a special accelerator. See below
        self.Bind(wx.EVT_MENU, self.OnCtrlShftG  , prev_it)        

        self.Bind(wx.EVT_MENU, self.OnHArrange   , harr_it)
        self.Bind(wx.EVT_MENU, self.OnVArrange   , varr_it)
        self.Bind(wx.EVT_MENU, self.OnDebug      , debug_it)
        
        ## shortcuts
        accels = [] # will hold keyboard shortcuts aka accelerators
        
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("M"), tgmap_it.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("A"), sela_it.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"), debug_it.GetId()))

        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("-"), zoomi_it.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("+"), zoomo_it.GetId()))

        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("F"), search_it.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , ord("G"), prev_it.GetId()))        
        
        # finish up        
        bar.Append(file_menu, "&File")
        bar.Append(edit_menu, "&Edit")
        bar.Append(insert_menu, "&Insert")
        bar.Append(selection_menu, "&Selection")
        bar.Append(view_menu, "&View")
        bar.Append(debug_menu, "&Debug")
        self.SetMenuBar(bar)

        ## especial items
        # These are ghost items created for the purpose of associating
        # an accelerator to them. Usually, the accelerator is multifunctional.
        # For example, we couldn't set ctrl + g as the callback and
        # accelerator for next_it (next search result) because we also
        # want to use ctrl + g for grouping. So we bind ctrl + G to a
        # ghost item whose only task is to decide what action to take.
        esp_menu = wx.Menu()
        
        ctrlg = wx.MenuItem(esp_menu, wx.ID_ANY, "ctrlg")
        esc   = wx.MenuItem(esp_menu, wx.ID_ANY, "esc")
        ctrlpgup = wx.MenuItem(esp_menu, wx.ID_ANY, "ctrl page up")
        ctrlpgdw = wx.MenuItem(esp_menu, wx.ID_ANY, "ctrl page down")

        esp_menu.AppendItem(ctrlg)        
        esp_menu.AppendItem(esc)
        esp_menu.AppendItem(ctrlpgup)
        esp_menu.AppendItem(ctrlpgdw)
        
        self.Bind(wx.EVT_MENU, self.OnCtrlG, ctrlg)
        self.Bind(wx.EVT_MENU, self.OnEsc,   esc)
        self.Bind(wx.EVT_MENU, self.OnCtrlPgUp, ctrlpgup)
        self.Bind(wx.EVT_MENU, self.OnCtrlPgDw, ctrlpgdw)
        
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G"), ctrlg.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27, esc.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_PAGEUP, ctrlpgup.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_PAGEDOWN, ctrlpgdw.GetId()))

        ## finally, create the table
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def InitSearchBar(self):
        """Initializes the search bar, `self.search_ctrl`."""
        if not self.ui_ready:
            # make new
            ctrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
            ctrl.Bind(wx.EVT_TEXT, self.Search)
            ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.OnCancelSearch)
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearchEnter)
        else:
            # or get the old one
            ctrl = self.search_ctrl

        # position
        bd = self.GetCurrentBoard()
        if bd:
            top = bd.GetRect().top
            right = bd.GetRect().right - ctrl.GetRect().width
            ctrl.SetPosition((right, top))

        # finish up
        ctrl.Hide()
        self.search_ctrl = ctrl

    def InitToolBar(self):
        """Initializes the toolbar."""
        toolbar = self.CreateToolBar(style=wx.TB_VERTICAL)

        # notebook and tab tools
        new_it = toolbar.AddLabelTool(wx.ID_NEW, "New",
                                      wx.ArtProvider.GetBitmap(wx.ART_NEW),
                                      kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_TOOL, self.OnNew, new_it)
        opn_it = toolbar.AddLabelTool(wx.ID_OPEN, "Open",
                                      wx.ArtProvider.GetBitmap(wx.ART_FOLDER_OPEN),
                                      kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_TOOL, self.OnOpen, opn_it)
        sav_it = toolbar.AddLabelTool(wx.ID_SAVE, "Save",
                                      wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE),
                                      kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_TOOL, self.OnSave, sav_it)
        toolbar.AddSeparator()

        # card and board tools
        del_it = toolbar.AddLabelTool(wx.ID_ANY, "Delete",
                                      wx.ArtProvider.GetBitmap(wx.ART_DELETE),
                                      kind=wx.ITEM_NORMAL)
        cpy_it = toolbar.AddLabelTool(wx.ID_COPY, "Copy",
                                      wx.ArtProvider.GetBitmap(wx.ART_COPY),
                                      kind=wx.ITEM_NORMAL)
        pas_it = toolbar.AddLabelTool(wx.ID_PASTE, "Paste",
                                      wx.ArtProvider.GetBitmap(wx.ART_PASTE),
                                      kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_TOOL, self.OnDelete, del_it)
        self.Bind(wx.EVT_TOOL, self.OnCopy, cpy_it)
        self.Bind(wx.EVT_TOOL, self.OnPaste, pas_it)

    def InitUI(self):
        """Initialize the GUI and controls."""
        sz = (20, 20)
        # # cleanup the previous UI, if any
        if self.ui_ready:
            pg = self.GetCurrentPage()
            sz = pg.GetSize()
            pg.Hide()
            self.sheet = None
            self.SetSizer(None)

        # make new UI
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)

        # execute only the first time; order matters
        if not self.ui_ready:
            self.InitMenuBar()
            self.CreateStatusBar()
            self.InitWelcome()
            self.InitSearchBar()
            self.InitToolBar()

        self.ui_ready = True

    def InitWelcome(self):
        """Initialize the `WelcomPage` shown at startup."""
        panel = WelcomePage(self)
        vbox = self.GetSizer()
        vbox.Add(panel, proportion=1, flag=wx.EXPAND)
        self.welcome = panel

    def InitNotebook(self, size=wx.DefaultSize):
        """Initialize the `Book` and delete the `WelcomePage`."""
        # delete the welcome page
        # at this point, self.GetSizer() should only have the WelcomePage
        box = self.GetSizer()
        if self.welcome:
            self.welcome.Hide()
        box.Clear()
        self.welcome = None

        # create and setup the notebook
        nb = Book(self, size=size)

        # bindings: make sure to Bind EVT_BK_NEW_PAGE before creating any pages!
        nb.Bind(Book.EVT_BK_NEW_PAGE, self.OnNewPage)

        # UI setup
        nb_box = wx.BoxSizer(wx.HORIZONTAL)
        nb_box.Add(nb, proportion=1,   flag=wx.ALL|wx.EXPAND, border=1)
        box.Add(nb_box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # finish up
        box.Layout()
        self.notebook = nb

    def Log(self, s):
        """Log the string `s` into the status bar.

        `s: ` a string.
        """
        self.StatusBar.SetStatusText(s)
        wx.CallLater(self.CLEAN_STATUS_BAR_AFTER_MS,
                     self.StatusBar.SetStatusText, "")

    def OnDebug(self, ev):
        """CTRL+D"""
        print "---DEBUG---"
        print self.GetCurrentPage().Dump()

    def Save(self, out_file):
        """Save the current `Book` to disk.

        * `out_file: ` path to the file.
        """
        di =  self.notebook.Dump()
        with open(out_file, 'w') as out:
            pickle.dump(di, out)

    def Load(self, path):
        """Load a `Book` from disk.

        * `path: ` path to the file.
        """
        with open(path, 'r') as f: d = pickle.load(f)
        self.notebook.Load(d)
        self.notebook.SetFocus()
                
        
    ### Callbacks

    def OnNewPage(self, ev):
        """Listens to `Book.EVT_BK_NEW_PAGE`."""
        ev.page.Bind(Page.EVT_PAGE_INSPECT, self.OnInspect)
        ev.page.Bind(Page.EVT_PAGE_CANCEL_INSPECT, self.OnCancelInspect)
        ev.page.board.Bind(Board.EVT_BOARD_DEL_CARD, self.AfterDelete)
        ev.page.board.Bind(Board.EVT_NEW_CARD, self.AfterCardCreated)

    def OnZoomIn(self, ev):
        """Listens to `wx.EVT_MENU` from the zoom controls in the view menu."""
        self.GetCurrentPage().ZoomIn()

    def OnZoomOut(self, ev):
        """Listens to `wx.EVT_MENU` from the zoom controls in the view menu."""
        self.GetCurrentPage().ZoomOut()

    def OnGroupSelection(self, ev):
        """Listens to `wx.EVT_MENU` from "Group selection" in the "selection" menu."""
        self.GetCurrentBoard().GroupSelected()

    def OnToggleMinimap(self, ev):
        """Listens to `wx.EVT_MENU` from "Show map" in the "view" menu."""
        self.GetCurrentPage().ToggleMinimap()

    def OnToggleCollapse(self, ev):
        """Listens to `wx.EVT_MENU` from "(Un)Collapse card" in the "view" menu."""
        for c in [t for t in self.GetCurrentBoard().GetSelection() if isinstance(t, Content)]:
            c.ToggleCollapse()

    def OnViewPageBar(self, ev):
        """Listens to `wx.EVT_MENU` from "Hide Page tool bar" in the "view" menu."""
        self.GetCurrentPage().ShowToolBar(show=ev.IsChecked())

    def OnMenuInspectCard(self, ev):
        """Listens to `wx.EVT_MENU` from "Inspect card" in the "view" menu."""
        pg = self.GetCurrentPage()
        cont = pg.GetCurrentContent()

        # toggle between Board and Inspect modes        
        if cont == Board:
            sel = pg.board.GetSelection()
            if len(sel) > 0:
                cards = [c for c in sel if isinstance(c, Content)]
                if cards:
                    pg.InspectCards(cards)
                    if len(cards) == 1:
                        self.Log("Inspecting \"" + cards[0].GetTitle() + "\".")
                    else:
                        self.Log("Inspecting " + str(len(cards)) + " cards.")
        elif cont == CardInspect:
            pg.CancelInspect()
            self.Log("Done inspecting.")

    def OnInspect(self, ev):
        """Listens to `Page.EVT_PAGE_INSPECT` from every `Page` in the `Book`."""
        if ev.number == 1:
            self.Log("Inspecting \"" + ev.title + "\".")
        else:
            self.Log("Inspecting " + str(ev.number) + " cards.")

    def OnCancelInspect(self, ev):
        """Listens to `Page.EVT_PAGE_CANCEL_INSPECT` from every `Page` in the `Book`."""
        self.Log("Done inspecting.")

    def OnSelectAll(self, ev):
        """Listens to `wx.EVT_MENU` from "Select All" in the "selection" menu."""
        board = self.GetCurrentBoard()
        board.UnselectAll()
        for c in board.GetCards():
            board.SelectCard(c)

    def OnSelectCurrent(self, ev):
        """Listens to `wx.EVT_MENU` from "Select Current" in the "selection" menu."""
        ctrl = self.FindFocus()
        parent = ctrl.GetParent()
        if isinstance(parent, Card):
            self.GetCurrentBoard().SelectCard(parent, new_sel=True)
            parent.SetFocusIgnoringChildren()

    def OnSelectNone(self, ev):
        """Listens to `wx.EVT_MENU` from "Select None" in the "selection" menu."""
        self.GetCurrentBoard().UnselectAll()
        self.GetCurrentBoard().SetFocusIgnoringChildren()

    def OnEsc(self, ev):
        """Listens to ESC."""
        # if searching: cancel search
        if self.FindFocus() == self.search_ctrl:
            self.CancelSearch()
            return

        # if on welcome page: nil
        if self.welcome:
            return

        # if inspecting: nil
        pg = self.GetCurrentPage()
        if pg:
            content = pg.GetCurrentContent()
            if content and content == CardInspect:
                return

        # if on board: cycle selection
        # none (cursor inside a card) -> card -> group -> page title label -> none (cursor inside the same card)
        content = pg.GetCurrentContent()
        if content == Board:
            bd = self.GetCurrentBoard()
            sel = bd.GetSelection()

            if isinstance(sel, list) and len(sel) > 1:
                # selecting a group: there's no more to select
                # so just cancel selection; when SelectionManager
                # is deactivated, it will return focus to the last
                # card that was selected
                bd.UnselectAll()
            elif len(sel) == 1:
                # selecting a card: select group (if any)
                card = sel[0]
                if bd.GetContainingGroups(card):
                    bd.SelectGroup(bd.GetContainingGroups(card)[0], True)
                # if no group, cancel selection
                else:
                    bd.UnselectAll()
            elif GetCardAncestor(self.FindFocus()):
                # inside a card: select the card
                card = GetCardAncestor(self.FindFocus())
                bd.SelectCard(card, True)
                bd.SetFocus()
            else:
                ev.Skip()
        else:
            ev.Skip()

    def OnCtrlPgUp(self, ev):
        """Listens to "CTRL+PAGEUP."""
        nb = self.notebook
        sel = nb.GetSelection()
        if sel > 0:
            nb.SetSelection(nb.GetSelection()-1)

    def OnCtrlPgDw(self, ev):
        """Listens to "CTRL+PAGEDOWN."""
        nb = self.notebook
        sel = nb.GetSelection()
        if sel < nb.GetPageCount() - 1:
            nb.SetSelection(nb.GetSelection()+1)

    def OnHArrange(self, ev):
        """Listens to `wx.EVT_MENU` from "Arrange Horizontally" in the "selection" menu."""
        self.GetCurrentBoard().ArrangeSelection(Board.HORIZONTAL)
        self.Log("Horizontal arrange.")

    def OnVArrange(self, ev):
        """Listens to `wx.EVT_MENU` from "Arrange Vertically" in the "selection" menu."""
        self.GetCurrentBoard().ArrangeSelection(Board.VERTICAL)
        self.Log("Vertical arrange.")

    def OnCopy(self, ev):
        """Listens to `wx.EVT_MENU` from "Copy" in the "selection" menu and to
        `wx.EVT_TOOL` from "Copy" in the toolbar.
        """
        sel = self.GetCurrentBoard().GetSelection()
        if sel:
            self.GetCurrentBoard().CopySelected()
            self.Log("Copy " + str(len(sel)) + " Cards.")

    def OnPaste(self, ev):
        """Listens to `wx.EVT_MENU` from "Paste" in the "selection" menu and to
        `wx.EVT_TOOL` from "Paste" in the toolbar.
        """
        self.GetCurrentBoard().PasteFromClipboard()
        self.Log("Paste " + str(len(self.GetCurrentBoard().GetSelection())) + " Cards.")

    def OnDelete(self, ev):
        """Requests board to delete some cards, raised from the menu. See AfterDelete."""
        bd = self.GetCurrentBoard()
        sel = len(bd.GetSelection())
        bd.DeleteSelected()

    def AfterDelete(self, ev):
        """Listens to `Board.EVT_BOARD_DEL_CARD`."""
        self.Log("Delete " + str(ev.number) + " Cards.")

    def OnCtrlF(self, ev):
        """Listens to CTRL+F."""
        if not self.search_ctrl.IsShown():
            self.InitSearchBar()
            self.search_ctrl.Show()
            self.search_ctrl.SetFocus()
        else:
            # make sure to call CancelSearch to clear up all variables
            self.CancelSearch()

    def OnSearchEnter(self, ev):
        """Listens to `wx.EVT_TEXT_ENTER` from the serach bar."""
        self.NextSearchResult()

    def OnCtrlG(self, ev):
        """Listens to CTRL+G."""
        bd = self.GetCurrentBoard()
        if self.search_ctrl.IsShown():
            self.NextSearchResult()
        elif bd.GetSelection():
            sel = bd.GetSelection()
            bd.GroupSelected()
            self.Log("Grouped " + str(len(sel)) + " cards.")

    def OnCtrlShftG(self, ev):
        """Listens to SHIFT+CTRL+G."""
        self.PrevSearchResult()

    def OnInsertContentRight(self, ev):
        """Listens to `wx.EVT_MENU` from "New Card: Right" in the "insert" menu."""
        self.GetCurrentBoard().PlaceNewCard("Content", below=False)

    def OnInsertContentBelow(self, ev):
        """Listens to `wx.EVT_MENU` from "New Card: Below" in the "insert" menu."""
        self.GetCurrentBoard().PlaceNewCard("Content", below=True)

    def OnInsertHeaderRight(self, ev):
        """Listens to `wx.EVT_MENU` from "New Header: Right" in the "insert" menu."""
        self.GetCurrentBoard().PlaceNewCard("Header", below=False)

    def OnInsertHeaderBelow(self, ev):
        """Listens to `wx.EVT_MENU` from "New Header: Below" in the "insert" menu."""
        self.GetCurrentBoard().PlaceNewCard("Header", below=True)        
        
    def OnInsertImage(self, ev):
        """Listens to `wx.EVT_MENU` from "Insert image" in the "insert" menu."""
        self.GetCurrentBoard().PlaceNewCard("Image", below=False)

    def AfterCardCreated(self, ev):
        """Listens to `Board.EVT_NEW_CARD` from the `Board` of every `Page`."""
        self.Log("Created new " + ev.subclass + " card.")

    def OnNew(self, ev):
        """Listens to `wx.EVT_TOOL` from "New" in the toolbar."""
        self.notebook.NewPage()

    def OnSave(self, ev):
        """Listens to `wx.EVT_MENU` from "Save" in the "file" menu."""
        # return focus after saving
        focus = self.FindFocus()
        if isinstance(focus, wx.TextCtrl):
            caret = focus.GetInsertionPoint()

        # if we don't have a path yet, ask for one
        path = ""
        if self.cur_file != "":
            path = self.cur_file
        else:
            fd = wx.FileDialog(self, "Save", os.getcwd(), "", "P files (*.p)|*.p",
                               wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            # check if user changed her mind
            if fd.ShowModal() == wx.ID_CANCEL:
                return
            path = fd.GetPath()

        # finish up
        self.Save(path)
        self.cur_file = path

        # restore focus and insertion point, if applicable
        if focus:
            focus.SetFocus()
        if isinstance(focus, wx.TextCtrl):
            focus.SetInsertionPoint(caret)
        
        self.Log("Saved file" + self.cur_file)

    def OnOpen(self, ev):
        """Listens to `wx.EVT_MENU` from "Open" in the "file" menu."""
        # ask for a file name
        fd = wx.FileDialog(self, "Open", "/home/leo/research/reading_notes/Kandel - Principles of Neural Science",
                           "", "P files (*.p)|*.p|All files|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind

        # delete the welcome page and create a new notebook
        self.InitNotebook()

        # load the chosen file
        self.cur_file = fd.GetPath()        
        self.Log("Loading file...")
        self.Load(self.cur_file)
        self.Log("Opened file" + self.cur_file)

    def OnQuit(self, ev):
        """Quit program."""
        self.Close()



######################
# WelcomePage class
######################            

class WelcomePage(wx.Panel):
    """
    The panel that is displayed as soon as the user starts the
    application. Gives options to load a file or start a new one.
    """
    
    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `ThreePyFiveFrame`.
        """
        super(WelcomePage, self).__init__(parent)
        self.InitUI()
        

    ### Auxiliary functions

    def InitUI(self):
        """Initialize the GUI and controls."""
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
        """Listens to `wx.EVT_BUTTON` from the "New book" button."""
        self.GetParent().InitNotebook()
        self.GetParent().notebook.NewPage()

    def OnLoadBook(self, ev):
        """Listens to `wx.EVT_BUTTON` from the "Load book" button."""
        self.GetParent().OnOpen(None)



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
for field in dir(wx.Frame):
    __pdoc__['ThreePyFiveFrame.%s' % field] = None
for field in dir(wx.Panel):
    __pdoc__['WelcomePage.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in ThreePyFiveFrame.__dict__.keys():
    if 'ThreePyFiveFrame.%s' % field in __pdoc__.keys():
        del __pdoc__['ThreePyFiveFrame.%s' % field]
for field in WelcomePage.__dict__.keys():
    if 'WelcomePage.%s' % field in __pdoc__.keys():
        del __pdoc__['WelcomePage.%s' % field]    
        


if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None)
    app.MainLoop()
