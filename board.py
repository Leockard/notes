#!/usr/bin/python

# board.py
# note taking class for notes.py

import wx
import wx.richtext as rt


######################
# BoardBase Class
######################

class BoardBase(wx.ScrolledWindow):
    MOVING_RECT_THICKNESS = 1
    BACKGROUND_CL = "#AAAAAA"    

    def __init__(self, parent, id = wx.ID_ANY, pos = (0, 0), size = (20, 20)):
        super(BoardBase, self).__init__(parent, size = size)

        self.cards = []
        self.selected_cards = []
        self.moving_cards_pos = []
        self.cur_scale = 1.0

        # Bindings
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self.OnMouseCaptureLost)

        # Other gui setup
        self.SetBackgroundColour(BoardBase.BACKGROUND_CL)
        self.SetScrollbars(20, 20, 6000, 6000) # method from wx.ScrolledWindow, NOT wx.Window
        self.SetFocus()

        
    ### Behavior functions
    
    def GetCards(self):
        """Returns a list of all cards held by the Board."""
        return self.cards

    def GetCard(self, label):
        """Returns the card with the label, or None."""
        li = [c for c in self.cards if c.label == label]
        if li: return li[0]
        else: return None

    def GetNextCard(self, card, cycle=True):
        """Returns the card with label consecutive to that of the argument, or None.
        If cycle=True, and card is the Card with the last label, return the Card with first label."""
        greater_lbl = [c for c in self.cards if c.label > card.label]
        greater_lbl.sort(key = lambda x: x.label)
        if greater_lbl:
            return greater_lbl[0]

        if not cycle:
            return None
            
        cards = self.cards[:]
        cards.sort(key = lambda x: x.label)
        return cards[0]

    def GetPrevCard(self, card, cycle=True):
        """Returns the card with label previous to that of the argument, or None.
        If cycle=True, and card is the Card with the last label, return the Card with last label."""
        lesser_lbl = [c for c in self.cards if c.label < card.label]
        lesser_lbl.sort(key = lambda x: x.label)
        if lesser_lbl:
            return lesser_lbl[-1]

        if not cycle:
            return None
            
        cards = self.cards[:]
        cards.sort(key = lambda x: x.label)
        return cards[-1]

    def NewCard(self, pos, label = -1, title="", kind="kind", content=""):
        if label == -1: label = len(self.cards)
        newcard = Content(self, label, wx.ID_ANY, pos, title, kind, content)
        newcard.SetFocus()
        self.SelectCard(newcard, True)
        
        newcard.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
        newcard.Bind(wx.EVT_KILL_FOCUS, self.OnCardKillFocus)
        newcard.Bind(wx.EVT_SET_FOCUS, self.OnCardSetFocus)
        
        self.cards.append(newcard)
        return newcard

    def NewHeader(self, pos, label = -1, txt=""):
        if label == -1: label = len(self.cards)
        newhead = Header(self, label, wx.ID_ANY, pos, txt)
        newhead.SetFocus()
        
        newhead.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
        
        self.cards.append(newhead)
        return newhead

    def SetScale(self, scale):
        """Rescales every card to scale. Use this to zoom in and out."""
        print "board.SetScale()"

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
            pos = c.GetPosition() + (Board.CARD_PADDING, Board.CARD_PADDING)
            if isinstance(c, Content):
                new.append(self.NewCard(pos, -1, c.GetTitle(), c.GetKind(), c.GetContent()))
            if isinstance(c, Header):
                new.append(self.NewHeader(pos, -1, c.GetHeader()))

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
            left = c.GetRect().right + Board.CARD_PADDING

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
            top = c.GetRect().bottom + Board.CARD_PADDING

                    
    ### Callbacks

    def OnCardSetFocus(self, ev):
        pass

    def OnCardKillFocus(self, ev):
        pass

    def OnChar(self, ev):
        print ev.GetKeyCode()

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
        self.drag_select = True
        self.Bind(wx.EVT_MOTION, self.OnDragSelect)

    def OnDragSelect(self, ev):
        if ev.Dragging() and not self.moving_cards_pos:
            # erase the last one selection rect
            self.PaintRect((self.init_pos[0], self.init_pos[1],
                            self.cur_pos[0], self.cur_pos[1]),
                            style = wx.TRANSPARENT,
                            refresh = False)
            
            # and draw the current one
            final_pos = ev.GetPosition() - self.init_pos
            self.PaintRect((self.init_pos[0], self.init_pos[1],
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
        pos = self.CalculateNewCardPosition(ev.GetPosition())
        self.NewCard(pos)

    def OnRightDown(self, ev):
        self.PopupMenu(BoardMenu(self.GetParent()), ev.GetPosition())

    def OnSize(self, ev):
        self.SetSize(ev.GetSize())

            
    ### Auxiliary functions

    def PaintRect(self, rect, thick = MOVING_RECT_THICKNESS, style = wx.SOLID, refresh = True):
        """Paints a rectangle. Use style = wx.TRANSPARENT to erase a rectangle."""
        dc = wx.ClientDC(self)
        # Brush is for background, Pen is for foreground
        dc.SetBrush(wx.Brush(self.GetBackgroundColour()))
        dc.SetPen(wx.Pen("BLACK", thick, style))
        dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])
        if refresh: self.Refresh()
        
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

    def CalculateNewCardPosition(self, newpos, below = False):
        """
        Returns the position for a new card, having received a double-click at pos.
        If argument below if False (by default), place the new card to the right of the
        current card. If it is True, place it below.
        """
        pos = newpos
        rect = wx.Rect(newpos.x, newpos.y, Content.DEFAULT_SZ[0], Content.DEFAULT_SZ[1])
        rects = [c.GetRect() for c in self.cards]

        if below:
            bottoms = [r.bottom for r in rects if rect.Intersects(r)]
            if len(bottoms) > 0:
                pos.y = max(bottoms) + Board.CARD_PADDING
        else:
            rights = [r.right for r in rects if rect.Intersects(r)]
            if len(rights) > 0:
                pos.x = max(rights) + Board.CARD_PADDING
                
        return pos
    
    def Dump(self):
        """Returns a dict with all the info in the current cards."""
        carddict = {}

        # we put the scrollbars at the top, to get the real positions
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

    

class BoardMenu(wx.Menu):
    def __init__(self, parent):
        super(BoardMenu, self).__init__()

        min_item = wx.MenuItem(self, wx.NewId(), "Minimize")
        self.AppendItem(min_item)
        close_item = wx.MenuItem(self, wx.NewId(), "Close")
        self.AppendItem(close_item)

        self.Bind(wx.EVT_MENU, self.OnMinimize, min_item)
        self.Bind(wx.EVT_MENU, self.OnClose, close_item)


    ### Callbacks
    
    def OnMinimize(self, ev):
        self.GetParent().Iconize()

    def OnClose(self, ev):
        self.GetParent().Close()            



######################
# Board Class
######################

class Board(wx.Panel):
    CARD_PADDING = 15

    def __init__(self, parent, id = wx.ID_ANY, pos = (0, 0), size = (20, 20)):
        super(Board, self).__init__(parent, size = size)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(hbox)

        # UI steup
        self.InitBar()
        self.InitBoard(pos, size)


    ### Auxiliary functions

    def InitBar(self):
        hbox = self.GetSizer()
        if not hbox: hbox = wx.BoxSizer(wx.HORIZONTAL)

        # make UI
        toolbar = wx.ToolBar(self, wx.ID_ANY, style=wx.TB_VERTICAL)
        del_it = toolbar.AddLabelTool(wx.ID_ANY, "Delete",
                                      wx.ArtProvider.GetBitmap(wx.ART_DELETE),
                                      kind=wx.ITEM_NORMAL)
        cpy_it = toolbar.AddLabelTool(wx.ID_ANY, "Copy",
                                      wx.ArtProvider.GetBitmap(wx.ART_COPY),
                                      kind=wx.ITEM_NORMAL)
        toolbar.Realize()

        # layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(toolbar, proportion=0, flag=wx.TOP, border=1)

        hbox.Add(vbox, proportion=0, flag=wx.LEFT|wx.EXPAND, border=1)

        # bindings
        self.Bind(wx.EVT_TOOL, self.OnDelete, del_it)
        self.Bind(wx.EVT_TOOL, self.OnCopy, cpy_it)

    def InitBoard(self, pos, size):
        hbox = self.GetSizer()
        if not hbox: hbox = wx.BoxSizer(wx.HORIZONTAL)
            
        board = BoardBase(self, id=id, pos=pos, size=size)
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        vbox2.Add(board, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)
        hbox.Add(vbox2, proportion=1, flag=wx.ALL|wx.EXPAND,  border=1)
        
        # set members
        self.board = board

    def OnCopy(self, ev):
        self.board.CopySelected()

    def OnDelete(self, ev):
        self.board.DeleteSelected()
    


######################
# Card Class
######################

class Card(wx.Panel):
    BORDER_WIDTH = 2
    
    def __init__(self, parent, id, pos, size, style):
        """Base class for every window that will be placed on Board. Override SetupUI()."""
        super(Card, self).__init__(parent, id, pos, size, style)

    def SetupUI(self):
        pass

    def GetLabel():
        return self.label


    
######################
# Card Header
######################

class Header(Card):
    DEFAULT_SZ = (150, 32)
    
    def __init__(self, parent, label, id, pos, header = "header..."):
        super(Header, self).__init__(parent, id, pos, Header.DEFAULT_SZ,
                                     style = wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        self.SetupUI()
        self.header.SetValue(header)
        self.label = label


    ### Behavior Functions
    def GetHeader(self):
        return self.header.GetValue()

    ### Auxiliary functions
    def SetupUI(self):
        # Controls
        txt = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_RICH)
        txt.SetHint("Header")
        
        # Boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(txt, proportion=1, flag=wx.LEFT|wx.EXPAND, border=Card.BORDER_WIDTH)

        vbox = wx.BoxSizer(wx.VERTICAL)                
        vbox.Add(txt, proportion=0, flag=wx.LEFT|wx.EXPAND, border=Card.BORDER_WIDTH)
        
        self.header = txt
        self.SetSizer(vbox)
        self.Show(True)

    def Dump(self):
        """Returns a dict with all the information contained."""
        return {"class": "Header", "label": self.label,
                "pos": self.GetPosition(), "header": self.GetHeader()}



            

######################
# Class Content
######################

class Content(Card):
    # Sizes
    DEFAULT_SZ = (250, 150)
    BIG_SZ     = (350, 250)

    # Labels
    DEFAULT_LBL    = "kind"
    CONCEPT_LBL    = "C"
    ASSUMPTION_LBL = "A"
    RESEARCH_LBL   = "R"
    FACT_LBL       = "F"
    # Colors
    DEFAULT_CL    = (220, 218, 213, 255)
    CONCEPT_CL    = (0, 128, 0, 255)
    ASSUMPTION_CL = (250, 128, 114, 255)
    RESEARCH_CL   = (255, 165, 0, 255)
    FACT_CL       = (70, 130, 180, 255)

    def __init__(self, parent, label, id, pos, title = "title...", kind = "kind", content = "Write here..."):
        super(Content, self).__init__(parent, id, pos, self.DEFAULT_SZ,
                                   style = wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        self.label = label
        self.InitUI()
        self.SetKind(kind)
        self.title.SetValue(title)
        self.content.SetValue(content)

        
    ### Behavior functions
    
    def GetTitle(self):
        return self.title.GetValue()

    def GetContent(self):
        return self.content.GetValue()
    
    def GetKind(self):
        return self.kindbut.GetLabel()

    def SetKind(self, kind):
        if kind == "kind":
            self.kindbut.SetLabel("kind")
        else:
            self.kindbut.SetLabel(kind[0])
            
        if   kind == Content.CONCEPT_LBL    : self.SetBackgroundColour(Content.CONCEPT_CL)
        elif kind == Content.ASSUMPTION_LBL : self.SetBackgroundColour(Content.ASSUMPTION_CL)
        elif kind == Content.RESEARCH_LBL   : self.SetBackgroundColour(Content.RESEARCH_CL)
        elif kind == Content.FACT_LBL       : self.SetBackgroundColour(Content.FACT_CL)
        else                                : self.SetBackgroundColour(Content.DEFAULT_CL)

    
    ### Auxiliary functions
    
    def InitUI(self):
        # Controls
        title = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_RICH)
        title.SetHint("Title")
        kindbut = wx.Button(self, wx.ID_ANY, label = "kind", size = (33, 23), style = wx.BORDER_NONE)
        kindbut.SetOwnFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False))
        content = rt.RichTextCtrl(self, size = (10, 10))
        # content.SetHint("Write here...")
        # label   = wx.StaticText(self, wx.ID_ANY, label = str(self.label), style = wx.ALIGN_RIGHT)
        
        # Boxes
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.LEFT|wx.CENTER, border=Card.BORDER_WIDTH)
        hbox1.Add(kindbut, proportion=0, flag=wx.RIGHT,          border=Card.BORDER_WIDTH)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(content, proportion=1, flag=wx.ALL|wx.EXPAND, border=Card.BORDER_WIDTH)        

        # hbox3 = wx.BoxSizer(wx.HORIZONTAL)        
        # hbox3.Add(label  , proportion=0, flag=wx.RIGHT, border=Card.BORDER_WIDTH)

        vbox = wx.BoxSizer(wx.VERTICAL)                
        vbox.Add(hbox1, proportion=0, flag=wx.LEFT |wx.EXPAND, border=Card.BORDER_WIDTH)
        vbox.Add(hbox2, proportion=1, flag=wx.LEFT |wx.EXPAND, border=Card.BORDER_WIDTH)
        # vbox.Add(hbox3, proportion=0, flag=wx.RIGHT|wx.EXPAND, border=Card.BORDER_WIDTH)
        
        # Bindings
        kindbut.Bind(wx.EVT_BUTTON, self.OnKindPressed)
        content.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

        self.kindbut = kindbut
        self.title = title
        self.content = content
        self.SetSizer(vbox)
        self.Show(True)

    def Dump(self):
        pos = self.GetPosition()
        return {"class": "Content",
                "label": self.label,
                "pos": (pos.x, pos.y),
                "kind": self.GetKind(),
                "title": self.GetTitle(),
                "content": self.GetContent()}


    ### Callbacks

    def OnKeyDown(self, ev):
        ### skip TAB, so that we don't input \t and tab traversal still works
        if ev.GetKeyCode() != 9:
            ev.ResumePropagation(True)
            ev.Skip()

    # def OnTextFocus(self, ev):
    #     ctrl = ev.GetEventObject()
    #     if ctrl.GetValue() == "title..." or ctrl.GetValue() == "Write here...":
    #         ctrl.ChangeValue("")
    #     # if not skipped, there will be no blinking cursor!
    #     ev.Skip()

    # def OnCopyPressed(self, ev):
    #     parent = self.GetParent()
    #     # pos = parent.CalculateNewCardPosition(self.GetPosition())
    #     pos = self.GetPosition() + (Board.CARD_PADDING, Board.CARD_PADDING)
    #     parent.NewCard(pos, title=self.GetTitle(), kind=self.GetKind(), content=self.GetContent())

    def OnKindPressed(self, ev):
        ctrl = ev.GetEventObject()
        rect = ctrl.GetRect()
        pos = ctrl.GetPosition() + (rect.width, rect.height)
        self.PopupMenu(KindSelectMenu(self), pos)


            
class KindSelectMenu(wx.Menu):
    def __init__(self, card):
        super(KindSelectMenu, self).__init__()
        self.card = card

        A_item = wx.MenuItem(self, wx.NewId(), "Assumption")
        C_item = wx.MenuItem(self, wx.NewId(), "Concept")
        R_item = wx.MenuItem(self, wx.NewId(), "Research")
        F_item = wx.MenuItem(self, wx.NewId(), "Fact")
        N_item = wx.MenuItem(self, wx.NewId(), "None")

        self.AppendItem(A_item)
        self.AppendItem(C_item)
        self.AppendItem(R_item)        
        self.AppendItem(F_item)
        self.AppendItem(N_item)

        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.ASSUMPTION_LBL), A_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.CONCEPT_LBL), C_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.RESEARCH_LBL), R_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.FACT_LBL), F_item)
        self.Bind(wx.EVT_MENU, lambda ev: self.OnSelect(ev, Content.DEFAULT_LBL), N_item)

        
    # Callbacks
    def OnSelect(self, ev, kind):
        # my parent is the control that displayed the menu
        if isinstance(self.card, Content):
            self.card.SetKind(kind)


######################
# Auxiliary functions
######################

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
