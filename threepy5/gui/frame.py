# -*- coding: utf-8 -*-
"""Contains the `ThreePyFiveFrame` class, the main `wx.Frame` which handles user input"""

import wx
import wxutils
import workspace
import threepy5.threepy5 as py5


##########################
# CustomSearchCtrl class
##########################

class CustomSearchCtrl(wx.SearchCtrl):
    """A specialized `wx.SearchCtrl` for `threepy5`."""

    def __init__(self, parent, style=wx.TE_PROCESS_ENTER):
        """Constructor."""
        super(CustomSearchCtrl, self).__init__(parent=parent, style=style)

        self.search_find = []
        self.search_str = ""
        self.boxset = None
        self.welcome = None
        self.search_head = None    # contains the current search index
                                   # when not searching, set to None

        self.Bind(wx.EVT_TEXT, self._on_text)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self._on_cancel_btn)
        self.Bind(wx.EVT_TEXT_ENTER, self._on_enter)


    ### methods

    def AutoPosition(self, board):
        """Position the search bar relative to a board.

        * `board: `, a `Board`.
        """
        top   = board.Rect.top
        right = board.Rect.right - self.Rect.width
        self.Position = (right, top)


    ### callbacks

    def _on_text(self, ev):
        pass

    def _on_cancel_btn(self, ev):
        pass

    def _on_enter(self, ev):
        pass
        


##########################
# ThreePyFiveFrame class
##########################

class Shelf(wx.Notebook):
    """A `Shelf` is where you store a `Box`. Just as `Box` stores multiple `Decks`,
    a `Shelf` notebook stores multiple `Workspaces`, each in one page.
    """
    
    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `ThreePyFiveFrame`.
        """
        super(Shelf, self).__init__(parent)
        self._init_box()
        self._init_menu()
        self._init_accels()


    ### init methods

    def _init_box(self):
        box = py5.Box()
        py5.subscribeList("decks", self._on_new_deck, self._on_pop_deck, box)

        box.NewDeck("foo bar")
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
        parent._init_shelf()

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

        # self.cur_file = ""
        self._init_UI()

        # self._init_shelf()

        self._init_accels()
        self.Show()


    ### init methods

    def _init_UI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        self.Sizer = box

        welp = WelcomePage(self)
        self.Sizer.Add(welp, proportion=1, flag=wx.EXPAND)
        self._welcome = welp

    def _init_accels(self):
        ghost = wx.Menu()
        
        dbg = wx.MenuItem(ghost, wx.ID_ANY, "Debug")
        self.Bind(wx.EVT_MENU, self._on_debug, dbg)
        accels = [wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("D") , dbg.GetId())]
        
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def _init_shelf(self):
        self._welcome.Hide()
        
        shelf = Shelf(self)
        self.Shelf = shelf

        self.Sizer.Clear()                
        self.Sizer.Add(shelf, proportion=1, flag=wx.EXPAND, border=0)
        self.Sizer.Layout()


    ### callbacks

    def _on_debug(self, ev):
        print "------DEBUG-----"
        print self.FindFocus()

