# -*- coding: utf-8 -*-
"""Contains the `Canvas` class, which allows the user to doodle over the `Deck`.
Also contains the `Workspace` class, which holds functionality to change between
`Board` and `Canvas`. As such, `Workspace` is the GUI equivalent of an
`AnnotatedDeck`.
"""
import wx
import threepy5.threepy5 as py5
import board


######################
# Class Canvas
######################

class Canvas(wxutils.AutoSize):
    """An `AutoSize` object which holds a `Canvas` as its only child."""
    
    def __init__(self, parent, size=wx.DefaultSize, pos=wx.DefaultPosition):
        """Constructor.

        * `parent: ` the parent `wx.Window`.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultPosition`.
        """
        super(Canvas, self).__init__(parent)

        # controls        
        ctrl = CanvasBase(self, bitmap=wx.NullBitmap)

        # boxes
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)
        box.Add(ctrl, proportion=1)

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)

        # finish up        
        self.ctrl = ctrl

                
    ### Behavior functions

    def SetOffset(self, pt):
        """Set the offset.

        * `pt: ` a (x, y) point.
        """
        self.ctrl.SetOffset(pt)

    def GetOffset(self):
        """Get the current offset.

        `returns: ` a (x, y) point.
        """
        return self.ctrl.GetOffset()

    def SetBackground(self, bmp):
        """Set the background over which to draw.

        * `bmp: ` a `wx.Bitmap` to serve as background.
        """
        if bmp:
            self.ctrl.SetBitmap(bmp)
            self.FitToChildren()

            
    ### Auxiliary functions

    def Dump(self):
        """Returns a `list` with all the info contained in this `Canvas`.

        `returns: ` a `list` of the form [(colour1, thickness1, [pt11, pt12, ...]), (colour2, thickness2, [pt21, pt22, ...]), ...].
        """
        return self.ctrl.lines

    def Load(self, li):
        """Load from a `list` returned by `Canvas.Dump`."""
        self.ctrl.lines = li


    ### Callbacks

    def OnShow(self, ev):
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
