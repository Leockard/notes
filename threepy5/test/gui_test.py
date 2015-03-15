# -*- coding: utf-8 -*-
"""Unit test for `threepy5` (gui layer)."""

import threepy5.threepy5 as py5
import threepy5.gui.wxutils as wxutils
import unittest
import wx
import threepy5.utils as utils
from threepy5.gui import board as newgui
from frame_test import TestFrame
from random import randint


class CardWinInit(unittest.TestCase):
    test_rect = utils.Rect(1,2,3,4)
    test_rating = 2
    test_kind = py5.Content.KIND_LBL_CONCEPT
    test_content = "this is content\n\nand this is more.\n\n\nrtag1: foo bar."
    test_collapsed = True
    test_title = "my title"
    test_path = "/home/leo/research/reading_notes/Kandel - Principles of Neural Science/brain.bmp"

    test_pts = [(1,2), (3,4), (-1,-1), (0,0), (2,-4)]
    test_lines = [test_pts, [(x+1, y-1) for x,y in test_pts]]

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testCardWinInit(self):
        """`CardWin` should properly track `Card` properties."""
        card = py5.Card()
        win = newgui.CardWin(self.frame, card)

        card.rect = self.test_rect

        self.assertEqual(list(win.Rect), list(card.rect))

    def testContentWinInit(self):
        """`ContentWin` should properly track `Card` properties."""
        card = py5.Content()
        win = newgui.ContentWin(self.frame, card)

        card.rect      = self.test_rect
        card.title     = self.test_title
        card.kind      = self.test_kind
        card.rating    = self.test_rating
        card.content   = self.test_content

        self.assertEqual(list(win.Rect), list(card.rect))
        self.assertEqual(win._title.Value, card.title)
        self.assertEqual(win._kind.Label, card.kind)
        self.assertEqual(win._rating.Rating, card.rating)
        self.assertEqual(win._content.Value, card.content)

    def testHeaderWinInit(self):
        """`HeaderWin` should properly track `Header` properties."""
        card = py5.Header()
        win = newgui.HeaderWin(self.frame, card)

        card.rect = self.test_rect
        card.header = self.test_title

        self.assertEqual(list(win.Rect), list(card.rect))
        self.assertEqual(win._header.Value, card.header)

    def testImageWinInit(self):
        """`ImageWin` should properly track `Image` properties."""
        card = py5.Image()
        win = newgui.ImageWin(self.frame, card)

        card.rect = self.test_rect

        self.assertEqual(list(win.Rect), list(card.rect))

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()


class testKindSelectMenu(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testNumberOfItems(self):
        """`KindSelectMenu` should have one item for every kind type, with the right label."""
        menu = newgui.ContentWin.KindButton.KindSelectMenu()

        menu_labels = set([it.Label for it in menu.MenuItems])

        self.assertEqual(menu.MenuItemCount, len(py5.Content.KIND_LBLS))
        self.assertEqual(menu_labels, set(py5.Content.KIND_LBLS))


    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()



class testBoard(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testAddCard(self):
        """`Board` should add all its `Card`s to its tracked `Deck`."""
        board = newgui.Board(self.frame)
        board.Deck.NewCard("Content")
        board.Deck.NewCard("Header", pos=(10,10))
        board.Deck.NewCard("Image", pos=(20,20))

        self.assertEqual(len(board.Deck.cards), 3)
        self.assertEqual(len(board.Cards), 3)

    def testDragSelect(self):
        """`Board` should select all `Card`s under the drag-select rect."""
        board = newgui.Board(self.frame)
        board.Deck.NewCard("Header", pos=(10,10))
        board.Deck.NewCard("Image", pos=(20,20))

        # simulate a click-drag from (0,0) to (30,30)
        # which should end up selecting both cards
        board._drag_start(wx.Point(0,0))
        for i in range(29):
            board._drag_update(wx.Point(i,i))
        board._drag_end(wx.Point(30,30))
        self.assertEqual(len(board.Selection), 2)

        board.Deck.NewCard("Content", pos=(200,200))
        cont = board.Cards[-1]
        board.Selector.Select(cont, new_sel=False)
        self.assertEqual(len(board.Selection), 3)

        board.Selector.Select(cont, new_sel=True)
        self.assertEqual(len(board.Selection), 1)

        board.Selector.UnselectAll()
        self.assertEqual(len(board.Selection), 0)

    def testDragMove(self):
        """`Board` should move all `Card`s when click-dragging."""
        board = newgui.Board(self.frame)
        num = 20
        cards = []
        start_pos = {}
        
        for i in range(num):
            pos = wx.Point(randint(1, 1000), randint(1, 1000))
            board.Deck.NewCard("Content", pos=pos)
            w = board.Cards[-1]
            cards.append(w)
            start_pos[w] = pos
            board.Selector.Select(w)
        self.assertEqual(len(board.Selection), len(cards))

        # simulate a click-drag from the top left corner of the first card
        # to the point (100, 100)
        start = cards[0].Position + wx.Point(3,3)
        board._move_start(cards[0], wx.Point(*start))
        for i in range(99):
            board._move_update(wx.Point(i,i))
        pad = cards[0].BORDER_WIDTH
        board._move_end(start + wx.Point(100,100) + wx.Point(pad,pad))
        self.assertEqual(len(board.Selection), len(cards))

        board.Scroll(0,0)
        final_pos = {}
        for c in board.Cards:
            final_pos[c] = c.Position

        for c in cards:
            self.assertEqual(start_pos[c] + (100,100), final_pos[c])

    def testFitToChildren(self):
        """`Board` should adequately enlarge its virtual size to fit all children."""
        board = newgui.Board(self.frame)
        rect = board.Rect

        for a in xrange(25):
            board.Deck.NewCard("Content", pos=(randint(0,1000),randint(0,1000)))
            c = board.Cards[-1]
            rect = rect.Union(c.Rect)

        bd_rect = wx.Rect(0,0,board.VirtualSize[0], board.VirtualSize[1])
        self.assertTrue(bd_rect.Contains(rect.TopLeft))
        self.assertTrue(bd_rect.Contains(rect.TopRight))
        self.assertTrue(bd_rect.Contains(rect.BottomLeft))
        self.assertTrue(bd_rect.Contains(rect.BottomRight))

    def testHorizontalArrange(self):
        """`Board` should adequately arrange its Cards."""
        board = newgui.Board(self.frame)
        num = 25

        for a in xrange(num):
            board.Deck.NewCard("Content", pos=(randint(0,100),randint(0,100)))
            board.Selector.Select(board.Cards[-1])
        self.assertTrue(len(board.Selection), num)

        board.ArrangeSelection(wx.HORIZONTAL)
        cards = board.Cards[:]
        cards.sort(key=lambda x: x.Position.x)

        pairs = [(cards[i], cards[i+1]) for i in range(len(cards)-1)]
        for c1, c2 in pairs:
            self.assertTrue(c1.Position.x <= c2.Position.x)
            self.assertTrue(c1.Position.y == c2.Position.y)

    def testVerticalArrange(self):
        """`Board` should adequately arrange its Cards."""
        board = newgui.Board(self.frame)
        num = 25

        for a in xrange(num):
            board.Deck.NewCard("Content", pos=(randint(0,100),randint(0,100)))
            board.Selector.Select(board.Cards[-1])
        self.assertTrue(len(board.Selection), num)

        board.ArrangeSelection(wx.VERTICAL)
        cards = board.Cards[:]
        cards.sort(key=lambda x: x.Position.y)

        pairs = [(cards[i], cards[i+1]) for i in range(len(cards)-1)]
        for c1, c2 in pairs:
            self.assertEqual(c1.Position.x, c2.Position.x)
            self.assertTrue(c1.Position.y <= c2.Position.y)

    def testSelectAll(self):
        """`Board` should correctly select all cards."""
        board = newgui.Board(self.frame)
        num = 25

        for a in xrange(num):
            board.Deck.NewCard("Content", pos=(randint(0,100),randint(0,100)))
        
        board.Selector.SelectAll()
        self.assertTrue(len(board.Selection), num)

    def testGroupSelected(self):
        """`Board` should correctly group all selected cards."""
        board = newgui.Board(self.frame)
        num = 25

        for a in xrange(num):
            board.Deck.NewCard("Content", pos=(randint(0,100),randint(0,100)))
        
        board.Selector.SelectAll()
        self.assertTrue(len(board.Selection), num)
        
        board.GroupSelected()
        self.assertTrue(board.Groups, 1)
        self.assertTrue(len(board.Groups[0].members), num)

    def testScrollToCard(self):
        """`Board` should put the whole `Card` into view."""
        board = newgui.Board(self.frame)
        num = 25

        for a in xrange(num):
            board.Deck.NewCard("Content", pos=(randint(0,100),randint(0,100)))
            w = board.Cards[-1]
            board.ScrollToCard(w)

            virt_rect = wx.Rect(board.Position.y, board.Position.x, board.VirtualSize[0], board.VirtualSize[1])
            self.assertTrue(virt_rect.Contains(w.Rect.TopLeft))
            self.assertTrue(virt_rect.Contains(w.Rect.TopRight))
            self.assertTrue(virt_rect.Contains(w.Rect.BottomLeft))
            self.assertTrue(virt_rect.Contains(w.Rect.BottomRight))

    def testCopyPaste(self):
        """`Board` should copy and paste cards correctly."""
        board = newgui.Board(self.frame)
        num = 25
        
        for a in xrange(num):
            class_ = ["Content", "Image", "Header"][randint(0,2)]
            board.Deck.NewCard(class_, pos=(randint(0,100),randint(0,100)))
        board.Selector.SelectAll()

        board.CopySelection()
        board.PasteFromClipboard()
        self.assertTrue(len(board.Deck.cards), 2 * num)

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()



class testSelectionManager(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testActive(self):
        """`SelectionManager` should handle its `Active` attribute according to focus and selection."""
        board = newgui.Board(self.frame)
        board.Deck.NewCard("Content")
        board.Deck.NewCard("Header", pos=(10,10))
        board.Deck.NewCard("Image", pos=(20,20))
        c1, c2, c3 = board.Cards

        self.assertFalse(board.Selector.Active)
        
        board.Selector.Select(c1)
        self.assertTrue(board.Selector.Active)
        self.assertTrue(board.Selector.HasFocus())
        self.assertEqual(board.Selector._last, c1)

        board.Selector.Select(c2, new_sel=False)
        self.assertTrue(board.Selector.Active)
        self.assertTrue(board.Selector.HasFocus())
        self.assertEqual(board.Selector._last, c2)

        board.Selector.Unselect(c1)
        self.assertTrue(board.Selector.Active)
        self.assertTrue(board.Selector.HasFocus())
        self.assertEqual(board.Selection, [c2])

        board.Selector.Select(c3)
        self.assertTrue(board.Selector.Active)
        self.assertTrue(board.Selector.HasFocus())
        self.assertEqual(board.Selector._last, c3)

        board.Selector.UnselectAll()
        self.assertTrue(board.Selector.Active)
        self.assertTrue(board.Selector.HasFocus())
        self.assertEqual(board.Selector._last, c3)
        self.assertEqual(board.Selection, [])
        
        board.Selector.Active = False
        self.assertFalse(board.Selector.Active)
        self.assertFalse(board.Selector.HasFocus())
        self.assertEqual(board.Selector._last, c3)
        self.assertEqual(board.Selection, [])
        self.assertEqual(c3, wxutils.GetCardAncestor(board.FindFocus()))

    def testSelectNearest(self):
        """`SelectionManager` should select the nearest card correctly."""
        board = newgui.Board(self.frame)
        board.Deck.NewCard("Content", pos=(15,15))
        board.Deck.NewCard("Content", pos=(15,200))
        board.Deck.NewCard("Content", pos=(300,15))
        board.Deck.NewCard("Content", pos=(300,200))

        tl, bl, tr, br = board.Cards
        tl.Card.title = "tl"
        bl.Card.title = "bl"
        tr.Card.title = "tr"
        br.Card.title = "br"

        board.Selector.Select(tl)
        self.assertEqual(len(board.Selection), 1)

        board.Selector.SelectNearest(wx.WXK_RIGHT, new_sel=True)
        self.assertEqual(board.Selection, [tr])

        board.Selector.SelectNearest(wx.WXK_DOWN, new_sel=True)
        self.assertEqual(board.Selection, [br])

        board.Selector.SelectNearest(wx.WXK_LEFT, new_sel=True)
        self.assertEqual(board.Selection, [bl])

        board.Selector.SelectNearest(wx.WXK_UP, new_sel=True)
        self.assertEqual(board.Selection, [tl])
        
    def testExtendSelection(self):
        """`SelectionManager` should extend the selection to the nearest card correctly."""
        board = newgui.Board(self.frame)
        board.Deck.NewCard("Content", pos=(15,15))
        board.Deck.NewCard("Content", pos=(15,200))
        board.Deck.NewCard("Content", pos=(300,15))
        board.Deck.NewCard("Content", pos=(300,200))
        tl, bl, tr, br = board.Cards
        
        board.Selector.Select(tl)
        self.assertEqual(len(board.Selection), 1)

        board.Selector.SelectNearest(wx.WXK_RIGHT, new_sel=False)
        self.assertEqual(board.Selection, [tl, tr])
        self.assertEqual(board.Selector._last, tr)

        board.Selector.SelectNearest(wx.WXK_DOWN, new_sel=False)
        self.assertEqual(board.Selection, [tl, tr, br])
        self.assertEqual(board.Selector._last, br)

        board.Selector.SelectNearest(wx.WXK_LEFT, new_sel=False)
        self.assertEqual(board.Selection, [tl, tr, br, bl])
        self.assertEqual(board.Selector._last, bl)

        board.Selector.SelectNearest(wx.WXK_UP, new_sel=False)
        self.assertEqual(board.Selection, [tl, tr, br, bl])
        self.assertEqual(board.Selector._last, bl)

    def testMoveSelection(self):
        """`SelectionManager` should move the selected cards correctly."""
        board = newgui.Board(self.frame)
        num = 10
        step = 10

        for i in range(num):
            board.Deck.NewCard("Content", pos=(randint(1, 10),randint(1, 10)))
            crd = board.Cards[-1]
            board.Selector.Select(crd, new_sel=False)
            init_pos = {c: c.Position for c in board.Selection}
            board.Selector.MoveSelection(step, step)
            for c in board.Selection:
                self.assertEqual(init_pos[c] + (step,step), c.Position)

    def testDeleteSelection(self):
        """`SelectionManager` should delete the selected cards correctly."""
        board = newgui.Board(self.frame)

        for i in range(10):
            c = board.Deck.NewCard("Content", pos=(randint(1, 10),randint(1, 10)))
            w = board.Cards[-1]
            board.Selector.Select(w)
            board.Selector.DeleteSelection()
            
            self.assertTrue(w not in board.Cards)
            self.assertTrue(w not in board.Selector.Selection)
            self.assertTrue(c not in board.Deck.cards)

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()        


class testImageWin(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testDragResize(self):
        pass
        # """ImageWin should correctly resize when its borders are click and dragged."""
        # board = newgui.Board(self.frame)
        # board.Deck.NewCard("Image", pos=(0,0))
        # w = board.Cards[-1]

        # w._resize_init()
        # for i in range(29):
        #     w._resize_update(True, wx.Point(i,i))
        # w._resize_end(wx.Point(30,30))

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()



class testEditText(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testColours(self):
        """`EditText` should correctly set and show its colours."""
        text = newgui.wxutils.EditText(self.frame)

        text.Input()
        self.assertEqual(text.BackgroundColour, text.Second)
        
        text.Static()
        self.assertEqual(text.BackgroundColour, text.First)
        

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()


        
class testAutoSize(unittest.TestCase):

    def setUp(self):
        self.app = wx.App()
        self.frame = TestFrame(None)
        # self.app.MainLoop()

    def testSize(self):
        """`AutoSize` should correctly set its size to fit its children."""
        auto = newgui.wxutils.AutoSize(self.frame)
        test_path = "/home/leo/research/reading_notes/Kandel - Principles of Neural Science/brain.bmp"
        bmp = wx.Bitmap(test_path)
        static = wx.StaticBitmap(auto, bitmap=bmp)
        auto.FitToChildren()

        virt_rect = wx.Rect(auto.Position.y, auto.Position.x, auto.VirtualSize[0], auto.VirtualSize[1])
        self.assertTrue(virt_rect.Contains(static.Rect.TopLeft))
        self.assertTrue(virt_rect.Contains(static.Rect.TopRight))
        self.assertTrue(virt_rect.Contains(static.Rect.BottomLeft))
        self.assertTrue(virt_rect.Contains(static.Rect.BottomRight))

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()
        
                
### finish testImageWin.testDragResize
### test coloured text
### test resize/rescale
### Workspace: switch board/canvas, ctrl+ / ctrl-, Workspace.Canvas.Annotation.lines (¿?)
###            while canvas is shown, selection manager should be active (no control focused)
###            and selection should be []
### CardView: add, set, restore, init
### DeckView: position, show/hide, Minicard position, ContentMini background colour
### CardWin _on_tab


if __name__ == "__main__":
    unittest.main()
