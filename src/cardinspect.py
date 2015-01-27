# inspect.py
# CardInspect class: for editing a single card

import wx
from card import *
from boardbase import BoardBase


######################
# CardInspect Class
######################        

class CardInspect(wx.Panel):
    CARD_PADDING = BoardBase.CARD_PADDING
    BACKGROUND_CL = "#CCCCCC"
    
    TITLE_FONT   = (18, wx.SWISS, wx.ITALIC, wx.BOLD)
    CONTENT_FONT = (14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

    def __init__(self, parent, card=None, pos=wx.DefaultPosition, size=wx.DefaultSize):
        super(CardInspect, self).__init__(parent, size=size)

        self.SetBackgroundColour(self.BACKGROUND_CL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)
        
        self.card = card

                
    ### Behavior functions

    def GetCard(self):
        return self.card

    def SetCard(self, new_card):
        # copy the card, since we don't want to add
        # the same window (card) in two different sizers!
        card = Content(self, -1, title=new_card.GetTitle(), kind=new_card.GetKind(), content=new_card.GetContent())
        card.title.SetFont(wx.Font(*self.TITLE_FONT))
        card.content.SetFont(wx.Font(*self.CONTENT_FONT))

        # erase pewvious cards and set new one
        box = self.GetSizer()
        box.Clear()
        box.Add(card, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.CARD_PADDING)
        
        box.Layout()
        self.card = card


    ### Auxiliary functions

