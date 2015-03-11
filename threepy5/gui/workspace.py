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
            self.FitToChildren()

            
    ### callbacks

    def _on_show(self, ev):
        """Listens to `wx.EVT_SHOW` events."""
        if ev.IsShown():
            self.ctrl.DrawLines()


                        
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
        
        self._init_board()
        self._init_canvas()        
        self._init_UI()
        
        self.WorkOn("Board")

        
    ### init methods

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

    def _init_UI(self):
        """Initialize this `Workspace`'s GUI and controls."""
        self._init_sizers()        
        # self._init_view()
        # self._init_sidebar()
        self._init_toolbar()

    def _init_sizers(self):
        # assumes all controls such as self.Board, self.Canvas, etc already exist
        work = wx.BoxSizer(wx.HORIZONTAL)
        work.Add(self.Board, proportion=1, flag=wx.EXPAND, border=0)

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(work, proportion=1, flag=wx.EXPAND, border=0)
        
        self.Sizer = main        
        self._working_sizer = work
        
    def _init_toolbar(self):
        # assumes the panel's sizer is already set
        bar = wx.ToolBar(self, style=wx.TB_HORIZONTAL|wx.TB_BOTTOM)
        getBMP = wx.ArtProvider.GetBitmap

        togg = bar.AddLabelTool(wx.ID_ANY, "toggle", bitmap=getBMP(wx.ART_CLOSE), kind=wx.ITEM_NORMAL)
        zoom = bar.AddControl(self.ZoomCombo(bar))
        
        self.Bind(wx.EVT_TOOL, self._on_toggle, togg)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(bar, proportion=1, flag=wx.EXPAND, border=0)
        self.Sizer.Add(box, proportion=0, flag=wx.EXPAND, border=0)

        bar.Realize()
        self._bar = bar
        self.zoom = zoom
        

    ### methods

    def WorkOn(self, ctrl):
        """Call to show ctrl in the working sizer.
        
        * `ctrl: `, the name of the ctrl to show, eg: "Board", "Canvas", etc.
        """
        if getattr(self, ctrl) in self._contents:
            window = getattr(self, ctrl)
            self._working_sizer.Clear()
            self._working_sizer.Add(window, proportion=1, flag=wx.EXPAND, border=0)
            for w in self._contents: w.Hide()
            window.Show()
            self.CurrentControl = window

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

            
    ### callbacks

    def _on_toggle(self, ev):
        print "toggle"
