# boardbase.py
# base board class for notes.py

import wx
from utilities import AutoSize
from utilities import MakeEncirclingRect
from card import *


######################
# BoardBase Class
######################

class BoardBase(AutoSize):
    MOVING_RECT_THICKNESS = 1
    BACKGROUND_CL = "#CCCCCC"
    PIXELS_PER_SCROLL = 20
    CARD_PADDING = 15

    def __init__(self, parent, id=wx.ID_ANY, pos=(0,0), size=wx.DefaultSize):
        super(BoardBase, self).__init__(parent, id=id, pos=pos, size=size, style=wx.BORDER_NONE)
        
        self.cards = []
        self.selected_cards = []
        self.moving_cards_pos = []
        self.drag_select = False
        self.scale = 1.0

        # Bindings
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)
        self.Bind(wx.EVT_CHILD_FOCUS, self.OnChildFocus)

        # Other gui setup
        self.SetBackgroundColour(BoardBase.BACKGROUND_CL)
        self.SetFocus()

        
    ### Behavior functions
    
    def GetCards(self):
        """Returns a list of all cards held by the Board."""
        return self.cards

    def GetHeaders(self):
        """Returns a list of all Header cards."""
        return [h for h in self.cards if isinstance(h, Header)]

    def GetContents(self):
        """Returns a list of all Content cards."""
        return [h for h in self.cards if isinstance(h, Content)]

    def GetCard(self, label):
        """Returns the card with the (internal) label, or None."""
        li = [c for c in self.cards if c.label == label]
        if li: return li[0]
        else: return None

    def GetContentsByKind(self, kind):
        """Returns a list of all Content cards of the kind. kind should be a Content.X_LBL constant."""
        return [c for c in self.GetContents() if c.GetKind() == kind or c.GetKind(long=True) == kind]

    def GetNextCard(self, ctrl, cycle=True):
        """Returns the card with label consecutive to that of the argument, or None.
        If cycle=True, and card is the Card with the last label, return the Card with first label."""
        card = ctrl.GetParent()
        if not isinstance(card, Card):
            card = card.GetParent()
            if not isinstance(card, Card):
                return

        greater_lbl = [c for c in self.cards if c.label > card.label]
        greater_lbl.sort(key = lambda x: x.label)
        if greater_lbl:
            return greater_lbl[0]

        if not cycle:
            return None
            
        cards = self.cards[:]
        cards.sort(key = lambda x: x.label)
        return cards[0]

    def GetPrevCard(self, ctrl, cycle=True):
        """Returns the card with label previous to that of the argument, or None.
        If cycle=True, and card is the Card with the last label, return the Card with last label."""
        card = ctrl.GetParent()
        if not isinstance(card, Card):
            card = card.GetParent()
            if not isinstance(card, Card):
                return

        lesser_lbl = [c for c in self.cards if c.label < card.label]
        lesser_lbl.sort(key = lambda x: x.label)
        if lesser_lbl:
            return lesser_lbl[-1]

        if not cycle:
            return None
            
        cards = self.cards[:]
        cards.sort(key = lambda x: x.label)
        return cards[-1]

    def PlaceNewCard(self, subclass, below = False):
        """
        Places a new Card on the board.
        class should be the string with the name of the Card subclass to create.
        below=False creates the new Card to the right of the currently selected
        Card in the board, if any. below=True creates it below.
        """
        pos = (0, 0)
        
        # if there are no cards, place this one on the top left corner
        if len(self.GetCards()) < 1:
            pos = (self.CARD_PADDING, self.CARD_PADDING)

        # if there's a selection, place it next to it
        elif self.GetFocusedCard():
            rect = self.GetFocusedCard().GetRect()
            if below:
                top = rect.bottom + self.CARD_PADDING
                left = rect.left
            else:
                top = rect.top
                left = rect.right + self.CARD_PADDING
            pos = (left, top)
        
        else: # otherwise, move it to the right of the last one
            rects = [c.GetRect() for c in self.GetCards()]
            rights = [r.right for r in rects]
            top = min([r.top for r in rects])
            left = max(rights) + self.CARD_PADDING
            pos = (left, top)

        new = self.NewCard(subclass, pos=pos)
            
        self.SelectCard(new, True)
        new.SetFocus()

    # def NewCard(self, subclass, pos, label=-1, title="", kind=Content.DEFAULT_LBL, content="", txt="", path=""):
    def NewCard(self, subclass, pos, label=-1, **kwargs):
        if label == -1: label = len(self.cards)

        if subclass == "Content":
            if "title" in kwargs.keys():
                title = kwargs["title"]
            else:
                title = Content.DEFAULT_TITLE
            if "kind" in kwargs.keys():
                kind = kwargs["kind"]
            else:
                kind = Content.DEFAULT_LBL
            if "content" in kwargs.keys():
                content = kwargs["content"]
            else:
                content = Content.DEFAULT_CONTENT
                
            new = Content(self, label, pos=pos, title=title, kind=kind, content=content,
                          size=[i*self.scale for i in Content.DEFAULT_SZ])

            # bindings        
            new.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
            new.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOverCard)
            new.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeaveCard)
            
        elif subclass == "Header":
            if "txt" in kwargs.keys(): txt = kwargs["txt"]
            else: txt = Header.DEFAULT_TITLE
            new = Header(self, label, pos=pos, header=txt, size=[i*self.scale for i in Header.DEFAULT_SZ])
            new.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
            
        elif subclass == "Image":
            if "path" in kwargs.keys(): path = kwargs["path"]
            else: path = Image.DEFAULT_PATH
            new = Image(self, label, pos=pos, path=path, size=[i*self.scale for i in Image.DEFAULT_SZ])
        
        new.SetFocus()
        self.cards.append(new)
        self.FitToChildren()
        return new

    def GetSelection(self):
        return self.selected_cards

    def SelectCard(self, card, new_sel = False):
        """
        Selects the card. If new_sel is True, erase all other
        selected cards and select only this one.
        """
        # if new_sel, select only this card
        if new_sel:
            self.UnselectAll()
            self.selected_cards = [card]
            self.PaintCardRect(card, card.GetPosition(), refresh = False)
        # else, select card only if it was not already selected
        elif card not in self.selected_cards:
            self.selected_cards.append(card)
            for c in self.selected_cards:
                self.PaintCardRect(c, c.GetPosition(), refresh = False)

    def UnselectCard(self, card):
        if card in self.selected_cards:
            self.selected_cards.remove(card)
            self.EraseCardRect(card, card.GetPosition())

    def UnselectAll(self):
        """
        Unselects all cards. Be sure to call this method instead of
        Unselecting() every card for proper rectangle erasing and attribute cleanup.
        """
        while len(self.selected_cards) > 0:
            c = self.selected_cards[0]
            self.UnselectCard(c)

    def CopySelected(self):
        sel = self.selected_cards[:]
        new = []

        for c in sel:
            pos = c.GetPosition() + (self.CARD_PADDING, self.CARD_PADDING)
            if isinstance(c, Content):
                new.append(self.NewCard("Content", pos=pos, title=c.GetTitle(), kind=c.GetKind(), content=c.GetContent()))
            if isinstance(c, Header):
                new.append(self.NewCard("Header", pos=pos, txt=c.GetHeader()))

        self.UnselectAll()
        for c in new: self.SelectCard(c, False)

    def DeleteSelected(self):
        sel = self.selected_cards
        for c in sel:
            c.Hide()
            self.cards.remove(c)
        self.UnselectAll()
        
    def GetFocusedCard(self):
        """Returns the card currently in focus, or None."""
        if self.selected_cards:
            obj = self.FindFocus()
            if isinstance(obj, Card):
                return obj
            elif isinstance(obj.GetParent(), EditText):
                return obj.GetGrandParent()
            else:
                return obj.GetParent()
        else:
            return None

    def HArrangeSelectedCards(self):
        """
        If there are any selected cards, arrange them in a horizontal grid,
        to the right of the left-most selected card.
        """
        if len(self.selected_cards) < 1: return

        # we unselect first so that we erase the selection rectangles correctly
        arrange = self.selected_cards[:]
        self.UnselectAll()         

        lefts = [c.GetRect().left for c in arrange]
        left = min(lefts)
        card = arrange[lefts.index(left)]
        top = card.GetRect().top
        arrange.sort(key=lambda x: x.GetRect().left)

        for c in arrange:
            c.SetPosition(wx.Point(left, top))
            left = c.GetRect().right + self.CARD_PADDING

        self.FitToChildren()

    def VArrangeSelectedCards(self):
        """
        If there are any selected cards, arrange them in a vertical grid,
        below of the top-most selected card.
        """
        if len(self.selected_cards) < 1: return

        # we unselect first so that we erase the selection rectangles correctly
        arrange = self.selected_cards[:]
        self.UnselectAll()         

        tops = [c.GetRect().top for c in arrange]
        top = min(tops)
        card = arrange[tops.index(top)]
        left = card.GetRect().left
        arrange.sort(key=lambda x: x.GetRect().top)

        for c in arrange:
            c.SetPosition(wx.Point(left, top))
            top = c.GetRect().bottom + self.CARD_PADDING

        self.FitToChildren()

                    
    ### Callbacks

    def __del__(self):
        # don't forget to stop all timers!
        pass

    def OnChildFocus(self, ev):
        pass # important to avoid automatic scrolling to focused child

    def OnCardLeftDown(self, ev):
        """Called when a child card has been clicked."""
        card = ev.GetEventObject()
        card.SetFocusIgnoringChildren()
        
        # selection
        if not wx.GetMouseState().ControlDown():    # no control: simple click
            self.SelectCard(card, new_sel = True)   # select only this card
        else:                                       # control down
            if card in self.selected_cards:         # ctrl + click while selected: unselect
                self.UnselectCard(card)
            elif card not in self.selected_cards:   # ctrl + click while not selected: add select
                self.SelectCard(card, new_sel = False)        

        # initiate moving
        self.CaptureMouse()
        self.Bind(wx.EVT_LEFT_UP, self.OnCardLeftUp)
        self.Bind(wx.EVT_MOTION, self.OnMovingCard)

        self.on_motion = False
        pos = card.GetPosition() + ev.GetPosition() # relative to the canvas
        self.moving_cards_pos = []
        for c in self.selected_cards:
            # (card, card position with respect to the original click, current position)
            self.moving_cards_pos.append((c, c.GetPosition() - pos, c.GetPosition()))
                    
    def OnMovingCard(self, ev):
        if ev.Dragging() and self.moving_cards_pos:
            # draw a rectangle while moving
            # order is important
            self.on_motion = True
            for c, orig, pos in self.moving_cards_pos:
                self.EraseCardRect(c, pos, refresh = False)
                pos = ev.GetPosition() + orig
                self.PaintCardRect(c, pos)

    def OnCardLeftUp(self, ev):
        # terminate moving
        if self.on_motion:
            self.selected_cards = []
            self.on_motion = False
            for c, orig, pos in self.moving_cards_pos:
                self.EraseCardRect(c, pos)
                
            if self.moving_cards_pos:
                for c, orig, pos in self.moving_cards_pos:
                    final_pos = ev.GetPosition() + orig - (Content.BORDER_WIDTH, Content.BORDER_WIDTH)
                    c.Move(final_pos)
                    
        self.moving_cards_pos = []
        self.ReleaseMouse()
        self.Unbind(wx.EVT_LEFT_UP)
        self.Unbind(wx.EVT_MOTION)

    def OnLeftDown(self, ev):
        self.UnselectAll()
        self.SetFocusIgnoringChildren()

        # initiate drag select
        self.init_pos = ev.GetPosition()
        self.cur_pos = ev.GetPosition()
        self.Bind(wx.EVT_MOTION, self.OnDragSelect)

    def OnDragSelect(self, ev):
        if ev.Dragging() and not self.moving_cards_pos:
            self.drag_select = True
            
            # erase the last one selection rect
            self.PaintRect(wx.Rect(self.init_pos[0], self.init_pos[1],
                            self.cur_pos[0], self.cur_pos[1]),
                            style = wx.TRANSPARENT,
                            refresh = False)
            
            # and draw the current one
            final_pos = ev.GetPosition() - self.init_pos
            self.PaintRect(wx.Rect(self.init_pos[0], self.init_pos[1],
                            final_pos[0], final_pos[1]),
                            refresh = False)

            self.cur_pos = final_pos

    def OnLeftUp(self, ev):
        # terminate drag select
        if self.drag_select:
            self.Unbind(wx.EVT_MOTION)
            self.drag_select = False
            final_rect = MakeEncirclingRect(self.init_pos, self.init_pos + self.cur_pos)            

            # erase the last selection rect
            self.PaintRect(final_rect, style = wx.TRANSPARENT)

            # select cards
            selected = [c for c in self.GetCards() if c.GetRect().Intersects(final_rect)]
            for c in selected: self.SelectCard(c)

    def OnMouseCaptureLost(self, ev):
        self.ReleaseMouse()

    def OnLeftDClick(self, ev):
        self.NewCard("Content", pos=ev.GetPosition(),
                      kind=Content.DEFAULT_LBL,
                      title="", content="")

    def OnMouseOverCard(self, ev):
        card = ev.GetEventObject()
        card.Unbind(wx.EVT_ENTER_WINDOW)
        card.ShowBar()

    def OnMouseLeaveCard(self, ev):
        card = ev.GetEventObject()
        card.Bind(wx.EVT_ENTER_WINDOW, self.OnMouseOverCard)
        
            
    ### Auxiliary functions
        
    def PaintRect(self, rect, thick = MOVING_RECT_THICKNESS, style = wx.SOLID, refresh = True):
        """Paints a rectangle. Use style = wx.TRANSPARENT to erase a rectangle."""
        dc = wx.ClientDC(self)
        # Brush is for background, Pen is for foreground
        dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
        dc.SetPen(wx.Pen("BLACK", thick, style))
        dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])
        if refresh: self.RefreshRect(rect)
        
    def PaintCardRect(self, card, pos, thick = MOVING_RECT_THICKNESS, style = wx.SOLID, refresh = True):
        """Paints a rectangle just big enough to encircle card.GetRect(), at pos."""
        x, y, w, h = card.GetRect()
        rect = wx.Rect(pos[0], pos[1], w, h)
        rect = rect.Inflate(2 * thick, 2 * thick)
        self.PaintRect(rect, thick=thick, style=style, refresh=refresh)

    def EraseCardRect(self, card, pos, thick = MOVING_RECT_THICKNESS, refresh = True):
        """Erases a rectangle drawn by PaintCardRect()."""
        # Brush is for background, Pen is for foreground
        x, y, w, h = card.GetRect()        
        rect = wx.Rect(pos[0], pos[1], w, h)
        rect = rect.Inflate(2 * thick, 2 * thick)
        self.PaintRect(rect, thick=thick, style=wx.TRANSPARENT, refresh=refresh)
    
    def Dump(self):
        """Returns a dict with all the info in the current cards."""
        carddict = {}

        # we put the scrollbars at the origin, to get the real positions
        self.Hide()
        view_start = self.GetViewStart()
        self.Scroll(0, 0)
        
        for c in self.cards:
            pos = c.GetPosition()
            carddict[c.GetId()] = c.Dump()
            
        # and return to the original view
        self.Scroll(view_start[0], view_start[1])
        self.Show()

        return carddict

    ### Callbacks

