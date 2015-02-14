# card.py
# -*- coding: utf-8 -*-

# Card classes. The windows that go in a BoardBase.

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
        # frect stores the floating point coordinates of this card's rect
        # in the usual order: [left, top, width, height]
        # see Card.Scale()
        self.frect = []

        # create CardBar
        # if Card.bar == None:
        #     Card.bar = CardBar.Create(self.GetParent())


    ### Behavior functions

    def __del__(self):
        pass

    def GetLabel(self):
        return self.label

    def ShowBar(self):
        CardBar.Associate(self)
        self.bar.Show()
        
    def HideBar(self):
        self.bar.Hide()

    def Delete(self):
        """Called by CardBar when the close button is pressed. Raises EVT_CARD_DELETE."""
        # simply raise a CardEvent. BoardBase should know what to do
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

    def Scale(self, factor):
        # it this is the first time, get the integer coordinate rect
        if not self.frect:
            self.frect = self.GetRect()

        # compute and store our "real" rect in floating point coordinates
        self.frect = [f * factor for f in self.frect]

        # wx.Rect() converts everything to integers
        # since factor is always a float, this is why
        # we need to store our own coordinates!
        self.SetRect(wx.Rect(*self.frect))

                        
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

    def Dump(self):
        """Override me!"""


    ### Callbacks

    def OnMouseEvent(self, ev):
        ev.SetEventObject(self)
        ev.SetPosition(ev.GetPosition() + self.main.GetPosition())
        self.GetEventHandler().ProcessEvent(ev)

        
    
######################
# Class Header
######################

class Header(Card):
    MIN_WIDTH = 150
    DEFAULT_SZ = (150, 32)
    DEFAULT_TITLE = ""
    
    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, header = "Header...", size=DEFAULT_SZ):
        super(Header, self).__init__(parent, label, id=id, pos=pos, size=size, style=wx.TAB_TRAVERSAL)
        self.InitUI()
        self.header.SetValue(header)
        self.len = len(self.GetHeader())


    ### Behavior Functions
    def GetHeader(self):
        return self.header.GetValue()

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
        return {"class": "Header",
               "label": self.label,
               "pos": self.GetPosition(),
               "width": sz.width,
               "height": sz.height,
               "header": self.GetHeader()}

    
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

    def ScrollToChar(self, pos):
        if pos > -1 and pos < len(self.GetValue()):
            sz = self.GetSize()
            x, y = self.PositionToCoords(pos)

            while y < 0:
                self.ScrollLines(-1)
                x, y = self.PositionToCoords(pos)
            # the offset should account for font height                
            while y >= sz.height - 18:
                self.ScrollLines(1)
                x, y = self.PositionToCoords(pos)
                

    ### Callbacks

    def OnKeyDown(self, ev):
        key = ev.GetKeyCode()
        
        # skip everything but tab
        if key != 9:
            if ev.ControlDown():
                if   key == ord("B"):
                    self.BoldRange()
                elif key == ord("I"):
                    self.ItalicRange()
                else:
                    ev.Skip()
            else:
                ev.Skip()
        # on TAB: don't input a \t char and simulate a tab traversal
        else:
            self.GetParent().Navigate(not ev.ShiftDown())


            
class KindButton(wx.Button):
    DEFAULT_SIZE = (33, 23)
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
        self.content.ScrollToChar(pos)

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

            event = self.CollapseEvent(id=wx.ID_ANY, collapsed=True)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def Uncollapse(self):
        if self.collapse_enabled and self.IsCollapsed():
            self.content.Show()
            self.SetSize(self.DEFAULT_SZ)
            
            event = self.CollapseEvent(id=wx.ID_ANY, collapsed=False)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def ToggleCollapse(self):
        if self.IsCollapsed():
            self.Uncollapse()
        else:
            self.Collapse()
            self.title.SetFocus()

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
        title = EditText(self.main)
        kindbut = KindButton(self.main)
        rating = StarRating(self.main)
        content = ContentText(self.main)
        
        # boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.ALL|wx.ALIGN_CENTRE, border=Card.BORDER_WIDTH)
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
        pos = self.GetPosition()
        return {"class": "Content",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "kind": self.GetKind(),
                "title": self.GetTitle(),
                "content": self.GetContent(),
                "collapsed": self.IsCollapsed(),
                "rating": self.rating.GetRating()}

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
        self.scale = 1.0
        self.path = path
        self.orig = None
        self.InitUI(path)

        
    ### Behavior funtions

    def LoadImage(self, path):
        # load the image
        bmp = wx.Bitmap(path)
        self.SetImage(bmp)
        self.Scale(self.scale)

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
            
        self.img.SetBitmap(bmp)
        self.img.SetSize(bmp.GetSize())
        self.GetCardSizer().Clear()
        self.GetCardSizer().Add(self.img, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)
        self.Fit()

    def Scale(self, factor):
        # Card.Scale takes care of the new rect size
        super(Image, self).Scale(factor)
        self.scale = factor

        # with the new rect, we only need resize the image to it
        if self.img:
            img = self.img.GetBitmap().ConvertToImage()

            if self.orig and self.img.GetSize() == self.orig.GetSize():
                # if we're returning to the original size, reload instead of resize,
                # because an image after several resizes looks bad
                bmp = self.orig
            else:
                bmp = wx.BitmapFromImage(img.Scale(*self.GetSize(),
                                    quality=wx.IMAGE_QUALITY_BILINEAR))
            self.SetImage(bmp)

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

        
    ### Callbacks

    def OnButton(self, ev):
        fd = wx.FileDialog(self, "Open", os.getcwd(), "", "All files (*.*)|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind
        self.LoadImage(fd.GetPath())


        
######################
# Class CardGroup
######################

class CardGroup():
    def __init__(self, label=-1, members=[]):
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

    
