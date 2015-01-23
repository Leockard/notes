#!/usr/bin/python

# notes.py
# main class and executable for note taking application

import wx
import os
import pickle
from page import Page
from board import Content
from board import Header
from canvas import Canvas
import wx.richtext as rt


######################
# Main Frame class
######################

class MyFrame(wx.Frame):
    def __init__(self, parent):
        super(MyFrame, self).__init__(parent, -1, "Board", size = (800, 600),
                                      style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE)

        self.accels = [] # will hold keyboard shortcuts aka accelerators
        self.SetTitle("Notes")
        self.cur_file = ""
        self.search_find = []
        self.searching = None      # contains the current search index
                                   # when not searching, set to None
        self.ui_ready = False
        self.InitUI()              # sets up the sizer and the buttons' bindings
        self.GetCurrentBoard().SetFocus()

        # keyboard shortcuts
        # accels is populated in InitUI()
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))


    ### Behavior Functions

    def GetCurrentBoard(self):
        """Returns the active board."""
        pg = self.notebook.GetCurrentPage()
        if pg: return pg.board
        else: return None

    def Search(self, ev):
        """
        Search the current text in the search bar in all of the Cards' texts.
        Cycle through finds with ctrl + G.
        """
        # search string in lower case
        s = self.search_ctrl.GetValue().lower()
                
        # if we were already searching, clear up the previous highlighting
        if self.search_find:
            # unhighlight results
            for c, i in self.search_find:
                c.SetStyle(i, i + len(s), c.GetDefaultStyle())

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

        # focus on the first find
        if finds:
            # highlight results
            for c, i in finds:
                c.SetStyle(i, i + len(s), wx.TextAttr(None, wx.YELLOW))

            # setup variables for ctrl + G cycling
            self.search_find = finds
            self.search_skip = False
            # save the current index in search_find
            # when done searching, set to None
            self.searching = 0

    def CancelSearch(self, ev):
        if self.search_find:
            for c, i in self.search_find:
                s = self.search_ctrl.GetValue()
                c.SetStyle(i, i + len(s), c.GetDefaultStyle())
            self.search_find = []
            self.searching = None

        self.search_ctrl.Hide()

    def PrevSearchResult(self):
        if self.searching != None:
            # used when changing direction in searching
            i = self.searching
            self.JumpSearchResults(i, i-1)
            
            # advance and wrap
            i -= 1
            if i < 0: i = len(self.search_find) - 1
            self.searching = i

    def NextSearchResult(self):
        """Add a strong highlight and scroll to the next search result."""
        if self.searching != None:
            # used when changing direction in searching
            i = self.searching
            self.JumpSearchResults(i-1, i)
            
            # advance and wrap
            i += 1            
            if i >= len(self.search_find): i = 0
            self.searching = i

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

        # strong hightlight on current search find
        ctrl = self.search_find[new][0]
        pos = self.search_find[new][1]
        ctrl.SetStyle(pos, pos + len(s), wx.TextAttr(None, wx.RED))

        # make sure the find is visible            
        card = ctrl.GetParent()            
        self.GetCurrentBoard().ScrollToCard(card)
        if isinstance(card, Content) and card.IsCollapsed():
            card.Uncollapse()

                    
    ### Auxiliary functions

    def InitMenuBar(self):
        bar = wx.MenuBar()

        # file menu
        file_menu = wx.Menu()                
        open_it = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open")
        save_it = wx.MenuItem(file_menu, wx.ID_SAVE, "&Save")
        quit_it = wx.MenuItem(file_menu, wx.ID_EXIT, "&Quit")

        file_menu.Append(wx.ID_NEW, "&New")        
        file_menu.AppendItem(open_it)
        file_menu.AppendItem(save_it)
        file_menu.AppendSeparator()
        file_menu.AppendItem(quit_it)

        # edit menu
        edit_menu = wx.Menu()
        sela_it        = wx.MenuItem(edit_menu, wx.ID_ANY, "Select All")
        seln_it        = wx.MenuItem(edit_menu, wx.ID_ANY, "Select None")
        copy_it        = wx.MenuItem(edit_menu, wx.ID_COPY, "Copy")
        delt_it        = wx.MenuItem(edit_menu, wx.ID_DELETE, "Delete")
        ctrltab_it     = wx.MenuItem(edit_menu, wx.ID_ANY, "Next Card")
        ctrlshfttab_it = wx.MenuItem(edit_menu, wx.ID_ANY, "Previous Card")
        unsel_it       = wx.MenuItem(edit_menu, wx.ID_ANY, "Unselect All")

        edit_menu.AppendItem(sela_it)
        edit_menu.AppendItem(seln_it)
        edit_menu.AppendItem(copy_it)
        edit_menu.AppendItem(delt_it)
        edit_menu.AppendItem(ctrltab_it)

        # insert menu
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
        
        # layout menu
        layout_menu = wx.Menu()                
        harr_it = wx.MenuItem(layout_menu, wx.ID_ANY, "Arrange &Horizontally")
        varr_it = wx.MenuItem(layout_menu, wx.ID_ANY, "Arrange &Vertically")
        layout_menu.AppendItem(harr_it)
        layout_menu.AppendItem(varr_it)

        # debug menu
        debug_menu = wx.Menu()                
        debug_it = wx.MenuItem(debug_menu, wx.ID_ANY, "&Debug")
        debug_menu.AppendItem(debug_it)

        # search menu
        # this is an invisible search menu, used only to have a MenuItem
        # to append to the AcceleratorTable
        search_menu = wx.Menu()
        search_it = wx.MenuItem(search_menu, wx.ID_ANY, "Search")
        next_it   = wx.MenuItem(search_menu, wx.ID_ANY, "Next")
        prev_it   = wx.MenuItem(search_menu, wx.ID_ANY, "Previous")
        search_menu.AppendItem(search_it)

        # bindings
        self.Bind(wx.EVT_MENU, self.OnQuit       , quit_it)
        self.Bind(wx.EVT_MENU, self.OnCopy       , copy_it)
        self.Bind(wx.EVT_MENU, self.OnSelectAll  , sela_it)
        self.Bind(wx.EVT_MENU, self.OnEsc        , seln_it)
        self.Bind(wx.EVT_MENU, self.OnDelete     , delt_it)
        self.Bind(wx.EVT_MENU, self.OnSave       , save_it)
        self.Bind(wx.EVT_MENU, self.OnOpen       , open_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlTab    , ctrltab_it)
        self.Bind(wx.EVT_MENU, self.OnHArrange   , harr_it)
        self.Bind(wx.EVT_MENU, self.OnVArrange   , varr_it)
        self.Bind(wx.EVT_MENU, self.OnDebug      , debug_it)
        self.Bind(wx.EVT_MENU, self.OnEsc        , unsel_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlF      , search_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlG      , next_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlShftG  , prev_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlRet    , contr_it)
        self.Bind(wx.EVT_MENU, self.OnAltRet     , headr_it)
        self.Bind(wx.EVT_MENU, self.OnImage      , img_it)
        self.Bind(wx.EVT_MENU, self.OnCtrlShftTab , ctrlshfttab_it)        
        self.Bind(wx.EVT_MENU, self.OnCtrlShftRet , contb_it)
        self.Bind(wx.EVT_MENU, self.OnAltShftRet  , headb_it)

        # shortcuts
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27, unsel_it.GetId())) # ESC
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 127, delt_it.GetId())) # DEL

        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("A"),      sela_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"),      debug_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("F"),      search_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G"),      next_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_TAB,    ctrltab_it.GetId()))                
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_RETURN, contr_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_RETURN, headr_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , ord("G"), prev_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_RETURN, contb_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_TAB,    ctrlshfttab_it.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_ALT  , wx.WXK_RETURN, headb_it.GetId()))

        # finish up        
        bar.Append(file_menu, "&File")
        bar.Append(edit_menu, "&Edit")
        bar.Append(insert_menu, "&Insert")
        bar.Append(layout_menu, "&Layout")        
        bar.Append(debug_menu, "&Debug")
        self.SetMenuBar(bar)

    def InitSearchBar(self):
        if not self.ui_ready:
            # make new
            ctrl = wx.SearchCtrl(self, style=wx.TE_PROCESS_ENTER)
            # ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.Search)
            ctrl.Bind(wx.EVT_TEXT, self.Search)
            ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.CancelSearch)
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnSearchEnter)
        else:
            # or get the old one
            ctrl = self.search_ctrl

        # position
        top = self.GetCurrentBoard().GetRect().top
        right = self.GetCurrentBoard().GetRect().right - ctrl.GetRect().width
        ctrl.SetPosition((right, top))

        # stuff
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
        self.Bind(wx.EVT_TOOL, self.OnDelete, del_it)
        self.Bind(wx.EVT_TOOL, self.OnCopy, cpy_it)

    def InitUI(self):
        sz = (20, 20)
        # # cleanup the previous UI, if any
        if self.ui_ready:
            pg = self.notebook.GetCurrentPage()
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
            self.InitNotebook(sz)            
            self.InitSearchBar()
            self.InitToolBar()
            
        self.ui_ready = True

    def InitNotebook(self, size = wx.DefaultSize):
        nb = wx.Notebook(self, size=size)

        # make starting page
        pg = Page(nb, size = size)
        # pg.board.SetBackgroundColour(Page.BACKGROUND_CL)
        nb.AddPage(pg, "Unittled Notes")

        # UI setup
        vbox = self.GetSizer()
        if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
        nb_box = wx.BoxSizer(wx.HORIZONTAL)
        nb_box.Add(nb, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        vbox.Add(nb_box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # bindings
        nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChange)

        # set members
        self.notebook = nb
        # self.board = pg.board

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

    def OnDebug(self, ev):
        print "debug"
        
    def Save(self, out_file, d):
        """Save the data in the dict d in the file out_file."""
        with open(out_file, 'w') as out:
            pickle.dump(d, out)

    def Load(self, path):
        carddict = {}
        board = self.GetCurrentBoard()
        with open(path, 'r') as f: carddict = pickle.load(f)
        for id, values in carddict.iteritems():
            pos = values["pos"]
            label = values["label"]
            if values["class"] == "Content":
                new = board.NewCard(values["class"], pos=pos, label=label,
                              title   = str(values["title"]),
                              kind    = values["kind"],
                              content = values["content"])
                if values["collapsed"]: new.Collapse()
            elif values["class"] == "Header":
                board.NewCard(values["class"], pos=pos, label=label,
                              size = (values["width"], values["height"]),
                              txt = values["header"])
            elif values["class"] == "Image":
                board.NewCard(values["class"], pos=pos, label=label,
                              path  = values["path"])

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

    def OnSelectAll(self, ev):
        board = self.GetCurrentBoard()
        board.UnselectAll()
        for c in board.GetCards():
            board.SelectCard(c)

    def OnPageChange(self, ev):
        pass

    def OnHArrange(self, ev):
        self.GetCurrentBoard().HArrangeSelectedCards()
        self.Log("Horizontal arrange.")

    def OnVArrange(self, ev):
        self.GetCurrentBoard().VArrangeSelectedCards()
        self.Log("Vertical arrange.")

    def OnEsc(self, ev):
        """Unselect all cards."""
        self.GetCurrentBoard().UnselectAll()
        self.GetCurrentBoard().SetFocusIgnoringChildren()

    def OnCopy(self, ev):
        """Copy selected cards."""
        if self.GetCurrentBoard().selected_cards:
            self.Log("Copy " + str(len(self.GetCurrentBoard().selected_cards)) + " Cards.")
            self.GetCurrentBoard().CopySelected()

    def OnDelete(self, ev):
        """Delete selected cards."""
        if self.GetCurrentBoard().selected_cards:
            self.Log("Delete " + str(len(self.GetCurrentBoard().selected_cards)) + " Cards.")
            self.GetCurrentBoard().DeleteSelected()
        else:
            ev.Skip()

    def OnCtrlF(self, ev):
        """Show/hide the search control."""
        shwn = self.search_ctrl.IsShown()
        
        if not shwn:
            self.InitSearchBar()
            self.search_ctrl.Show()
            self.search_ctrl.SetFocus()
        else:
            self.search_ctrl.Hide()
            self.GetCurrentBoard().SetFocus()
            self.CancelSearch(None)
            self.searching = None

    def OnSearchEnter(self, ev):
        """Go to next search find."""
        self.NextSearchResult()

    def OnCtrlG(self, ev):
        """Go to next search find."""
        self.NextSearchResult()

    def OnCtrlShftG(self, ev):
        """Go to previous search find."""
        self.PrevSearchResult()

    def OnCtrlTab(self, ev):
        """Selects next card."""
        self.GetCurrentBoard().GetNextCard(self.FindFocus()).SetFocus()

    def OnCtrlShftTab(self, ev):
        """Selects previous card."""
        self.GetCurrentBoard().GetPrevCard(self.FindFocus()).SetFocus()

    def OnCtrlRet(self, ev):
        """Add a new content card to the board, to the right of the current card."""
        self.GetCurrentBoard().PlaceNewCard("Content", below=False)
        self.Log("Placed new Content card.")

    def OnCtrlShftRet(self, ev):
        """Add a new content card to the board, below of the current one."""
        self.GetCurrentBoard().PlaceNewCard("Content", below=True)
        self.Log("Placed new Content card.")

    def OnAltRet(self, ev):
        """Add a new header to the board, to the right of the current card."""
        self.GetCurrentBoard().PlaceNewCard("Header", below=False)
        self.Log("Placed new Header.")
        
    def OnAltShftRet(self, ev):
        """Add a new header to the board, to the right of the current card."""
        self.GetCurrentBoard().PlaceNewCard("Header", below=True)
        self.Log("Placed new Header.")

    def OnImage(self, ev):
        self.GetCurrentBoard().PlaceNewCard("Image", below=False)
        self.Log("Placed new Image.")

    def OnNew(self, ev):
        self.notebook.AddPage(Page(self.notebook), "Unittled Notes 2", select=True)

    def OnSave(self, ev):
        """Save file."""
        # return focus after saving
        focus = self.FindFocus()

        # if there's a current file, save it
        if self.cur_file != "":
            self.Save(self.cur_file, self.GetCurrentBoard().Dump())
            
        else: # else, ask for a file name
            fd = wx.FileDialog(self, "Save", os.getcwd(), "", "P files (*.p)|*.p",
                               wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind

            # let Save() worry about serializing
            self.Save(fd.GetPath(), self.GetCurrentBoard().Dump())
            self.cur_file = fd.GetPath()

        focus.SetFocus()
        self.Log("Saved file" + self.cur_file)

    def OnOpen(self, ev):
        """Open file."""
        # ask for a file name
        fd = wx.FileDialog(self, "Open", os.getcwd(), "", "P files (*.p)|*.p|All files|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind

        pg = Page(self.notebook)
        self.notebook.AddPage(pg, fd.GetPath(), select=True)

        self.GetCurrentBoard().Hide()     # hide while we load/paint all the info
        self.Load(fd.GetPath())           # load and paint all cards
        self.GetCurrentBoard().Show()     # show everything at the same time
        
        self.cur_file = fd.GetPath()
        self.Log("Opened file" + self.cur_file)        

    def OnQuit(self, ev):
        """Quit program."""
        self.Close()


if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame(None)
    frame.Show(True)
    app.MainLoop()
