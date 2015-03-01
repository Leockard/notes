"""Unit test for threepy5.py (gui layer)."""

import threepy5.threepy5 as py5
import threepy5.gui.wxutils as wxutils
import unittest
import wx
from threepy5.gui import board as newgui
from frame_test import TestFrame


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

    def testNumberOfItems(self):
        """`KindSelectMenu` should have one item for every kind type, with the right label."""
        menu = newgui.ContentWin.KindButton.KindSelectMenu()

        menu_labels = set([it.Label for it in menu.MenuItems])

        self.assertEqual(menu.MenuItemCount, len(py5.Content.KIND_LBLS))
        self.assertEqual(menu_labels, set(py5.Content.KIND_LBLS))


    def tearDown(self):
        wx.CallAfter(self.app.Exit)
        # self.app.MainLoop()


### test Board class: drag selection, selection, new cards, fit to children
### test AutoSize class with a StaticBitmap


if __name__ == "__main__":
    unittest.main()
