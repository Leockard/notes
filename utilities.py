# utilities.py
# some auxiliary classes for notes.py

import wx


######################
# Auxiliary classes
######################

class AutoSize(wx.ScrolledWindow):
    SCROLL_STEP = 20
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        super(AutoSize, self).__init__(parent, id=id, pos=pos, size=size, style=style)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.SetScrollRate(self.SCROLL_STEP, self.SCROLL_STEP)
        self.content_sz = wx.Size(size[0], size[1])
        self.SetVirtualSize(size)

    def OnSize(self, ev):
        real_sz = ev.GetSize()
        virt_sz = self.content_sz
        if real_sz.x > virt_sz.x: self.content_sz = wx.Size(real_sz.x, virt_sz.y)
        if real_sz.y > virt_sz.y: self.content_sz = wx.Size(virt_sz.x, real_sz.y)
        self.SetVirtualSize(self.content_sz)

    def FitToChildren(self):
        """Call to set the virtual (content) size to fit the children."""
        rects = [c.GetRect() for c in self.GetChildren()]
        # left   = min(rects, key=lambda r: r.left)       # don't add windows in negative positions
        # top    = min(rects, key=lambda r: r.top)        # don't add windows in negative positions
        right  = max(rects, key=lambda r: r.right).right
        bottom = max(rects, key=lambda r: r.bottom).bottom
        sz = self.content_sz
        if right  > sz.x: sz = wx.Size(right, sz.y)
        if bottom > sz.y: sz = wx.Size(sz.x, bottom)
        self.content_sz = sz
        self.SetVirtualSize(self.content_sz)

        

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
