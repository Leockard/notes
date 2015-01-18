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
        self.searching = None      # contains the current search index
                                   # when not searching, set to None
        self.ui_ready = False
        self.InitUI()              # sets up the sizer and the buttons' bindings
        self.GetCurrentBoard().SetFocus()

        # Keyboard shortcuts
        # accels is populated in InitUI()
        self.SetAcceleratorTable(wx.AcceleratorTable(self.accels))


    ### Behavior Functions

    def GetCurrentBoard(self):
        """Returns the active board."""
        return self.notebook.GetCurrentPage().board

    def PlaceNewCard(self, subclass, below = False):
        """
        Places a new Card in the board.
        class should be the string with the name of the Card subclass to create.
        below=False creates the new Card to the right of the currently selected
        Card in the board, if any. below=True creates it below.
        """
        pos = (0, 0)
        
        # if there are no cards, place this one on the top left corner
        if len(self.GetCurrentBoard().GetCards()) < 1:
            pos = (Page.CARD_PADDING, Page.CARD_PADDING)

        elif self.GetCurrentBoard().GetFocusedCard():
            pos = self.GetCurrentBoard().CalculateNewCardPosition(self.GetCurrentBoard().GetFocusedCard().GetPosition(), below)
        
        else: # otherwise, move it to the right of the last one
            rects = [c.GetRect() for c in self.GetCurrentBoard().GetCards()]
            rights = [r.right for r in rects]
            top = min([r.top for r in rects])
            left = max(rights) + Page.CARD_PADDING
            pos = (left, top)

        if subclass == "Content":
            self.GetCurrentBoard().NewCard(pos)
        elif subclass == "Header":
            self.GetCurrentBoard().NewHeader(pos)
        self.Log("New " + subclass + " card created.")

    def Search(self, ev):
        """
        Search the current text in the search bar in all of the Cards' texts.
        Cycle through finds with ctrl + G.
        """
        # gather all values in which to search
        # including the control they appear in
        txt_ctrls = []
        for c in self.GetCurrentBoard().GetCards():
            if isinstance(c, Content):
                txt_ctrls.append((c.GetTitle(),   c.title))
                txt_ctrls.append((c.GetContent(), c.content))
            if isinstance(c, Header):
                txt_ctrls.append((c.GetHeader(),  c.header))

        # search for the string
        s = self.search_ctrl.GetValue()        
        finds = []
        for txt, ctrl in txt_ctrls:
            if txt.find(s) > -1: finds.append(ctrl)

        print "controls: " + str(len(txt_ctrls))
        print "finds: " + str(len(finds))

        # focus on the first find
        if finds:
            # finds[0].SetFocus()
            # finds[0].SetSelection(0, 3)
            # self.search_ctrl.SetFocus()
            self.search_find = finds
            # save the current index in search_find
            # when done searching, set to None
            self.searching = 0         

    def CancelSearch(self, ev):
        self.searching = None

                    
    ### Auxiliary functions

    def InitMenuBar(self):
        bar = wx.MenuBar()

        # file menu
        file_menu = wx.Menu()                
        open_item = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open")
        save_item = wx.MenuItem(file_menu, wx.ID_SAVE, "&Save")
        quit_item = wx.MenuItem(file_menu, wx.ID_EXIT, "&Quit")

        file_menu.Append(wx.ID_NEW, "&New")        
        file_menu.AppendItem(open_item)
        file_menu.AppendItem(save_item)
        file_menu.AppendSeparator()
        file_menu.AppendItem(quit_item)

        # edit menu
        edit_menu        = wx.Menu()
        copy_item        = wx.MenuItem(edit_menu, wx.ID_COPY, "Copy")
        delt_item        = wx.MenuItem(edit_menu, wx.ID_DELETE, "Delete")
        nwcdr_item       = wx.MenuItem(edit_menu, wx.ID_ANY, "New Card: Right")
        nwcdb_item       = wx.MenuItem(edit_menu, wx.ID_ANY, "New Card: Below")
        nwhdr_item       = wx.MenuItem(edit_menu, wx.ID_ANY, "New Header: Right")
        nwhdb_item       = wx.MenuItem(edit_menu, wx.ID_ANY, "New Header: Below")
        ctrltab_item     = wx.MenuItem(edit_menu, wx.ID_ANY, "Next Card")
        ctrlshfttab_item = wx.MenuItem(edit_menu, wx.ID_ANY, "Previous Card")
        unsel_item       = wx.MenuItem(edit_menu, wx.ID_ANY, "Unselect All")

        edit_menu.AppendItem(copy_item)
        edit_menu.AppendItem(delt_item)
        edit_menu.AppendItem(nwcdr_item)
        edit_menu.AppendItem(nwcdb_item)
        edit_menu.AppendItem(nwhdr_item)
        edit_menu.AppendItem(nwhdb_item)
        edit_menu.AppendItem(ctrltab_item)

        # layout menu
        layout_menu = wx.Menu()                
        harr_item = wx.MenuItem(layout_menu, wx.ID_ANY, "Arrange &Horizontally")
        varr_item = wx.MenuItem(layout_menu, wx.ID_ANY, "Arrange &Vertically")
        layout_menu.AppendItem(harr_item)
        layout_menu.AppendItem(varr_item)

        # debug menu
        debug_menu = wx.Menu()                
        debug_item = wx.MenuItem(debug_menu, wx.ID_ANY, "&Debug")
        debug_menu.AppendItem(debug_item)

        # search menu
        # this is an invisible search menu, used only to have a MenuItem
        # to append to the AcceleratorTable
        search_menu = wx.Menu()
        search_item = wx.MenuItem(search_menu, wx.ID_ANY, "Search")
        next_item   = wx.MenuItem(search_menu, wx.ID_ANY, "Next")
        prev_item   = wx.MenuItem(search_menu, wx.ID_ANY, "Previous")
        search_menu.AppendItem(search_item)

        # bindings
        self.Bind(wx.EVT_MENU, self.OnQuit      , quit_item)
        self.Bind(wx.EVT_MENU, self.OnCopy      , copy_item)
        self.Bind(wx.EVT_MENU, self.OnDelete    , delt_item)
        self.Bind(wx.EVT_MENU, self.OnSave      , save_item)
        self.Bind(wx.EVT_MENU, self.OnOpen      , open_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlTab   , ctrltab_item)
        self.Bind(wx.EVT_MENU, self.OnHArrange  , harr_item)
        self.Bind(wx.EVT_MENU, self.OnVArrange  , varr_item)
        self.Bind(wx.EVT_MENU, self.OnDebug     , debug_item)
        self.Bind(wx.EVT_MENU, self.OnEsc       , unsel_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlF     , search_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlG     , next_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlShftG , prev_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlRet   , nwcdr_item)
        self.Bind(wx.EVT_MENU, self.OnAltRet    , nwhdr_item)
        self.Bind(wx.EVT_MENU, self.OnCtrlShftTab , ctrlshfttab_item)        
        self.Bind(wx.EVT_MENU, self.OnCtrlShftRet , nwcdb_item)
        self.Bind(wx.EVT_MENU, self.OnAltShftRet  , nwhdb_item)        

        # shortcuts
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27, unsel_item.GetId())) # ESC
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 127, delt_item.GetId())) # DEL
        
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D"),      debug_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("F"),      search_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G"),      next_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_TAB,    ctrltab_item.GetId()))                
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_RETURN, nwcdr_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_RETURN, nwhdr_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , ord("G"), prev_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_RETURN, nwcdb_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_TAB,    ctrlshfttab_item.GetId()))
        self.accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_ALT  , wx.WXK_RETURN, nwhdb_item.GetId()))

        # finish up        
        bar.Append(file_menu, "&File")
        bar.Append(edit_menu, "&Edit")
        bar.Append(layout_menu, "&Layout")        
        bar.Append(debug_menu, "&Debug")
        self.SetMenuBar(bar)

    def InitSearchBar(self):
        if not self.ui_ready:
            # make new
            ctrl = wx.SearchCtrl(self, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
            ctrl.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.Search)
            ctrl.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.CancelSearch)
            ctrl.Bind(wx.EVT_TEXT_ENTER, self.Search)
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
        del_it = toolbar.AddLabelTool(wx.ID_ANY, "Delete",
                                      wx.ArtProvider.GetBitmap(wx.ART_DELETE),
                                      kind=wx.ITEM_NORMAL)
        cpy_it = toolbar.AddLabelTool(wx.ID_ANY, "Copy",
                                      wx.ArtProvider.GetBitmap(wx.ART_COPY),
                                      kind=wx.ITEM_NORMAL)

        # bindings
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
        self.InitNotebook(sz)

        # execute only the first time
        if not self.ui_ready:
            self.InitMenuBar()
            self.CreateStatusBar()
            self.InitSearchBar()
            self.InitToolBar()
            
        self.ui_ready = True

    def InitNotebook(self, size = wx.DefaultSize):
        nb = wx.Notebook(self, size=size)

        # make starting page
        pg = Page(nb, size = size)
        # pg.board.SetBackgroundColour(Page.BACKGROUND_CL)
        nb.AddPage(pg, "TabOne")

        # UI setup
        vbox = self.GetSizer()
        if not vbox: vbox = wx.BoxSizer(wx.VERTICAL)
        nb_box = wx.BoxSizer(wx.HORIZONTAL)
        nb_box.Add(nb, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        vbox.Add(nb_box, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # set members
        self.notebook = nb
        self.board = pg.board        

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
        print self.board.GetCards()[0].title.text.GetSize()
        print self.board.GetCards()[0].title.entry.GetSize()

    def Save(self, out_file, d):
        """Save the data in the dict d in the file out_file."""
        with open(out_file, 'w') as out:
            pickle.dump(d, out)

    def Load(self, path):
        carddict = {}
        board = self.GetCurrentBoard()
        with open(path, 'r') as f: carddict = pickle.load(f)
        for id, values in carddict.iteritems():
            if values["class"] == "Content":
                board.NewCard(pos     = values["pos"],
                              label   = values["label"],
                              title   = str(values["title"]),
                              kind    = values["kind"],
                              content = values["content"])
            elif values["class"] == "Header":
                board.NewHeader(pos   = values["pos"],
                                label = values["label"],
                                txt   = values["header"])

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

    def OnHArrange(self, ev):
        self.GetCurrentBoard().HArrangeSelectedCards()
        self.Log("Horizontal arrange.")

    def OnVArrange(self, ev):
        self.GetCurrentBoard().VArrangeSelectedCards()
        self.Log("Vertical arrange.")

    def OnEsc(self, ev):
        """Unselect all cards."""
        self.GetCurrentBoard().UnselectAll()

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

    def OnZoom(self, ev):
        """Zoom in and out."""
        scale = ev.GetString()[:-1] # all strings have the % sign at the end
        scale = float(scale) / 100
        print scale
        self.GetCurrentBoard().SetScale(scale)

    def OnCtrlF(self, ev):
        """Show/hide the search control."""
        print "ctrl f"
        shwn = self.search_ctrl.IsShown()
        
        if not shwn:
            self.InitSearchBar()
            self.search_ctrl.Show()
            self.search_ctrl.SetFocus()
        else:
            self.search_ctrl.Hide()
            self.board.SetFocus()
            self.searching = None

    def OnCtrlG(self, ev):
        """Go to next search find."""
        print "ctrl g"
        if self.searching != None:
            i = self.searching + 1
            if i >= len(self.search_find): i = 0
            self.search_find[i].SetFocus()
            self.search_find[i].SetSelection(0, 3)
            pos = self.search_find[i].GetPosition()
            self.GetCurrentBoard().Scroll(-1, pos.y / Page.PIXELS_PER_SCROLL)
            self.searching = i

    def OnCtrlShftG(self, ev):
        """Go to previous search find."""
        print "ctrl shft g"
        if self.searching != None:
            i = self.searching - 1
            if i < 0: i = len(self.search_find) - 1
            self.search_find[i].SetFocus()
            self.search_find[i].SetSelection(0, 3)
            self.searching = i

    def OnToolBarDelete(self, ev):
        print "toolbar delete"

    def OnToolBarCopy(self, ev):
        print "toolbar copy"
    
    def OnCtrlTab(self, ev):
        """Selects next card."""
        card = self.FindFocus().GetParent()
        self.GetCurrentBoard().GetNextCard(card).SetFocus()

    def OnCtrlShftTab(self, ev):
        """Selects previous card."""
        card = self.FindFocus().GetParent()
        self.GetCurrentBoard().GetPrevCard(card).SetFocus()

    def OnBitmapShow(self, ev):
        """Called when the bitmap is shown:enalbe scribbling mode."""
        if ev.IsShown():
            print "bitmap show"

    def OnBitmapLeftDown(self, ev):
        print "bitmap click"
    
    def OnCtrlRet(self, ev):
        """Add a new content card to the board, to the right of the current card."""
        self.PlaceNewCard("Content", False)

    def OnCtrlShftRet(self, ev):
        """Add a new content card to the board, below of the current one."""
        self.PlaceNewCard("Content", True)

    def OnAltRet(self, ev):
        """Add a new header to the board, to the right of the current card."""
        self.PlaceNewCard("Header", False)
        
    def OnAltShftRet(self, ev):
        """Add a new header to the board, to the right of the current card."""
        self.PlaceNewCard("Header", True)

    def OnSave(self, ev):
        """Save file."""
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

        self.Log("Saved file" + self.cur_file)

    def OnOpen(self, ev):
        """Open file."""
        # ask for a file name
        fd = wx.FileDialog(self, "Open", os.getcwd(), "", "P files (*.p)|*.p|All files|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        # fd = wx.FileDialog(self, "Open", os.getcwd(), "", "",
        #                    wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind

        self.InitUI()                     # setup new UI elements
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
