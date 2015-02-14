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
        Call to set the virtual (content) size to fit the children. If there are
        no children, keeps the virtual size as it is.
        """
        children = self.GetChildren()
        if len(children) == 0: return

        # set view start at (0,0) to get absolute cordinates
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
    DEFAULT_SZ = (200, 25)
    DEFAULT_FONT = (12, wx.SWISS, wx.ITALIC, wx.BOLD)
    DEFAULT_2_CL = (255, 255, 255, 255)
    
    def __init__(self, parent, value="", pos=wx.DefaultPosition, size=DEFAULT_SZ,
                 style=wx.BORDER_NONE|wx.TE_RICH|wx.TE_PROCESS_ENTER|wx.TE_MULTILINE):
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
        self.ShowSecondColour()

    def OnKillFocus(self, ev):
        self.SetSelection(0,0)
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

    DeleteEvent, EVT_MGR_DELETE = ne.NewCommandEvent()

    def __init__(self, parent):
        super(SelectionManager, self).__init__(parent, size=self.SIZE, pos=self.POS)
        self.cards = []
        self.last = None
        self.active = False
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())


    ### behavior functions

    def Activate(self):
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.SetFocus()
        self.active = True

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
        self.active = False

    def IsActive(self):
        return self.active

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

    def DeleteSelected(self):
        number = len(self.cards)
        while len(self.cards) > 0:
            c = self.cards[-1]
            c.Delete()
            if c in self.cards:
                self.cards.remove(c)

        # raise the event; it differs from Card.DeleteEvent in that
        # we raise only one event for every delete action
        # e.g., if we delete five cards, there will be five Card.DeleteEvent's
        # raised, but only one SelectionManager.DeleteEvent
        event = self.DeleteEvent(id=wx.ID_ANY, number=number)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

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
            else:
                ev.Skip()

        # pass the CTRL keys to the last selected card
        elif ev.ControlDown():
            if key == ord("I"):
                self.last.OnCtrlI(ev)
            else:
                ev.Skip()

        # no modifiers
        else:
            # arrow keys: select next card    
            if   key == wx.WXK_LEFT:
                self.SelectNext("left")
            elif key == wx.WXK_RIGHT:
                self.SelectNext("right")
            elif key == wx.WXK_UP:
                self.SelectNext("up")
            elif key == wx.WXK_DOWN:
                self.SelectNext("down")

            # DEL: delete all selection
            elif key == wx.WXK_DELETE:
                self.DeleteSelected()
                
            # deactivate on any other key that's not a modifier
            elif key != 308 and key != 306:
                self.Deactivate()



class StarRating(wx.Button):
    PATH = "/home/leo/code/notes/img/"
    
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
            StarRating.BMPS = [wx.Bitmap(self.PATH + self.FILES[n]) for n in range(4)]

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
