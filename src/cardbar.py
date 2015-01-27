# cardbar.py
# singleton module for Card bar

import wx


#### "members"
ASSOC_CARD = None
BUTTON_SZ = (10, 10)
BAR = None


#### "init"
def Create(parent, orient=wx.VERTICAL):
    bar = wx.Panel(parent)
    
    # buttons
    coll = wx.BitmapButton(bar, bitmap=wx.ArtProvider.GetBitmap(wx.ART_MINUS, size=BUTTON_SZ))
    maxz = wx.BitmapButton(bar, bitmap=wx.ArtProvider.GetBitmap(wx.ART_PLUS,  size=BUTTON_SZ))
    delt = wx.BitmapButton(bar, bitmap=wx.ArtProvider.GetBitmap(wx.ART_CLOSE, size=BUTTON_SZ))
    
    # UI
    box = wx.BoxSizer(orient)
    box.Add(coll, proportion=1)
    box.Add(maxz, proportion=1)
    box.Add(delt, proportion=1)
    bar.SetSizerAndFit(box)
    bar.Hide()        
    
    # Bindigns
    bar.Bind(wx.EVT_SHOW, OnShow)
    coll.Bind(wx.EVT_BUTTON, OnCollapse)
    maxz.Bind(wx.EVT_BUTTON, OnMaximize)
    delt.Bind(wx.EVT_BUTTON, OnClose)

    global BAR
    BAR = bar
    return bar


#### "methods"

### Behavior functions

def GetBar():
    if BAR: return BAR
    else: return Create()

def Associate(card):
    """Associate this bar to card: buttons in the sizebar will operate on it."""
    global ASSOC_CARD
    ASSOC_CARD = card

        
### Callbacks

def OnShow(ev):
    global ASSOC_CARD
    global BAR
    top = ASSOC_CARD.GetRect().top
    left = ASSOC_CARD.GetRect().right
    BAR.SetPosition((left, top))
    if ev.IsShown():
        BAR.Show()
        wx.CallLater(3000, BAR.Hide)

def OnCollapse(ev):
    global ASSOC_CARD
    ASSOC_CARD.Collapse()

def OnMaximize(ev):
    global ASSOC_CARD
    ASSOC_CARD.Uncollapse()

def OnClose(ev):
    global ASSOC_CARD
    ASSOC_CARD.Delete()
