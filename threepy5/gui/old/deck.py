# -*- coding: utf-8 -*-
"""
This module holds the `Deck` and its helper class `SelectionManager`.
`Deck` is the window that holds all `Card`s. Every `Box` has a `Deck`.
`SelectionManager` handles selection.
"""

import wx
import json
import ast
import card
import wx.lib.newevent as ne
import wxutils

    
######################
# Deck Class
######################

class Deck(wxutils.AutoSize):
    """
    `Deck` is the parent window of all `Card`s. It handles position, selection,
    arrangement, and listens to individual Cards' events, so that `Box`
    only needs to listen to `Deck` events.
    """
                
    MOVING_RECT_THICKNESS = 1
    BACKGROUND_CL = "#CCCCCC"
    CARD_PADDING = 15
    HORIZONTAL = 2
    VERTICAL   = 4

    # LEFT   = 2
    # RIGHT  = 4
    # DOWN   = 8
    # UP     = 16

    NewCardEvent, EVT_NEW_CARD = ne.NewEvent()
    DeleteEvent,  EVT_DEL_CARD = ne.NewEvent()
    ReqViewEvent, EVT_REQUEST_VIEW = ne.NewEvent()

    def __init__(self, parent, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.BORDER_NONE):
        """Constructor.

        * `parent: ` the parent `wx.Window`.
        * `style: ` by default is `wx.BORDER_NONE`.
        """
        super(Deck, self).__init__(parent, pos=pos, size=size, style=style)

        # members
        self.cards = []
        self.groups = []
        self.moving_cards_pos = []
        self.drag_select = False
        self.menu_position = (0, 0)
        self.scale = 1.0
        self.selec = SelectionManager(self)
        self.InitAccels()
        self.InitMenu()

        # Bindings
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)
        self.Bind(wx.EVT_CHILD_FOCUS, self.OnChildFocus)
        self.Bind(self.selec.EVT_MGR_DELETE, self.OnMgrDelete)
        
        # other gui setup
        self.SetBackgroundColour(Deck.BACKGROUND_CL)        


    ### Behavior functions
    
    # def GetCards(self):
    #     """Returns a list of all `Card`s held by this object.

    #     `returns: ` a list of `Card`s.
    #     """
    #     return self.cards

    # def GetHeaders(self):
    #     """Returns a list of all `Header` `Card`s.
        
    #     `returns: ` a list of `Header`.
    #     """
    #     return [h for h in self.cards if isinstance(h, Header)]

    # def GetContents(self):
    #     """Returns a list of all `Content` `Card`s.

    #     `returns: ` a list of `Content`.
    #     """
    #     return [h for h in self.cards if isinstance(h, Content)]

    def GetCard(self, label):
        """Returns the specified `Card`.

        * `label: ` the label id of the `Card`. Labels are mostly used internally.

        `returns: ` the requested `Card`, or None.
        """
        li = [c for c in self.cards if c.label == label]
        if li: return li[0]
        else: return None

    def GetContentsByKind(self, kind):
        """Returns a list of all Content cards of the `kind`.

        * `kind `: must be a `Content.*_LBL` constant.
        
        `returns: ` a list of `Content`s, all of the same `kind`.
        """
        return [c for c in self.GetContents() if c.GetKind() == kind or c.GetKind(long=True) == kind]

    def GetNextCard(self, card, direc):
        """
        Returns the nearest `Card` to `card` in the direction `direc`.

        * `card: ` a `Card` held by this object.
        * `direc: ` must be one of `Deck.LEFT`, `Deck.RIGHT`, `Deck.UP`, or `Deck.DOWN`.

        `returns: ` the closest `Card` in the specified direction, or `None`.
        """
        # depending on the direction we compare a different side
        # of the cards, as well as get the points whose distance
        # we're going to calculate in a different way
        if   direc == Deck.LEFT:
            side  = lambda x: x.right
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == Deck.RIGHT:
            side  = lambda x: x.left
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetTopRight()
        elif direc == Deck.UP:
            side  = lambda x: x.bottom
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == Deck.DOWN:
            side  = lambda x: x.top
            getp1 = lambda x: x.GetBottomLeft()
            getp2 = lambda x: x.GetTopLeft()

        # get those cards whose "side" is in the desired position with respect to card
        rect = card.GetRect()
        nxt = []
        if direc == Deck.LEFT or direc == Deck.UP:
            nxt = [c for c in self.GetCards() if side(c.GetRect()) < side(rect)]
        elif direc == Deck.RIGHT or direc == Deck.DOWN:
            nxt = [c for c in self.GetCards() if side(c.GetRect()) > side(rect)]
        else:
            return None

        # we're going to use getp1 to get a point in card and compare
        # it to the point got by getp2 on all the cards in nxt
        if nxt:
            # order them by distance
            nxt.sort(key=lambda x: wxutils.dist2(getp1(x.GetRect()), getp2(rect)))
            # and return the nearest one
            return nxt[0]
        else:
            return None

    # def GetPadding(self):
    #     """Returns `self.CARD_PADDING`, fixed for scale.

    #     `returns: ` the current scaled padding width (float)."""
    #     return self.CARD_PADDING * self.scale

    def PlaceNewCard(self, subclass, pos=wx.DefaultPosition, below=False):
        """
        Places a new `Card` on this `Deck`.

        * `subclass: ` should be the string with the name of the `Card` subclass to create ("Content", "Header", "Image").
        * `pos: ` the position where to put the new `Card`. If it is the default, use `below` to determine
        where to put it.
        * `below ` when `False`, creates the new `Card` to the right of the currently selected
        `Card` in the `Deck`, if any; when `True` creates it below.

        `returns: ` the new `Card`.
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
            elif wxutils.GetCardAncestor(self.FindFocus()):
                rect = wxutils.GetCardAncestor(self.FindFocus()).GetRect()
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
    
        new = self.NewCard(subclass, pos=pos, scroll=True)
        self.UnselectAll()
        new.SetFocus()

        return new

    def NewCard(self, subclass, pos=wx.DefaultPosition, scroll=False):
        """
        Create a new `Card` of type `subclass` at `pos`.

        * `pos: ` the position where to create the `Card`.
        * `scroll: ` if True, scroll the `Deck` so that the new `Card` is in view.

        `returns: ` the new `Card`.
        """
        # never use labels, always let Deck set its own
        label = len(self.cards)

        # create the new card with the unscaled position
        # so that we can just call new.Stretch() afterward
        # to set both position and size
        pos = [i / self.scale for i in pos]

        if subclass == "Content":
            new = card.Content(self, label, pos=pos)
        elif subclass == "Header":
            new = card.Header(self, label, pos=pos)
        elif subclass == "Image":
            new = card.Image(self, label, pos=pos)
        new.Stretch(self.scale)

        # set bindings for every card
        new.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
        new.Bind(wx.EVT_CHILD_FOCUS, self.OnCardChildFocus)
        new.Bind(card.Card.EVT_DELETE, self.OnCardDelete)
        new.Bind(card.Card.EVT_COLLAPSE, self.OnCardCollapse)
        new.Bind(card.Card.EVT_REQUEST_VIEW, self.OnCardRequest)
        for ch in new.GetChildren():
            ch.Bind(wx.EVT_LEFT_DOWN, self.OnCardChildLeftDown)

        # raise the appropriate event
        event = self.NewCardEvent(id=wx.ID_ANY, subclass=subclass)
        event.SetEventObject(new)
        self.GetEventHandler().ProcessEvent(event)

        # make enough space and breathing room for the new card
        self.FitToChildren()
        self.ExpandVirtualSize(self.GetPadding() * 2, self.GetPadding() * 2)
        
        # make sure the new card is visible
        if scroll:
            rect = new.GetRect()
            deck = self.GetRect()
            if rect.bottom > deck.bottom or rect.right > deck.right or rect.left < 0 or rect.top < 0:
                self.ScrollToCard(new)

        # finish up
        new.SetFocus()
        self.cards.append(new)
        return new

    # def MoveCard(self, card, dx, dy):
    #     """Move the `Card`.

    #     `dx: ` the amount of pixels to move in the X direction.
    #     `dy: ` the amount of pixels to move in the Y direction.
    #     """
    #     card.MoveBy(dx, dy)

    # def GetSelection(self):
    #     """Return the current selected `Card`s.

    #     `returns: ` a list of `Card`s.
    #     """
    #     return self.selec.GetSelection()

    # def SelectCard(self, card, new_sel=False):
    #     """Select the specified `Card`.

    #     * `card: ` the `Card` to select.
    #     * `new_sel: ` if `True`, unselects all other `Card`s before selecting `card`.
    #     """
    #     self.selec.SelectCard(card, new_sel)

    # def UnselectCard(self, card):
    #     """Unselect the specified `Card`.

    #     * `card: ` the `Card` to unselect.
    #     """
    #     self.selec.UnselectCard(card)

    # def UnselectAll(self):
    #     """Unselect all `Card`s.
    #     """
    #     self.selec.UnselectAll()
    #     self.selec.Deactivate()

    # def SelectGroup(self, group, new_sel=True):
    #     """Select every `Card` in `group`.

    #     * `group: ` a `CardGroup` to select.
    #     * `new_sel: ` if `True`, unselects all other `Card`s before selecting.
    #     """
    #     self.selec.SelectGroup(group, new_sel)

    # def DeleteSelected(self):
    #     """Deletes every `Card` currently selected.
    #     """
    #     self.selec.DeleteSelected()

    def CopySelected(self):
        """Copies every `Card` currently selected to `wx.TheClipboard`.
        """
        # get the data
        data = []
        for c in self.GetSelection():
            data.append(c.Dump())

        # create our own custom data object
        obj = wx.CustomDataObject("CardList")
        obj.SetData(str([json.dumps(d) for d in data]))

        # write the data to the clipboard
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(obj)
            wx.TheClipboard.Close()

    def PasteFromClipboard(self, pos=wx.DefaultPosition):
        """Pastes every `Card` currently in `wx.TheClipboard`.
        """
        if wx.TheClipboard.Open():
            # get data
            obj = wx.CustomDataObject("CardList")
            wx.TheClipboard.GetData(obj)

            # don't use eval()! Use ast.literal_eval() instead
            data = [json.loads(d) for d in ast.literal_eval(obj.GetData())]

            # create new cards with the data
            for d in data:
                # copy all info and set focus to it
                card = self.NewCard(d["class"])
                card.Load(d)
                card.SetFocus()

                # default position: a step away from the original
                if pos == wx.DefaultPosition:
                    new_pos = [i + self.GetPadding() for i in d["pos"]]
                else:
                    new_pos = pos
                    
                card.SetPosition(new_pos)

            wx.TheClipboard.Close()

    # def GetGroups(self):
    #     """Get the list of `CardGroup`s defined for this `Deck`.

    #     `returns: ` a list of `CardGroup`s.
    #     """
    #     return self.groups

    def GetContainingGroups(self, card):
        """Get a list of every `CardGroup` that contains `card`.

        * `card: ` a `Card`.

        `returns: ` a list of `CardGroup`s.
        """
        return [g for g in self.groups if card in g.GetMembers()]

    # def NewGroup(self, cards=[]):
    #     """Create a new `CardGroup` with `cards` as members.

    #     * `cards: ` a list of `Card`s.
    #     """
    #     self.groups.append(card.CardGroup(label=len(self.groups), members=cards))

    def GroupSelected(self):
        """Creates a new `CardGroup` with the selected `Card`s as members.
        """
        sel = self.GetSelection()
        if sel: self.NewGroup(sel)

    def ScrollToCard(self, card):
        """Scroll in both direction so that `card` is fully in view.

        * `card: ` a `Card` to scroll to.
        """
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
        """Scroll in both direction so that `pt` is in view. `Deck.ScrollToCard` basically just calls
        this function twice, on a `Card`'s corner points.

        * `pt: ` a (x, y) point.
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

    # def ArrangeSelection(self, orient):
    #     """Arranges the selected cards according to `orient`.

    #     * `orient: ` must be one of `Deck.HORIZONTAL` or `Deck.VERTICAL`.
    #     """
    #     if   orient == Deck.HORIZONTAL:
    #         self.HArrangeSelectedCards()
    #     elif orient == Deck.VERTICAL:
    #         self.VArrangeSelectedCards()

    # def HArrangeSelectedCards(self):
    #     """Same as `Deck.ArrangeSelection(Deck.HORIZONTAL)`. Arranges `Card`s
    #     in a horizontal row, to the right of the left-most selected card.
    #     """
    #     if len(self.GetSelection()) < 1: return

    #     # we unselect first so that we erase the selection rectangles correctly
    #     arrange = self.GetSelection()[:]
    #     self.UnselectAll()         

    #     lefts = [c.GetRect().left for c in arrange]
    #     left = min(lefts)
    #     card = arrange[lefts.index(left)]
    #     top = card.GetRect().top
    #     arrange.sort(key=lambda x: x.GetRect().left)

    #     for c in arrange:
    #         c.SetPosition(wx.Point(left, top))
    #         left = c.GetRect().right + self.GetPadding()

    #     self.FitToChildren()
    #     self.selec.SetFocus()

    # def VArrangeSelectedCards(self):
    #     """Same as `Deck.ArrangeSelection(Deck.VERTICAL)`. Arranges `Card`s
    #     in a vertical column, below of the top-most selected card.
    #     """
    #     if len(self.GetSelection()) < 1: return

    #     # value-copy the list since we may do weird things to it
    #     arrange = self.GetSelection()[:]

    #     # compute the pivot
    #     tops = [c.GetRect().top for c in arrange]
    #     top = min(tops)
    #     card = arrange[tops.index(top)]
    #     left = card.GetRect().left
    #     arrange.sort(key=lambda x: x.GetRect().top)

    #     # and align all to the pivot
    #     for c in arrange:
    #         c.SetPosition(wx.Point(left, top))
    #         top = c.GetRect().bottom + self.GetPadding()

    #     self.FitToChildren()
    #     self.selec.SetFocus()

                    
    ### Callbacks

    # def OnCardCollapse(self, ev):
    #     """Listens to `Card.EVT_COLLAPSE`."""
    #     card = ev.GetEventObject()
    #     card.SetSize([i*self.scale for i in card.GetSize()])
        
    # def OnCardDelete(self, ev):
    #     """Listens to every `Card.EVT_DELETE`."""
    #     card = ev.GetEventObject()
    #     self.cards.remove(card)
    #     self.UnselectCard(card)

    # def OnMgrDelete(self, ev):
    #     """Listens to `SelectionManager.EVT_MGR_DELETE`, which is raised
    #     on every delete action. `Deck.DeleteSelected` calls every selected
    #     `Card`'s `Delete` method, which raises many `Card.EVT_DELETE`,
    #     and then raises only one `SelectionManager.EVT_MGR_DELETE` event.
    #     """
    #     self.selec.Deactivate()

    #     # raise the event again, with event object = self
    #     event = self.DeleteEvent(id=wx.ID_ANY, number=ev.number)
    #     event.SetEventObject(self)
    #     self.GetEventHandler().ProcessEvent(event)

    # def OnCardRequest(self, ev):
    #     """Listens to `Card.EVT_REQUEST_VIEW` and raises `Deck.EVT_REQUEST_VIEW`
    #     with the same card as event object. The difference is that now a
    #     `Box` can `Bind` only once to `EVT_REQUEST_VIEW` events coming
    #     from this `Deck`, instead of having to bind to every individual card.
    #     """
    #     event = Deck.ReqViewEvent(id=wx.ID_ANY)
    #     event.SetEventObject(ev.GetEventObject())
    #     self.GetEventHandler().ProcessEvent(event)

    # def OnChildFocus(self, ev):
    #     """Listens to `wx.EVT_CHILD_FOCUS`."""
    #     # important to avoid automatically scrolling to focused child
    #     pass 

    # def OnCardChildLeftDown(self, ev):
    #     """Listens to `wx.EVT_LEFT_DOWN` events on every `Card`'s child window."""
    #     self.UnselectAll()
    #     ev.Skip()

    # def OnCardLeftDown(self, ev):
    #     """Listens to `wx.EVT_LEFT_DOWN` events from every `Card`."""
    #     card = ev.GetEventObject()

    #     # bring to front and select
    #     card.Raise()
    #     self.selec.SelectCard(card)

    #     # initiate moving
    #     self.CaptureMouse()
    #     self.Bind(wx.EVT_LEFT_UP, self.OnCardLeftUp)
    #     self.Bind(wx.EVT_MOTION, self.OnMovingCard)

    #     self.on_motion = False
    #     pos = card.GetPosition() + ev.GetPosition() # relative to the canvas
    #     self.moving_cards_pos = []
    #     for c in self.GetSelection():
    #         # (card, pos w.r.t. the original click, current pos)
    #         self.moving_cards_pos.append((c, c.GetPosition() - pos, c.GetPosition()))

    # def OnCardChildFocus(self, ev):
    #     """Listens to `wx.EVT_CHILD_FOCUS` from every `Card`."""
    #     self.UnselectAll()
    #     ev.Skip()

    # def OnMovingCard(self, ev):
    #     """Listens to `wx.EVT_MOTION` events from `Card`s only while a `Card` is being click-dragged."""
    #     if ev.Dragging() and self.moving_cards_pos:
    #         # draw a rectangle while moving
    #         # order is important
    #         self.on_motion = True
    #         for c, orig, pos in self.moving_cards_pos:
    #             self.EraseCardRect(c, pos, refresh = False)
    #             pos = ev.GetPosition() + orig
    #             self.PaintCardRect(c, pos)

    # def OnCardLeftUp(self, ev):
    #     """Listens to `wx.EVT_LEFT_UP` events from `Card`s only while a `Card` is being click-dragged."""
    #     # terminate moving
    #     if self.on_motion:
    #         self.on_motion = False
    #         for c, orig, pos in self.moving_cards_pos:
    #             self.EraseCardRect(c, pos)
                
    #         if self.moving_cards_pos:
    #             for c, orig, pos in self.moving_cards_pos:
    #                 final_pos = ev.GetPosition() + orig - (Content.BORDER_WIDTH, Content.BORDER_WIDTH)
    #                 # since we need to set absolute final position, we use
    #                 # Card.Move instead of Card.MoveBy
    #                 c.Move(final_pos)
                    
    #     self.moving_cards_pos = []
    #     self.ReleaseMouse()
    #     self.Unbind(wx.EVT_LEFT_UP)
    #     self.Unbind(wx.EVT_MOTION)

    # def OnLeftDown(self, ev):
    #     """Listens to `wx.EVT_LEFT_DOWN` from this object."""
    #     self.UnselectAll()
    #     self.selec.SetFocus()

    #     # initiate drag select
    #     self.init_pos = ev.GetPosition()
    #     self.cur_pos = ev.GetPosition()
    #     self.Bind(wx.EVT_MOTION, self.OnDragSelect)

    # def OnDragSelect(self, ev):
    #     """Listens to `wx.EVT_MOTION` events from this object, only when the user is click-dragging."""
    #     if ev.Dragging() and not self.moving_cards_pos:
    #         self.drag_select = True
            
    #         # erase the last one selection rect
    #         self.PaintRect(wx.Rect(self.init_pos[0], self.init_pos[1],
    #                         self.cur_pos[0], self.cur_pos[1]),
    #                         style = wx.TRANSPARENT,
    #                         refresh = False)
            
    #         # and draw the current one
    #         final_pos = ev.GetPosition() - self.init_pos
    #         self.PaintRect(wx.Rect(self.init_pos[0], self.init_pos[1],
    #                         final_pos[0], final_pos[1]),
    #                         refresh = False)

    #         self.cur_pos = final_pos

    # def OnLeftUp(self, ev):
    #     """Listens to `wx.EVT_LEFT_UP` events from this object."""
    #     # terminate drag select
    #     if self.drag_select:
    #         # erase the last selection rect
    #         final_rect = wxutils.MakeEncirclingRect(self.init_pos, self.init_pos + self.cur_pos)                        
    #         self.PaintRect(final_rect, style = wx.TRANSPARENT)

    #         # select cards
    #         selected = [c for c in self.GetCards() if c.GetRect().Intersects(final_rect)]
    #         self.SelectGroup(card.CardGroup(selected), new_sel=True)
            
    #         # finish up
    #         self.Unbind(wx.EVT_MOTION)
    #         self.drag_select = False
    #         self.FitToChildren()
    #         self.selec.SetFocus()

    # def OnMouseCaptureLost(self, ev):
    #     """Listens to `wx.EVT_MOUSE_CAPTURE_LOST` events from this object."""
    #     self.ReleaseMouse()

    # def OnLeftDClick(self, ev):
    #     """Listens to `wx.EVT_LEFT_DCLICK` events from this object."""
    #     self.NewCard("Content", pos=ev.GetPosition())
        
    # def OnCtrlRet(self, ev):
    #     """Listens to CTRL+RET."""
    #     self.PlaceNewCard("Content", below=False)

    # def OnCtrlShftRet(self, ev):
    #     """Listens to CTRL+SHIFT+RET."""
    #     self.PlaceNewCard("Content", below=True)

    # def OnAltRet(self, ev):
    #     """Listens to ALT+RET."""
    #     self.PlaceNewCard("Header", below=False)
        
    # def OnAltShftRet(self, ev):
    #     """Listens to ALT+SHIFT+RET."""
    #     self.PlaceNewCard("Header", below=True)

    # def OnRightDown(self, ev):
    #     """Listens to `wx.EVT_RIGHT_DOWN` events."""
    #     self.menu_position = ev.GetPosition()
    #     self.PopupMenu(self.menu, ev.GetPosition())

    # def OnPaste(self, ev):
    #     """Listens to the "Paste" `wx.EVT_MENU` event from the context menu."""
    #     self.PasteFromClipboard(self.menu_position)

    # def OnInsertContent(self, ev):
    #     """Listens to the "Insert Content" `wx.EVT_MENU` event from the context menu."""
    #     self.PlaceNewCard("Content", pos=self.menu_position)

    # def OnInsertHeader(self, ev):
    #     """Listens to the "Insert Header" `wx.EVT_MENU` event from the context menu."""
    #     self.PlaceNewCard("Header", pos=self.menu_position)

    # def OnInsertImg(self, ev):
    #     """Listens to the "Insert Image" `wx.EVT_MENU` event from the context menu."""
    #     self.PlaceNewCard("Image", pos=self.menu_position)

    # def OnClose(self, ev):
    #     """Listens to the "Close" `wx.EVT_MENU` event from the context menu."""
    #     # should close tab
    #     pass
        
            
    ### Auxiliary functions

    # def InitMenu(self):
    #     """Initializes the `wx.Menu` to display on right click."""
    #     # make menu
    #     menu = wx.Menu()
    #     self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

    #     # edit actions
    #     past_it = wx.MenuItem(menu, wx.ID_PASTE, "Paste")
    #     self.Bind(wx.EVT_MENU, self.OnPaste, past_it)

    #     # insert actions
    #     cont_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Content")
    #     self.Bind(wx.EVT_MENU, self.OnInsertContent, cont_it)

    #     head_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Header")
    #     self.Bind(wx.EVT_MENU, self.OnInsertHeader, head_it)
        
    #     img_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Image")
    #     self.Bind(wx.EVT_MENU, self.OnInsertImg, img_it)
        
    #     # tab actions
    #     close_it = wx.MenuItem(menu, wx.ID_ANY, "Close")
    #     self.Bind(wx.EVT_MENU, self.OnClose, close_it)

    #     menu.AppendItem(past_it)
    #     menu.AppendItem(cont_it)
    #     menu.AppendItem(head_it)
    #     menu.AppendItem(img_it)
    #     menu.AppendSeparator()
    #     menu.AppendItem(close_it)        

    #     self.menu = menu

    # def InitAccels(self):
    #     """Initializes the `wx.AcceleratorTable`."""
    #     # we create ghost menus so that we can
    #     # bind its items to some accelerators
    #     accels = []
    #     ghost = wx.Menu()

    #     contr = wx.MenuItem(ghost, wx.ID_ANY, "New Card: Right")
    #     contb = wx.MenuItem(ghost, wx.ID_ANY, "New Card: Below")
    #     headr = wx.MenuItem(ghost, wx.ID_ANY, "New Header: Right")
    #     headb = wx.MenuItem(ghost, wx.ID_ANY, "New Header: Below")

    #     self.Bind(wx.EVT_MENU, self.OnCtrlRet    , contr)
    #     self.Bind(wx.EVT_MENU, self.OnAltRet     , headr)
    #     self.Bind(wx.EVT_MENU, self.OnCtrlShftRet , contb)
    #     self.Bind(wx.EVT_MENU, self.OnAltShftRet  , headb)

    #     accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_RETURN , contr.GetId()))
    #     accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_RETURN  , headr.GetId()))
    #     accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_RETURN, contb.GetId()))
    #     accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_ALT  , wx.WXK_RETURN, headb.GetId()))

    #     self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    # def PaintRect(self, rect, thick=MOVING_RECT_THICKNESS, style=wx.SOLID, refresh=True):
    #     """Paints a rectangle over this window. Used for click-dragging.

    #     * `rect: ` a `wx.Rect`.
    #     * `thick: ` line thickness. By default, is `Deck.MOVING_RECT_THICKNESS`.
    #     * `style: ` a `dc.Pen` style. Use `wx.TRANSPARENT` to erase a rectangle.
    #     * `refresh: ` whether to call `Refresh` after the rectangle is painted.
    #     """
    #     dc = wx.ClientDC(self)
    #     # Brush is for background, Pen is for foreground
    #     dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
    #     dc.SetPen(wx.Pen("BLACK", thick, style))
    #     dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])
    #     if refresh: self.RefreshRect(rect)
        
    # def PaintCardRect(self, card, pos, thick=MOVING_RECT_THICKNESS, style=wx.SOLID, refresh=True):
    #     """Paints a rectangle just big enough to encircle `card`.

    #     * `card: ` a `Card`.
    #     * `pos: ` where to paint the rectangle.
    #     * `thick: ` line thickness. By default, is `Deck.MOVING_RECT_THICKNESS`.
    #     * `style: ` a `dc.Pen` style. Use `wx.TRANSPARENT` to erase a rectangle.
    #     * `refresh: ` whether to call `Refresh` after the rectangle is painted.
    #     """
    #     x, y, w, h = card.GetRect()
    #     rect = wx.Rect(pos[0], pos[1], w, h)
    #     rect = rect.Inflate(2 * thick, 2 * thick)
    #     self.PaintRect(rect, thick=thick, style=style, refresh=refresh)

    # def EraseCardRect(self, card, pos, thick=MOVING_RECT_THICKNESS, refresh=True):
    #     """Erases a rectangle drawn by PaintCardRect().

    #     * `card: ` a `Card`.
    #     * `pos: ` where to paint the rectangle.
    #     * `thick: ` line thickness. By default, is `Deck.MOVING_RECT_THICKNESS`.
    #     * `refresh: ` whether to call `Refresh` after the rectangle is painted.
    #     """
    #     # Brush is for background, Pen is for foreground
    #     x, y, w, h = card.GetRect()        
    #     rect = wx.Rect(pos[0], pos[1], w, h)
    #     rect = rect.Inflate(2 * thick, 2 * thick)
    #     self.PaintRect(rect, thick=thick, style=wx.TRANSPARENT, refresh=refresh)
    
    def DumpCards(self):
        """Dumps all the `Card`s' info in a `dict`.

        `returns: ` a `dict` of the form {id1: data1, id2: data2, ...}.
        """
        carddict = {}

        # we put the scrollbars at the origin, to get the real positions
        shown = self.IsShown()
        if shown: self.Hide()
        view_start = self.GetViewStart()
        self.Scroll(0, 0)

        # with the scrollbars at the origin, dump the cards        
        for c in self.cards:
            carddict[c.GetId()] = c.Dump()
            carddict[c.GetId()]["pos"] = [i / self.scale for i in carddict[c.GetId()]["pos"]]
            
        # and return to the original view
        self.Scroll(view_start[0], view_start[1])
        if shown: self.Show()

        return carddict

    def DumpGroups(self):
        """Dumps all the `CardGroup`s' info in a `dict`.

        `returns: ` a `dict` of the form {label1: data1, label2: data2, ...}.
        """
        d = {}
        for g in self.groups: d[g.GetLabel()] = g.Dump()
        return d

    def Dump(self):
        """Returns a `dict` with all the info contained in this `Deck`.

        `returns: ` a `dict` of the form {"cards": self.DumpCards(), "groups": self.DumpGroups()}.
        """
        return {"cards": self.DumpCards(), "groups": self.DumpGroups()}

    def Load(self, d):
        """Read a `dict` and load all its data.

        * `d: ` a `dict` in the format returned by `Dump`.
        """
        if "cards" in d.keys():
            # note we are not loading the wx id of the windows
            # instead, as identifier, we use label, which should
            # be a value of the dict values
            for id, values in d["cards"].iteritems():
                new = self.NewCard(values["class"])
                new.Load(values)
                    
        if "groups" in d.keys():
            # here again we use the label as identifier
            # but this time the label is the key in the dictionary
            for label, members in d["groups"].iteritems():
                cards = [self.GetCard(l) for l in members]
                self.NewGroup(cards)


                
###########################
# SelectionManager Class
###########################
                                
class SelectionManager(wx.Window):
    """
    `SelectionManager` is an invisible window that positions itself on the top left corner of a `Deck`
    and gets focus every time a card is (or many cards are) selected. This is done to hide carets
    and selections from other controls while selection is active. `SelectionManager` also manages
    card selection by managing key down events, such as arrow keys to move selection, shift + arrow
    keys to extend selection, etc.
    """
    SIZE = (1,1)
    POS  = (0,0)

    DeleteEvent, EVT_MGR_DELETE = ne.NewCommandEvent()

    def __init__(self, parent):
        """Constructor.
        
        * `parent: ` the parent `wx.Window`, usually a `Deck`.
        """
        super(SelectionManager, self).__init__(parent, size=self.SIZE, pos=self.POS)
        self.cards = []
        self.last = None
        self.active = False
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())


    ### behavior functions

    # def Activate(self):
    #     """Prepare this object to manage selection.
    #     """
    #     self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
    #     self.SetFocus()
    #     self.active = True

    # def Deactivate(self):
    #     """Signal this object to stop managing selection. All `Card`s in the
    #     current selection are unselected.
    #     """
    #     # return focus to the last card
    #     if self.last:
    #         self.last.SetFocus()
    #         self.last = None
    #     else:
    #         self.GetGrandParent().SetFocus()
            
    #     # clean up
    #     self.UnselectAll()
    #     self.Unbind(wx.EVT_KEY_DOWN)
    #     self.active = False

    # def IsActive(self):
    #     """Check if this object is managing selection.

    #     `returns: ` `True` if active, `False` otherwise.
    #     """
    #     return self.active

    # def GetSelection(self):
    #     """Get the selected `Card`s.

    #     `returns: ` a list of `Card`s.
    #     """
    #     return self.cards

    # def SelectCard(self, card, new_sel=False):
    #     """Selects `card`.

    #     * `new_sel: ` if `True`, unselects all other `Card`s before selecting `card`.
    #     """
    #     # if new_sel, select only this card
    #     if new_sel:
    #         self.Activate()
    #         self.UnselectAll()
    #         self.cards = [card]
    #         card.Select()
    #         self.last = card
            
    #     # else, select card only if it was not already selected
    #     elif card not in self.cards:
    #         if not self.IsActive():
    #             self.Activate()
    #         self.cards.append(card)                        
            
    #         for c in self.cards:
    #             c.Select()
    #             self.last = card

    # def UnselectCard(self, card):
    #     """Removes `card` from the current selection.

    #     * `card: ` a `Card`.
    #     """
    #     if card in self.cards:
    #         self.cards.remove(card)
    #         card.Unselect()

    # def UnselectAll(self):
    #     """Unselects all cards. Be sure to call this method instead of
    #     `Unselect` on every card for proper cleanup.
    #     """
    #     while len(self.cards) > 0:
    #         c = self.cards[0]
    #         self.UnselectCard(c)

    # def SelectGroup(self, group, new_sel=True):
    #     """Select every `Card` in `group`.

    #     * `group: ` a `CardGroup` to select.
    #     * `new_sel: ` if `True`, unselects all other `Card`s before selecting.
    #     """
    #     # in case we are coming from a card that's inside the group,
    #     # we may want to return to that card after selection ends
    #     # so we select the group but restore the last card after
    #     if self.last and self.last in group.GetMembers():
    #         crd = self.last

    #     if new_sel: self.UnselectAll()
    #     for c in group.GetMembers(): self.SelectCard(c)

    #     if crd:
    #         self.last = crd

    def DeleteSelected(self):
        """Deletes every `Card` currently selected."""
        # store the number of cards we're deleting to raise the event
        number = len(self.cards)
        
        # remember to use while instead of for, since in every
        # iteration self.cards is growing shorter
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

    # def SelectNext(self, direc, new_sel=False):
    #     """Selects next `Card` in the specified direction.

    #     * `direc: ` direc should be one of `Deck.LEFT`, `Deck.RIGHT`, `Deck.UP`, or `Deck.DOWN`.
    #     * `new_sel: ` if `True`, unselect all others and select only the next card,
    #     if `False`, add it to current selection.
    #     """
    #     nxt = self.GetParent().GetNextCard(self.last, direc)
    #     if nxt:
    #         self.SelectCard(nxt, new_sel)

    # def MoveSelected(self, dx, dy):
    #     """Move all selected `Card`s.

    #     `dx: ` the amount of pixels to move in the X direction.
    #     `dy: ` the amount of pixels to move in the Y direction.
    #     """
    #     for c in self.GetSelection():
    #         self.GetParent().MoveCard(c, dx, dy)


    ### callbacks

    # def OnCardLeftDown(self, ev):
    #     print "Mgr.OnCardLeftDown"
    #     card = ev.GetEventObject()
        
    #     if not ev.ShiftDown():
    #         # no shift: select only this card
    #         self.SelectCard(card, new_sel = True)
    #     else:                                      
    #         if card in self.GetSelection():
    #             # shift + click while selected: unselect
    #             self.UnselectCard(card)
    #         elif card not in self.GetSelection():
    #             # shift + click while not selected: add select   
    #             self.SelectCard(card, new_sel = False)

    # def OnKeyDown(self, ev):
    #     """Listens to `wx.EVT_KEY_DOWN`, only when activated."""
    #     if not self.IsActive():
    #         ev.Skip()
    #         return

    #     key = ev.GetKeyCode()
    #     bd = self.GetParent()

    #     # alt + arrow: move selection
    #     if ev.AltDown():
    #         if   key == wx.WXK_LEFT:
    #             self.MoveSelected(-bd.SCROLL_STEP, 0)
    #         elif key == wx.WXK_RIGHT:
    #             self.MoveSelected(bd.SCROLL_STEP, 0)
    #         elif key == wx.WXK_UP:
    #             self.MoveSelected(0, -bd.SCROLL_STEP)
    #         elif key == wx.WXK_DOWN:
    #             self.MoveSelected(0, bd.SCROLL_STEP)
    #         else:
    #             ev.Skip()

    #     # ctrl key
    #     elif ev.ControlDown():
    #         if   key == ord("U"):
    #             # since collapsing takes away focus, store selection
    #             cards = self.GetSelection()[:]

    #             # for the same reason, don't iterate over self.GetSelection
    #             for c in cards:
    #                 if isinstance(c, card.Content):
    #                     c.ToggleCollapse()

    #             # restore selection
    #             self.SelectGroup(card.CardGroup(members=cards), True)
                
    #         elif key == ord("I"):
    #             pass
            
    #         else:
    #             ev.Skip()

    #     # meta key
    #     elif ev.MetaDown():
    #         ev.Skip()

    #     # shift key
    #     elif ev.ShiftDown():
    #         if   key == wx.WXK_LEFT:
    #             self.SelectNext(Deck.LEFT, new_sel=False)
    #         elif key == wx.WXK_RIGHT:
    #             self.SelectNext(Deck.RIGHT, new_sel=False)
    #         elif key == wx.WXK_UP:
    #             self.SelectNext(Deck.UP, new_sel=False)
    #         elif key == wx.WXK_DOWN:
    #             self.SelectNext(Deck.DOWN, new_sel=False)
    #         else:
    #             ev.Skip()

    #     # function keys
    #     elif wxutils.IsFunctionKey(key):
    #         ev.Skip()

    #     # no modifiers
    #     else:
    #         # arrow keys: select next card    
    #         if   key == wx.WXK_LEFT:
    #             self.SelectNext(Deck.LEFT, new_sel=True)
    #         elif key == wx.WXK_RIGHT:
    #             self.SelectNext(Deck.RIGHT, new_sel=True)
    #         elif key == wx.WXK_UP:
    #             self.SelectNext(Deck.UP, new_sel=True)
    #         elif key == wx.WXK_DOWN:
    #             self.SelectNext(Deck.DOWN, new_sel=True)

    #         # DEL: delete all selection
    #         elif key == wx.WXK_DELETE:
    #             self.DeleteSelected()
                
    #         # all other keys cancel selection
    #         else:
    #             self.Deactivate()

                

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
for field in dir(wxutils.AutoSize):
    __pdoc__['Deck.%s' % field] = None
for field in dir(wx.Window):
    __pdoc__['SelectionManager.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in Deck.__dict__.keys():
    if 'Deck.%s' % field in __pdoc__.keys():
        del __pdoc__['Deck.%s' % field]
for field in SelectionManager.__dict__.keys():
    if 'SelectionManager.%s' % field in __pdoc__.keys():
        del __pdoc__['SelectionManager.%s' % field]
