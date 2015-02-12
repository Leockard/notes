# utilities.py
# some auxiliary classes for notes.py

import wx
import wx.lib.stattext as st
from math import sqrt


######################
# Auxiliary classes
######################

class AutoSize(wx.ScrolledWindow):
    SCROLL_STEP = 10
    
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
            self.SetVirtualSize(self.content_sz)

    def AutoSizeOnSize(self, ev):
        self.UpdateContentSize(ev.GetSize())
        ev.Skip()

    def FitToChildren(self):
        """
        Call to set the virtual (content) size to fit the children. If there are
        no children, keeps the virtual size as it is.
        """
        children = self.GetChildren()
        if len(children) == 0: return

        # set view start at 0, 0 to get absolute cordinates
        view = self.GetViewStart()

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
        self.Scroll(view[0], view[1])


                
class EditText(wx.TextCtrl):
    DEFAULT_SZ = (200, 25)
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    DEFAULT_2_CL = (255, 255, 255, 255)
    
    def __init__(self, parent, id = wx.ID_ANY, value="",
                 pos=wx.DefaultPosition, size=DEFAULT_SZ,
                 style=wx.BORDER_NONE|wx.TAB_TRAVERSAL|wx.TE_RICH|wx.TE_PROCESS_ENTER):
        super(EditText, self).__init__(parent, id=id, pos=pos, size=size, style=style, value=value)

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
        # important
        ev.Skip()

    def OnSetFocus(self, ev):
        self.ShowSecondColour()

    def OnKillFocus(self, ev):
        self.ShowFirstColour()
        
        

class SelectionManager(wx.Window):
    """
    SelectionManager is an invisible window that positions itself on the top left corner of a Board
    and gets focus every time a card is (or many cards are) selected. This is done to hide carets
    and selections from other controls while selection is active. SelectionManager also manages
    card selection by managing key down events, such as arrow keys to move selection, shift + arrow
    keys to extend selection, etc.
    """
    SIZE = (1,1)
    POS  = (0,0)

    def __init__(self, parent):
        super(SelectionManager, self).__init__(parent, size=self.SIZE, pos=self.POS)
        self.cards = []
        self.last = None
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())


    ### behavior functions

    def Activate(self):
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.SetFocus()

    def Deactivate(self):
        # return focus to the last card
        if self.last:
            self.last.SetFocus()
            self.last = None
        else:
            self.GetParent().SetFocus()
            
        # clean up
        for c in self.cards:
            c.Unselect()
        self.cards = []
        self.Unbind(wx.EVT_KEY_DOWN)

    def GetSelection(self):
        return self.cards

    def SelectCard(self, card, new_sel=False):
        """
        Selects the card. If new_sel is True, erase all other
        selected cards and select only this one.
        """
        # if new_sel, select only this card
        if new_sel:
            self.Activate()
            self.UnselectAll()
            self.cards = [card]
            card.Select()
            self.last = card
            
        # else, select card only if it was not already selected
        elif card not in self.cards:
            self.cards.append(card)
            for c in self.cards:
                self.Activate()                
                c.Select()
                self.last = card

    def UnselectCard(self, card):
        n = len(self.cards)
        if card in self.cards:
            self.cards.remove(card)
            card.Unselect()

    def UnselectAll(self):
        """
        Unselects all cards. Be sure to call this method instead of
        Unselect()ing every card for proper cleanup.
        """
        while len(self.cards) > 0:
            c = self.cards[0]
            self.UnselectCard(c)

    def SelectGroup(self, group, new_sel):
        if new_sel: self.UnselectAll()
        for c in group.GetMembers(): self.SelectCard(c)

    def SelectNext(self, direc):
        """
        Selects next card in the specified direction. The selected
        card may not be the same as the one returned from GetNextCard().
        direc should be one of "left", "right", "up" or "down".
        """
        if   direc == "left":
            side  = lambda x: x.right
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == "right":
            side  = lambda x: x.left
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetTopRight()
        elif direc == "up":
            side  = lambda x: x.bottom
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == "down":
            side  = lambda x: x.top
            getp1 = lambda x: x.GetBottomLeft()
            getp2 = lambda x: x.GetTopLeft()

        sel = self.GetSelection()
        bd = self.GetParent()
        if len(sel) == 1:
            # get those that are above me
            rect = sel[0].GetRect()
            nxt = []
            if direc == "left" or direc == "up":
                nxt = [c for c in bd.GetCards() if side(c.GetRect()) < side(rect)]
            elif direc == "right" or direc == "down":
                nxt = [c for c in bd.GetCards() if side(c.GetRect()) > side(rect)]
            if nxt:
                # if any, order them by distance
                nxt.sort(key=lambda x: dist2(getp1(x.GetRect()), getp2(rect)))
                # and select the nearest one
                self.SelectCard(nxt[0], True)

    def MoveSelected(self, dx, dy):
        """Move all selected cards by dx, dy."""
        for c in self.GetSelection():
            self.GetParent().MoveCard(c, dx, dy)


    ### callbacks

    def OnKeyDown(self, ev):
        key = ev.GetKeyCode()
        bd = self.GetParent()

        # alt + arrow: move selection
        if ev.AltDown():
            if   key == wx.WXK_LEFT:
                self.MoveSelected(-bd.SCROLL_STEP, 0)
            elif key == wx.WXK_RIGHT:
                self.MoveSelected(bd.SCROLL_STEP, 0)
            elif key == wx.WXK_UP:
                self.MoveSelected(0, -bd.SCROLL_STEP)
            elif key == wx.WXK_DOWN:
                self.MoveSelected(0, bd.SCROLL_STEP)

        # naked arrow keys: select next card    
        else:
            if   key == wx.WXK_LEFT:
                self.SelectNext("left")
            elif key == wx.WXK_RIGHT:
                self.SelectNext("right")
            elif key == wx.WXK_UP:
                self.SelectNext("up")
            elif key == wx.WXK_DOWN:
                self.SelectNext("down")
                
            # any other key: cancel selection and
            # return focus to the last card
            else:
                self.Deactivate()

    
    
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

def DumpSizerChildren(sizer, depth=1):
    """Recursively prints all children."""
    print ("    " * (depth - 1)) + "Sizer: ", sizer
    
    for c in sizer.GetChildren():
        if c.IsWindow():
            print "    " * depth, c.GetWindow()
        elif c.IsSizer():
            DumpSizerChildren(c.GetSizer(), depth + 1)
        else:
            print "wtf"

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
