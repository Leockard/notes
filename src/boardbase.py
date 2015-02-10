# boardbase.py
# base board class for notes.py

import wx
from utilities import *
import wx.lib.newevent as ne
from card import *
import json


######################
# BoardBase Class
######################

class BoardBase(AutoSize):
    MOVING_RECT_THICKNESS = 1
    BACKGROUND_CL = "#CCCCCC"
    CARD_PADDING = 15
    HORIZONTAL = 1
    VERTICAL   = 2

    NewCardEvent, EVT_NEW_CARD = ne.NewEvent()

    def __init__(self, parent, id=wx.ID_ANY, pos=(0,0), size=wx.DefaultSize):
        super(BoardBase, self).__init__(parent, id=id, pos=pos, size=size, style=wx.BORDER_NONE)
        
        self.cards = []
        self.groups = []
        self.selected_cards = []
        self.moving_cards_pos = []
        self.drag_select = False
        self.scale = 1.0
        self.InitAccels()

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

    def GetPadding(self):
        """Returns the correct padding width. Scales along with cards when zoom changes."""
        return self.CARD_PADDING * self.scale

    def PlaceNewCard(self, subclass, pos=wx.DefaultPosition, below=False):
        """
        Places a new Card on the board.
        subclass should be the string with the name of the Card subclass to create.
        below=False creates the new Card to the right of the currently selected
        Card in the board, if any. below=True creates it below.
        """
        if pos == wx.DefaultPosition:
            pos = (0, 0)
            pad = self.GetPadding()
            
            # if there are no cards, place this one on the top left corner
            if len(self.GetCards()) < 1:
                pos = (pad, pad)
    
            # if there's a selection, place it next to it
            elif self.GetSelection():
                rect = self.GetSelection()[-1].GetRect()
                if below:
                    top = rect.bottom + pad
                    left = rect.left
                else:
                    top = rect.top
                    left = rect.right + pad
                pos = (left, top)

            # if cursor is inside a card, place it next to it
            elif GetCardAncestor(self.FindFocus()):
                rect = GetCardAncestor(self.FindFocus()).GetRect()
                if below:
                    top = rect.bottom + pad
                    left = rect.left
                else:
                    top = rect.top
                    left = rect.right + pad
                pos = (left, top)
            
            else: # otherwise, move it to the right of the last one
                rects = [c.GetRect() for c in self.GetCards()]
                rights = [r.right for r in rects]
                top = min([r.top for r in rects])
                left = max(rights) + pad
                pos = (left, top)
    
        new = self.NewCard(subclass, pos=pos)
        self.UnselectAll()
        new.SetFocus()

    def NewCard(self, subclass, pos, label=-1, **kwargs):
        # never use labels, always let Board set its own
        # or use -1 (default) if it doesn't matter
        # for ex, if it's a temporary object
        if label == -1: label = len(self.cards)

        # unpack values and set bindings based on subclass
        if subclass == "Content":
            if "title" in kwargs.keys(): title = kwargs["title"]
            else: title = Content.DEFAULT_TITLE
            if "kind" in kwargs.keys(): kind = kwargs["kind"]
            else: kind = Content.DEFAULT_LBL
            if "content" in kwargs.keys(): content = kwargs["content"]
            else: content = Content.DEFAULT_CONTENT
                
            sz = [i*self.scale for i in Content.DEFAULT_SZ]
            new = Content(self, label, pos=pos, title=title, kind=kind, content=content, size=sz)
            
        elif subclass == "Header":
            if "txt" in kwargs.keys(): txt = kwargs["txt"]
            else: txt = Header.DEFAULT_TITLE
            if "size" in kwargs.keys():
                w = kwargs["size"][0]
                h = kwargs["size"][1]
            else:
                w = Header.DEFAULT_SZ[0]
                h = Header.DEFAULT_SZ[1]

            sz = [i*self.scale for i in (w, h)]
            new = Header(self, label, pos=pos, header=txt, size=sz)
            
        elif subclass == "Image":
            if "path" in kwargs.keys(): path = kwargs["path"]
            else: path = Image.DEFAULT_PATH

            sz = [i*self.scale for i in Image.DEFAULT_SZ]
            new = Image(self, label, pos=pos, path=path, size=sz)

        # set bindings for every card
        new.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
        new.Bind(wx.EVT_CHILD_FOCUS, self.OnCardChildFocus)
        new.Bind(Card.EVT_CARD_DELETE, self.OnCardDelete)
        new.Bind(Card.EVT_CARD_COLLAPSE, self.OnCardCollapse)
        new.Bind(Card.EVT_CARD_REQUEST_INSPECT, self.OnCardRequest)
        for ch in new.GetChildren():
            ch.Bind(wx.EVT_LEFT_DOWN, self.OnCardChildLeftDown)

        # raise the appropriate event
        event = self.NewCardEvent(id=wx.ID_ANY)
        event.SetEventObject(new)
        self.GetEventHandler().ProcessEvent(event)

        # finish up
        new.SetFocus()
        self.cards.append(new)
        self.FitToChildren()
        return new

    def MoveCard(self, card, dx, dy):
        """Move card by (dx, dy)."""
        pos = card.GetPosition()
        card.Move((pos.x + dx, pos.y + dy))

    def SelectNext(self, direc):
        """
        Selects next card in the specified direction. The selected
        card may not be the same as the one returned from GetNextCard().
        direc should be one of "left", "right", "top" or "bottom".
        """
        if   direc == "left":
            side  = lambda x: x.right
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == "right":
            side  = lambda x: x.left
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetTopRight()
        elif direc == "top":
            side  = lambda x: x.bottom
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == "bottom":
            side  = lambda x: x.top
            getp1 = lambda x: x.GetBottomLeft()
            getp2 = lambda x: x.GetTopLeft()

        sel = self.GetSelection()
        if len(sel) == 1:
            # get those that are above me
            rect = sel[0].GetRect()
            if direc == "left" or direc == "top":
                nxt = [c for c in self.GetCards() if side(c.GetRect()) < side(rect)]
            elif direc == "right" or direc == "bottom":
                nxt = [c for c in self.GetCards() if side(c.GetRect()) > side(rect)]
            if nxt:
                # if any, order them by distance
                nxt.sort(key=lambda x: dist2(getp1(x.GetRect()), getp2(rect)))
                # and select the nearest one
                self.SelectCard(nxt[0], True)
        else:
            ev.Skip()

    def MoveSelected(self, dx, dy):
        """Move all selected cards by dx, dy."""
        for c in self.GetSelection():
            self.MoveCard(c, dx, dy)

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
            card.Select()
            
        # else, select card only if it was not already selected
        elif card not in self.selected_cards:
            self.selected_cards.append(card)
            for c in self.selected_cards:
                c.Select()

    def UnselectCard(self, card):
        if card in self.selected_cards:
            self.selected_cards.remove(card)
            card.Unselect()

    def UnselectAll(self):
        """
        Unselects all cards. Be sure to call this method instead of
        Unselecting() every card for proper rectangle erasing and attribute cleanup.
        """
        while len(self.selected_cards) > 0:
            c = self.selected_cards[0]
            self.UnselectCard(c)

    def SelectGroup(self, group, new_sel=True):
        if new_sel: self.UnselectAll()
        for c in group.GetMembers(): self.SelectCard(c)

    def CopySelected(self):
        print "copy"
        # get the data        
        card = self.GetSelection()[0]
        data = card.Dump()

        print data

        # create our own custom data object
        obj = wx.CustomDataObject("Card")
        obj.SetData(json.dumps(data))

        # write the data to the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(obj)
            wx.TheClipboard.Close()

    def PasteFromClipboard(self, pos=wx.DefaultPosition):
        print pos
        if wx.TheClipboard.Open():
            print "get from the clipboard"
            # get data
            obj = wx.CustomDataObject("Card")
            wx.TheClipboard.GetData(obj)
            print obj.GetData()
            data = json.loads(obj.GetData())

            # create new card with the data
            if pos == wx.DefaultPosition:
                pos = [i + self.GetPadding() for i in data["pos"]]
            card = self.NewCard("Content", pos=pos, title=data["title"],
                                kind=data["kind"], content=data["content"])

            wx.TheClipboard.Close()

    def GetFocusedCard(self):
        """Returns the card currently in focus, or None."""
        obj = self.FindFocus()
        if isinstance(obj, Card):
            return obj
        elif isinstance(obj.GetParent(), EditText):
            return obj.GetGrandParent()
        elif isinstance(obj.GetParent(), Card):
            return obj.GetParent()
        else:
            return None

    def GetGroups(self):
        return self.groups

    def GetContainingGroups(self, card):
        return [g for g in self.groups if card in g.GetMembers()]

    def NewGroup(self, cards=[]):
        self.groups.append(CardGroup(label=len(self.groups), members=cards))

    def GroupSelected(self):
        sel = self.GetSelection()
        if sel: self.NewGroup(sel)

    def ScrollToCard(self, card):
        """If the card is in view, don't do anything. Otherwise, scroll it into view."""
        rect = card.GetRect()
        pt = rect.GetBottomRight()
        pt = self.CalcUnscrolledPosition(pt)
        self.ScrollToPoint(pt)

        # call rect again since we may have scrolled the window
        rect = card.GetRect()
        pt = rect.GetTopLeft()        
        pt = self.CalcUnscrolledPosition(pt)
        self.ScrollToPoint(pt)

    def ScrollToPoint(self, pt):
        """
        If the point is in view, don't do anything. Otherwise, scroll it into view.
        The point must be in absolute (content size) coordinates.
        """
        step = self.SCROLL_STEP

        # get the current rect in view, in pixels
        # coordinates relative to underlying content size
        view = [k * step for k in self.GetViewStart()]
        sz = self.GetClientSize()
        rect = wx.Rect(view[0], view[1], sz.width, sz.height)

        # point we're scrolling to (already in pixels)
        # relative to content size

        # nothing to do
        if rect.Contains(pt):
            return

        # scroll the point into view
        scroll = False
        pad = self.GetPadding()

        # if one of the argumets is wx.DefaultCoord,
        # we will not scroll in that direction
        ysc = wx.DefaultCoord
        xsc = wx.DefaultCoord
        
        # remember y coordinate grows downward
        if pt.x >= rect.right or pt.x <= rect.left:
            scroll = True
            xsc = pt.x - pad      # where we want to go
            xsc /= step           # in scroll units
        if pt.y <= rect.top or pt.y >= rect.bottom:
            scroll = True
            ysc = pt.y - pad      # where we want to go
            ysc /= step           # in scroll units

        if scroll:
            # will scroll as much as it's possible
            # i.e., pt will not necessarily be in the top left corner after scrolling
            # but it will surely be inside the view
            self.Scroll(xsc, ysc)

    def ArrangeSelection(self, orient):
        """Use BoardBase.HORIZONTAL or BoardBase.VERTICAL."""
        if   orient == BoardBase.HORIZONTAL:
            self.HArrangeSelectedCards()
        elif orient == BoardBase.VERTICAL:
            self.VArrangeSelectedCards()

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
            left = c.GetRect().right + self.GetPadding()

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
            top = c.GetRect().bottom + self.GetPadding()

        self.FitToChildren()

                    
    ### Callbacks

    def __del__(self):
        # don't forget to stop all timers!
        pass

    def OnCardCollapse(self, ev):
        card = ev.GetEventObject()
        card.SetSize([i*self.scale for i in card.GetSize()])
        
    def OnCardDelete(self, ev):
        card = ev.GetEventObject()
        self.cards.remove(card)
        self.UnselectCard(card)

    def OnCardRequest(self, ev):
        """
        Raises the event again, with the same card as event object. The difference
        is that now a Page() can Bind() to EVT_CARD_REQUEST_INSPECT events coming from
        this board, instead of having to bind to every individual card.
        """
        event = Card.InspectEvent(id=wx.ID_ANY)
        event.SetEventObject(ev.GetEventObject())
        self.GetEventHandler().ProcessEvent(event)

    def OnChildFocus(self, ev):
        pass # important to avoid automatic scrolling to focused child

    def OnCardChildLeftDown(self, ev):
        """Called when a Card's child window is clicked."""
        self.UnselectAll()
        ev.Skip()

    def OnCardLeftDown(self, ev):
        """Called when a child card has been clicked."""
        card = ev.GetEventObject()

        # bring to front and set focus
        card.SetFocus()
        card.Raise()
        
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

    def OnCardChildFocus(self, ev):
        """If a child of card is focused, unselect all (including parent)."""
        self.UnselectAll()
        ev.Skip()

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
        self.NewCard("Content", pos=ev.GetPosition())
        

            def OnMoveLeft(self, ev):
        self.MoveSelected(-self.SCROLL_STEP, 0)

    def OnMoveRight(self, ev):
        self.MoveSelected(self.SCROLL_STEP, 0)

    def OnMoveUp(self, ev):
        self.MoveSelected(0, -self.SCROLL_STEP)

    def OnMoveDown(self, ev):
        self.MoveSelected(0, self.SCROLL_STEP)

    def OnSelectionLeft(self, ev):
        if len(self.GetSelection()) == 1:
            self.SelectNext("left")
        else:
            ev.Skip()
    
    def OnSelectionRight(self, ev):
        if len(self.GetSelection()) == 1:
            self.SelectNext("right")
        else:
            ev.Skip()

    def OnSelectionUp(self, ev):
        if len(self.GetSelection()) == 1:
            self.SelectNext("top")
        else:
            ev.Skip()

    def OnSelectionDown(self, ev):
        if len(self.GetSelection()) == 1:
            self.SelectNext("bottom")
        else:
            ev.Skip()

            
    ### Auxiliary functions

    def InitAccels(self):
        # we create ghost menus so that we can
        # bind its items to some accelerators
        accels = []
        ghost = wx.Menu()

        # move selected cards        
        movel = wx.MenuItem(ghost, wx.ID_ANY, "Move Left")
        mover = wx.MenuItem(ghost, wx.ID_ANY, "Move Right")
        moveu = wx.MenuItem(ghost, wx.ID_ANY, "Move Up")
        moved = wx.MenuItem(ghost, wx.ID_ANY, "Move Down")
        self.Bind(wx.EVT_MENU, self.OnMoveLeft  , movel)
        self.Bind(wx.EVT_MENU, self.OnMoveRight , mover)
        self.Bind(wx.EVT_MENU, self.OnMoveUp    , moveu)
        self.Bind(wx.EVT_MENU, self.OnMoveDown  , moved)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_LEFT,  movel.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_RIGHT, mover.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_UP,    moveu.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_DOWN,  moved.GetId()))
        
        # select next card
        selr = wx.MenuItem(ghost, wx.ID_ANY, "Select Right")
        sell = wx.MenuItem(ghost, wx.ID_ANY, "Select Left")
        selu = wx.MenuItem(ghost, wx.ID_ANY, "Select Up")
        seld = wx.MenuItem(ghost, wx.ID_ANY, "Select Down")
        self.Bind(wx.EVT_MENU, self.OnSelectionLeft  , sell)
        self.Bind(wx.EVT_MENU, self.OnSelectionRight , selr)
        self.Bind(wx.EVT_MENU, self.OnSelectionUp    , selu)
        self.Bind(wx.EVT_MENU, self.OnSelectionDown  , seld)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_LEFT,  sell.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_RIGHT, selr.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_UP,    selu.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_DOWN,  seld.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

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
    
    def DumpCards(self):
        """Returns a dict with all the info in the current cards."""
        carddict = {}

        # we put the scrollbars at the origin, to get the real positions
        self.Hide()
        view_start = self.GetViewStart()
        self.Scroll(0, 0)
        
        for c in self.cards:
            carddict[c.GetId()] = c.Dump()
            
        # and return to the original view
        self.Scroll(view_start[0], view_start[1])
        self.Show()

        return carddict

    def DumpGroups(self):
        d = {}
        for g in self.groups: d[g.GetLabel()] = g.Dump()
        return d

    def Dump(self):
        """Returns a dict with all the info contained in this Board."""
        return {"cards": self.DumpCards(), "groups": self.DumpGroups()}

    def Load(self, d):
        """Argument should be a dict returned by Dump."""
        if "cards" in d.keys():
            # note we are not loading the id
            # instead, as identifier, we use label
            for id, values in d["cards"].iteritems():
                pos = values["pos"]
                label = values["label"]
                if values["class"] == "Content":
                    new = self.NewCard(values["class"], pos=pos, label=label,
                                  title   = str(values["title"]),
                                  kind    = values["kind"],
                                  content = values["content"])
                    if values["collapsed"]: new.Collapse()
                elif values["class"] == "Header":
                    self.NewCard(values["class"], pos=pos, label=label,
                                  size = (values["width"], values["height"]),
                                  txt = values["header"])
                elif values["class"] == "Image":
                    self.NewCard(values["class"], pos=pos, label=label,
                                  path  = values["path"])
                    
        if "groups" in d.keys():
            # here again we use the label as identifier
            # but this time the label is the key in the dictionary
            for label, members in d["groups"].iteritems():
                cards = [self.GetCard(l) for l in members]
                self.NewGroup(cards)

