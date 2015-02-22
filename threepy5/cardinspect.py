# -*- coding: utf-8 -*-
"""
Inspect classes are used to take a closer look at certain objects.
"""

import wx
import re
from card import *
from board import Deck
from utilities import *


######################
# DeckInspect Class
######################

class DeckInspect(AutoSize):
    """Displays a "minimap" of the current `Deck`. Uses `MiniCard` to represent a `Card` on the `Deck`."""

    DEFAULT_FACTOR  = 5
    BACKGROUND_CL   = (255, 255, 255, 255)
    DEFAULT_MINI_CL = (220, 218, 213, 255)
    
    def __init__(self, parent, deck=None, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Page`.
        * `deck: ` the `Deck` we are inspecting.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(DeckInspect, self).__init__(parent, pos=pos, size=size)

        # members        
        self.factor = DeckInspect.DEFAULT_FACTOR
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
        """Sets the `Deck` we are going to inspect.
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
# CardInspect Class
######################        

class CardInspect(wx.Panel):
    """Displays a screen-sized `Content` `Card` to facilitate editing. While
    inspecting, the `Card`s are `Reparent`ed to this window.
    """
    
    CARD_PADDING = Deck.CARD_PADDING
    BACKGROUND_CL = "#CCCCCC"
    
    TITLE_FONT   = (18, wx.SWISS, wx.ITALIC, wx.BOLD)
    CONTENT_FONT = (14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def __init__(self, parent, cards=[], pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Page`.
        * `cards: ` the `Card`s we are inspecting.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(CardInspect, self).__init__(parent, size=size)
        
        # GUI
        self.SetBackgroundColour(self.BACKGROUND_CL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # members
        self.cards = {}

                
    ### Behavior functions

    def GetCards(self):
        """Returns the `Card`s currently under inspection.

        `returns: ` a `list` of `Card`s.
        """
        return self.cards.keys()

    def AddCard(self, card):
        """Adds one `Card`s to the inspection view.

        * `card: ` a `Card`.
        """
        # setup and reparent: wil restore parent when done. See RestoreCards.
        self.cards[card] = {}
        self.cards[card]["parent"] = card.GetParent()
        self.cards[card]["rect"] = card.GetRect()
        card.Reparent(self)
        card.SetInspecting(True)
        card.content.SetFocus()
        
        # setup UI
        box = self.GetSizer()
        box.Add(card, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.CARD_PADDING)
        box.Layout()

        # bindings
        card.Bind(Card.EVT_CARD_CANCEL_INSPECT, self.OnCancelInspect)

    def SetCards(self, cards):
        """Clears previous `Card`s and inspects the new ones.

        * `cards: ` a `list` of `Card`s.
        """
        self.Clear()
        for c in cards: self.AddCard(c)

    def Restore(self):
        """Restores the `Card`s under inspection to their original parents and positions."""
        for c in self.cards:
            c.Reparent(self.cards[c]["parent"])
            c.SetRect(self.cards[c]["rect"])
        self.Clear()

    def Clear(self):
        """Clear all `Card`s under inspection."""
        self.GetSizer().Clear()
        for c in self.cards.keys():
            c.SetInspecting(False)
        self.cards = {}


    ### Callbacks

    def OnCancelInspect(self, ev):
        """Listens to `Card.EVT_CARD_CANCEL_INSPECT` on every `Card` under inspection."""
        self.Restore()
        event = Card.CancelInspectEvent(id=wx.ID_ANY)
        event.SetEventObject(ev.GetEventObject())
        self.GetEventHandler().ProcessEvent(event)
    


######################
# MiniCard Class
######################        

class MiniCard(wx.Window):
    """The little cards shown in a `DeckInspect`"""
    
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `DeckInspect`.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(MiniCard, self).__init__(parent, pos=pos, size=size)
        
        self.SetBackgroundColour("#FFFFFF")



######################
# TagsInspect Class
######################        

class TagsInspect(wx.Panel):
    """The sidebard that displays a `Content` `Card`'s tags."""

    TAGS_REGEX = "^(\w+):(.*)$"
    
    def __init__(self, parent, deck, pos=wx.DefaultPosition, size=wx.DefaultSize):
        """Constructor.

        * `parent: ` the parent `Page`.
        * `deck: ` the parent `Deck` of the `Card`s we are inspecting.
        * `pos: ` by default, is `wx.DefaultSize`.
        * `size: ` by default, is `wx.DefaultSize`.
        """
        super(TagsInspect, self).__init__(parent, pos=pos, size=size)
        self.deck = deck
        self.InitUI()

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)
        deck.Bind(Deck.EVT_NEW_CARD, self.OnNewCard)


    ### Behavior functions

    def ParseTags(self, txt):
        """Parses a string looking for tags.

        * `txt: ` a string, the contents of a `Content`.

        `returns: ` a string to display in the `TagsInspect` view, representing the tags found in `text`.
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
    __pdoc__['DeckInspect.%s' % field] = None
for field in dir(wx.Panel):
    __pdoc__['CardInspect.%s' % field] = None
for field in dir(wx.Window):
    __pdoc__['MiniCard.%s' % field] = None
for field in dir(wx.Panel):
    __pdoc__['TagsInspect.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in DeckInspect.__dict__.keys():
    if 'DeckInspect.%s' % field in __pdoc__.keys():
        del __pdoc__['DeckInspect.%s' % field]
for field in CardInspect.__dict__.keys():
    if 'CardInspect.%s' % field in __pdoc__.keys():
        del __pdoc__['CardInspect.%s' % field]
for field in MiniCard.__dict__.keys():
    if 'MiniCard.%s' % field in __pdoc__.keys():
        del __pdoc__['MiniCard.%s' % field]
for field in TagsInspect.__dict__.keys():
    if 'TagsInspect.%s' % field in __pdoc__.keys():
        del __pdoc__['TagsInspect.%s' % field]
