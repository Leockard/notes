# -*- coding: utf-8 -*-
"""Contains the `ThreePyFiveFrame` class, the main `wx.Frame` which handles user input"""

import wx
import re
import os
import pickle
import wxutils
import board
import workspace
import threepy5.threepy5 as py5


##########################
# CustomSearchCtrl class
##########################

class CustomSearchCtrl(wx.SearchCtrl):
    """A specialized `wx.SearchCtrl` for `threepy5`."""
    SUCCESS  = 2
    FAILURE  = 4
    EMPTY    = 8
    _COLOURS = {SUCCESS: wx.YELLOW, FAILURE: wx.RED, EMPTY: wx.WHITE}

    def __init__(self, parent, style=wx.TE_PROCESS_ENTER):
        """Constructor."""
        super(CustomSearchCtrl, self).__init__(parent=parent, style=style)

        self._str = ""
        """The current search string."""
        
        self._match = []
        """A list of (ctrl, pos) tuples where `ctrl` is a text control and `pos` is
        the position where there's a match of the current search string."""

        self._head = None
        """Points to the index in `self._match` of the currently focused search result."""

        self._txt_ctrls = []
        """A list of (str, ctrl) tuples where `ctrl` is a text control and `str` is its
        contents at the time of initializing search. These are all the fields where search
        is performed."""

        self.Bind(wx.EVT_TEXT, self._on_text)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_cancel_btn)
        self.Bind(wx.EVT_TEXT_ENTER, self._on_enter)
        self.Bind(wx.EVT_SHOW, self._on_show)
        self._init_accels()        

        
    ### init methods

    def _init_accels(self):
        accels = []
        ghost = wx.Menu()

        esc = wx.MenuItem(ghost, wx.ID_ANY, "esc")
        self.Bind(wx.EVT_MENU, self._on_esc, esc)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27 , esc.GetId()))

        prev = wx.MenuItem(ghost, wx.ID_ANY, "previous")
        self.Bind(wx.EVT_MENU, self._on_shft_ctrl_g, prev)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL, ord("G") , prev.GetId()))

        nxt = wx.MenuItem(ghost, wx.ID_ANY, "next")
        self.Bind(wx.EVT_MENU, self._on_ctrl_g, nxt)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("G") , nxt.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

        
    ### properties

    @property
    def Status(self):
        """One of `CustomSearchCtrl.SUCCESS`, `FAILURE` or `EMPTY`."""
        # this property doesn't have a setter to keep it private
        # see self._set_status() instead
        return self._status

            
    ### methods

    def _set_status(self, status):
        """Private setter for `self.Status`.

        * `status: ` one of `CustomSearchCtrl.SUCCESS`, `FAILURE` or `EMPTY`.
        """
        if status in self._COLOURS.keys():
            self.BackgroundColour = self._COLOURS[status]
        if status is self.SUCCESS:
            for ctrl, index in self._match:
                ctrl.SetStyle(index, index + len(self._str), wx.TextAttr(wx.NullColour, wx.YELLOW))
        elif status is self.FAILURE:
            self.BackgroundColour = wx.RED
            self._match = []
            self._str   = ""
            self._head  = None
        elif status is self.EMPTY:
            self._search_cleanup()
            self.BackgroundColour = wx.WHITE

    def AutoPosition(self):
        """Position the search bar relative to the parent."""
        rect  = self.Parent.Shelf.CurrentWorkspace.Rect
        top   = rect.top
        right = rect.right - self.Rect.width
        self.Position = (right, top)

    def _search_start(self):
        self._match = []
        self._str   = ""
        self._head  = None

        # where are we searching?
        wins = self.Parent.Shelf.CurrentWorkspace.CurrentControl.Cards

        # gather all (lower case) values in which to search
        # including the control they appear in
        txt_ctrls = []
        for w in wins:
            if isinstance(w, board.ContentWin):
                txt_ctrls.append((w.Card.title.lower(),   w._title))
                txt_ctrls.append((w.Card.content.lower(), w._content))
            elif isinstance(w, board.HeaderWin):
                txt_ctrls.append((w.Card.header.lower(),  w._header))

        self._txt_ctrls = txt_ctrls

    def CancelSearch(self):
        self._search_cleanup()
        self.Hide()
        self.Parent.SetFocus()
        # set focus on last result
        # return the focus to the last selected card

    def _search_cleanup(self):
        """Clean up control highlighting."""
        if self._match:
            for ctrl, index in self._match:
                attr = ctrl.DefaultStyle
                attr.BackgroundColour = ctrl.BackgroundColour
                ctrl.SetStyle(index, index + len(self._str), attr)

    def _search_update(self):
        """Search the current text in the search bar in all of the `Card`s'
        texts (titles, contents, etc). Cycle through finds with (SHIFT+)CTRL+G.
        """
        self._search_cleanup()
        s = self.Value.lower()

        match = []
        for txt, ctrl in self._txt_ctrls:
            pos = [m.start() for m in re.finditer(s, txt)]
            for p in pos:
                match.append((ctrl, p))

        if match:
            self._match = match
            self._str   = s
            self._head  = 0
            self._set_status(self.SUCCESS)
        else:
            self._set_status(self.FAILURE)
        
    def PrevSearchResult(self):
        """Highlights the previous search result."""
        if self._head != None:
            old = i = self._head
            new = i - 1
            if new < 0: new = len(self._match) - 1
            self._jump_search_match(old, new)
            self._head = new

    def NextSearchResult(self):
        """Highlights the next search result with a strong highlight and scrolls it into view."""
        if self._head != None:
            old = i = self._head
            new = i + 1
            if new >= len(self._match): new = 0
            self._jump_search_match(old, new)
            self._head = new

    def _jump_search_match(self, old, new):
        """Unhighlights the `old` search result and highlights the `new` one. Don't use this
        method directly, instead use `PrevSearchResult` and `NextSearchResult`.

        * `old: ` a valid index in the internal search result list (`self._match`).
        * `new: ` idem.
        """
        ctrl, pos = self._match[old]
        ctrl.SetStyle(pos, pos + len(self._str), wx.TextAttr(None, wx.YELLOW))

        ctrl, pos = self._match[new]
        ctrl.SetStyle(pos, pos + len(self._str), wx.TextAttr(None, wx.RED))

        # make sure the matching ctrl is visible
        win = wxutils.GetCardAncestor(ctrl)
        if win:
            self.Parent.Shelf.CurrentWorkspace.Board.ScrollToCard(win)
            if isinstance(win, board.ContentWin):
                if win.Card.collapsed:
                    win.Card.collapsed = False
                win.ScrollToChar(pos)


    ### callbacks

    def _on_show(self, ev):
        if ev.IsShown():
            self.AutoPosition()
            self._search_start()

    def _on_text(self, ev):
        if ev.String:
            self._search_update()
        else:
            self._set_status(self.EMPTY)

    def _on_cancel_btn(self, ev):
        self.CancelSearch()

    def _on_esc(self, ev):
        self.CancelSearch()

    def _on_enter(self, ev):
        if self.Value:
            self._search_update()

    def _on_shft_ctrl_g(self, ev):
        self.PrevSearchResult()

    def _on_ctrl_g(self, ev):
        self.NextSearchResult()



##########################
# ThreePyFiveFrame class
##########################

class Shelf(wx.Notebook):
    """A `Shelf` is where you store a `Box`. Just as `Box` stores multiple `Decks`,
    a `Shelf` notebook stores multiple `Workspaces`, each in one page.
    """
    
    def __init__(self, parent, placeholder=True):
        """Constructor.

        * `parent: ` the parent `ThreePyFiveFrame`.
        """
        super(Shelf, self).__init__(parent)
        self._init_box()
        self._init_menu()
        self._init_accels()

        if placeholder:
            self.Box.NewDeck("Untitled Deck")


    ### init methods

    def _init_box(self, placeholder=True):
        box = py5.Box()
        py5.subscribeList("decks", self._on_new_deck, self._on_pop_deck, box)
        self.Box = box                

    def _init_menu(self):
        menu = wx.Menu()
        # self.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
        
        name = wx.MenuItem(menu, wx.ID_ANY, "Change current box name")
        # self.Bind(wx.EVT_MENU, self._on_name_change, name)

        close = wx.MenuItem(menu, wx.ID_CLOSE, "Close box")
        # self.Bind(wx.EVT_MENU, self._on_close, close)

        pg_forward = wx.MenuItem(menu, wx.ID_ANY, "Move box forward")
        # self.Bind(wx.EVT_MENU, self._on_box_forward, pg_forward)

        menu.AppendItem(name)
        menu.AppendItem(pg_forward)
        menu.AppendItem(close)

    def _init_accels(self):
        accels = []
        ghost = wx.Menu()

        ctrln = wx.MenuItem(ghost, wx.ID_ANY, "ctrln")
        self.Bind(wx.EVT_MENU, self._on_ctrl_n, ctrln)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("N") , ctrln.GetId()))

        ctrlpgu = wx.MenuItem(ghost, wx.ID_ANY, "ctrl page up")
        self.Bind(wx.EVT_MENU, self._on_ctrl_pg_up, ctrlpgu)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_PAGEUP , ctrlpgu.GetId()))

        ctrlpgd = wx.MenuItem(ghost, wx.ID_ANY, "ctrl page down")
        self.Bind(wx.EVT_MENU, self._on_ctrl_pg_down, ctrlpgd)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_PAGEDOWN , ctrlpgd.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))


    ### properties
    
    @property
    def CurrentWorkspace(self):
        """The `Workspace` currently in view."""
        return self.GetCurrentPage()

    
    ### methods    

    def NewDeck(self):
        """Creates a new `AnnotatedDeck`, by asking the user for the name.

        `returns: ` `True` if a new `Deck` was succesfully created.
        """
        dlg = wx.TextEntryDialog(self, "New deck name: ")
        if dlg.ShowModal() == wx.ID_OK:
            self.Box.NewDeck(dlg.Value)
            return True
        else:
            return False


    ### callbacks

    def _on_ctrl_n(self, ev):
        self.NewDeck()

    def _on_ctrl_pg_up(self, ev):
        sel = self.Selection
        if sel > 0:
            self.Selection = sel - 1

    def _on_ctrl_pg_down(self, ev):
        sel = self.Selection
        if sel < self.PageCount - 1:
            self.Selection = sel + 1


    ### subscribers
    
    def _on_new_deck(self, val):
        ws = workspace.Workspace(self)
        ws.Deck = val
        self.AddPage(ws, val.name, select=True)
        ws.Board.SetFocus()

    def _on_pop_deck(self, val):
        print "pop deck"



######################
# WelcomePage class
######################

class WelcomePage(wx.Panel):
    """The panel that is displayed as soon as the user starts the
    application. Gives options to load a file or start a new one.
    """
    
    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `ThreePyFiveFrame`.
        """
        super(WelcomePage, self).__init__(parent)
        self._init_UI()
        

    ### init methods

    def _init_UI(self):
        newb  = wx.Button(self, label="New box set")
        loadb = wx.Button(self, label="Load box set")
        
        newb.Bind(wx.EVT_BUTTON, self._on_new)
        loadb.Bind(wx.EVT_BUTTON, self._on_load)        

        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)
        box.Add(newb, proportion=0)
        box.Add(loadb, proportion=0)


    ### callbacks

    def _on_new(self, ev):
        parent = self.Parent
        parent._init_shelf(placeholder=True)

    def _on_load(self, ev):
        self.Parent._on_open(None)
        

        
##########################
# ThreePyFiveFrame class
##########################
        
class ThreePyFiveFrame(wx.Frame):
    """A `ThreePyFiveFrame` handles a `Box` as well as application-level functionality."""
    
    DEFAULT_SZ = (800, 600)
    DEFAULT_TITLE = "3py5"

    def __init__(self, parent=None, title=DEFAULT_TITLE, size=DEFAULT_SZ, style=wx.DEFAULT_FRAME_STYLE):
        """Constructor."""
        super(ThreePyFiveFrame, self).__init__(parent, title=title, size=size, style=style)

        self._init_UI()
        self._init_search()
        self._init_accels()

        self._file_name = ""
        """Path to the ".p" file."""

        self.Show()


    ### init methods

    def _init_UI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        self.Sizer = box

        welp = WelcomePage(self)
        self.Sizer.Add(welp, proportion=1, flag=wx.EXPAND)
        self._welcome = welp

        self._init_menu()
        self.CreateStatusBar()

    def _init_menu(self):
        bar = wx.MenuBar()

        file_menu = wx.Menu()
        new = wx.MenuItem(file_menu, wx.ID_NEW,  "&New")
        opn = wx.MenuItem(file_menu, wx.ID_OPEN, "&Open")
        save = wx.MenuItem(file_menu, wx.ID_SAVE, "&Save")
        quit = wx.MenuItem(file_menu, wx.ID_EXIT, "&Quit")

        file_menu.AppendItem(new)
        file_menu.AppendItem(opn)
        file_menu.AppendItem(save)
        file_menu.AppendSeparator()
        file_menu.AppendItem(quit)

        self.Bind(wx.EVT_MENU, self._on_new  , new)
        self.Bind(wx.EVT_MENU, self._on_open , opn)
        self.Bind(wx.EVT_MENU, self._on_save , save)
        self.Bind(wx.EVT_MENU, self._on_exit , quit)
        
        
        bar.Append(file_menu, "&File")
        self.SetMenuBar(bar)

    def _init_accels(self):
        ghost = wx.Menu()
        
        dbg = wx.MenuItem(ghost, wx.ID_ANY, "Debug")
        self.Bind(wx.EVT_MENU, self._on_debug, dbg)
        accels = [wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D") , dbg.GetId())]

        ctrlf = wx.MenuItem(ghost, wx.ID_ANY, "ctrlf")
        self.Bind(wx.EVT_MENU, self._on_ctrl_f, ctrlf)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("F") , ctrlf.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def _init_search(self):
        ctrl = CustomSearchCtrl(self)
        ctrl.Hide()
        self._search_ctrl = ctrl

    def _init_shelf(self, placeholder):
        self._welcome.Hide()
        
        shelf = Shelf(self, placeholder)
        self.Shelf = shelf

        self.Sizer.Clear()                
        self.Sizer.Add(shelf, proportion=1, flag=wx.EXPAND, border=0)
        self.Sizer.Layout()


    ### methods

    def Open(self):
        path = "/home/leo/research/reading_notes/Kandel - Principles of Neural Science"
        format_str = "P files (*.p)|*.p|All files|*.*"
        fd = wx.FileDialog(self, "Open", path, "", format_str, wx.FD_OPEN|wx.FD_FILE_MUST_EXIST)

        if fd.ShowModal() == wx.ID_OK:
            with open(fd.GetPath(), "r") as f:
                self._file_name = fd.GetPath()
                self._init_shelf(placeholder=False)
                
                self.Shelf.Hide()
                self.Shelf.Box.Load(pickle.load(f))
                self.Shelf.Show()
            self.Shelf.SetFocus()

    def Save(self):
        # remember focus to restore after saving
        focus = self.FindFocus()
        if isinstance(focus, wx.TextCtrl):
            caret = focus.GetInsertionPoint()

        # if we don't have a path yet, ask for one
        path = ""
        if self._file_name == "":
            fd = wx.FileDialog(self, "Save", os.getcwd(), "", "P files (*.p)|*.p",
                               wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            if fd.ShowModal() == wx.ID_CANCEL:
                path = ""
            else:
                path = fd.GetPath()
        else:
            path = self._file_name

        if path:
            with open(path, 'w') as out:
                pickle.dump(self.Shelf.Box.Dump(), out)
            self._file_name = path

        if focus:
            focus.SetFocus()
        if isinstance(focus, wx.TextCtrl):
            focus.SetInsertionPoint(caret)

    def Log(self, s):
        """Log the string `s` into the status bar.

        `s: ` a string.
        """
        self.StatusBar.SetStatusText(s)


    ### callbacks
    
    def _on_ctrl_f(self, ev):
        if not self._search_ctrl.IsShown():
            self._search_ctrl.Show()
            self._search_ctrl.SetFocus()
        else:
            self._search_ctrl.CancelSearch()

    def _on_new(self, ev):
        self.Shelf.NewDeck()
        
    def _on_open(self, ev):
        self.Open()
        
    def _on_save(self, ev):
        self.Save()
    
    def _on_exit(self, ev):
        self.Close()

    def _on_debug(self, ev):
        print "------DEBUG-----"
        win = self.Shelf.CurrentWorkspace.Board.Cards[-1]
        ctrl = win._content
        for i in range(len(ctrl.Value)):
            attr = wx.TextAttr()
            ctrl.GetStyle(i, attr)
            print attr.BackgroundColour
