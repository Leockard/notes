# -*- coding: utf-8 -*-
"""Contains the `Canvas` class, which allows the user to doodle over the `Deck`.
Also contains the `Workspace` class, which holds functionality to change between
`Board` and `Canvas`. As such, `Workspace` is the GUI equivalent of an
`AnnotatedDeck`.
"""
import wx
import wxutils
import board
import threepy5.threepy5 as py5
import threepy5.utils as utils
import re


######################
# Class Canvas
######################

class Canvas(wxutils.AutoSize):
    """An `AutoSize` object which holds a `Canvas` as its only child."""
    
    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `wx.Window`.
        """
        super(Canvas, self).__init__(parent)
        self._init_UI()
        self.Bind(wx.EVT_SHOW, self._on_show)
        self.Bind(wx.EVT_IDLE, self._on_idle)


    ### init methods

    def _init_UI(self):
        ctrl = wxutils.CanvasBase(self, bitmap=wx.NullBitmap)
        
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(ctrl, proportion=1, flag=wx.EXPAND)
        
        self.Sizer = box
        self.ctrl = ctrl        

                        
    ### methods

    def SetBackgroundBMP(self, bmp):
        """Set the background over which to draw.

        * `bmp: ` a `wx.Bitmap` to serve as background.
        """
        if bmp:
            self.ctrl.SetBitmap(bmp)
            self.ctrl._buffer = bmp
            self.FitToChildren()

    def _save_lines(self):
        self.Annotation.lines = self.ctrl.lines

            
    ### callbacks

    def _on_show(self, ev):
        if ev.IsShown():
            self.ctrl.DrawLines()

    def _on_idle(self, ev):
        self._save_lines()


        
######################
# CardView Class
######################        

class CardView(wx.Panel):
    """Displays a screen-sized `Content` `CardWin` to facilitate editing. While
    viewing, the `Card` is `Reparent`ed to this window.
    """
    WIN_PADDING = board.Board.WIN_PADDING
    BACKGROUND_CL = board.Board.BACKGROUND_CL
    TITLE_FONT   = (18, wx.SWISS, wx.ITALIC, wx.BOLD)
    CONTENT_FONT = (14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `Box`.
        """
        super(CardView, self).__init__(parent)
        self._cards = {}
        self._init_UI()


    ### init methods

    def _init_UI(self):
        self.BackgroundColour = self.BACKGROUND_CL
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(box)


    ### properties

    @property
    def Cards(self):
        """The `Card`s currently under viewing."""
        return self._cards.keys()

    
    ### methods

    def AddCard(self, win):
        """Adds one `CardWin` to the viewing control.

        * `win: ` a `CardWin`.
        """
        self._cards[win] = {}
        self._cards[win]["parent"] = win.Parent
        self._cards[win]["rect"]   = win.Rect
        pos = win.CaretPos
        win.Reparent(self)
        win.CaretPos = pos
        
        box = self.Sizer
        box.Add(win, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.WIN_PADDING)
        box.Layout()

    def SetCards(self, cards):
        """Clears previous `Card`s and views the new ones.

        * `cards: ` a `list` of `Card`s.
        """
        self.Clear()
        for c in cards: self.AddCard(c)

    def Restore(self):
        """Restores the viewed `Card`s to their original parents and positions."""
        for w in self._cards.keys():
            pos = w.CaretPos
            w.Reparent(self._cards[w]["parent"])
            w.Rect = self._cards[w]["rect"]
            w.CaretPos = pos
        self.Clear()

    def Clear(self):
        """Clear all viewed `Card`s."""
        self.Sizer.Clear()
        # for c in self._cards.keys():
        #     c.SetViewing(False)
        self._cards = {}


    ### callbacks

    def _on_cancel_view(self, ev):
        """Listens to `Card.EVT_CANCEL_VIEW` on every viewed `Card`."""
        self.Restore()
        event = card.Card.CancelViewEvent(id=wx.ID_ANY)
        event.SetEventObject(ev.GetEventObject())
        self.GetEventHandler().ProcessEvent(event)


        
######################
# TagView Class
######################        

class TagView(wx.Panel):
    """A sidebar that displays a `Content`'s tags."""

    TAGS_REGEX = "^(\w+):(.*)$"
    """Regex used to extract tags from a `Content`'s content text."""
    
    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `Box`.
        * `deck: ` the parent `Deck` of the `Card`s we are viewing.
        """
        super(TagView, self).__init__(parent)
        self._init_UI()

        self.Bind(wx.EVT_SHOW, self._on_show)


    ### init methods

    def _init_UI(self):
        """Initialize this window's GUI and controls."""
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)

        txt = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.txt = txt        
        box.Add(txt, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
    

    ### methods

    def ParseTags(self, txt):
        """Parses a string looking for tags.

        * `txt: ` a string, the contents of a `Content`.

        `returns: ` a string to display in the `TagView` view, representing the tags found in `text`.
        """
        string = ""
        results = re.findall(self.TAGS_REGEX, txt, re.MULTILINE)
        for tag, val in results:
            string += tag + ":" + val
            string += "\n\n"
        return string

    def ShowTags(self):
        """Shows the `card`'s tags.

        * `card: ` a `Content`, whose contents will be parsed.
        """
        win = wxutils.GetCardAncestor(self.FindFocus())
        if win and isinstance(win, board.ContentWin):
            self.txt.SetValue(self.ParseTags(win.Card.content))
    

    ### callbacks

    def _on_show(self, ev):
        if ev.IsShown():
            self.ShowTags()

        
                        
######################
# Class Workspace
######################

class Workspace(wx.Panel):
    """Holds an `AnnotatedDeck` and provides functionality to manipulate the
    interface between `Canvas` and `Board`.

    To be able to show different controls at the same time, `Workspace` handles
    a few sizers, which are setup at construction time and are be used throughout
    the lifetime of the instance. For example, `Workspace.ShowBoard()` not only
    `Show()`s the `Board`, but adds it to the sizer specializing in showing the
    main current content of this `Workspace`, called "the working sizer" within
    the code.
    """

    ZOOM_SCALES = ["50%", "100%", "150%", "200%"]

    ############################
    # helper Class ZoomCombo
    ############################

    class ZoomCombo(wx.ComboBox):
        """The `wx.ComboBox` for choosing the zoom scale."""

        ZOOM_CHOICES = ["50%", "100%", "150%", "200%"]

        def __init__(self, parent, choices=ZOOM_CHOICES, style=wx.TE_PROCESS_ENTER):
            """Constructor."""
            super(Workspace.ZoomCombo, self).__init__(parent=parent, choices=choices, style=style)
            self.Value = self.ZOOM_CHOICES[1]

            self.Bind(wx.EVT_COMBOBOX, self._on_combo)
            self.Bind(wx.EVT_TEXT_ENTER, self._on_enter)


        ### properties

        @property
        def Scale(self):
            return self.GetScaleFromStr(self.Value)
        

        ### methods

        def GetScaleFromStr(self, s):
            """Parses a string to extract a scale.
            
            * `s: ` is be a string of the type "\d\d\d?%?" (eg, "100%" or "75").
            
            `returns: `the float corresponding to the scale.
            """
            scale = 1.0
            if utils.isnumber(s):
                scale = float(s)/100
            elif utils.isnumber(s[:-1]) and s[-1] == "%":
                scale = float(s[:-1])/100
            return scale

        
        ### callbacks

        def _on_combo(self, ev):
            self.GrandParent.Zoom(self.GetScaleFromStr(ev.String))

        def _on_enter(self, ev):
            self.GrandParent.Zoom(self.GetScaleFromStr(ev.String))


    ##############
    # Workspace
    ##############

    def __init__(self, parent):
        """Constructor."""
        super(Workspace, self).__init__(parent=parent)
        self.Deck = py5.AnnotatedDeck()
        """The tracked `AnnotatedDeck`."""
        
        self._contents = []
        """A list of all controls that can be shown in the working sizer."""

        self.CurrentControl = None
        """The current window being shown in the working sizer."""

        self.Scale = 1.0
        """The current zoom scale."""
        
        self._init_UI()
        self._init_accels()
        
        self.WorkOn("Board")

        
    ### init methods

    def _init_UI(self):
        """Initialize this `Workspace`'s GUI and controls."""
        self._init_board()
        self._init_canvas()
        self._init_viewer()
        self._init_sidebar()
        self._init_sizers()        
        self._init_toolbar()

    def _init_board(self):
        bd = board.Board(self)
        bd.Hide()
        bd.Deck = self.Deck
        self._contents.append(bd)
        self.Board = bd

    def _init_canvas(self):
        cv = Canvas(self)
        cv.Hide()
        cv.Annotation = self.Deck.annotation
        self._contents.append(cv)
        self.Canvas = cv

    def _init_viewer(self):
        vw = CardView(self)
        vw.Hide()
        self._contents.append(vw)
        self.CardViewer = vw

    def _init_sidebar(self):
        sb = TagView(self)
        sb.Hide()
        self.TagViewer = sb

    def _init_sizers(self):
        # assumes all controls such as self.Board, self.Canvas, etc already exist

        work = wx.BoxSizer(wx.HORIZONTAL)
        work.Add(self.Board, proportion=1, flag=wx.EXPAND, border=0)
        
        side = wx.BoxSizer(wx.VERTICAL)
        side.Add(self.TagViewer, proportion=1, flag=wx.EXPAND, border=0)

        upper = wx.BoxSizer(wx.HORIZONTAL)
        upper.Add(side, proportion=0, flag=wx.EXPAND, border=0)
        upper.Add(work, proportion=1, flag=wx.EXPAND, border=0)

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(upper, proportion=1, flag=wx.EXPAND, border=0)
        
        self.Sizer = main        
        self._working_sizer = work
        self._sidebar_sizer = side
        
    def _init_toolbar(self):
        # assumes the panel's sizer is already set
        bar = wx.ToolBar(self, style=wx.TB_HORIZONTAL|wx.TB_BOTTOM)
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(bar, proportion=1, flag=wx.EXPAND, border=0)
        self.Sizer.Add(box, proportion=0, flag=wx.EXPAND, border=0)
        
        getBMP = wx.ArtProvider.GetBitmap

        togg = bar.AddLabelTool(wx.ID_ANY, "toggle", bitmap=getBMP(wx.ART_CLOSE), kind=wx.ITEM_NORMAL)
        self.Bind(wx.EVT_TOOL, self._on_toolbar_toggle, togg)
        
        zoom = self.ZoomCombo(bar)
        bar.AddControl(zoom)

        bar.Realize()
        self._bar = bar
        self.zoom = zoom

    def _init_accels(self):
        accels = []
        ghost = wx.Menu()
        
        ctrle = wx.MenuItem(ghost, wx.ID_ANY, "ctrle")
        self.Bind(wx.EVT_MENU, self._on_ctrl_e, ctrle)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("E"), ctrle.GetId()))

        ctrlp = wx.MenuItem(ghost, wx.ID_ANY, "ctrlp")
        self.Bind(wx.EVT_MENU, self._on_ctrl_plus, ctrlp)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("+"), ctrlp.GetId()))

        ctrlm = wx.MenuItem(ghost, wx.ID_ANY, "ctrlm")
        self.Bind(wx.EVT_MENU, self._on_ctrl_minus, ctrlm)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("-"), ctrlm.GetId()))

        ctrli = wx.MenuItem(ghost, wx.ID_ANY, "ctrli")
        self.Bind(wx.EVT_MENU, self._on_ctrl_i, ctrli)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("I"), ctrli.GetId()))

        fn9 = wx.MenuItem(ghost, wx.ID_ANY, "F9")
        self.Bind(wx.EVT_MENU, self._on_fn_9, fn9)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F9, fn9.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))
        

    ### methods

    def _get_board_bmp(self):
        """Returns a screenshot BMP of the `Board`."""
        sz = self.Board.ClientSize
        bmp = None

        if sz.width > -1 and sz.height > -1:
            bmp = wx.EmptyBitmap(sz.width, sz.height)
            dc = wx.MemoryDC()
            
            dc.SelectObject(bmp)
            dc.Blit(0, 0,                         # pos
                    sz.x, sz.y,                   # size
                    wx.ClientDC(self.Board),      # src
                    0, 0)                         # offset
            bmp = dc.GetAsBitmap()
            dc.SelectObject(wx.NullBitmap)

        return bmp

    def WorkOn(self, ctrl):
        """Call to show ctrl in the working sizer.
        
        * `ctrl: `, the name of the ctrl to show, eg: "Board", "Canvas", etc.
        """
        if getattr(self, ctrl) in self._contents:
            window = getattr(self, ctrl)
            
            if window is self.Canvas:
                self.Canvas.ctrl._offset = wx.Point(*self.Board.GetViewStartPixels())
                window.SetBackgroundBMP(self._get_board_bmp())
                
            self._working_sizer.Clear()
            self._working_sizer.Add(window, proportion=1, flag=wx.EXPAND, border=0)
            for w in self._contents: w.Hide()
            window.Show()
            self.CurrentControl = window

            window.SetFocus()
            self.Layout()

    def Zoom(self, new_scale):
        """Zoom in or out the `Board`. Effectively changes the scale of all
        relevant coordinates.

        * `new_scale: ` the new scale for all coordinates.
        """
        self.Board.Scale = new_scale
        self.Canvas.Scale = new_scale
        self.zoom.Value = str(int(new_scale * 100)) + "%"
        self.Scale = new_scale            

    def _toggle_board_canvas(self):
        if self.CurrentControl is self.Board:
            self.WorkOn("Canvas")
        elif self.CurrentControl is self.Canvas:
            self.WorkOn("Board")

    def ViewCard(self, win):
        self.CardViewer.SetCards([win])
        self.WorkOn("CardViewer")

    def CancelViewCard(self):
        self.CardViewer.Restore()
        self.WorkOn("Board")

    def ToggleSidebar(self):
        """Show/Hide the sidebar."""
        self._sidebar_sizer.Clear()
        
        if not self.TagViewer.IsShown():
            self._sidebar_sizer.Add(self.TagViewer, proportion=1, flag=wx.EXPAND, border=1)            
            self.TagViewer.Show()
        else:
            self._sidebar_sizer.Clear()
            self.TagViewer.Hide()
            
        self.Layout()
        
            
    ### callbacks

    def _on_toolbar_toggle(self, ev):
        self._toggle_board_canvas()

    def _on_ctrl_e(self, ev):
        self._toggle_board_canvas()

    def _on_ctrl_i(self, ev):
        if self.CurrentControl is self.Board:
            win = self.Board.FindFocusOrSelection()
            if win:
                self.ViewCard(win)
        elif self.CurrentControl is self.CardViewer:
            self.CancelViewCard()

    def _on_ctrl_plus(self, ev):
        scales = [self.zoom.GetScaleFromStr(s) for s in self.ZOOM_SCALES]
        cur_scale = self.zoom.Scale
        if cur_scale not in scales:
            scales.append(self.zoom.Scale)
            scales.sort()
        index = scales.index(cur_scale)

        if index < len(scales) - 1:
            new_scale = scales[index + 1]
            self.Zoom(new_scale)

    def _on_ctrl_minus(self, ev):
        scales = [self.zoom.GetScaleFromStr(s) for s in self.ZOOM_SCALES]
        cur_scale = self.zoom.Scale
        if cur_scale not in scales:
            scales.append(self.zoom.Scale)
            scales.sort()
        index = scales.index(cur_scale)

        if index > 0:
            new_scale = scales[index - 1]
            self.Zoom(new_scale)

    def _on_fn_9(self, ev):
        self.ToggleSidebar()

