#!/usr/bin/python
# -*- coding: utf-8 -*-

# notes.py
# main class and executable for note taking application

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


######################
# Main Frame class
######################

class MyFrame(wx.Frame):
    DEFAULT_SZ = (800, 600)
    DEFAULT_PAGE_NAME = "Untitled Notes"
    CLEAN_STATUS_BAR_AFTER_MS = 5000

    def __init__(self, parent, title="Board", size=DEFAULT_SZ, style=wx.DEFAULT_FRAME_STYLE|wx.NO_FULL_REPAINT_ON_RESIZE):
        super(MyFrame, self).__init__(parent, title=title, size=size, style=style)

        self.accels = [] # will hold keyboard shortcuts aka accelerators
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

        # keyboard shortcuts
        # accels is populated in InitUI()
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))

        # Done.
        self.Show()

        
    ### Behavior Functions

    def GetCurrentPage(self):
        """Returns the active page, or None."""
        result = None
        if self.notebook:
            result = self.notebook.GetCurrentPage()
        return result

    def GetCurrentBoard(self):
        """Returns the active board, or None."""
        result = None
        pg = self.GetCurrentPage()
        if pg and hasattr(pg, "board"):
            result = pg.board
        return result

    def Search(self, ev):
        """
        Search the current text in the search bar in all of the Cards' texts.
        Cycle through finds with ctrl + G.
        """
        # search string in lower case
        s = self.search_ctrl.GetValue().lower()
        
        # base case: not search string
        # the user may just have erased everything
        # reset variables and quit
        if not s:
            self.search_ctrl.SetBackgroundColour(wx.WHITE)
            self.search_find = []
            self.search_str = ""
            self.search_head = None
            return
                
        # if we were already searching, clear up  highlighting
        if self.search_find:
            # unhighlight previous results
            for c, i in self.search_find:
                c.SetStyle(i, i + len(self.search_str), c.GetDefaultStyle())

        # gather all values in which to search
        # including the control they appear in
        txt_ctrls = []
        for c in self.GetCurrentBoard().GetCards():
            if isinstance(c, Content):
                txt_ctrls.append((c.GetTitle().lower(),   c.title))
                txt_ctrls.append((c.GetContent().lower(), c.content))
            if isinstance(c, Header):
                txt_ctrls.append((c.GetHeader().lower(),  c.header))

        # do the actual searching
        finds = []
        for txt, ctrl in txt_ctrls:
            pos = txt.find(s)
            if pos > -1: finds.append((ctrl, pos))

        # if success: highlight and setup vars for cycling
        if finds:
            self.search_ctrl.SetBackgroundColour(wx.YELLOW)
            for c, i in finds:
                c.SetStyle(i, i + len(s), wx.TextAttr(wx.NullColour, wx.YELLOW))

            self.search_find = finds
            self.search_str = s
            # when done, set to None
            self.search_head = 0

        # if not found: make sure variables are setup correctly too
        else:
            self.search_ctrl.SetBackgroundColour(wx.RED)
            self.search_find = []
            self.search_str = ""
            self.search_head = None

    def OnCancelSearch(self, ev):
        """Called when the cancel button in the search control is pressed."""
        self.CancelSearch()

    def CancelSearch(self):
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
        if self.search_head != None:
            old = i = self.search_head
            new = i - 1
            if new < 0: new = len(self.search_find) - 1
            self.JumpSearchResults(old, new)
            self.search_head = new

    def NextSearchResult(self):
        """Add a strong highlight and scroll to the next search result."""
        if self.search_head != None:
            old = i = self.search_head
            new = i + 1
            if new >= len(self.search_find): new = 0
            self.JumpSearchResults(old, new)
            self.search_head = new

    def JumpSearchResults(self, old, new):
        """
        Unhighlights the old search result and highlights the new one.
        old and new must be valid indices in the internal search results list.
        This is just a convenience function for Prev- and NextSearchResult.
        Use those ones instead.
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

        self.Bind(wx.EVT_MENU, self.OnInsertContent , contr_it)
        self.Bind(wx.EVT_MENU, self.OnInsertHeader  , headr_it)
        self.Bind(wx.EVT_MENU, self.OnInsertContent , contb_it)
        self.Bind(wx.EVT_MENU, self.OnInsertHeader  , headb_it)        
        self.Bind(wx.EVT_MENU, self.OnInsertImage   , img_it)

        self.Bind(wx.EVT_MENU, self.OnCtrlF      , search_it)
        # self.Bind(wx.EVT_MENU, self.OnCtrlG      , next_it)     # ctrl+g is a special accelerator. See below
        self.Bind(wx.EVT_MENU, self.OnCtrlShftG  , prev_it)        

        self.Bind(wx.EVT_MENU, self.OnHArrange   , harr_it)
        self.Bind(wx.EVT_MENU, self.OnVArrange   , varr_it)
        self.Bind(wx.EVT_MENU, self.OnDebug      , debug_it)
        
        ## shortcuts
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("M"), tgmap_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("A"), sela_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"), debug_it.GetId()))

        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("-"), zoomi_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("+"), zoomo_it.GetId()))

        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("F"), search_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , ord("G"), prev_it.GetId()))        
        
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
        # an accelerator to them. The accelerator is a multifunctional
        # one. For example, we couldn't set ctrl + g as the callback and
        # accelerator for next_it (next search result) because we also
        # want to use ctrl + g for grouping. So we bind ctrl + G to a
        # ghost item whose only task is to decide what action to take.
        esp_menu = wx.Menu()
        
        ctrlg = wx.MenuItem(esp_menu, wx.ID_ANY, "ctrlg")
        esc   = wx.MenuItem(esp_menu, wx.ID_ANY, "esc")        
        esp_menu.AppendItem(ctrlg)        
        esp_menu.AppendItem(esc)
        
        self.Bind(wx.EVT_MENU, self.OnCtrlG, ctrlg)
        self.Bind(wx.EVT_MENU, self.OnEsc,   esc)
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G"), ctrlg.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27, esc.GetId()))

    def InitSearchBar(self):
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
        panel = WelcomePage(self)
        vbox = self.GetSizer()
        vbox.Add(panel, proportion=1, flag=wx.EXPAND)
        self.welcome = panel

    def InitNotebook(self, size = wx.DefaultSize):
        # delete the welcome page
        # at this point, self.GetSizer() should only have the WelcomePage
        box = self.GetSizer()
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

    def CreateBitmap(self):
        """Take a picture of the current card board."""
        # Create a DC for the whole screen area
        rect = self.GetCurrentBoard().GetScreenRect()
        bmp = wx.EmptyBitmap(rect.width, rect.height)

        dc = wx.MemoryDC() # MemoryDCs are for painting over BMPs
        dc.SelectObject(bmp)
        dc.Blit(0, 0, rect.width, rect.height, wx.ScreenDC(),
                 rect.x, rect.y) # offset in the original DC
        dc.SelectObject(wx.NullBitmap)

        return bmp

    def Log(self, s):
        """Log the string s into the status bar."""
        self.StatusBar.SetStatusText(s)
        wx.CallLater(self.CLEAN_STATUS_BAR_AFTER_MS,
                     self.StatusBar.SetStatusText, "")

    def OnDebug(self, ev):
        print "---DEBUG---"

    def Save(self, out_file):
        """Save the data in the out_file."""
        di =  self.notebook.Dump()
        with open(out_file, 'w') as out:
            pickle.dump(di, out)

    def Load(self, path):
        with open(path, 'r') as f: d = pickle.load(f)
        self.notebook.Load(d)
        self.notebook.SetFocus()

    def AddAccelerator(self, entry):
        """entry should be a AcceleratorEntry()."""
        self.accels.append()
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))

    def RemoveAccelerator(self, entry):
        """entry should be the same AcceleratorEntry object that was passed to AddAccelerator()."""
        if entry in self.accels:
            self.accels.remove(entry)
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))
                
        
    ### Callbacks

    def OnNewPage(self, ev):
        ev.page.Bind(Page.EVT_PAGE_INSPECT, self.OnInspect)
        ev.page.Bind(Page.EVT_PAGE_CANCEL_INSPECT, self.OnCancelInspect)
        ev.page.board.Bind(Board.EVT_BOARD_DEL_CARD, self.AfterDelete)
        ev.page.board.Bind(Board.EVT_NEW_CARD, self.AfterCardCreated)

    def OnZoomIn(self, ev):
        self.GetCurrentPage().ZoomIn()

    def OnZoomOut(self, ev):
        self.GetCurrentPage().ZoomOut()

    def OnGroupSelection(self, ev):
        self.GetCurrentBoard().GroupSelected()

    def OnToggleMinimap(self, ev):
        self.GetCurrentPage().ToggleMinimap()

    def OnToggleCollapse(self, ev):
        for c in [t for t in self.GetCurrentBoard().GetSelection() if isinstance(t, Content)]:
            c.ToggleCollapse()

    def OnViewPageBar(self, ev):
        self.GetCurrentPage().ShowToolBar(show=ev.IsChecked())

    def OnMenuInspectCard(self, ev):
        """Called by the View menu item."""
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
        if ev.number == 1:
            self.Log("Inspecting \"" + ev.title + "\".")
        else:
            self.Log("Inspecting " + str(ev.number) + " cards.")

    def OnCancelInspect(self, ev):
        self.Log("Done inspecting.")

    def OnSelectAll(self, ev):
        board = self.GetCurrentBoard()
        board.UnselectAll()
        for c in board.GetCards():
            board.SelectCard(c)

    def OnSelectCurrent(self, ev):
        ctrl = self.FindFocus()
        parent = ctrl.GetParent()
        if isinstance(parent, Card):
            self.GetCurrentBoard().SelectCard(parent, new_sel=True)
            parent.SetFocusIgnoringChildren()

    def OnSelectNone(self, ev):
        """Unselect all cards."""
        self.GetCurrentBoard().UnselectAll()
        self.GetCurrentBoard().SetFocusIgnoringChildren()

    def OnEsc(self, ev):
        """
        When in board: cycle selection through card, group, board.
        When searching: cancel search.
        When in CardInspect: don't do anything.
        """
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
        content = pg.GetCurrentContent()
        if content == Board:
            bd = self.GetCurrentBoard()
            sel = bd.GetSelection()

            if isinstance(sel, list) and len(sel) > 1:
                # selecting a group: there's no more to select
                # so just cancel selection
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

    def OnHArrange(self, ev):
        self.GetCurrentBoard().ArrangeSelection(Board.HORIZONTAL)
        self.Log("Horizontal arrange.")

    def OnVArrange(self, ev):
        self.GetCurrentBoard().ArrangeSelection(Board.VERTICAL)
        self.Log("Vertical arrange.")

    def OnCopy(self, ev):
        """Copy selected cards."""
        sel = self.GetCurrentBoard().GetSelection()
        if sel:
            self.GetCurrentBoard().CopySelected()
            self.Log("Copy " + str(len(sel)) + " Cards.")

    def OnPaste(self, ev):
        """Copy cards in the clip board."""
        self.GetCurrentBoard().PasteFromClipboard()
        self.Log("Paste " + str(len(self.GetCurrentBoard().GetSelection())) + " Cards.")

    def OnDelete(self, ev):
        """Requests board to delete some cards, raised from the menu. See AfterDelete."""
        bd = self.GetCurrentBoard()
        sel = len(bd.GetSelection())
        bd.DeleteSelected()

    def AfterDelete(self, ev):
        """Called after a delete action on a board."""
        self.Log("Delete " + str(ev.number) + " Cards.")

    def OnCtrlF(self, ev):
        """Show/hide the search control."""
        if not self.search_ctrl.IsShown():
            self.InitSearchBar()
            self.search_ctrl.Show()
            self.search_ctrl.SetFocus()
        else:
            # make sure to call CancelSearch to clear up all variables
            self.CancelSearch()

    def OnSearchEnter(self, ev):
        """Go to next search find."""
        self.NextSearchResult()

    def OnCtrlG(self, ev):
        """Special accel: if searching, Go to next search find. If not, group selection."""
        bd = self.GetCurrentBoard()
        if self.search_ctrl.IsShown():
            self.NextSearchResult()
        elif bd.GetSelection():
            sel = bd.GetSelection()
            bd.GroupSelected()
            self.Log("Grouped " + str(len(sel)) + " cards.")

    def OnCtrlShftG(self, ev):
        """Go to previous search find."""
        self.PrevSearchResult()

    def OnInsertContent(self, ev):
        """Add a new content card to the board, to the right of the current card."""
        self.GetCurrentBoard().PlaceNewCard("Content", below=False)

    def OnInsertHeader(self, ev):
        """Add a new header to the board, to the right of the current card."""
        self.GetCurrentBoard().PlaceNewCard("Header", below=False)

    def OnInsertImage(self, ev):
        self.GetCurrentBoard().PlaceNewCard("Image", below=False)

    def AfterCardCreated(self, ev):
        self.Log("Created new " + ev.subclass + " card.")

    def OnNew(self, ev):
        self.notebook.NewPage()

    def OnSave(self, ev):
        """Save file."""
        # return focus after saving
        focus = self.FindFocus()

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

        if focus:
            focus.SetFocus()
        
        self.Log("Saved file" + self.cur_file)

    def OnOpen(self, ev):
        """Open file."""
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
        self.GetParent().InitNotebook()
        self.GetParent().notebook.NewPage()

    def OnLoadBook(self, ev):
        self.GetParent().OnOpen(None)



if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None)
    app.MainLoop()
