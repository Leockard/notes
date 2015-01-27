# inspect.py
# CardInspect class: for editing a single card

import wx
from card import *
from boardbase import BoardBase


######################
# BoardInspect Class
######################

class BoardInspect(wx.Window):
    DEFAULT_FACTOR = 5
    BACKGROUND_CL   = (255, 255, 255, 255)
    DEFAULT_MINI_CL = (220, 218, 213, 255)
    
    def __init__(self, parent, board=None, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(BoardInspect, self).__init__(parent, pos=(200, 200), size=(400, 250))
        
        self.factor = BoardInspect.DEFAULT_FACTOR
        self.cards = {}
        self.SetBackgroundColour(self.BACKGROUND_CL)

        self.SetBoard(board)


    ## Behavior functions

    def Clear(self):
        self.cards = {}

    def SetBoard(self, board):
        # clean up and add everything
        self.Clear()
        for c in board.GetCards():
            self.AddCard(c)
            
        board.Bind(BoardBase.EVT_NEW_CARD, self.OnNewCard)
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


    ### Callbacks

    def OnNewCard(self, ev):
        self.AddCard(ev.GetEventObject())

    def OnDeleteCard(self, ev):
        self.RemoveCard(ev.GetEventObject())

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

        self.SetBackgroundColour(self.BACKGROUND_CL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)
        
        self.cards = cards

                
    ### Behavior functions

    def GetCards(self):
        return self.cards

    def AddCard(self, new_card):
        # copy the card, since we don't want to add
        # the same window (card) in two different sizers!
        card = Content(self, -1, title=new_card.GetTitle(), kind=new_card.GetKind(), content=new_card.GetContent())
        card.title.SetFont(wx.Font(*self.TITLE_FONT))
        card.content.SetFont(wx.Font(*self.CONTENT_FONT))

        # erase pewvious cards and set new one
        box = self.GetSizer()
        box.Add(card, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.CARD_PADDING)
        
        box.Layout()
        self.cards.append(card)

    def SetCards(self, cards):
        """Clears previous cards and sets the new ones."""
        self.Clear()
        for c in cards: self.AddCard(c)

    def Clear(self):
        """Clear all contained cards."""
        self.GetSizer().Clear()
        self.cards = []


    ### Auxiliary functions



######################
# MiniCard Class
######################        

class MiniCard(wx.Window):
    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(MiniCard, self).__init__(parent, pos=pos, size=size)
        
        self.SetBackgroundColour("#FFFFFF")
