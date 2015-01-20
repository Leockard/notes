# card.py
# Card classes. The windows that go in a BoardBase.

import wx
import wx.richtext as rt
import cardbar as CardBar


######################
# Card Class
######################

class Card(wx.Panel):
    BORDER_WIDTH = 2
    BORDER_THICK = 5
    # bar = CardBar.GetBar()
    bar = None
    
    def __init__(self, parent, id, pos, size, style):
        """Base class for every window that will be placed on Board. Override SetupUI()."""
        super(Card, self).__init__(parent, id, pos, size, style)
        if Card.bar == None:
            Card.bar = CardBar.Create(self.GetParent())


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
        
    ### Auxiliary functions
        
    def InitUI(self):
        """Override me!"""
        pass

    def Dump(self):
        """Override me!"""


    
######################
# Card Header
######################

class Header(Card):
    DEFAULT_SZ = (150, 32)
    
    def __init__(self, parent, label, id, pos, header = "header..."):
        super(Header, self).__init__(parent, id, pos, Header.DEFAULT_SZ,
                                     style = wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        self.SetupUI()
        self.header.SetValue(header)
        self.label = label


    ### Behavior Functions
    def GetHeader(self):
        return self.header.GetValue()

    ### Auxiliary functions
    def InitUI(self):
        # Controls
        txt = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_RICH)
        txt.SetHint("Header")
        
        # Boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(txt, proportion=1, flag=wx.LEFT|wx.EXPAND, border=Card.BORDER_WIDTH)

        vbox = wx.BoxSizer(wx.VERTICAL)                
        vbox.Add(txt, proportion=0, flag=wx.LEFT|wx.EXPAND, border=Card.BORDER_WIDTH)
        
        self.header = txt
        self.SetSizer(vbox)
        self.Show(True)

    def Dump(self):
        """Returns a dict with all the information contained."""
        return {"class": "Header", "label": self.label,
                "pos": self.GetPosition(), "header": self.GetHeader()}

            

######################
# Class Content
######################

class Content(Card):
    # sizes
    DEFAULT_SZ   = (250, 150)
    COLLAPSED_SZ = (250, 30)
    BIG_SZ       = (350, 250)
    KIND_BTN_SZ  = (33, 23)

    # labels
    DEFAULT_LBL    = "kind"
    CONCEPT_LBL    = "C"
    ASSUMPTION_LBL = "A"
    RESEARCH_LBL   = "R"
    FACT_LBL       = "F"

    # colours
    DEFAULT_CL    = (220, 218, 213, 255)
    # thanks paletton.com!    
    # border colours    
    CONCEPT_CL    = (149, 246, 214, 255)
    ASSUMPTION_CL = (255, 188, 154, 255)
    RESEARCH_CL   = (255, 232, 154, 255)
    FACT_CL       = (169, 163, 247, 255)
    # content background colours
    CONCEPT_BG_CL    = (242, 254, 250, 255) 
    ASSUMPTION_BG_CL = (255, 247, 243, 255)
    RESEARCH_BG_CL   = (255, 252, 243, 255) 
    FACT_BG_CL       = (245, 244, 254, 255)
    # content text colours
    CONCEPT_CNT_CL    = (24, 243, 171, 255)
    ASSUMPTION_CNT_CL = (255, 102, 25, 255)
    RESEARCH_CNT_CL   = (255, 202, 25, 255)
    FACT_CNT_CL       = (68, 54, 244, 255)
    

    def __init__(self, parent, label, id=wx.ID_ANY, pos=wx.DefaultPosition, size=DEFAULT_SZ, title="", kind=DEFAULT_LBL, content=""):
        super(Content, self).__init__(parent, id=id, pos=pos, size=size,
                                      style=wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        self.label = label

        self.InitUI()
        self.SetKind(kind)
        # self.title.SetValue(title)
        # print "title from init: " + str(title)
        if title: self.title.SetLabel(title)
        if content: self.content.SetValue(content)

        
    ### Behavior functions

    def Collapse(self):
        if not self.IsCollapsed():
            self.content.Hide()
            self.SetSize(self.COLLAPSED_SZ)

    def UnCollapse(self):
        if self.IsCollapsed():
            self.content.Show()
            self.SetSize(self.DEFAULT_SZ)

    def IsCollapsed(self):
        return not self.content.IsShown()

    def GetTitle(self):
        return self.title.GetValue()

    def GetContent(self):
        return self.content.GetValue()
    
    def GetKind(self):
        return self.kindbut.GetLabel()

    def SetKind(self, kind):
        if kind == "kind": self.kindbut.SetLabel("kind")
        else:              self.kindbut.SetLabel(kind[0])
        self.SetColours(kind)

    
    ### Auxiliary functions
    
    def InitUI(self):
        # Controls
        # title = wx.TextCtrl(self, style = wx.TE_RICH)
        title = EditText(self)
        # title.SetHint("Title")
        
        kindbut = wx.Button(self, label = "kind", size=Content.KIND_BTN_SZ, style=wx.BORDER_NONE)
        kindbut.SetOwnFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False))
        
        content = rt.RichTextCtrl(self, size = (10, 10))
        content.SetHint("Write here...")
        
        # Boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.LEFT|wx.CENTER, border=Card.BORDER_WIDTH)
        hbox1.Add(kindbut, proportion=0, flag=wx.RIGHT,          border=Card.BORDER_WIDTH)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(content, proportion=1, flag=wx.EXPAND, border=Card.BORDER_THICK)

        # hbox3 = wx.BoxSizer(wx.HORIZONTAL)        
        # hbox3.Add(label  , proportion=0, flag=wx.RIGHT, border=Card.BORDER_WIDTH)

        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)
        vbox.Add(hbox1, proportion=0, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)
        vbox.Add(hbox2, proportion=1, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_THICK)
        # vbox.Add(hbox3, proportion=0, flag=wx.RIGHT|wx.EXPAND, border=Card.BORDER_WIDTH)
        
        # Bindings
        kindbut.Bind(wx.EVT_BUTTON, self.OnKindPressed)
        content.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.kindbut = kindbut
        self.title = title
        self.content = content
        self.Show(True)

    def Dump(self):
        pos = self.GetPosition()
        return {"class": "Content",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "kind": self.GetKind(),
                "title": self.GetTitle(),
                "content": self.GetContent()}

    def SetColours(self, kind):
        if   kind == Content.CONCEPT_LBL:
             self.SetBackgroundColour(Content.CONCEPT_CL)
             self.content.SetBackgroundColour(Content.CONCEPT_BG_CL)
             # self.content.BeginTextColour(Content.CONCEPT_CNT_CL)
        elif kind == Content.ASSUMPTION_LBL:
             self.SetBackgroundColour(Content.ASSUMPTION_CL)
             self.content.SetBackgroundColour(Content.ASSUMPTION_BG_CL)
             # self.content.BeginTextColour(Content.ASSUMPTION_CNT_CL)
        elif kind == Content.RESEARCH_LBL:
             self.SetBackgroundColour(Content.RESEARCH_CL)
             self.content.SetBackgroundColour(Content.RESEARCH_BG_CL)
             # self.content.BeginTextColour(Content.RESEARCH_CNT_CL)
        elif kind == Content.FACT_LBL:
             self.SetBackgroundColour(Content.FACT_CL)
             self.content.SetBackgroundColour(Content.FACT_BG_CL)
             # self.content.BeginTextColour(Content.FACT_CNT_CL)
        else:
             self.SetBackgroundColour(Content.DEFAULT_CL)


    ### Callbacks

    def OnKeyDown(self, ev):
        ### skip TAB, so that we don't input \t and tab traversal still works
        if ev.GetKeyCode() != 9:
            ev.ResumePropagation(True)
            ev.Skip()

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
# Auxiliary classes
######################
                
class EditText(wx.Control):
    def __init__(self, parent, id = wx.ID_ANY, label="", pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(EditText, self).__init__(parent, id=id, pos=pos, size=size, style=wx.BORDER_NONE)

        self.InheritAttributes()
        self.BackgroundColour = parent.BackgroundColour

        self.text  = wx.StaticText(self, label=label, style=wx.BORDER_NONE|wx.ST_NO_AUTORESIZE)
        self.entry = wx.TextCtrl(self,   value=label, style=wx.BORDER_SUNKEN|wx.TE_PROCESS_ENTER)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.text,  proportion=1, flag=wx.ALL|wx.EXPAND, border=0)
        box.Add(self.entry, proportion=1, flag=wx.ALL|wx.EXPAND, border=0)
        self.SetSizer(box)

        self.text.Bind(wx.EVT_LEFT_DOWN, self.ShowEntry)
        self.text.Bind(wx.EVT_TEXT_ENTER, self.ShowEntry)
        self.entry.Bind(wx.EVT_LEFT_DOWN, self.ShowText)
        self.entry.Bind(wx.EVT_TEXT_ENTER, self.ShowText)
        self.entry.Bind(wx.EVT_KILL_FOCUS, self.ShowText)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        self.text.Show()
        self.entry.Hide()        
        self.Show()


    ### Behavior functions

    def SetLabel(self, lbl):
        # print "label passed to SetLabel: " + str(lbl)
        self.text.SetLabel(lbl)
        self.entry.SetValue(lbl)
        return super(EditText, self).SetLabel(lbl)        

    def SetValue(self, lbl):
        self.SetLabel(lbl)

    def GetLabel(self):
        print "getlabel"
        return self.text.GetLabel()

    def GetValue(self):
        return self.GetLabel()

    def ShowEntry(self, ev):
        print "show entry: " + str(ev.GetEventObject())
        self.text.Hide()
        self.entry.Show()
        self.entry.SetFocus()

    def ShowText(self, ev):
        print "showtext: " + str(ev.GetEventObject())
        self.entry.Hide()
        self.text.SetLabel(self.entry.GetValue())
        self.text.Show()


    ### Auxiliary functions
    
    def ShouldInheritColours(self):
        return True

    def InheritBackgroundColour(self):
        return True

    
    ### Callbacks

    def OnFocus(self, ev):
        if self.text.IsShown():
            self.text.SetFocus()
        else:
            self.entry.SetFocus()
