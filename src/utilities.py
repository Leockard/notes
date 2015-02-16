# utilities.py
# -*- coding: utf-8 -*-

# some auxiliary classes for notes.py

import wx
import wx.lib.stattext as st
import wx.lib.newevent as ne
from math import sqrt


######################
# Auxiliary classes
######################

class AutoSize(wx.ScrolledWindow):
    SCROLL_STEP = 10
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        super(AutoSize, self).__init__(parent, id=id, pos=pos, size=size, style=style)

        self.content_sz = wx.Size(size[0], size[1])
        self.SetScrollRate(self.SCROLL_STEP, self.SCROLL_STEP)

        # bindings
        self.Bind(wx.EVT_SIZE, self.AutoSizeOnSize)

        
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
            self.SetVirtualSize(self.content_sz)

    def FitToChildren(self):
        """
        Call to set the virtual (content) size to tightyly fit the children.
        If there are no children, keeps the virtual size as it is (don't shrink).
        """
        children = self.GetChildren()
        if len(children) == 0: return

        # set view start at (0,0) to get absolute cordinates
        shown = self.IsShown()
        if shown: self.Hide()
        view = self.GetViewStart()
        self.Scroll(0, 0)

        # calculate children extension
        rects = [c.GetRect() for c in self.GetChildren()]
        right  = max(rects, key=lambda r: r.right).right
        bottom = max(rects, key=lambda r: r.bottom).bottom

        # compare and update
        sz = self.content_sz
        if right  > sz.x: sz = wx.Size(right, sz.y)
        if bottom > sz.y: sz = wx.Size(sz.x, bottom)
        self.content_sz = sz
        self.SetVirtualSize(self.content_sz)

        # return to the previous scroll position
        self.Scroll(view[0], view[1])
        if shown: self.Show()

    def ExpandVirtualSize(self, dx, dy):
        """Enlarges the virtual size by dx, dy."""
        size = wx.Size(self.content_sz.x + dx, self.content_sz.y + dy)
        self.SetVirtualSize(size)
        self.content_sz = size


    ### Callbacks

    def AutoSizeOnSize(self, ev):
        self.UpdateContentSize(ev.GetSize())
        ev.Skip()


        

class ColouredText(wx.TextCtrl):
    def __init__(self, parent, value ="", size=wx.DefaultSize, pos=wx.DefaultPosition, style=0):
        super(ColouredText, self).__init__(parent, value=value, size=size, pos=pos, style=style)

    def SetBackgroundColour(self, new_cl):
        # If we change background colour from A to B, but a char in the text
        # has background colour C, TextCtrl.SetBackgroundColour() won't change
        # it correctly. Solution: store the bg colour (of those chars that have
        # a different bg colour than the current one), change the bg for all
        # and then restore the ones saved.
        text = self.GetValue()
        attr = wx.TextAttr()
        cur = self.GetBackgroundColour()
        char_old_bg = {}

        # store those bg's different than the current
        for i in range(len(text)):
            self.GetStyle(i, attr)
            old = attr.GetBackgroundColour()
            if old != cur:
                char_old_bg[i] = old

        # set the new bg for all, but don't use attr again!
        # char_old_bg is pointing to one of its members
        super(ColouredText, self).SetBackgroundColour(new_cl)
        self.SetStyle(0, len(text), wx.TextAttr(None, new_cl))

        # restore the saved ones
        for i in char_old_bg.keys():
            attr.SetBackgroundColour(char_old_bg[i])
            self.SetStyle(i, i+1, attr)



class EditText(ColouredText):
    DEFAULT_SZ = (200, 20)
    DEFAULT_STYLE = wx.BORDER_NONE|wx.TE_RICH|wx.TE_PROCESS_ENTER|wx.TE_MULTILINE|wx.TE_NO_VSCROLL
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    DEFAULT_2_CL = (255, 255, 255, 255)
    
    def __init__(self, parent, value="", pos=wx.DefaultPosition, size=DEFAULT_SZ, style=DEFAULT_STYLE):
        super(EditText, self).__init__(parent, pos=pos, size=size, style=style, value=value)

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
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

    
    ### Behavior functions

    def ToggleColours(self):
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

    def GetSecondColour(self):
        return self.second_cl

    def SetFirstColour(self, cl):
        self.first_cl = cl
        self.SetBackgroundColour(self.first_cl)

    def GetFirstColour(self):
        return self.first_cl


    ### Callbacks

    def OnKeyDown(self, ev):
        # skip everything but tab
        if ev.GetKeyCode() != 9:
            ev.Skip()
        # on TAB: don't input a \t char and simulate a tab traversal
        else:
            self.Navigate(not ev.ShiftDown())

    def OnEnter(self, ev):
        self.ToggleColours()
        self.Navigate(not wx.MouseState().ShiftDown())
    
    def OnLeftDown(self, ev):
        if self.GetBackgroundColour() == self.first_cl:
            self.ShowSecondColour()
        # important
        ev.Skip()

    def OnSetFocus(self, ev):
        self.SetInsertionPoint(self.GetLastPosition())
        self.ShowSecondColour()

    def OnKillFocus(self, ev):
        self.SetSelection(0,0)
        self.ShowFirstColour()
        
        

######################
# Auxiliary functions
######################

def GetAncestors(ctrl):
    """Returns a list of ctrl's parent and its parent's parent and so on."""
    ancestors = []
    while ctrl:
        ancestors.append(ctrl.GetParent())
        ctrl = ctrl.GetParent()
    # the last element was None
    del ancestors[-1]
    return ancestors

def GetCardAncestor(ctrl):
    """If the ctrl is inside a Card, return it. Otherwise, return None."""
    from card import Card
    cards = [p for p in GetAncestors(ctrl) if isinstance(p, Card)]
    if cards:
        return cards[0]
    else:
        return None

def DumpSizerChildren(sizer, depth=1, full=False):
    """Recursively prints all children."""
    # prepare the info string for the sizer
    # indentation
    sizer_info = str("    " * (depth - 1))

    # obj info
    if full: sizer_info = sizer_info + "Sizer: " # + str(sizer)
    else:    sizer_info = sizer_info + "Sizer: " # + str(sizer.__class__)

    # orientation
    orient = sizer.GetOrientation()
    if orient == wx.VERTICAL: sizer_info = sizer_info + "vertical"
    else:                     sizer_info = sizer_info + "horizontal"
        
    print sizer_info

    # for each children: indentation, class and shown state
    for c in sizer.GetChildren():
        if c.IsWindow():
            msg = str("    " * depth)

            if full: msg = msg + str(c.GetWindow())
            else:    msg = msg + str(c.GetWindow().__class__)

            if c.IsShown(): msg = msg + ", shown"
            else:           msg = msg + ", hidden"                

            print msg

        # and recursively for nested sizers
        elif c.IsSizer():
            DumpSizerChildren(c.GetSizer(), depth + 1, full)

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

def dist2(p1, p2):
    return sum([i**2 for i in p1 - p2])

def dist(p1, p2):
    return sqrt(dist2(p1, p2))

def IsFunctionKey(key):
    fkeys = [wx.WXK_F1, wx.WXK_F2, wx.WXK_F3, wx.WXK_F4, wx.WXK_F5, wx.WXK_F6, wx.WXK_F7, wx.WXK_F8, wx.WXK_F9, wx.WXK_F10, wx.WXK_F11, wx.WXK_F12, wx.WXK_F13, wx.WXK_F14, wx.WXK_F15, wx.WXK_F16, wx.WXK_F17, wx.WXK_F18, wx.WXK_F19, wx.WXK_F20, wx.WXK_F21, wx.WXK_F22, wx.WXK_F23, wx.WXK_F24]
    return any([key == k for k in fkeys])
