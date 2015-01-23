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
            print "changing content_sz"
            self.content_sz = wx.Size(sz.x, self.content_sz.y)
        if sz.y > virt_sz.y:
            flag = True
            print "changing content_sz"
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


                
class EditText(wx.TextCtrl):
    DEFAULT_SZ = (200, 25)
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    DEFAULT_2_CL = (255, 255, 255, 255)
    
    def __init__(self, parent, id = wx.ID_ANY, label="",
                 pos=wx.DefaultPosition, size=DEFAULT_SZ,
                 style=wx.BORDER_NONE|wx.TAB_TRAVERSAL):
        super(EditText, self).__init__(parent, id=id, pos=pos, size=size,
                                       style=style|wx.TE_PROCESS_ENTER)

        # colours
        self.first_cl = parent.GetBackgroundColour()
        self.second_cl = self.DEFAULT_2_CL
        self.SetBackgroundColour(self.first_cl)

        # style
        self.SetFont(wx.Font(*self.DEFAULT_FONT))
        
        # bindings
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_TEXT_ENTER, self.ToggleColours)

    
    ### Behavior functions

    def ToggleColours(self, ev):
        if self.GetBackgroundColour() == self.first_cl:
            self.ShowSecondColour()
        else:
            self.ShowFirstColour()
    
    def ShowFirstColour(self):
        self.SetBackgroundColour(self.first_cl)

    def ShowSecondColour(self):
        self.SetBackgroundColour(self.second_cl)

    def SetSecondColour(self, cl):
        self.second_cl = cl

    def SetFirstColour(self, cl):
        self.first_cl = cl
        self.SetBackgroundColour(self.first_cl)


    ### Callbacks
    
    def OnLeftDown(self, ev):
        if self.GetBackgroundColour() == self.first_cl:
            self.ShowSecondColour()
        else:
            ev.Skip()

    def OnSetFocus(self, ev):
        self.ShowSecondColour()

    def OnKillFocus(self, ev):
        self.ShowFirstColour()
        
        

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
