# card.py
# Card classes. The windows that go in a BoardBase.

import wx
import os
import wx.richtext as rt
import wx.lib.newevent as ne
from utilities import EditText


######################
# Card Class
######################

class Card(wx.Panel):
    BORDER_WIDTH = 2
    BORDER_THICK = 5
    SELECT_CL = (0, 0, 0, 0)

    bar = None
    
    DeleteEvent, EVT_CARD_DELETE = ne.NewCommandEvent()
    CollapseEvent, EVT_CARD_COLLAPSE = ne.NewCommandEvent()
    InspectEvent, EVT_CARD_REQUEST_INSPECT = ne.NewEvent()
    
    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        """Base class for every window that will be placed on Board. Override SetupUI()."""
        super(Card, self).__init__(parent, id, pos, size, style=style)
        self.main = None
        self.InitBorder()
        self.label = label

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

    def SetCardSizer(self, sz):
        self.main.SetSizer(sz)

    def GetCardSizer(self):
        return self.main.GetSizer()

                        
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
        txt.SetHint("Header...")
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

            

######################
# Class Content
######################
class Content(Card):
    # sizes
    DEFAULT_SZ   = (250, 150)
    COLLAPSED_SZ = (250, 30)
    BIG_SZ       = (350, 250)
    KIND_BTN_SZ  = (33, 23)

    # default control contents
    DEFAULT_TITLE   = ""
    DEFAULT_CONTENT = ""
    
    # kind labels
    DEFAULT_LBL     = "kind"    
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

    # colours; thanks paletton.com!        
    COLOURS = {}
    COLOURS[DEFAULT_LBL]    = {"border": (220, 218, 213, 255), "bg": (255, 255, 255, 255)}
    COLOURS[CONCEPT_LBL]    = {"border": (149, 246, 214, 255), "bg": (242, 254, 250, 255)}
    COLOURS[ASSUMPTION_LBL] = {"border": (255, 188, 154, 255), "bg": (255, 247, 243, 255)}
    COLOURS[RESEARCH_LBL]   = {"border": (255, 232, 154, 255), "bg": (255, 252, 243, 255)}
    COLOURS[FACT_LBL]       = {"border": (169, 163, 247, 255), "bg": (245, 244, 254, 255)}

    # fonts
    KIND_FONT = (8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False)

    # content text colours
    # CONCEPT_CNT_CL    = (24, 243, 171, 255)
    # ASSUMPTION_CNT_CL = (255, 102, 25, 255)
    # RESEARCH_CNT_CL   = (255, 202, 25, 255)
    # FACT_CNT_CL       = (68, 54, 244, 255)

    # Content events
    KindEvent, EVT_CONT_KIND = ne.NewCommandEvent()

    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, size=DEFAULT_SZ, title="", kind=DEFAULT_LBL, content=""):
        super(Content, self).__init__(parent, label, id=id, pos=pos, size=size, style=wx.TAB_TRAVERSAL)
        
        self.InitUI()
        self.InitAccels()

        self.SetKind(kind)
        if title: self.title.SetValue(title)
        if content: self.content.SetValue(content)

        
    ### Behavior functions

    def BoldRange(self, start, end):
        self.content.SetStyle(start, end, wx.TextAttr(None, None, self.content.GetFont().Bold()))

    def ItalicRange(self, start, end):
        self.content.SetStyle(start, end, wx.TextAttr(None, None, self.content.GetFont().Italic()))

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
        ctrl = self.content
        if pos > -1 and pos < len(ctrl.GetValue()):
            sz = ctrl.GetSize()
            x, y = ctrl.PositionToCoords(pos)

            while y < 0:
                ctrl.ScrollLines(-1)
                x, y = ctrl.PositionToCoords(pos)
            # the offset should account for font height                
            while y >= sz.height - 18:
                ctrl.ScrollLines(1)
                x, y = ctrl.PositionToCoords(pos)

    def Collapse(self):
        if not self.IsCollapsed():
            self.content.Hide()
            self.SetSize(self.COLLAPSED_SZ)

            event = self.CollapseEvent(id=wx.ID_ANY, collapsed=True)
            event.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(event)

    def Uncollapse(self):
        if self.IsCollapsed():
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
        event = self.InspectEvent(id=wx.ID_ANY)
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
        if long: return self.LONG_LABELS[self.kindbut.GetLabel()]
        else:    return self.kindbut.GetLabel()

    def SetKind(self, kind):
        if kind == "kind": self.kindbut.SetLabel("kind")
        else:              self.kindbut.SetLabel(kind[0])
        self.SetColours(kind)

        event = self.KindEvent(id=wx.ID_ANY)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

    
    ### Auxiliary functions
    
    def InitUI(self):
        # controls
        title = EditText(self.main)
        title.SetHint("Title...")
        
        kindbut = wx.Button(self.main, label = "kind", size=Content.KIND_BTN_SZ, style=wx.BORDER_NONE)
        kindbut.SetOwnFont(wx.Font(*self.KIND_FONT))
        
        content = wx.TextCtrl(self.main, size=(10,10), style=wx.TE_RICH|wx.TE_MULTILINE|wx.TE_NO_VSCROLL)
        
        # boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)
        hbox1.Add(kindbut, proportion=0, flag=wx.ALL,           border=Card.BORDER_WIDTH)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(content, proportion=1, flag=wx.EXPAND)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetCardSizer(vbox)
        vbox.Add(hbox1, proportion=0, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)
        vbox.Add(hbox2, proportion=1, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_THICK)
        
        # bindings
        kindbut.Bind(wx.EVT_BUTTON, self.OnKindPressed)
        content.Bind(wx.EVT_KEY_DOWN, self.OnContentKeyDown)

        self.kindbut = kindbut
        self.title = title
        self.content = content
        self.Show(True)

    def InitAccels(self):
        # ghost menu to generate menu item events and setup accelerators
        accels = []        
        ghost = wx.Menu()

        # content style
        bold = wx.MenuItem(ghost, wx.ID_ANY, "Bold selection")
        ital = wx.MenuItem(ghost, wx.ID_ANY, "Italic selection")
        self.Bind(wx.EVT_MENU, self.OnCtrlB , bold)
        self.Bind(wx.EVT_MENU, self.OnCtrlI , ital)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("B"), bold.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("I"), ital.GetId()))

        # view
        coll = wx.MenuItem(ghost, wx.ID_ANY, "Toggle collapse")
        self.Bind(wx.EVT_MENU, self.OnCtrlU , coll)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("U"), coll.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def Dump(self):
        pos = self.GetPosition()
        return {"class": "Content",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "kind": self.GetKind(),
                "title": self.GetTitle(),
                "content": self.GetContent(),
                "collapsed": self.IsCollapsed()}

    def SetColours(self, kind):
        self.SetBackgroundColour(self.COLOURS[kind]["border"])
        self.title.SetFirstColour(self.COLOURS[kind]["border"])
        self.title.SetSecondColour(self.COLOURS[kind]["bg"])
        self.content.SetBackgroundColour(self.COLOURS[kind]["bg"])


    ### Callbacks

    def OnCtrlB(self, ev):
        start, end = self.content.GetSelection()
        if start != end:
            self.BoldRange(start, end)

    def OnCtrlI(self, ev):
        start, end = self.content.GetSelection()
        if start != end:
            self.ItalicRange(start, end)
        else:
            # inspect!
            pass

    def OnCtrlU(self, ev):
        self.ToggleCollapse()

    def OnContentKeyDown(self, ev):
        # skip anything but TAB, so that we don't input \t and tab traversal still works
        if ev.GetKeyCode() != 9:
            ev.ResumePropagation(True)
            ev.Skip()
        else:
            self.Navigate(wx.MouseState().ShiftDown())

    def OnKindPressed(self, ev):
        ctrl = ev.GetEventObject()
        rect = ctrl.GetRect()
        pos = ctrl.GetPosition() + (rect.width, rect.height)
        self.PopupMenu(KindSelectMenu(self), pos)



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

        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.ASSUMPTION_LBL), A_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.CONCEPT_LBL), C_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.RESEARCH_LBL), R_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.FACT_LBL), F_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.DEFAULT_LBL), N_item)

        
    # Callbacks
    def OnSelect(self, ev, kind):
        # my parent is the control that displayed the menu
        if isinstance(self.card, Content):
            self.card.SetKind(kind)

            

######################
# Class Image
######################            

class Image(Card):
    DEFAULT_SZ = (50, 50)
    DEFAULT_PATH = ""
    
    def __init__(self, parent, label, path=None, id=wx.ID_ANY, pos=wx.DefaultPosition, size=DEFAULT_SZ):
        super(Image, self).__init__(parent, label, id=id, pos=pos, size=size)
        self.btn = None
        self.InitUI(path)
        self.path = path


    ### Behavior funtions

    def SetImage(self, path):
        bmp = wx.Bitmap(path)
        img = wx.StaticBitmap(self.main)
        img.SetBitmap(bmp)
        img.SetSize(bmp.GetSize())
        
        if self.btn:
            self.btn.Hide()
            del self.btn
            self.btn = None

        self.path = path
        self.GetCardSizer().Add(img, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)
        self.Fit()

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
            self.SetImage(path)        

    def Dump(self):
        pos = self.GetPosition()
        return {"class": "Image",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "path": self.path}

        
    ### Callbacks

    def OnButton(self, ev):
        fd = wx.FileDialog(self, "Save", os.getcwd(), "", "All files (*.*)|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if fd.ShowModal() == wx.ID_CANCEL: return # user changed her mind
        self.SetImage(fd.GetPath())


        
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

    
