# -*- coding: utf-8 -*-
"""This module contains classes derived from wx that could be
used outside of `threepy5`.
"""
import wx
import wx.lib.stattext as st
import wx.lib.newevent as ne


#####################################################
#             Reusable wx classes                   #
#####################################################

######################
# Class AutoSize
######################

class AutoSize(wx.ScrolledWindow):
    """`AutoSize` is a `wx.ScrolledWindow` that automates the process of setting
    up a window which has a "virtual size". In `wx`, "virtual size" is the size of
    the underlying contents of the window, while "size" is the screen real estate
    it occupies). `AutoSize` also holds various methods to facilitate the management
    of virtual size.
    """
    SCROLL_STEP = 10

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(AutoSize, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_SIZE, self.__on_size)
        self.SetScrollRate(self.SCROLL_STEP, self.SCROLL_STEP)

        self._virtual_sz = wx.Size(0, 0)
        if "size" in kwargs.keys():
            sz = kwargs["size"]
            self._virtual_sz = wx.Size(sz[0], sz[1])


    ### methods

    def UpdateVirtualSize(self, sz):
        """Recompute the virtual size.

        * `sz: ` a `(width, height)` size tuple. If it contains a dimension that
        is bigger than the current virtual size, change the virtual size.
        """
        flag = False
        virt_sz = self._virtual_sz

        if sz.x > virt_sz.x:
            flag = True
            self._virtual_sz = wx.Size(sz.x, self._virtual_sz.y)
        if sz.y > virt_sz.y:
            flag = True
            self._virtual_sz = wx.Size(self._virtual_sz.x, sz.y)

        if flag:
            self.VirtualSize = self._virtual_sz

    def FitToChildren(self, pad=0):
        """Call to set the virtual size to fit the children. If there are
        no children, keeps the virtual size as it is (don't shrink). If the
        window is resized, the new size will be enough to fit all children,
        plus a padding.

        * `pad: ` additional padding in case the window is resized.
        """
        if len(self.Children) == 0:
            return

        # set view start at (0,0) to get absolute cordinates
        shown = self.IsShown()
        if shown: self.Hide()
        view = self.GetViewStart()
        self.Scroll(0, 0)

        # calculate children extension
        rects = [c.Rect for c in self.Children]
        right  = max(rects, key=lambda r: r.right).right
        bottom = max(rects, key=lambda r: r.bottom).bottom

        # compare and update
        sz = self._virtual_sz
        if right  > sz.x: sz = wx.Size(right + pad, sz.y)
        if bottom > sz.y: sz = wx.Size(sz.x, bottom + pad)
        self._virtual_sz = sz
        self.VirtualSize = self._virtual_sz

        # return to the previous scroll position
        self.Scroll(view[0], view[1])
        if shown: self.Show()

    def ExpandVirtualSize(self, dx, dy):
        """Enlarge the virtual size.

        * `dx: ` pixels to add in the X direction.
        * `dy: ` pixels to add in the Y direction.
        """
        size = wx.Size(self._virtual_sz.x + dx, self._virtual_sz.y + dy)
        self._virtual_sz = size
        self.VirtualSize = size

    def GetViewStartPixels(self):
        """Return the point at which the current view starts, ie, the absolute
        coordinates of the point that, due to the scrollbars, currently lies at `(0,0)`.
        """
        view = self.GetViewStart()
        return wx.Point(*[v * self.SCROLL_STEP for v in view])


    ### Callbacks

    def __on_size(self, ev):
        """Listens to `wx.EVT_SIZE`."""
        self.UpdateVirtualSize(ev.GetSize())
        ev.Skip()



class ColouredText(wx.TextCtrl):
    """
    `ColouredText` overrides `TextCtrl.SetBackgroundColour`, so that all chars'
    background colours are changed correctly.
    """

    def __init__(self, parent, value ="", size=wx.DefaultSize, pos=wx.DefaultPosition, style=0):
        """Constructor.

        * `parent: ` the parent window.
        * `value: ` the intial text for this control.
        * `size: ` by default, is `wx.DefaultSize`.
        * `pos: ` by default, is `wx.DefaultPosition`.
        * `style: ` the style for this window.
        """
        super(ColouredText, self).__init__(parent, value=value, size=size, pos=pos, style=style)

    def SetBackgroundColour(self, new_cl):
        """Overridden from `wx.TextCtrl`. Changes the background colour respecting
        each individual char's background, as set by `wx.TextCtrl.SetStyle`.

        If we change background colour from A to B, but a char in the text
        has background colour C, `TextCtrl.SetBackgroundColour` won't change
        it correctly. This method solves that problem.
        """
        # Solution: store the bg colour of those chars that have
        # a different bg colour than the current one, change the bg for all
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
    """
    `EditText` is a `wx.TextCtrl` that changes background colour when it has
    focus. Basically, we want to make it look like a `wx.StaticText`, except when
    the user is editing its contents, in which case we want it to look like
    a `wx.TextCtrl`. The background colour `EditText` has when it looks like a
    `wx.StaticText` (which is in most cases its parent's background colour) is
    called "first colour". The colour it has when it looks like a regular `wx.TextCtrl`
    is the "second colour". The second colour is usually whie.
    """
                
    DEFAULT_SZ = (200, 20)
    DEFAULT_STYLE = wx.BORDER_NONE|wx.TE_RICH|wx.TE_PROCESS_ENTER|wx.TE_MULTILINE|wx.TE_NO_VSCROLL
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    DEFAULT_2_CL = (255, 255, 255, 255)
    
    def __init__(self, parent, value="", pos=wx.DefaultPosition, size=DEFAULT_SZ, style=DEFAULT_STYLE, first_cl=None):
        """Constructor.

        * `parent: ` the parent window.
        * `value: ` the intial text for this control.
        * `pos: ` by default, is `wx.DefaultPosition`.
        * `size: ` by default, is `wx.DefaultSize`.
        * `style: ` by default, is `EditText.DEFAULT_STYLE`.
        """
        super(EditText, self).__init__(parent, pos=pos, size=size, style=style, value=value)

        # colours
        self.first_cl = first_cl or parent.GetBackgroundColour()
        self.second_cl = self.DEFAULT_2_CL
        self.SetBackgroundColour(self.first_cl)

        # style
        self.SetFont(wx.Font(*self.DEFAULT_FONT))
        
        # bindings
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnKillFocus)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnEnter)

    
    ### Behavior functions

    def ToggleColours(self):
        """Change between first and second colours."""
        if self.GetBackgroundColour() == self.first_cl:
            self.ShowSecondColour()
        else:
            self.ShowFirstColour()
    
    def ShowFirstColour(self):
        """Set the background to the first colour."""
        self.SetBackgroundColour(self.first_cl)

    def ShowSecondColour(self):
        """Set the background to the second colour."""
        self.SetBackgroundColour(self.second_cl)

    def SetSecondColour(self, cl):
        """Sets the second colour."""
        self.second_cl = cl

    def GetSecondColour(self):
        """Get the second colour.

        `returns: ` a `(R, G, B, alpha)` tuple."""
        return self.second_cl

    def SetFirstColour(self, cl):
        """Sets the first colour."""
        self.first_cl = cl
        self.SetBackgroundColour(self.first_cl)

    def GetFirstColour(self):
        """Get the first colour.
        
        `returns: ` a `(R, G, B, alpha)` tuple."""
        return self.first_cl


    ### callbacks

    def OnEnter(self, ev):
        self.ToggleColours()
        self.Navigate(not wx.MouseState().ShiftDown())
    
    def OnLeftDown(self, ev):
        if self.GetBackgroundColour() == self.first_cl:
            self.ShowSecondColour()
        ev.Skip()

    def OnSetFocus(self, ev):
        last = self.GetLastPosition()
        self.SetInsertionPoint(last)
        self.SetSelection(0, last)
        self.ShowSecondColour()

    def OnKillFocus(self, ev):
        self.SetSelection(0,0)
        self.ShowFirstColour()
        
        

#####################################################
#             Reusable wx functions                 #
#####################################################

def GetAncestors(ctrl):
    """Returns a list of all of ctrl's wx.Window ancestors.
    
    * `ctrl: ` a wx object.
    
    `returns: ` a list of all wx ancestors of `ctrl`.
    """
    ancestors = []
    while ctrl:
        ancestors.append(ctrl.GetParent())
        ctrl = ctrl.GetParent()
    # the last element was None
    del ancestors[-1]
    return ancestors

def GetCardAncestor(ctrl):
    """Returns the Card ancestor of its argument.

    * `ctrl: ` a wx object.

    `returns: ` The first `Card` ancestor of `ctrl`, or `None`.
    """
    from board import CardWin
    cards = [p for p in GetAncestors(ctrl) if isinstance(p, CardWin)]
    if cards:
        return cards[0]
    else:
        return None

def DumpSizerChildren(sizer, depth=1, full=False):
    """Recursively prints all children of a wx.Sizer.

    * `sizer: ` a `wx.Sizer`.
    * `depth: ` the depth at which to start printing items. Should always
    be `1` when called from outside itself.
    * `full: ` set to `True` to print full object information, including
    memory address.
    """
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
            else:    msg = msg + str(c.GetWindow().__class__.__name__)

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

    * `p1: ` any object with two fields addressable as `p1[0]` and `p1[1]`.
    * `p2: ` idem.

    `returns: ` a `wx.Rect` with top left corner at `p1`, bottom right corner at `p2` and positive width and height.
    """
    l = min(p1[0], p2[0])
    t = min(p1[1], p2[1])
    w = abs(p1[0] - p2[0])
    h = abs(p1[1] - p2[1])
    return wx.Rect(l, t, w, h)

def IsFunctionKey(key):
    """Check if `key` is a function key.

    * `key: ` a `wx.KeyCode`, eg, as returned by `wx.MouseEvent.GetKeyCode()`.

    `returns: ` `True` if `key` is one of the 24 possible values of `wx.WXK_F*`, or `False`.
    """
    fkeys = [wx.WXK_F1, wx.WXK_F2, wx.WXK_F3, wx.WXK_F4, wx.WXK_F5, wx.WXK_F6, wx.WXK_F7, wx.WXK_F8, wx.WXK_F9, wx.WXK_F10, wx.WXK_F11, wx.WXK_F12, wx.WXK_F13, wx.WXK_F14, wx.WXK_F15, wx.WXK_F16, wx.WXK_F17, wx.WXK_F18, wx.WXK_F19, wx.WXK_F20, wx.WXK_F21, wx.WXK_F22, wx.WXK_F23, wx.WXK_F24]
    return any([key == k for k in fkeys])



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
for field in dir(wx.ScrolledWindow):
    __pdoc__['AutoSize.%s' % field] = None
for field in dir(wx.TextCtrl):
    __pdoc__['ColouredText.%s' % field] = None
for field in dir(ColouredText):
    __pdoc__['EditText.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in AutoSize.__dict__.keys():
    if 'AutoSize.%s' % field in __pdoc__.keys():
        del __pdoc__['AutoSize.%s' % field]
for field in ColouredText.__dict__.keys():
    if 'ColouredText.%s' % field in __pdoc__.keys():
        del __pdoc__['ColouredText.%s' % field]
for field in EditText.__dict__.keys():
    if 'EditText.%s' % field in __pdoc__.keys():
        del __pdoc__['EditText.%s' % field]
