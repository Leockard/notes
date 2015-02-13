# inspect.py
# Inspect classes: for editing a single card or viewing the whole board

import wx
from card import *
from boardbase import BoardBase
from utilities import *


######################
# BoardInspect Class
######################

class BoardInspect(AutoSize):
    DEFAULT_FACTOR  = 5
    BACKGROUND_CL   = (255, 255, 255, 255)
    DEFAULT_MINI_CL = (220, 218, 213, 255)
    
    def __init__(self, parent, board=None, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(BoardInspect, self).__init__(parent, pos=pos, size=size)

        # members        
        self.factor = BoardInspect.DEFAULT_FACTOR
        self.cards = {}
        self.SetBackgroundColour(self.BACKGROUND_CL)
        self.SetBoard(board)

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)


    ## Behavior functions

    def Clear(self):
        self.cards = {}

    def SetBoard(self, board):
        # clean up and add every card already present
        self.Clear()
        for c in board.GetCards():
            self.AddCard(c)

        # set sizes
        sz = [i / self.factor for i in board.GetSize()]
        self.SetSize(sz)
        self.UpdateContentSize(board.content_sz)

        # set scroll
        step = board.GetScrollPixelsPerUnit()
        self.SetScrollRate(step[0] / self.factor, step[1] / self.factor)

        # listen to events
        board.Bind(BoardBase.EVT_NEW_CARD, self.OnNewCard)
        board.Bind(wx.EVT_SIZE, self.OnBoardSize)
        board.Bind(wx.EVT_SCROLLWIN, self.OnBoardScroll)
        
        self.board = board
    
    def AddCard(self, card):
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
        if card in self.cards.keys():
            mini = self.cards[card]
            mini.Hide()
            mini.Destroy()
            del self.cards[card]

    def SetPosition(self):
        w, h = self.GetSize()
        rect = self.board.GetClientRect()
        pos = (rect.right - w, rect.bottom - h)
        self.Move(pos)


    ### Callbacks

    def OnShow(self, ev):
        self.SetPosition()

    def OnBoardScroll(self, ev):
        view = ev.GetEventObject().GetViewStart()
        self.Scroll(view.x / self.factor, view.y / self.factor)

    def OnBoardSize(self, ev):
        board = ev.GetEventObject()
        self.SetSize([i / self.factor for i in board.GetSize()])
        self.SetPosition()

    def OnNewCard(self, ev):
        self.AddCard(ev.GetEventObject())

    def OnDeleteCard(self, ev):
        self.RemoveCard(ev.GetEventObject())
        # dont' consume it! BoardBase also needs it
        ev.Skip()

    def OnContentKind(self, ev):
        card = ev.GetEventObject()
        self.cards[card].SetBackgroundColour(card.GetBackgroundColour())
            


######################
# CardInspect Class
######################        

class CardInspect(wx.Panel):
    CARD_PADDING = BoardBase.CARD_PADDING
    BACKGROUND_CL = "#CCCCCC"
    
    TITLE_FONT   = (18, wx.SWISS, wx.ITALIC, wx.BOLD)
    CONTENT_FONT = (14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def __init__(self, parent, cards=[], pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(CardInspect, self).__init__(parent, size=size)
        
        # GUI
        self.SetBackgroundColour(self.BACKGROUND_CL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # members
        self.pairs = {}

                
    ### Behavior functions

    def GetCards(self):
        """
        Returns the cards currently shown on the inspection view,
        not the ones on the board.
        """
        return self.pairs.keys()

    def GetInspectingCards(self):
        """
        Returns the original cards that we are inspecting which
        are currently on the board. Not the ones shown on the
        inspection view.
        """
        return self.pairs.values()

    def GetPairs(self):
        """
        Returns a dict where each pair has a Card for key and
        for value. The key is the card currently shown on the
        inspection view, while the value is the corresponding
        card on the board it represents.
        """
        return self.pairs

    def AddCard(self, new_card):
        # copy the card, since we don't want to reparent it
        card = Content(self, -1, title=new_card.GetTitle(), kind=new_card.GetKind(), content=new_card.GetContent())
        card.title.SetFont(wx.Font(*self.TITLE_FONT))
        card.content.SetFont(wx.Font(*self.CONTENT_FONT))
        card.DisableCollapse()

        # setup UI
        box = self.GetSizer()
        box.Add(card, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.CARD_PADDING)
        box.Layout()
        self.pairs[card] = new_card

        # bindings
        card.Bind(Card.EVT_CARD_CANCEL_INSPECT, self.OnCancelInspect)

        # finish up
        new_card.SetInspecting(True)
        card.SetInspecting(True)

    def SetCards(self, cards):
        """Clears previous cards and sets the new ones."""
        self.Clear()
        for c in cards: self.AddCard(c)

    def Clear(self):
        """Clear all contained cards."""
        for c in self.pairs.keys():
            c.Delete()
        self.GetSizer().Clear()
        for c in self.pairs.values():
            c.SetInspecting(False)
        self.pairs = {}


    ### Auxiliary functions

    ### Callbacks

    def OnCancelInspect(self, ev):
        event = Card.CancelInspectEvent(id=wx.ID_ANY)
        event.SetEventObject(ev.GetEventObject())
        self.GetEventHandler().ProcessEvent(event)
    


######################
# MiniCard Class
######################        

class MiniCard(wx.Window):
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(MiniCard, self).__init__(parent, pos=pos, size=size)
        
        self.SetBackgroundColour("#FFFFFF")



######################
# TagsInspect Class
######################        

class TagsInspect(wx.Panel):
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(TagsInspect, self).__init__(parent, pos=pos, size=size)
        self.InitUI()

        # bindings
        self.Bind(wx.EVT_SHOW, self.OnShow)
        
    ### Auxiliary functions

    def InitUI(self):
        box = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(box)

        txt = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.txt = txt        
        box.Add(txt, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)


    ### Callbacks

    def OnShow(self, ev):
        if ev.IsShown():
            card = GetCardAncestor(self.FindFocus())
            if card and isinstance(card, Content):
                self.txt.SetValue(card.GetContent())
