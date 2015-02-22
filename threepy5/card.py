# -*- coding: utf-8 -*-
"""
A card is the "virutal index card"; it is a window that goes on the
Board. It can hold text, images, etc.
"""

import wx
import os
import wx.richtext as rt
import wx.lib.newevent as ne
from utilities import *


######################
# Card Class
######################

class Card(wx.Panel):
    BORDER_WIDTH = 2
    BORDER_THICK = 5
    SELECT_CL = (0, 0, 0, 0)

    bar = None

    DeleteEvent,   EVT_CARD_DELETE = ne.NewCommandEvent()
    CollapseEvent, EVT_CARD_COLLAPSE = ne.NewCommandEvent()
    ReqInspectEvent,    EVT_CARD_REQUEST_INSPECT = ne.NewEvent()
    CancelInspectEvent, EVT_CARD_CANCEL_INSPECT = ne.NewEvent()

    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        """Base class for every window that will be placed on Board. Override SetupUI()."""
        super(Card, self).__init__(parent, id, pos, size, style=style)
        self.main = None
        self.InitBorder()
        self.label = label
        self.scale = 1.0
        # frect stores the floating point coordinates of this card's rect
        # in the usual order: [left, top, width, height]. See Card.Stretch()
        self.frect = []

        # create CardBar
        # if Card.bar == None:
        #     Card.bar = CardBar.Create(self.GetParent())


    ### Behavior functions

    def __del__(self):
        pass

    def GetChildren(self):
        return self.main.GetChildren()

    def GetLabel(self):
        return self.label

    def ShowBar(self):
        CardBar.Associate(self)
        self.bar.Show()

    def HideBar(self):
        self.bar.Hide()

    def Delete(self):
        """Called by CardBar when the close button is pressed. Raises EVT_CARD_DELETE."""
        event = self.DeleteEvent(id=wx.ID_ANY)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        self.Hide()
        self.Destroy()

    def Select(self):
        """Show this card as selected. At the time, the border colour changes."""
        self.SetBorderColour(self.SELECT_CL)

    def Unselect(self):
        self.SetBorderColour(self.GetParent().GetBackgroundColour())

    def SetBorderColour(self, cl):
        super(Card, self).SetBackgroundColour(cl)

    def SetBackgroundColour(self, cl):
        self.main.SetBackgroundColour(cl)

    def GetBackgroundColour(self):
        return self.main.GetBackgroundColour()

    def SetCardSizer(self, sz):
        self.main.SetSizer(sz)

    def GetCardSizer(self):
        return self.main.GetSizer()

    def SetPosition(self, pt):
        """Sets this Card's position to pt. Overrides float coordinates."""
        super(Card, self).SetPosition(pt)
        self.ResetFRect()

    def Fit(self):
        """Fits this Card to its contents. Overrides float coordinates."""
        super(Card, self).Fit()
        self.ResetFRect()

    def SetSize(self, sz):
        """Set size to this window. Overrides float coordinates."""
        super(Card, self).SetSize(sz)
        self.ResetFRect()

    def Move(self, pt):
        """Sets this Card's position to pt. Overrides float coordinates."""
        super(Card, self).Move(pt)
        self.ResetFRect()

    def MoveBy(self, dx, dy):
        """
        Moves the card by the offsets dx, dy. Unlike SetPosition() and Move(),
        this method preserves the underlying float coordinates, if any. See Card.frect.
        """
        bd = self.GetParent()
        if not self.frect:
            self.ResetFRect()

        # self.frect stores the aboslute coordinates
        abs_left = self.frect[0] + dx
        abs_top  = self.frect[1] + dy

        # but Move() is expecting coordinates relative to the start of the view port
        start = self.GetParent().GetViewStartPixels()
        rel_left = abs_left - start[0]
        rel_top  = abs_top  - start[1]

        self.frect = (abs_left, abs_top, self.frect[2], self.frect[3])
        super(Card, self).Move((rel_left, rel_top))

    def Stretch(self, factor):
        # if we haven't stored our float coordinates yet
        if not self.frect:
            self.ResetFRect()

        # only scale if we're a sensitive factor away from 1.0
        if abs(factor - 1.0) < 0.001:
            return

        # keep count of the scale after every stretch
        self.scale *= factor

        # wx.Rect() converts everything to integers
        # since factor is always a float, this is why
        # we need to store our own coordinates!
        self.frect = [f * factor for f in self.frect]
        self.SetRect(wx.Rect(*self.frect))

    def SetScale(self, new_scale):
        self.Stretch(new_scale / self.scale)

    def GetScale(self):
        return self.scale

    def NavigateOut(self, forward):
        bd = self.GetParent()

        # try to get the nearest card
        if forward:
            nxt = bd.GetNextCard(self, "right")
            if not nxt:
                nxt = bd.GetNextCard(self, "down")
        else:
            nxt = bd.GetNextCard(self, "left")
            if not nxt:
                nxt = bd.GetNextCard(self, "up")

        # and navigate!
        if nxt:
            nxt.SetFocus()
        else:
            self.GetParent().Navigate(forward)


    ### Auxiliary functions

    def InitBorder(self):
        # border is just a window that sits behind the actual controls
        # it's used for changing selection rect around the card
        self.SetBorderColour(self.GetParent().GetBackgroundColour())

        # main is the window where the real controls will be placed
        main = wx.Panel(self, style=wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(main, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # since it's the main window displayed as a Card
        # we have to make it work like one
        # basically, just redirect all events
        main.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

        # use Set/GetCardSizer to get the control sizer
        self.SetSizer(box)
        self.main = main

    def InitUI(self):
        """Override me!"""
        pass

    def ResetFRect(self):
        """Store our float-valued, absolute coordinates."""
        start = self.GetParent().GetViewStartPixels()
        self.frect = [float(x) for x in self.GetRect()]

        # GetRect() returns coordinates relative to the current view point
        # we have to manually add the start of the view point (in pixels)
        # to store absolute coordinates
        self.frect[0] += start[0]
        self.frect[1] += start[1]

    def Dump(self):
        """Override me!"""

    def Load(self):
        """Override me!"""


    ### Callbacks

    def OnMouseEvent(self, ev):
        ev.SetEventObject(self)
        ev.SetPosition(ev.GetPosition() + self.main.GetPosition())
        self.GetEventHandler().ProcessEvent(ev)

    def OnTab(self, ev):
        """Only called by children, not bound to any event. See Navigate()."""
        ctrl = ev.GetEventObject()
        forward = not ev.ShiftDown()
        children = self.GetChildren()
        index = children.index(ctrl)

        if index == 0 and not forward:
            self.NavigateOut(forward)
        elif index == len(children)-1 and forward:
            self.NavigateOut(forward)
        else:
            self.Navigate(forward)



######################
# Class Header
######################

class Header(Card):
    MIN_WIDTH = 150
    DEFAULT_SZ = (150, 32)
    DEFAULT_TITLE = ""

    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, header = "", size=DEFAULT_SZ):
        super(Header, self).__init__(parent, label, id=id, pos=pos, size=size, style=wx.TAB_TRAVERSAL)
        self.InitUI()
        self.SetHeader(header)
        self.len = len(self.GetHeader())


    ### Behavior Functions

    def GetHeader(self):
        return self.header.GetValue()

    def SetHeader(self, head):
        self.header.SetValue(head)

    ### Auxiliary functions

    def InitUI(self):
        # Controls
        txt = EditText(self.main)
        txt.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        # Boxes
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(txt, proportion=0, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)

        self.header = txt
        self.SetCardSizer(vbox)
        self.Show(True)

    def Dump(self):
        """Returns a dict with all the information contained."""
        sz = self.GetSize()
        pos = self.GetPosition()
        return {"class": "Header",
               "label": self.label,
               "pos": (pos.x, pos.y),
               "width": sz.width,
               "height": sz.height,
               "header": self.GetHeader()}

    def Load(self, dic):
        if "label" in dic.keys():
            self.label = dic["label"]
        if "pos" in dic.keys():
            self.SetPosition(dic["pos"])
        if "width" in dic.keys():
            w, h = self.GetSize()
            self.SetSize((dic["width"], h))
        if "height" in dic.keys():
            w, h = self.GetSize()
            self.SetSize((w, dic["height"]))
        if "header" in dic.keys():
            self.SetHeader(dic["header"])



    ### Callbacks

    def OnKeyUp(self, ev):
        # calculate the sizes to compare
        new_len = len(self.GetHeader())

        sw, sh = self.GetSize()

        dc = wx.WindowDC(self)
        dc.SetFont(self.header.GetFont())
        tw, th = dc.GetTextExtent(self.GetHeader())
        # print "new text size: ", (tw, th)

        # if we're too short: elongate
        if new_len > self.len and tw + 20 > sw:
            # print "we're too short"
            self.SetSize((tw + 25, sh))

        # if we're too long: shorten
        # but not more than the minimum size!
        if new_len < self.len and sw > self.MIN_WIDTH and tw - 20 < sw:
            # print "we're too long: ", sw
            self.SetSize((tw + 10, sh))

        self.len = new_len

        # important!
        ev.Skip()


############################################
# Classes for the controls in Content card
############################################

class ContentText(ColouredText):
    def __init__(self, parent, size=wx.DefaultSize, style=wx.TE_RICH|wx.TE_MULTILINE|wx.TE_NO_VSCROLL):
        super(ContentText, self).__init__(parent, size=size, style=style)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)


    ### Behavior functions

    def BoldRange(self):
        start, end = self.GetSelection()
        self.SetStyle(start, end, wx.TextAttr(None, None, self.GetFont().Bold()))

    def ItalicRange(self):
        start, end = self.GetSelection()
        self.SetStyle(start, end, wx.TextAttr(None, None, self.GetFont().Italic()))


    ### Callbacks

    def OnKeyDown(self, ev):
        key = ev.GetKeyCode()

        if ev.ControlDown():
            if   key == ord("B"):
                self.BoldRange()
            elif key == ord("I"):
                self.ItalicRange()
                
            else:
                ev.Skip()
                
        else:
            if key == 9:
                # On TAB: instead of writing a "\t" char, let the card handle it
                GetCardAncestor(self).OnTab(ev)
            else:
                ev.Skip()



class KindButton(wx.Button):
    DEFAULT_SIZE = (33, 20)
    DEFAULT_FONT = (8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False)

    DEFAULT_LBL    = "kind"
    CONCEPT_LBL    = "C"
    ASSUMPTION_LBL = "A"
    RESEARCH_LBL   = "R"
    FACT_LBL       = "F"
    DEFAULT_LBL_LONG    = "kind"
    CONCEPT_LBL_LONG    = "Concept"
    ASSUMPTION_LBL_LONG = "Assumption"
    RESEARCH_LBL_LONG   = "Research"
    FACT_LBL_LONG       = "Fact"
    LONG_LABELS = {CONCEPT_LBL: CONCEPT_LBL_LONG, ASSUMPTION_LBL: ASSUMPTION_LBL_LONG, RESEARCH_LBL: RESEARCH_LBL_LONG, FACT_LBL: FACT_LBL_LONG, DEFAULT_LBL: DEFAULT_LBL_LONG}


    def __init__(self, parent, size=DEFAULT_SIZE, pos=wx.DefaultPosition, label="kind", style=wx.BORDER_NONE):
        super(KindButton, self).__init__(parent, size=size, pos=pos, label=label, style=style)
        self.SetOwnFont(wx.Font(*self.DEFAULT_FONT))
        self.Bind(wx.EVT_BUTTON, self.OnPress)


    ### Behavior functions

    def GetKind(self, long=False):
        if long: return self.LONG_LABELS[self.GetLabel()]
        else:    return self.GetLabel()

    def SetKind(self, kind):
        if kind == "kind": self.SetLabel("kind")
        else:              self.SetLabel(kind[0])

    ### Callbacks

    def OnPress(self, ev):
        rect = self.GetRect()
        self.PopupMenu(KindSelectMenu(GetCardAncestor(self)), (rect.width, rect.height))



class KindSelectMenu(wx.Menu):
    def __init__(self, card):
        super(KindSelectMenu, self).__init__()
        self.card = card

        A_item = wx.MenuItem(self, wx.NewId(), "Assumption")
        C_item = wx.MenuItem(self, wx.NewId(), "Concept")
        R_item = wx.MenuItem(self, wx.NewId(), "Research")
        F_item = wx.MenuItem(self, wx.NewId(), "Fact")
        N_item = wx.MenuItem(self, wx.NewId(), "None")

        self.AppendItem(A_item)
        self.AppendItem(C_item)
        self.AppendItem(R_item)
        self.AppendItem(F_item)
        self.AppendItem(N_item)

        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, KindButton.ASSUMPTION_LBL), A_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, KindButton.CONCEPT_LBL), C_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, KindButton.RESEARCH_LBL), R_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, KindButton.FACT_LBL), F_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, KindButton.DEFAULT_LBL), N_item)


    # Callbacks
    def OnSelect(self, ev, kind):
        # my parent is the control that displayed the menu
        if isinstance(self.card, Content):
            self.card.SetKind(kind)



######################
# Class Content
######################

class Content(Card):
    # sizes
    DEFAULT_SZ   = (250, 150)
    COLLAPSED_SZ = (250, 30)
    BIG_SZ       = (350, 250)

    # default control contents
    DEFAULT_TITLE   = ""
    DEFAULT_CONTENT = ""

    # # kind labels
    DEFAULT_KIND = "kind"
    # DEFAULT_LBL     = "kind"
    # CONCEPT_LBL    = "C"
    # ASSUMPTION_LBL = "A"
    # RESEARCH_LBL   = "R"
    # FACT_LBL       = "F"
    # DEFAULT_LBL_LONG    = "kind"
    # CONCEPT_LBL_LONG    = "Concept"
    # ASSUMPTION_LBL_LONG = "Assumption"
    # RESEARCH_LBL_LONG   = "Research"
    # FACT_LBL_LONG       = "Fact"
    # LONG_LABELS = {CONCEPT_LBL: CONCEPT_LBL_LONG, ASSUMPTION_LBL: ASSUMPTION_LBL_LONG, RESEARCH_LBL: RESEARCH_LBL_LONG, FACT_LBL: FACT_LBL_LONG, DEFAULT_LBL: DEFAULT_LBL_LONG}

    # colours; thanks paletton.com!
    COLOURS = {}
    COLOURS[KindButton.DEFAULT_LBL]    = {"border": (220, 218, 213, 255), "bg": (255, 255, 255, 255)}
    COLOURS[KindButton.CONCEPT_LBL]    = {"border": (149, 246, 214, 255), "bg": (242, 254, 250, 255)}
    COLOURS[KindButton.ASSUMPTION_LBL] = {"border": (255, 188, 154, 255), "bg": (255, 247, 243, 255)}
    COLOURS[KindButton.RESEARCH_LBL]   = {"border": (255, 232, 154, 255), "bg": (255, 252, 243, 255)}
    COLOURS[KindButton.FACT_LBL]       = {"border": (169, 163, 247, 255), "bg": (245, 244, 254, 255)}

    # content text colours
    # CONCEPT_CNT_CL    = (24, 243, 171, 255)
    # ASSUMPTION_CNT_CL = (255, 102, 25, 255)
    # RESEARCH_CNT_CL   = (255, 202, 25, 255)
    # FACT_CNT_CL       = (68, 54, 244, 255)

    # Content events
    KindEvent, EVT_CONT_KIND = ne.NewCommandEvent()

    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, size=DEFAULT_SZ,
                 title="", kind=KindButton.DEFAULT_LBL, content="", rating=0):
        super(Content, self).__init__(parent, label, id=id, pos=pos, size=size, style=wx.TAB_TRAVERSAL)

        self.InitUI()
        self.InitAccels()

        self.inspecting = False
        self.collapse_enabled = True

        if title:   self.title.SetValue(title)
        if content: self.content.SetValue(content)
        self.SetKind(kind)
        self.rating.SetRating(rating)


    ### Behavior functions

    def SetInspecting(self, val):
        self.inspecting = val

    def GetInspecting(self):
        return self.inspecting

    def SetRating(self, n):
        self.rating.SetRating(n)

    def GetCaretPos(self):
        """
        Returns a tuple (ctrl, pos) where ctrl may be "title" or "content",
        and pos is the position of the caret within that control. If other
        controls are focused or the card's contents are not focused at all,
        returns (None, -1).
        """
        ctrl = self.FindFocus()
        pos = None

        if ctrl == self.title:
            pos = ctrl.GetInsertionPoint()
            ctrl = "title"
        elif ctrl == self.content:
            pos = ctrl.GetInsertionPoint()
            ctrl = "content"
        else:
            pos = -1
            ctrl = None

        return (ctrl, pos)

    def SetCaretPos(self, ctrl, pos):
        """
        Accepts a tuple (ctrl, pos) where ctrl may be "title" or "content",
        and pos is the desired position of the caret within that control.
        """
        if ctrl == "title":
            ctrl = self.title
            ctrl.SetFocus()
            ctrl.SetInsertionPoint(pos)
        elif ctrl == "content":
            ctrl = self.content
            ctrl.SetFocus()
            ctrl.SetInsertionPoint(pos)

    def ScrollToChar(self, pos):
        self.content.ShowPosition(pos)

    def DisableCollapse(self):
        """Calling Collapse() or Uncollapse() after calling this function will do nothing."""
        self.collapse_enabled = False

    def EnableCollapse(self):
        """Calling Collapse() or Uncollapse() after calling this function will work again."""
        self.collapse_enabled = True

    def Collapse(self):
        if self.collapse_enabled and not self.IsCollapsed():
            self.content.Hide()
            self.SetSize(self.COLLAPSED_SZ)

            # raise the event
            event = self.CollapseEvent(id=wx.ID_ANY, collapsed=True)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def Uncollapse(self):
        if self.collapse_enabled and self.IsCollapsed():
            self.content.Show()
            self.SetSize(self.DEFAULT_SZ)

            # raise the event
            event = self.CollapseEvent(id=wx.ID_ANY, collapsed=False)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def ToggleCollapse(self):
        if self.IsCollapsed():
            self.Uncollapse()
        else:
            if self.FindFocus() == self.content:
                self.title.SetFocus()
            self.Collapse()

    def IsCollapsed(self):
        return not self.content.IsShown()

    def RequestInspect(self):
        """
        Call to raise an event signaling that this card wants to be inspected.
        Interested classes should listen to Card.EVT_CARD_REQUEST_INSPECT.
        """
        event = self.ReqInspectEvent(id=wx.ID_ANY)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def CancelInspect(self):
        """Signals this card wants to stop being inspected."""
        event = self.CancelInspectEvent(id=wx.ID_ANY)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    def GetTitle(self):
        return self.title.GetValue()

    def SetTitle(self, title):
        self.title.SetValue(title)

    def GetContent(self):
        return self.content.GetValue()

    def SetContent(self, value):
        self.content.SetValue(value)

    def GetKind(self, long=False):
        return self.kindbut.GetKind()

    def SetKind(self, kind):
        self.kindbut.SetKind(kind)
        self.SetColours(kind)

        event = self.KindEvent(id=wx.ID_ANY)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)


    ### Auxiliary functions

    def InitUI(self):
        # controls
        title = TitleEditText(self.main)
        kindbut = KindButton(self.main)
        rating = StarRating(self.main)
        content = ContentText(self.main)

        # boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.LEFT|wx.ALIGN_CENTRE, border=Card.BORDER_THICK)
        hbox1.Add(kindbut, proportion=0, flag=wx.ALL|wx.ALIGN_CENTRE, border=Card.BORDER_WIDTH)
        hbox1.Add(rating,  proportion=0, flag=wx.ALL|wx.EXPAND, border=0)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(content, proportion=1, flag=wx.EXPAND)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetCardSizer(vbox)
        vbox.Add(hbox1, proportion=0, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)
        vbox.Add(hbox2, proportion=1, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_THICK)

        self.kindbut = kindbut
        self.title = title
        self.content = content
        self.rating = rating
        self.Show(True)

    def InitAccels(self):
        # ghost menu to generate menu item events and setup accelerators
        accels = []
        ghost = wx.Menu()

        # view
        coll = wx.MenuItem(ghost, wx.ID_ANY, "Toggle collapse")
        insp = wx.MenuItem(ghost, wx.ID_ANY, "Request inspection")
        self.Bind(wx.EVT_MENU, self.OnCtrlU, coll)
        self.Bind(wx.EVT_MENU, self.OnCtrlI, insp)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("U"), coll.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("I"), insp.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def Dump(self):
        """
        Dumps all of this Card's information into a dictionary and returns it.
        See also: Load.
        """
        if self.frect: pos = self.frect[:2]
        else:          pos = self.GetPosition()

        return {"class": "Content",
                "label": self.label,
                "pos": (pos[0], pos[1]),
                "kind": self.GetKind(),
                "title": self.GetTitle(),
                "content": self.GetContent(),
                "collapsed": self.IsCollapsed(),
                "rating": self.rating.GetRating()}

    def Load(self, dic):
        """
        Reads the dictionary returned by Card.Dump and loads all the info into this Card.
        See also: Dump.
        """
        if "label" in dic.keys():
            self.label = dic["label"]
        if "title" in dic.keys():
            self.SetTitle(dic["title"])
        if "kind" in dic.keys():
            self.SetKind(dic["kind"])
        if "content" in dic.keys():
            self.SetContent(dic["content"])
        if "rating" in dic.keys():
            self.SetRating(dic["rating"])
        if "pos" in dic.keys():
            self.SetPosition(dic["pos"])
        if "collapsed" in dic.keys():
            if dic["collapsed"]: self.Collapse()

    def SetColours(self, kind):
        self.SetBackgroundColour(self.COLOURS[kind]["border"])
        self.title.SetFirstColour(self.COLOURS[kind]["border"])
        self.title.SetSecondColour(self.COLOURS[kind]["bg"])
        self.content.SetBackgroundColour(self.COLOURS[kind]["bg"])


    ### Callbacks

    def OnCtrlI(self, ev):
        # if there's a selection, let ContentText handle styling
        start, end = self.content.GetSelection()
        if start != end:
            ev.Skip()
            return

        # if not, then handle inspection
        if not self.inspecting:
            self.RequestInspect()
        elif self.inspecting:
            self.CancelInspect()

    def OnCtrlU(self, ev):
        self.ToggleCollapse()



######################
# Class Image
######################

class Image(Card):
    DEFAULT_SZ = (50, 50)
    DEFAULT_PATH = ""

    def __init__(self, parent, label, path=None, id=wx.ID_ANY, pos=wx.DefaultPosition, size=DEFAULT_SZ):
        super(Image, self).__init__(parent, label, id=id, pos=pos, size=size)
        self.btn = None
        self.img = None
        self.path = path
        self.orig = None
        self.resizing = False
        self.resize_w = False
        self.resize_h = False
        self.InitUI(path)

        # bindings
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOverBorder)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeaveBorder)
        self.main.Bind(wx.EVT_LEFT_DOWN, self.OnBorderLeftDown)

        
    ### Behavior funtions

    def LoadImage(self, path):
        # load the image
        bmp = wx.Bitmap(path)
        self.SetImage(bmp)
        self.SetScale(self.GetScale())

        # hide the button
        if self.btn:
            self.btn.Hide()
            self.btn = None

        # set members
        self.path = path
        self.orig = bmp
        self.GetParent().SetFocus()

    def SetImage(self, bmp):
        if not self.img:
            self.img = wx.StaticBitmap(self.main)

        # set the bitmap
        self.img.SetBitmap(bmp)
        self.img.SetSize(bmp.GetSize())
        self.img.Bind(wx.EVT_LEFT_DOWN, self.OnImageLeftDown)

        # setup the card sizer
        self.GetCardSizer().Clear()
        self.GetCardSizer().Add(self.img, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)

        self.Fit()

    def Stretch(self, factor):
        if abs(factor - 1.0) < 0.001:
            return

        # Card.Stretch takes care of the new rect size
        super(Image, self).Stretch(factor)

        # having handled the new rect, we only need to resize the image to it
        if self.img:
            # if we're returning to the original size, reload instead of resize,
            # to cancel out scaling smoothing
            if abs(self.GetScale() - 1.0) < 0.001:
                bmp = self.orig
            else:
                bmp = self.ResizeBitmap(*self.GetSize())

            self.SetImage(bmp)

    def ResizeBitmap(self, w, h, quality=wx.IMAGE_QUALITY_BILINEAR):
        img = self.img.GetBitmap().ConvertToImage()
        return wx.BitmapFromImage(img.Scale(w, h, quality))

            
    ### Auxiliary functions

    def InitUI(self, path=None):
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetCardSizer(vbox)

        if not path:
            btn = wx.BitmapButton(self.main, bitmap=wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE), size=self.DEFAULT_SZ)
            vbox.Add(btn, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)
            self.btn = btn
            btn.Bind(wx.EVT_BUTTON, self.OnButton)
        else:
            self.LoadImage(path)

    def Dump(self):
        pos = self.GetPosition()
        return {"class": "Image",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "path": self.path}

    def Load(self, dic):
        if "label" in dic.keys():
            self.label = dic["label"]
        if "pos" in dic.keys():
            self.SetPosition(dic["pos"])
        if "path" in dic.keys():
            self.LoadImage(dic["path"])


    ### Callbacks

    def OnButton(self, ev):
        fd = wx.FileDialog(self, "Open", os.getcwd(), "", "All files (*.*)|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind
        self.LoadImage(fd.GetPath())

    def OnImageLeftDown(self, ev):
        """All mouse events from the StaticBitmap are redirected as coming from this card."""
        ev.SetEventObject(self)
        ev.SetPosition(ev.GetPosition() + self.img.GetPosition())
        self.GetEventHandler().ProcessEvent(ev)

    def OnMouseOverBorder(self, ev):
        self.Bind(wx.EVT_MOTION, self.OnMotionOverBorder)

    def OnMotionOverBorder(self, ev):
        x, y =  ev.GetPosition()
        win_w, win_h = self.GetSize()
        img_w, img_h = self.img.GetSize()
        w_border = win_w - img_w
        h_border = win_h - img_h

        right  = abs(x - win_w) < w_border
        bottom = abs(y - win_h) < h_border
        top    = y < h_border
        left   = x < w_border

        if   (left and top) or (right and bottom):
            self.resize_w = True
            self.resize_h = True
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENWSE))
        elif (right and top) or (left and bottom):
            self.resize_w = True
            self.resize_h = True
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
        elif left or right:
            self.resize_w = True
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))
        elif top or bottom:
            self.resize_h = True
            self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENS))

    def OnMouseLeaveBorder(self, ev):
        self.SetCursor(wx.NullCursor)

    def OnBorderLeftDown(self, ev):
        self.CaptureMouse()                
        self.Unbind(wx.EVT_MOTION)
        self.Bind(wx.EVT_MOTION, self.OnDragResize)
        self.Bind(wx.EVT_LEFT_UP, self.OnBorderLeftUp)

    def OnBorderLeftUp(self, ev):
        # since we captured the mouse, ev.GetPosition() returns
        # coordinates relative to this card's top left corner
        # thus: the new position is our new size
        if self.resizing:
            ev_w, ev_h = ev.GetPosition()
            cur_w, cur_h = self.GetSize()
            new_w, new_h = cur_w, cur_h

            if   self.resize_w and self.resize_h:
                new_w, new_h = ev_w, ev_h
            elif not self.resize_w and self.resize_h:
                new_h = ev_h
            elif self.resize_w and not self.resize_h:
                new_w = ev_w
            self.SetSize(wx.Size(new_w, new_h))
            
            self.resize_w = False
            self.resize_h = False
        
        self.Unbind(wx.EVT_MOTION)
        self.Unbind(wx.EVT_LEFT_UP)
        self.ReleaseMouse()        

    def OnDragResize(self, ev):
        if ev.Dragging():
            self.resizing = True
            



######################
# Class TitleEditText
######################

class TitleEditText(EditText):
    # have to use own MAX length since wx.TextCtrl.SetMaxLength
    # is only implemented for single line text controls
    MAXLEN_PX = 175
    HEIGHT_PX = EditText.DEFAULT_SZ[1]

    DEFAULT_WIDTH = EditText.DEFAULT_SZ[0]
    DEFAULT_HEIGHT = EditText.DEFAULT_SZ[1]
    HEIGHTS = [DEFAULT_HEIGHT, DEFAULT_HEIGHT * 1.75, DEFAULT_HEIGHT * 2]

    DEFAULT_FONT = EditText.DEFAULT_FONT
    DEFAULT_FONT_SZ = EditText.DEFAULT_FONT[0]
    FONT_SIZES = [DEFAULT_FONT_SZ, DEFAULT_FONT_SZ - 2, DEFAULT_FONT_SZ - 2 - 2]


    def __init__(self, parent):
        super(TitleEditText, self).__init__(parent)
        # set initial lines
        self.current_height = 0
        self.current_font_sz = 0
        self.lines = 0
        self.SetOneLine()

        # save a reference to our Client's GetTextExtent:
        # we're going to use it every time the text chagnes
        # and we don't want to build a wx.ClientDC every time
        dc = wx.MemoryDC()
        dc.SetFont(wx.Font(*self.DEFAULT_FONT))
        self.GetTextExtent = dc.GetTextExtent

        # bindings
        self.Bind(wx.EVT_TEXT, self.OnTextEntry)


    ### Behavior functions

    def SetValue(self, val):
        super(TitleEditText, self).SetValue(val)
        self.ComputeLines()

    def SetHeightAndFontSize(self, height, font_sz):
        # SetMinSize + Layout will force the containing Sizer to resize
        size = (self.DEFAULT_WIDTH, height)
        self.SetMinSize(size)
        self.GetParent().Layout()
        font = list(self.DEFAULT_FONT)
        font[0] = font_sz
        self.SetFont(wx.Font(*font))

        # members
        self.current_height = size[1]
        self.current_font_sz = font_sz

    def SetOneLine(self):
        self.SetHeightAndFontSize(self.HEIGHTS[0], self.DEFAULT_FONT_SZ)
        self.lines = 1

    def SetTwoLines(self):
        self.SetHeightAndFontSize(self.HEIGHTS[1], self.FONT_SIZES[1])
        self.lines = 2

    def SetThreeLines(self):
        self.SetHeightAndFontSize(self.HEIGHTS[2], self.FONT_SIZES[2])
        self.lines = 3

    def ComputeLines(self):
        # restore the insertion point after
        pt = self.GetInsertionPoint()

        # prepare text
        txt = self.GetValue()
        if self.lines == 2:
            index = len(txt) / 2
            txt = txt[:index+1] + "\n" + txt[index+1:]
        elif self.lines == 3:
            index = len(txt) / 3
            txt = txt[:index+1] + "\n" + txt[index+1:index*2-1] + "\n" + txt[index*2+1:]

        w, h = self.GetTextExtent(txt)
        if w >= self.MAXLEN_PX and abs(self.current_height - h) <= 3:
            if self.lines == 1:
                self.SetTwoLines()
            elif self.lines == 2:
                self.SetThreeLines()

        # restore
        self.SetInsertionPoint(pt)


    ### Callbacks

    def OnTextEntry(self, ev):
        self.ComputeLines()



######################
# Class StarRating
######################

class StarRating(wx.Button):
    PATH = "../img/"

    # thanks openclipart.org for the stars!
    # https://openclipart.org/detail/117079/5-star-rating-system-by-jhnri4
    FILES = ["stars_0.png", "stars_1.png", "stars_2.png", "stars_3.png"]
    BMPS = []
    MAX = 3

    def __init__(self, parent):
        super(StarRating, self).__init__(parent, size=(20, 35),
                                         style=wx.BORDER_NONE|wx.BU_EXACTFIT)

        # the first instance loads all BMPs
        if not StarRating.BMPS:
            StarRating.BMPS = [wx.Bitmap(self.PATH + self.FILES[n]) for n in range(self.MAX + 1)]

        self.rating = 0
        self.SetRating(0)

        # bindings
        self.Bind(wx.EVT_BUTTON, self.OnPress)

    ### Behavior functions

    def SetRating(self, n):
        self.SetBitmap(self.BMPS[n])
        self.rating = n

    def GetRating(self):
        return self.rating

    def IncreaseRating(self, wrap=True):
        """If wrap is True, and we increase to more than the maximum rating, we set it to zero."""
        new = self.GetRating() + 1
        if new > self.MAX:
            new = 0
        self.SetRating(new)


    ### Callbacks

    def OnPress(self, ev):
        self.IncreaseRating()



######################
# Class CardGroup
######################

class CardGroup():
    def __init__(self, members=[], label=-1):
        # save references to cards, not to the list
        self.members = members[:]
        self.label = label

    def GetMembers(self):
        return self.members

    def GetLabel(self):
        return self.label

    def Add(self, card):
        self.members.append(card)

    def Remove(self, card):
        self.members.remove(card)

    def Dump(self):
        return [c.label for c in self.members]



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
for field in dir(wx.Panel):
    __pdoc__['Card.%s' % field] = None
for field in dir(Card):
    __pdoc__['Header.%s' % field] = None
for field in dir(ColouredText):
    __pdoc__['ContentText.%s' % field] = None
for field in dir(wx.Button):
    __pdoc__['KindButton.%s' % field] = None
for field in dir(wx.Menu):
    __pdoc__['KindSelectMenu.%s' % field] = None
for field in dir(Card):
    __pdoc__['Content.%s' % field] = None
for field in dir(Card):
    __pdoc__['Image.%s' % field] = None
for field in dir(EditText):
    __pdoc__['TitleEditText.%s' % field] = None
for field in dir(wx.Button):
    __pdoc__['StarRating.%s' % field] = None
# CardGroup has no ancestors!    
# for field in dir():
#     __pdoc__['CardGroup.%s' % field] = None


# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in Card.__dict__.keys():
    if 'Card.%s' % field in __pdoc__.keys():
        del __pdoc__['Card.%s' % field]
for field in Header.__dict__.keys():
    if 'Header.%s' % field in __pdoc__.keys():
        del __pdoc__['Header.%s' % field]
for field in ContentText.__dict__.keys():
    if 'ContentText.%s' % field in __pdoc__.keys():
        del __pdoc__['ContentText.%s' % field]
for field in KindButton.__dict__.keys():
    if 'KindButton.%s' % field in __pdoc__.keys():
        del __pdoc__['KindButton.%s' % field]
for field in KindSelectMenu.__dict__.keys():
    if 'KindSelectMenu.%s' % field in __pdoc__.keys():
        del __pdoc__['KindSelectMenu.%s' % field]
for field in Content.__dict__.keys():
    if 'Content.%s' % field in __pdoc__.keys():
        del __pdoc__['Content.%s' % field]
for field in Image.__dict__.keys():
    if 'Image.%s' % field in __pdoc__.keys():
        del __pdoc__['Image.%s' % field]
for field in TitleEditText.__dict__.keys():
    if 'TitleEditText.%s' % field in __pdoc__.keys():
        del __pdoc__['TitleEditText.%s' % field]
for field in StarRating.__dict__.keys():
    if 'StarRating.%s' % field in __pdoc__.keys():
        del __pdoc__['StarRating.%s' % field]
