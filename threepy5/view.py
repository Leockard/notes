# -*- coding: utf-8 -*-
"""
View classes are used to take a closer look at certain objects.
"""

import wx
import re
from card import *
from deck import Deck
from utilities import *


######################
# DeckView Class
######################

class DeckView(AutoSize):
    """Displays a "minimap" of the current `Deck`. Uses `MiniCard` to represent a `Card` on the `Deck`."""

    DEFAULT_FACTOR  = 5
    BACKGROUND_CL   = (255, 255, 255, 255)
    DEFAULT_MINI_CL = (220, 218, 213, 255)
    
    def __init__(self, parent, deck=None, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Box`.
        * `deck: ` the `Deck` we are viewing.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(DeckView, self).__init__(parent, pos=pos, size=size)

        # members        
        self.factor = DeckView.DEFAULT_FACTOR
        self.cards = {}
        self.SetBackgroundColour(self.BACKGROUND_CL)
        self.SetDeck(deck)

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)


    ## Behavior functions

    def Clear(self):
        """Delete all `MiniCard`s from this view."""
        self.cards = {}

    def SetDeck(self, deck):
        """Sets the `Deck` we are going to view.
        * `deck: ` a `Deck`.
        """
        # clean up and add every card already present
        self.Clear()
        for c in deck.GetCards():
            self.AddCard(c)

        # set sizes
        sz = [i / self.factor for i in deck.GetSize()]
        self.SetSize(sz)
        self.UpdateContentSize(deck.content_sz)

        # set scroll
        step = deck.GetScrollPixelsPerUnit()
        self.SetScrollRate(step[0] / self.factor, step[1] / self.factor)

        # listen to events
        deck.Bind(Deck.EVT_NEW_CARD, self.OnNewCard)
        deck.Bind(wx.EVT_SIZE, self.OnDeckSize)
        deck.Bind(wx.EVT_SCROLLWIN, self.OnDeckScroll)
        
        self.deck = deck
    
    def AddCard(self, card):
        """Adds a new `MiniCard`."""
        # resize and create
        r = wx.Rect(*[i / self.factor for i in card.GetRect()])
        mini = MiniCard(self, pos=(r.left, r.top), size=(r.width, r.height))

        # if it's a content card, also mimic its colour
        if isinstance(card, Content):
            mini.SetBackgroundColour(card.GetBackgroundColour())
        else:
            mini.SetBackgroundColour(self.DEFAULT_MINI_CL)

        # listen to various actions that we want to reflect
        card.Bind(Card.EVT_CARD_DELETE, self.OnDeleteCard)
        if isinstance(card, Content):
            card.Bind(Content.EVT_CONT_KIND, self.OnContentKind)

        # retain a reference to the original, for deleting
        self.cards[card] = mini

    def RemoveCard(self, card):
        """Remove a `MiniCard`."""
        if card in self.cards.keys():
            mini = self.cards[card]
            mini.Hide()
            mini.Destroy()
            del self.cards[card]

    def SetPosition(self):
        """Calculates position relative to the `Deck`."""
        w, h = self.GetSize()
        rect = self.deck.GetClientRect()
        pos = (rect.right - w, rect.bottom - h)
        self.Move(pos)


    ### Callbacks

    def OnShow(self, ev):
        """Listens to `wx.EVT_SHOW`."""
        self.SetPosition()

    def OnDeckScroll(self, ev):
        """Listens to `wx.EVT_SCROLLWIN` from the underlying `Deck`."""
        view = ev.GetEventObject().GetViewStart()
        self.Scroll(view.x / self.factor, view.y / self.factor)

    def OnDeckSize(self, ev):
        """Listens to `wx.EVT_SIZE` from the underlying `Deck`."""
        self.SetSize([i / self.factor + 30 for i in self.deck.GetSize()])
        self.SetPosition()

    def OnNewCard(self, ev):
        """Listens to `Deck.EVT_NEW_CARD`."""
        self.AddCard(ev.GetEventObject())

    def OnDeleteCard(self, ev):
        """Listens to `Card.EVT_CARD_DELETE` from each `Card` on the `Deck`."""
        self.RemoveCard(ev.GetEventObject())
        # dont' consume it! Deck also needs it
        ev.Skip()

    def OnContentKind(self, ev):
        """Listens to `Content.EVT_CONT_KIND` events from each `Content`."""
        card = ev.GetEventObject()
        self.cards[card].SetBackgroundColour(card.GetBackgroundColour())
            


######################
# CardView Class
######################        

class CardView(wx.Panel):
    """Displays a screen-sized `Content` `Card` to facilitate editing. While
    viewing, the `Card`s are `Reparent`ed to this window.
    """
    
    CARD_PADDING = Deck.CARD_PADDING
    BACKGROUND_CL = "#CCCCCC"
    
    TITLE_FONT   = (18, wx.SWISS, wx.ITALIC, wx.BOLD)
    CONTENT_FONT = (14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def __init__(self, parent, cards=[], pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Box`.
        * `cards: ` the `Card`s we are viewing.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(CardView, self).__init__(parent, size=size)
        
        # GUI
        self.SetBackgroundColour(self.BACKGROUND_CL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # members
        self.cards = {}

                
    ### Behavior functions

    def GetCards(self):
        """Returns the `Card`s currently under viewing.

        `returns: ` a `list` of `Card`s.
        """
        return self.cards.keys()

    def AddCard(self, card):
        """Adds one `Card` to the viewing control.

        * `card: ` a `Card`.
        """
        # setup and reparent: wil restore parent when done. See RestoreCards.
        self.cards[card] = {}
        self.cards[card]["parent"] = card.GetParent()
        self.cards[card]["rect"] = card.GetRect()
        card.Reparent(self)
        card.SetViewing(True)
        card.content.SetFocus()
        
        # setup UI
        box = self.GetSizer()
        box.Add(card, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.CARD_PADDING)
        box.Layout()

        # bindings
        card.Bind(Card.EVT_CARD_CANCEL_VIEW, self.OnCancelView)

    def SetCards(self, cards):
        """Clears previous `Card`s and views the new ones.

        * `cards: ` a `list` of `Card`s.
        """
        self.Clear()
        for c in cards: self.AddCard(c)

    def Restore(self):
        """Restores the viewed `Card`s to their original parents and positions."""
        for c in self.cards:
            c.Reparent(self.cards[c]["parent"])
            c.SetRect(self.cards[c]["rect"])
        self.Clear()

    def Clear(self):
        """Clear all viewed `Card`s."""
        self.GetSizer().Clear()
        for c in self.cards.keys():
            c.SetViewing(False)
        self.cards = {}


    ### Callbacks

    def OnCancelView(self, ev):
        """Listens to `Card.EVT_CARD_CANCEL_VIEW` on every viewed `Card`."""
        self.Restore()
        event = Card.CancelViewEvent(id=wx.ID_ANY)
        event.SetEventObject(ev.GetEventObject())
        self.GetEventHandler().ProcessEvent(event)
    


######################
# MiniCard Class
######################        

class MiniCard(wx.Window):
    """The little cards shown in a `DeckView`"""
    
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `DeckView`.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(MiniCard, self).__init__(parent, pos=pos, size=size)
        
        self.SetBackgroundColour("#FFFFFF")



######################
# TagView Class
######################        

class TagView(wx.Panel):
    """The sidebard that displays a `Content` `Card`'s tags."""

    TAGS_REGEX = "^(\w+):(.*)$"
    
    def __init__(self, parent, deck, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Box`.
        * `deck: ` the parent `Deck` of the `Card`s we are viewing.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(TagView, self).__init__(parent, pos=pos, size=size)
        self.deck = deck
        self.InitUI()

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)
        deck.Bind(Deck.EVT_NEW_CARD, self.OnNewCard)


    ### Behavior functions

    def ParseTags(self, txt):
        """Parses a string looking for tags.

        * `txt: ` a string, the contents of a `Content`.

        `returns: ` a string to display in the `TagView` view, representing the tags found in `text`.
        """
        string = ""
        results = re.findall(self.TAGS_REGEX, txt, re.MULTILINE)
        for tag, val in results:
            string += tag + ":" + val
            string += "\n\n"
        return string

    def ShowTags(self, card):
        """Shows the `card`'s tags.

        * `card: ` a `Content`, whose contents will be parsed.
        """
        self.txt.SetValue(self.ParseTags(card.GetContent()))
    
        
    ### Auxiliary functions

    def InitUI(self):
        """Initialize this window's GUI and controls."""
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)

        txt = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.txt = txt        
        box.Add(txt, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)


    ### Callbacks

    def OnShow(self, ev):
        """Listens to `wx.EVT_SHOW`."""
        if ev.IsShown():
            card = GetCardAncestor(self.FindFocus())
            if card and isinstance(card, Content):
                self.ShowTags(card)

    def OnNewCard(self, ev):
        """Listens to `Deck.EVT_NEW_CARD`."""
        card = ev.GetEventObject()
        for ch in card.GetChildren():
            ch.Bind(wx.EVT_SET_FOCUS, self.OnCardChildFocus)

    def OnCardChildFocus(self, ev):
        """Listens to `wx.EVT_SET_FOCUS` on every `Card`."""
        card = GetCardAncestor(ev.GetEventObject())
        if self.IsShown():
            self.ShowTags(card)
        ev.Skip()



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
for field in dir(AutoSize):
    __pdoc__['DeckView.%s' % field] = None
for field in dir(wx.Panel):
    __pdoc__['CardView.%s' % field] = None
for field in dir(wx.Window):
    __pdoc__['MiniCard.%s' % field] = None
for field in dir(wx.Panel):
    __pdoc__['TagView.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in DeckView.__dict__.keys():
    if 'DeckView.%s' % field in __pdoc__.keys():
        del __pdoc__['DeckView.%s' % field]
for field in CardView.__dict__.keys():
    if 'CardView.%s' % field in __pdoc__.keys():
        del __pdoc__['CardView.%s' % field]
for field in MiniCard.__dict__.keys():
    if 'MiniCard.%s' % field in __pdoc__.keys():
        del __pdoc__['MiniCard.%s' % field]
for field in TagView.__dict__.keys():
    if 'TagView.%s' % field in __pdoc__.keys():
        del __pdoc__['TagView.%s' % field]
