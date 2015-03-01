"""Unit test for threepy5.py (gui layer)."""

import threepy5.threepy5 as py5
import threepy5.gui.wxutils as wxutils
import unittest
import wx
from threepy5.gui import board as newgui
from frame_test import TestFrame
from random import randint


class CardWinInit(unittest.TestCase):
    test_rect = (1,2,3,4)
    test_rating = 2
    test_kind = py5.Content.KIND_LBL_CONCEPT
    test_content = "this is content\n\nand this is more.\n\n\nrtag1: foo bar."
    test_collapsed = True
    test_title = "my title"
    test_path = "/home/leo/research/reading_notes/Kandle - Principles of Neural Science/brain.bmp"

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

        self.assertEqual(win.Rect, card.rect)

    def testContentWinInit(self):
        """`ContentWin` should properly track `Card` properties."""
        card = py5.Content()
        win = newgui.ContentWin(self.frame, card)

        card.rect = self.test_rect
        card.title = self.test_title
        card.kind = self.test_kind
        card.rating = self.test_rating
        card.content = self.test_content
        card.collapsed = self.test_collapsed

        self.assertEqual(win.Rect, card.rect)
        self.assertEqual(win._title.Value, card.title)
        self.assertEqual(win._kind.Label, card.kind)
        self.assertEqual(win._rating.Rating, card.rating)
        self.assertEqual(win._content.Value, card.content)
        self.assertEqual(win._collapsed, card.collapsed)

    def testHeaderWinInit(self):
        """`HeaderWin` should properly track `Header` properties."""
        card = py5.Header()
        win = newgui.HeaderWin(self.frame, card)

        card.rect = self.test_rect
        card.header = self.test_title

        self.assertEqual(win.Rect, card.rect)
        self.assertEqual(win._header.Value, card.header)

    def testImageWinInit(self):
        """`ImageWin` should properly track `Image` properties."""
        card = py5.Image()
        win = newgui.ImageWin(self.frame, card)

        card.rect = self.test_rect

        self.assertEqual(win.Rect, card.rect)

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
        board.AddCard("Content")
        board.AddCard("Header", pos=(10,10))
        board.AddCard("Image", pos=(20,20))

        self.assertEqual(len(board.Deck.cards), 3)
        self.assertEqual(len(board.Cards), 3)

    def testDragSelect(self):
        """`Board` should select all `Card`s under the drag-select rect."""
        board = newgui.Board(self.frame)
        board.AddCard("Header", pos=(10,10))
        board.AddCard("Image", pos=(20,20))

        # simulate a click-drag from (0,0) to (30,30)
        # which should end up selecting both cards
        board._drag_init(wx.Point(0,0))
        for i in range(29):
            board._drag_update(wx.Point(i,i))
        board._drag_end(wx.Point(30,30))
        self.assertEqual(len(board.Selection), 2)

        cont = board.AddCard("Content", pos=(200,200))
        board.Selector.Select(cont, new_sel=False)
        self.assertEqual(len(board.Selection), 3)

        board.Selector.Select(cont, new_sel=True)
        self.assertEqual(len(board.Selection), 1)

        board.Selector.UnselectAll()
        self.assertEqual(len(board.Selection), 0)

    def testDragMove(self):
        """`Board` should move all `Card`s when click-dragging."""
        board = newgui.Board(self.frame)
        cards = []
        start_pos = {}
        for i in range(50):
            pos = wx.Point(randint(1, 1000), randint(1, 1000))
            c = board.AddCard("Content", pos=pos)
            cards.append(c)
            start_pos[c] = pos
        board.Selector.SelectGroup(py5.CardGroup(members=cards))
        self.assertEqual(len(board.Selection), len(cards))

        # simulate a click-drag from the top left corner of the first card
        # to the point (1000, 1000)
        start = cards[0].Position + wx.Point(3,3)
        board._move_init(cards[0], wx.Point(*start))
        for i in range(999):
            board._move_update(wx.Point(i,i))
        pad = cards[0].BORDER_WIDTH
        board._move_end(start + wx.Point(1000,1000) + wx.Point(pad,pad))
        self.assertEqual(len(board.Selection), len(cards))

        final_pos = {}
        for c in board.Cards:
            final_pos[c] = c.Position

        for c in cards:
            self.assertEqual(start_pos[c] + (1000,1000), final_pos[c])

    def testFitToChildren(self):
        board = newgui.Board(self.frame)
        rect = board.Rect

        for a in xrange(100):
            c = board.AddCard("Content", pos=(randint(0,1000),randint(0,1000)))
            rect = rect.Union(c.Rect)

        bd_rect = wx.Rect(0,0,board.VirtualSize[0], board.VirtualSize[1])
        self.assertTrue(bd_rect.Contains(rect.TopLeft))
        self.assertTrue(bd_rect.Contains(rect.TopRight))
        self.assertTrue(bd_rect.Contains(rect.BottomLeft))
        self.assertTrue(bd_rect.Contains(rect.BottomRight))

    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()

### test Board dump and load
### test AutoSize class with a StaticBitmap


if __name__ == "__main__":
    unittest.main()
