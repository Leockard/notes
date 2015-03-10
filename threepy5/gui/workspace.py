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
    Show()s the `Board`, but adds it to the sizer specializing in showing the
    main current content of this `Workspace`, called "the working sizer" within
    the code.
    """

    def __init__(self, parent):
        """Constructor."""
        super(Workspace, self).__init__(parent=parent)
        self.Deck = py5.AnnotatedDeck()
        self._init_board()
        self._init_canvas()        
        self._init_UI()

        
    ### init methods

    def _init_board(self):
        self.Board = board.Board(self)
        self.Board.Deck = self.Deck

    def _init_canvas(self):
        self.Canvas = Canvas(self)
        self.Canvas.Annotation = self.Deck.annotation

    def _init_UI(self):
        """Initialize this `Workspace`'s GUI and controls."""
        self._init_sizers()        
        # self._init_view()
        # self._init_sidebar()
        # self._init_buttonBar()

        # self.WorkOn("Board")

    def _init_sizers(self):
        # assumes all controls such as self.Board, self.Canvas, etc already exist
        work = wx.BoxSizer(wx.HORIZONTAL)
        work.Add(self.Board, proportion=1, flag=wx.EXPAND, border=0)

        main = wx.BoxSizer(wx.VERTICAL)
        main.Add(work, proportion=1, flag=wx.EXPAND, border=0)
        
        self.Sizer = main        
        self.working_sizer = work

    ### methods

    # def WorkOn(self, name):
