# utilities.py
# some auxiliary classes for notes.py

import wx
import inspect
import wx.lib.stattext as st


######################
# Auxiliary classes
######################

class AutoSize(wx.ScrolledWindow):
    SCROLL_STEP = 20
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        super(AutoSize, self).__init__(parent, id=id, pos=pos, size=size, style=style)
        self.Bind(wx.EVT_SIZE, self.AutoSizeOnSize)
        self.SetScrollRate(self.SCROLL_STEP, self.SCROLL_STEP)
        self.content_sz = wx.Size(size[0], size[1])

    def UpdateContentSize(self, sz):
        """
        If sz contains a dimension that is bigger than the
        current virtual size, change the virtual size.
        """
        flag = False
        virt_sz = self.content_sz
        
        if sz.x > virt_sz.x:
            flag = True
            self.content_sz = wx.Size(sz.x, self.content_sz.y)
        if sz.y > virt_sz.y:
            flag = True
            self.content_sz = wx.Size(self.content_sz.x, sz.y)
            
        if flag:
            print "calling vritual size with: ", self.content_sz
            self.SetVirtualSize(self.content_sz)

    def AutoSizeOnSize(self, ev):
        self.UpdateContentSize(ev.GetSize())

    def FitToChildren(self):
        """
        Call to set the virtual (content) size to fit the children. If there are
        no children, keeps the virtual size as it is (does not shrink).
        """
        print "fit to children"
        children = self.GetChildren()
        if len(children) == 0: return
        
        rects = [c.GetRect() for c in self.GetChildren()]
        # left   = min(rects, key=lambda r: r.left)       # don't add windows in negative positions
        # top    = min(rects, key=lambda r: r.top)        # don't add windows in negative positions
        right  = max(rects, key=lambda r: r.right).right
        bottom = max(rects, key=lambda r: r.bottom).bottom
        sz = self.content_sz
        print "ri, bo: ", right, bottom
        print "cur sz: ", sz
        if right  > sz.x: sz = wx.Size(right, sz.y)
        if bottom > sz.y: sz = wx.Size(sz.x, bottom)
        self.content_sz = sz
        print "new sz: ", self.content_sz
        self.SetVirtualSize(self.content_sz + (1000, 1000))



class Text(st.GenStaticText):
    def __init__(self, parent, id=wx.ID_ANY, label="", size=wx.DefaultSize, style=0):
        super(Text, self).__init__(parent, label=label, style=wx.BORDER_NONE, size=size)

    def AcceptsFocus(self):
        return True

    def AcceptsFocusFromKeyboard(self):
        return True


    
class EditText(wx.Panel):
    DEFAULT_SZ = (200, 25)
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    
    def __init__(self, parent, id = wx.ID_ANY, label="", pos=wx.DefaultPosition, size=DEFAULT_SZ, style=wx.BORDER_NONE|wx.TAB_TRAVERSAL):
        super(EditText, self).__init__(parent, id=id, pos=pos, size=size, style=style)

        # self.text  = st.GenStaticText(self, label=label, style=wx.BORDER_NONE, size=size)
        self.text  = Text(self, label=label, style=wx.BORDER_NONE, size=size)
        self.entry = wx.TextCtrl(self, value=label,
                                 style=wx.BORDER_SUNKEN|wx.TE_PROCESS_ENTER|wx.TE_MULTILINE,
                                 size=size)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.text,  proportion=1, flag=wx.LEFT|wx.EXPAND, border=5)
        box.Add(self.entry, proportion=1, flag=wx.ALL|wx.EXPAND,  border=0)
        self.SetSizer(box)

        self.text.Bind(wx.EVT_LEFT_DOWN, self.ShowEntry)
        self.text.Bind(wx.EVT_CHAR, self.OnChar)
        self.entry.Bind(wx.EVT_LEFT_DOWN, self.ShowText)
        self.entry.Bind(wx.EVT_TEXT_ENTER, self.ShowText)
        self.entry.Bind(wx.EVT_KILL_FOCUS, self.ShowText)
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocus)

        self.text.SetFont(wx.Font(self.DEFAULT_FONT[0], self.DEFAULT_FONT[1], self.DEFAULT_FONT[2], self.DEFAULT_FONT[3]))
        self.text.Show()
        self.entry.Hide()
        self.Show()


    ### Behavior functions

    def SetHint(self, txt):
        # note we are not calling SetLabel on purpose.
        # we only need to change the label of text, not of entry
        self.text.SetLabel(txt)

    def SetFont(self, font):
        self.text.SetFont(font)

    def SetBackgroundColour(self, cl):
        super(EditText, self).SetBackgroundColour(cl)
        self.text.SetBackgroundColour(cl)

    def SetEntryColour(self, cl):
        self.entry.SetBackgroundColour(cl)

    def SetLabel(self, lbl):
        self.text.SetLabel(lbl)
        self.entry.SetValue(lbl)
        return super(EditText, self).SetLabel(lbl)        

    def GetLabel(self):
        return self.text.GetLabel()

    def ShowEntry(self, ev):
        print self.text.AcceptsFocus()
        print self.text.AcceptsFocusFromKeyboard()
        self.entry.Show()
        self.entry.SetFocus()

    def ShowText(self, ev):
        self.entry.Hide()
        self.text.SetLabel(self.entry.GetValue())
        self.text.Show()
        self.text.SetFocus()


    ### Auxiliary functions

    
    ### Callbacks

    def OnChar(self, ev):
        code = ev.GetKeyCode()
        if code == 13 or code == 32 or code in range(65, 91) or code in range(97, 123):
            self.ShowEntry(None) # ShowEntry doesn't really use its argument
        else:
            ev.Skip()

    def OnFocus(self, ev):
        print "receiving focus"
        if self.text.IsShown():
            self.text.SetFocus()
        else:
            self.entry.SetFocus()
        
        

######################
# Auxiliary functions
######################

def MakeEncirclingRect(p1, p2):
    """
    Returns the wx.Rect with two opposite vertices at p1, p2.
    Width and height are guaranteed to be positive.
    """
    l = min(p1[0], p2[0])
    t = min(p1[1], p2[1])
    w = abs(p1[0] - p2[0])
    h = abs(p1[1] - p2[1])
    return wx.Rect(l, t, w, h)

def isnumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
