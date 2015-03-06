# -*- coding: utf-8 -*-
import wx
import wxutils
import json
import threepy5.utils as utils
from os import getcwd as oscwd
from threepy5.threepy5 import pub
from ast import literal_eval
import threepy5.threepy5 as py5

import wx.lib.expando as exp




######################
# Class Selectable
######################

class Selectable(wx.Panel):
    """A Selectable is the parent for all `Board` child windows that allow selection.

    The important feature of `Selectable` is that it consists of an underlying window, the
    "border" window, which is the same colour of the parent `Board`. When the `Selectable`
    is selected, the border window changes colour to signal selection. The border
    window has only one child, the `Selectable`'s "main" window, which holds the actual
    controls shown to the user. The "main" window is what one would normally assume is
    the real `Selectable` window. While this distinction is referred throughout the code as
    border/main windows, note the fact that the border window "IS" the `Selectable` (the
    `wx.Panel`), while the main window is its sole child. Most of the code is designed
    towards hiding this fact.

    While contrived, this is done due to the fact that in `wx`, the easiest way to paint a
    rectangle around a window (in this case, to show selection), is by putting it into a
    bigger window and setting that window's background, which in actuality looks like a
    paint-able border or shadow.

    We must take care to make the `Selectable` object behave appropriately according to its
    border and main windows. For example, we override `wx.Winwdow.Children` to return the
    main window's children, when it would normally return just the main window (since it is
    the only child of the border window).

    Given the particular organization of `Selectable` chidlren, the correct way to do add
    and show controls to this window is the following:

    1. create a `wx` control: `ctrl = wx.Window(parent=self)`, note the parent should be this `Selectable` object.
    2. create a `wx.Sizer` object: `box = wx.BoxSizer(...)`
    3. add the `ctrl` to the sizer: `box.Add(ctrl, ...)`, and
    4. set `box` as this `Selectable`'s `Sizer`, by doing `self.Sizer = box`.
    """
    BORDER_WIDTH = 2
    BORDER_THICK = 5
    SELECT_CL = (0, 0, 0, 0)

    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `Board`.
        """
        super(Selectable, self).__init__(parent)
        self._selected = False
        self._main = None
        self._init_border()


    ### init methods

    def _init_border(self):
        """Called from __init__ to Initialize this `Selectable`'s border window."""
        # remember that the border window is actually `Selectable` window
        # every reference to self will return attributes from the border window
        self.BorderColour = self.Parent.BackgroundColour

        # main is the window where the real controls will be placed
        main = wx.Panel(self, style=wx.BORDER_RAISED|wx.TAB_TRAVERSAL)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(main, proportion=1, flag=wx.ALL|wx.EXPAND, border=1)

        # since it's the main window that is displayed as a `Selectable`
        # we have to make it work like one: redirect all events
        main.Bind(wx.EVT_MOUSE_EVENTS, self._on_mouse_event)

        # use Sizer to get the "real" control sizer
        super(Selectable, self).SetSizer(box)
        self._main = main


    ### properties

    @property
    def Children(self):
        """The main window's children.

        `returns: ` a `list` of `wx.Window`s.
        """
        return self._main.Children

    @Children.setter
    def Children(self, ch):
        """Set the main window's children."""
        self._main.Children = ch

    @property
    def BackgroundColour(self):
        """The main window background colour.

        `returns: ` a `wx.Colour`.
        """
        return self._main.BackgroundColour

    @BackgroundColour.setter
    def BackgroundColour(self, cl):
        """Change the main window background colour."""
        self._main.BackgroundColour = cl

    @property
    def BorderColour(self):
        """The colour that the border window sets when this `Selectable` is selected."""
        return super(Selectable, self).BackgroundColour

    @BorderColour.setter
    def BorderColour(self, cl):
        """Set the colour that the border window colour sets when this `Selectable` is selected."""
        super(Selectable, self).SetBackgroundColour(cl)

    @property
    def Sizer(self):
        """The sizer for the main window. All controls should be added to this sizer."""
        return self._main.Sizer

    @Sizer.setter
    def Sizer(self, sizer):
        """Sets the sizer for the main window. Due to the particular arrangement of border/main
        windows, `sizer` will be the sizer of the main window, not the border. For correct
        showing of `sizer`'s children, we need to reparent them before setting `sizer`: any
        window in `sizer` that's a child of this `Selectable` window will be `Reparent`ed to
        the main window.
        """
        def reparent(sz):
            for child in sz.Children:
                if child.IsWindow():
                    child.Window.Reparent(self._main)
                elif child.IsSizer():
                    reparent(child.Sizer)

        reparent(sizer)
        self._main.Sizer = sizer

    @property
    def Selected(self):
        """The selection state of the window."""
        return self._selected

    @Selected.setter
    def Selected(self, val):
        """Select this window. Changes the border window colour."""
        if val:
            self.BorderColour = self.SELECT_CL
            self._selected = True
        else:
            self.BorderColour = self.Parent.BackgroundColour
            self._selected = False


    ### callbacks

    def _on_mouse_event(self, ev):
        """Listens to `wx.EVT_MOUSE_EVENTS` in the main window and raises it again
        with EventObject set to this window."""
        ev.EventObject = self
        # wx.Event does not implement a __set__ for Position
        ev.SetPosition(ev.Position + self._main.Position)
        self.EventHandler.ProcessEvent(ev)




######################
# Class CardWin
######################

class CardWin(Selectable):
    """Base  window class that tracks a `Card`. Just as `Card` itself, this is an abstract class."""
    DEFAULT_SZ = (20,20)

    def __init__(self, parent, card=None, style=0):
        """Constructor.

        * `parent: ` the parent `Board`.
        * `card: ` the `Card` object whose data we are showing.
        * `style: ` the style for this window.
        """
        super(Selectable, self).__init__(parent, style=style)
        self._selected = False
        self._init_border()
        self._init_UI()
        
        self.Card = card
        """The tracked `Card`."""

        py5.track(self._on_destroy, self.Card)


    ### init methods

    def _init_UI(self):
        """Called from __init__ to initialize this `CardWin`'s GUI and controls. Must override.
        """
        pass


    ### properties

    @property
    def Card(self):
        """The `Card` being tracked."""
        return self._card

    @Card.setter
    def Card(self, card):
        """Set the `Card` to track."""
        if card is None:
            return

        self._card = card
        self.Rect = wx.Rect(*card.rect)
        py5.subscribe("rect", self._update_rect, card)


    ### subscribers

    def _on_destroy(self):
        # wxpython objects are False after they are destroyed
        if self:
            self.Destroy()


    ### methods

    def _navigate_out(self, forward):
        """Simulate TAB navigation.

        * `forward: ` if `True`, try to navigate forward. `False` for backward.
        """
        for p in wxutils.GetAncestors(self):
            if hasattr(p, "Navigate"):
                p.Navigate(forward)


    ### subscribers: listen to changes in the underlying Card object

    def _update_rect(self, val):
        self.Rect = wx.Rect(val.left, val.top, val.width, val.height)


    ### callbacks

    def _on_tab(self, ev):
        """Not bound to any event, called by children when simulating TAB traversal."""
        ctrl = ev.GetEventObject()
        forward = not ev.ShiftDown()
        index = self.Children.index(ctrl)

        if index == 0 and not forward:
            self._navigate_out(forward)
        elif index == len(self.Children)-1 and forward:
            self._navigate_out(forward)
        else:
            # wx.Panel.Navigate
            self.Navigate(forward)





######################
# Class HeaderWin
######################

class HeaderWin(CardWin):
    """`CardWin` that holds a title or header. Consists of a single `EditText` control."""
    MIN_WIDTH = 150
    DEFAULT_SZ = py5.Header.DEFAULT_SZ

    def __init__(self, parent, card=None):
        """Constructor.

        * `parent: ` the parent `wx.Win`.
        * `card: ` the `Card` object whose data we are showing.
        """
        super(HeaderWin, self).__init__(parent, card=card, style=wx.TAB_TRAVERSAL)


    ### init methods

    def _init_UI(self):
        """Overridden from `CardWin`."""
        head = wxutils.EditText(self)
        # txt.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(head, proportion=0, flag=wx.ALL|wx.EXPAND, border=CardWin.BORDER_WIDTH)

        self.Sizer = vbox
        self._header = head


    ### properties

    @CardWin.Card.setter
    def Card(self, card):
        """Set the `Header` to track. Overridden from `CardWin`."""
        CardWin.Card.fset(self, card)
        if card is None:
            return

        self._header.Value = card.header
        # pub.subscribe(self._update_header, "UPDATE_HEADER")
        py5.subscribe("header", self._update_header, card)


    ### subscribers: listen to changes in the underlying Card object

    def _update_header(self, val)     : self._header.Value = val




##########################
# Class ImagePlaceHolder
##########################

class ImagePlaceHolder(Selectable):
    """A `Selectable` with a button to load an image from disk. Does not track any `Card`s."""
    DEFAULT_SZ = (50, 50)

    def __init__(self, parent):
        """Constructor.

        * `parent: ` the parent `Board`.
        """
        super(ImagePlaceHolder, self).__init__(parent)
        # only `CardWin`s call _init_UI, selectable doesn't!
        self._init_UI()

    def _init_UI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        btn = wx.BitmapButton(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_MISSING_IMAGE), size=self.DEFAULT_SZ)
        btn.Bind(wx.EVT_BUTTON, self._on_press)
        vbox.Add(btn, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)

        self.Sizer = vbox
        self._btn = btn

    def _on_press(self, ev):
        """Listens to `wx.EVT_BUTTON` from the "load image" button."""
        fd = wx.FileDialog(self, "Open", oscwd(), "", "All files (*.*)|*.*",
                           wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if fd.ShowModal() == wx.ID_OK:
            img = py5.Image(rect=self.Rect, path=fd.Path, scale=1.0)
            imgwin = ImageWin(self.Parent, card=img)
            self.Destroy()




######################
# Class ImageWin
######################

class ImageWin(CardWin):
    """A `CardWin` that holds a single image."""
    DEFAULT_SZ = py5.Image.DEFAULT_SZ

    def __init__(self, parent, card=None):
        """Constructor.

        * `parent: ` the parent `Board`.
        * `card: ` the `Card` object whose data we are showing.
        """
        super(ImageWin, self).__init__(parent, card=card)


    ### init methods

    def _init_UI(self):
        """Overridden from `CardWin`."""
        self._bmp = wx.StaticBitmap(self)

        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self._bmp, proportion=1, flag=wx.ALL|wx.EXPAND, border=self.BORDER_THICK)
        self.Sizer = box


    ### properties

    @CardWin.Card.setter
    def Card(self, card):
        """Set the `Image` to track. Overridden from `CardWin`."""
        CardWin.Card.fset(self, card)
        if card is None:
            return

        bmp = wx.Bitmap(card.path)
        self._bmp.SetBitmap(bmp)
        self.Fit()

        # only start listening to events once we have a Card
        # self._rating.Bind(wx.EVT_BUTTON, self._on_rating_pressed)





######################
# Class ContentWin
######################

class ContentWin(CardWin):
    """A `CardWin` that tracks a `Content`. Tags are not handled, since they are parsed
    and shown by `*View` objects.
    """
    # sizes
    DEFAULT_SZ   = py5.Content.DEFAULT_RECT[2:]
    COLLAPSED_SZ = (250, 30)

    # colours; thanks paletton.com!
    # see threepy5/img/Color palette by Paletton.com.html
    # downloaded on 26/feb/2015
    COLOURS = {}
    COLOURS[py5.DEFAULT_KIND]                = {"strong": (220, 218, 213, 255), "soft": (255, 255, 255, 255)}
    COLOURS[py5.Content.KIND_LBL_CONCEPT]    = {"strong": (149, 246, 214, 255), "soft": (242, 254, 250, 255)}
    COLOURS[py5.Content.KIND_LBL_ASSUMPTION] = {"strong": (255, 188, 154, 255), "soft": (255, 247, 243, 255)}
    COLOURS[py5.Content.KIND_LBL_RESEARCH]   = {"strong": (255, 232, 154, 255), "soft": (255, 252, 243, 255)}
    COLOURS[py5.Content.KIND_LBL_FACT]       = {"strong": (169, 163, 247, 255), "soft": (245, 244, 254, 255)}


    ##############################
    # helper class: TitleEditText
    ##############################

    # the order of the parents is important, since Expando
    # doesn't call super()!
    class TitleEditText(wxutils.EditText, exp.ExpandoTextCtrl):
        """The window for the title field."""
        FONT_SIZES = {1: 12, 2: 10, 3:8}

        def __init__(self, parent, size=(100,-1), first=None):
            """Constructor.

            * `parent: ` the parent `Content`.
            """
            super(ContentWin.TitleEditText, self).__init__(parent, size=size, first=first)
            self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
            self.Bind(exp.EVT_ETC_LAYOUT_NEEDED, self._on_layout_needed)

        def _on_key_down(self, ev):
            key = ev.GetKeyCode()
            if key == 9:
                # On TAB: instead of writing a "\t" char, let the card handle it
                wxutils.GetCardAncestor(self)._on_tab(ev)
            else:
                # here is where we call the expando magic
                self.Parent.Layout()
                ev.Skip()

        def _on_layout_needed(self, ev):
            # self.NumberOfLines always returns 1
            font = self.Font
            new_sz = self.FONT_SIZES.get(self.GetNumberOfLines(), self.FONT_SIZES[3])
            font.PointSize = new_sz
            self.Font = font


    ##############################
    # helper class: ContentText
    ##############################

    class ContentText(wxutils.ColouredText):
        """The main text field on a `ContentWin`."""

        def __init__(self, parent, style=wx.TE_RICH|wx.TE_MULTILINE):
            """Constructor.

            * `parent: ` the parent `Content`.
            * `style: ` by default is wx.TE_RICH|wx.TE_MULTILINE.
            """
            super(ContentWin.ContentText, self).__init__(parent, style=style)
            self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

        def _on_key_down(self, ev):
            key = ev.GetKeyCode()

            if ev.ControlDown():
                # bold
                # italic
                ev.Skip()

            else:
                if key == 9:
                    # On TAB: instead of writing a "\t" char, let the card handle it
                    wxutils.GetCardAncestor(self)._on_tab(ev)
                else:
                    ev.Skip()


    ##############################
    # helper class: KindButton
    ##############################

    class KindButton(wx.Button):
        """The `wx.Button` which selects the kind of a `ContentWin`."""

        DEFAULT_SZ = (33, 20)
        DEFAULT_FONT = (8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, False)

        DEFAULT_LBL = py5.DEFAULT_KIND
        BUTTON_LBL  = {kind: kind[0] for kind in py5.Content.KIND_LBLS}
        BUTTON_LBL[DEFAULT_LBL] = DEFAULT_LBL
        KIND_LBL    = {but: kind for kind, but in BUTTON_LBL.items()}


        #################################
        # helper class: KindSelectMenu
        #################################

        class KindSelectMenu(wx.Menu):
            """The `wx.Menu` that pops up from a `KindButton`."""

            def __init__(self):
                """Constructor."""
                super(ContentWin.KindButton.KindSelectMenu, self).__init__()

                for lbl in py5.Content.KIND_LBLS:
                    item = wx.MenuItem(self, wx.ID_ANY, lbl)
                    self.AppendItem(item)


        ##################
        # KindButton
        ##################

        def __init__(self, parent, label=DEFAULT_LBL, size=DEFAULT_SZ, style=wx.BORDER_NONE):
            """Constructor.

            * `parent: ` the parent `Content`.
            * `label: ` by default, is `DEFAULT_LBL`.
            * `style: ` by default, is `wx.BORDER_NONE`.
            """
            super(ContentWin.KindButton, self).__init__(parent, label=label, size=size, style=style)
            self.SetOwnFont(wx.Font(*self.DEFAULT_FONT))
            self.Bind(wx.EVT_BUTTON, self.OnPress)
            self.menu = self.KindSelectMenu()
            # don't Bind() to menu: let the containing ContentWin handle it
            # since EVT_MENU is a CommandEvent, the parent will get a EVT_MENU
            # event given that we do not handle it (or handle it but skip() it).

        @property
        def Label(self):
            """Get the current kind."""
            return self.KIND_LBL[super(ContentWin.KindButton, self).Label]

        @Label.setter
        def Label(self, kind):
            """Sets the current kind.

            * `kind: ` one of `Content.KIND_LBL_*`.
            """
            self.SetLabel(self.BUTTON_LBL[kind])

        def OnPress(self, ev):
            """Listens to `wx.EVT_BUTTON`."""
            self.PopupMenu(self.menu, (self.Rect.width, self.Rect.height))


    ################################
    # helper class: StarRating
    ################################

    class StarRating(wx.Button):
        """The `wx.Button` that displays the rating on a `Content` `Card`."""

        # thanks openclipart.org for the stars!
        # https://openclipart.org/detail/117079/5-star-rating-system-by-jhnri4
        # accessed on 26/feb/2015
        FILES = ["stars_0.png", "stars_1.png", "stars_2.png", "stars_3.png"]
        SIZE = (20, 35)
        BMPS = []
        MAX = py5.Content.RATING_MAX
        PATH = "/home/leo/code/threepy5/threepy5/img/"

        def __init__(self, parent):
            """Constructor.

            * `parent: ` the parent `Content`.
            """
            super(ContentWin.StarRating, self).__init__(parent, size=ContentWin.StarRating.SIZE, style=wx.BORDER_NONE|wx.BU_EXACTFIT)
            self.Rating = 0

            # the first instance loads all BMPs
            rat = ContentWin.StarRating
            if not rat.BMPS:
                rat.BMPS = [wx.Bitmap(self.PATH + self.FILES[n]) for n in range(self.MAX + 1)]

            # bindings
            # self.Bind(wx.EVT_BUTTON, self.OnPress)

        @property
        def Rating(self):
            """Get the current rating.

            `returns: ` an `int`.
            """
            return self._rating

        @Rating.setter
        def Rating(self, n):
            """Sets the rating, and sets the image to reflect it.

            * `n: ` the new rating.
            """
            self._rating = n
            if self.BMPS:
                self.SetBitmap(self.BMPS[n])


    ######################
    # ContentWin
    ######################

    def __init__(self, parent, card=None):
        """Constructor.

        * `parent: ` the parent `Board`.
        * `card: ` the `Card` object whose data we are showing.
        """
        super(ContentWin, self).__init__(parent, card=card)
        self._init_accels()

        self.Viewing = False
        """The viewing condition for this `Card`. This is `True` if this
        `ContentWin` is being inspected by a `*View` object."""

        self.CollapseEnabled = True
        """If `CollapseEnabled` is `True`, calling `Collapse` or `Uncollapse` will work normally.
        If it is `False` they will not do anything."""


    ### init methods

    def _init_UI(self):
        """Overridden from `CardWin`."""
        title   = self.TitleEditText(self, first=self.BackgroundColour)
        kind    = self.KindButton(self)
        rating  = self.StarRating(self)
        content = self.ContentText(self)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox1.Add(title,   proportion=1, flag=wx.LEFT|wx.ALIGN_CENTRE, border=CardWin.BORDER_THICK)
        hbox1.Add(kind,    proportion=0, flag=wx.ALL|wx.ALIGN_CENTRE, border=CardWin.BORDER_WIDTH)
        hbox1.Add(rating,  proportion=0, flag=wx.ALL|wx.EXPAND, border=0)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(content, proportion=1, flag=wx.EXPAND)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox1, proportion=0, flag=wx.ALL|wx.EXPAND, border=CardWin.BORDER_WIDTH)
        vbox.Add(hbox2, proportion=1, flag=wx.ALL|wx.EXPAND, border=CardWin.BORDER_THICK)

        self.Sizer = vbox
        self._title   = title                
        self._kind    = kind
        self._content = content
        self._rating  = rating
        self.Show()

    def _init_accels(self):
        """Initializes the `wx.AcceleratorTable`."""
        # ghost menu to generate menu item events and setup accelerators
        accels = []
        ghost = wx.Menu()

        coll = wx.MenuItem(ghost, wx.ID_ANY, "Toggle collapse")
        insp = wx.MenuItem(ghost, wx.ID_ANY, "Request view")
        self.Bind(wx.EVT_MENU, self._on_ctrl_u, coll)
        self.Bind(wx.EVT_MENU, self._on_ctrl_i, insp)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("U"), coll.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("I"), insp.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))


    ### properties

    @CardWin.Card.setter
    def Card(self, card):
        """Set the `Content` to track. Overridden from `CardWin`."""
        CardWin.Card.fset(self, card)
        if card is None:
            return

        self._title.Value    = card.title
        self._kind.Kind      = card.kind
        self._rating.Rating  = card.rating
        self._content.Value  = card.content
        # self._collapsed      = card.collapsed

        # pub.subscribe(self._update_title     , "UPDATE_TITLE")
        # pub.subscribe(self._update_kind      , "UPDATE_KIND")
        # pub.subscribe(self._update_rating    , "UPDATE_RATING")
        # pub.subscribe(self._update_content   , "UPDATE_CONTENT")
        # pub.subscribe(self._update_collapsed , "UPDATE_COLLAPSED")
        py5.subscribe("title", self._update_title, card)
        py5.subscribe("kind", self._update_kind, card)
        py5.subscribe("rating", self._update_rating, card)
        py5.subscribe("content", self._update_content, card)
        py5.subscribe("collapsed", self._update_collapsed, card)

        # only start listening to events once we have a Card
        self._rating.Bind(wx.EVT_BUTTON, self._on_rating_pressed)
        self._title.Bind(wx.EVT_TEXT, self._on_title_entry)
        self._content.Bind(wx.EVT_TEXT, self._on_content_entry)

        # since EVT_MENU is a CommandEvent, we will receive the EVT_MENU,
        # unless it's handled by the menu or the button and not skipped
        self.Bind(wx.EVT_MENU, self._on_kind_selected)

    @property
    def CaretPos(self):
        """Get the position where the caret (insertion point) is in the window.

        `returns: ` a tuple `(ctrl, pos)` where `ctrl` is a `wx.TextCtrl` instance,
        and `pos` is the position of the caret within that control. If other controls
        are focused or the `ContentWin`'s children are not focused at all, returns
        `(None, -1)`.
        """
        ctrl = self.FindFocus()
        pos = None

        if ctrl == self.title:
            pos = ctrl.InsertionPoint
        elif ctrl == self.content:
            pos = ctrl.InsertionPoint
        else:
            ctrl = None
            pos = -1

        return (ctrl, pos)

    @CaretPos.setter
    def CaretPos(self, ctrl, pos):
        """Accepts a tuple `(ctrl, pos)` where `ctrl` is a child `wx.TextCtrl` of this
        window and `pos` is the desired position of the caret within that control.
        """
        ctrl.SetFocus()
        ctrl.InsertionPoint = pos


    ### methods

    def ScrollToChar(self, pos):
        """Scrolls the content text control to put the char in the specified position in view.

        * `pos: ` the position for the specified character.
        """
        self.content.ShowPosition(pos)

    def _collapse(self, val):
        if self.CollapseEnabled:
            if val:
                self._content.Hide()
                self.Size = self.COLLAPSED_SZ
            else:
                self._content.Show()
                self.Size = self.DEFAULT_SZ

    def _set_colours(self):
        """Set all controls' colours according to the `kind`."""
        self.BackgroundColour          = self.COLOURS[self.Card.kind]["strong"]        
        self._content.BackgroundColour = self.COLOURS[self.Card.kind]["soft"]
        self._title.First              = self.COLOURS[self.Card.kind]["strong"]
        self._title.Second             = self.COLOURS[self.Card.kind]["soft"]
        self._title.Static()


    ### subscribers: listen to changes in the underlying Card object

    def _update_title(self, val)     : self._title.Value = val
    def _update_rating(self, val)    : self._rating.Rating = val
    def _update_content(self, val)   : self._content.Value = val
    def _update_collapsed(self, val) : self._collapse(val)
    def _update_kind(self, val):
        self._kind.Label = val;
        self._set_colours()


    ### callbacks
    

    ### controllers: callbacks that change the model's state

    def _on_kind_selected(self, ev): self.Card.kind = self._kind.menu.FindItemById(ev.Id).Label
    def _on_rating_pressed(self, ev): self.Card.IncreaseRating()

    def _on_ctrl_u(self, ev):
        self.Card.collapsed = not self.Card.collapsed

    def _on_ctrl_i(self, ev):
        print "ctrl i"

    # in the following callbacks, we need to set the value silently
    # otherwise, a new "UPDATE_*" message would be published and we would
    # generate a infinite recursion exception
    def _on_title_entry(self, ev): py5.Content.title.silently(self.Card, self._title.Value)
    def _on_content_entry(self, ev): py5.Content.content.silently(self.Card, self._content.Value)


######################
# Class Board
######################

class Board(wxutils.AutoSize):
    """`Board` holds a `Deck` and is the parent window of all `CardWin`s that
    track `Card`s from that `Deck`. It handles position, selection, arrangement,
    and listens to individual Cards' events, so that `Box` only needs to listen
    to `Deck` events.
    """
    WIN_PADDING = py5.Deck.PADDING
    BACKGROUND_CL = "#CCCCCC"
    MOVING_RECT_THICKNESS = 1


    ################################
    # maybe private!!!
    # RemoveCard  = RemoveDesc("Cards")
    # AddGroup    = AddDesc("Cards")
    # RemoveGroup = RemoveDesc("Cards")
    ################################


    ##################################
    # helper Class SelectionManager
    ##################################

    class SelectionManager(wx.Window):
        """`SelectionManager` is an invisible window that positions itself on the top left corner of a
        `Board` and gets focus every time a card is (or many cards are) selected. This is done to hide
        carets and selection hints from controls while selection is active. `SelectionManager` also
        manages card selection by managing key down events, such as arrow keys to move selection,
        shift + arrow keys to extend selection, etc.
        """
        SIZE = (1,1)
        POS  = (0,0)

        def __init__(self, parent):
            """Constructor.

            * `parent: ` the parent `wx.Window`, usually a `Deck`.
            """
            super(Board.SelectionManager, self).__init__(parent, size=self.SIZE, pos=self.POS)
            self.BackgroundColour = self.Parent.BackgroundColour
            
            self.Selection = []
            """The currently selected `Card`s"""

            self._last = None
            """The last `Card` added to the current selection."""

            self.Active = False
            
            self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)
            self.Bind(wx.EVT_SET_FOCUS, self._on_set_focus)
            self.Bind(wx.EVT_KILL_FOCUS, self._on_kill_focus)


        ### properties

        @property
        def Active(self):
            """`True` if we're doing a selection task. As of writing, this means having focus."""
            return self._active

        @Active.setter
        def Active(self, val):
            """If `val` is `True`, grab focus."""
            if val and not self.HasFocus():
                self.SetFocus()
            else:
                self.UnselectAll()
                if self._last:
                    self._last.SetFocus()
            self._active = val
        

        ### methods

        def Select(self, card, new_sel=False):
            """Selects `card`.

            * `card: ` a `Card`.
            * `new_sel: ` if `True`, unselects all other `Card`s before selecting `card`.
            If `False`, adds `card` to the current selection.
            """
            if not self.Active:
                self.Active = True

            # if new_sel, select only this card
            if new_sel:
                self.UnselectAll()
                self.Selection = [card]
                card.Selected = True
                self._last = card

            # else, select card only if it was not already selected
            elif card not in self.Selection:
                self.Selection.append(card)
                card.Selected = True
                self._last = card

        def SelectGroup(self, group, new_sel=True):
            """Select every `Card` in `group`.

            * `group: ` a `CardGroup`.
            * `new_sel: ` if `True`, unselects all other `Card`s before selecting.
            """
            # in case we are coming from a card that's inside the group,
            # we may want to return to that card after selection ends
            # so we select the group but restore the last card after
            crd = None
            if self._last and self._last.Card._id in group.members:
                crd = self._last

            if new_sel: self.UnselectAll()
            for id_ in group.members:
                w = self.Parent.GetWindowById(id_)
                if w:
                    self.Select(w)

            if crd:
                self._last = crd

        def SelectNearest(self, direc, new_sel=False):
            """Selects the nearest `CardWin` in the specified direction.
            
            * `direc: ` direc should be one of `wx.WXK_LEFT`, `wx.WXK_RIGHT`, `wx.WXK_UP`, or `wx.WXK_DOWN`.
            * `new_sel: ` if `True`, unselect all others and select only the next card.
            """
            nxt = self.Parent.Nearest(self._last, direc)
            if nxt:
                self.Select(nxt, new_sel)

        def SelectAll(self):
            """Selects every `CardWin` in the `Board`."""
            self.UnselectAll()
            for w in self.Parent.Cards:
                self.Select(w)

        def Unselect(self, card):
            """Removes `card` from the current selection.

            * `card: ` a `Card`.
            """
            if card in self.Selection:
                self.Selection.remove(card)
                card.Selected = False

        def UnselectAll(self):
            """Unselects all cards. Be sure to call this method instead of calilng
            `Unselect` on every card for proper cleanup.
            """
            while len(self.Selection) > 0:
                c = self.Selection[0]
                self.Unselect(c)

        def MoveSelection(self, dx, dy):
            """Move all selected `Card`s.
            
            `dx: ` the amount of pixels to move in the X direction.
            `dy: ` the amount of pixels to move in the Y direction.
            """
            for c in self.Selection:
                c.Card.MoveBy(dx, dy)

        def DeleteSelection(self):
            """Deletes every `Card` currently selected."""
            # remember to use while instead of for, since in every
            # iteration self.Selection is growing shorter
            while len(self.Selection) > 0:
                c = self.Selection[-1]
                self.Selection.remove(c)
                self.Parent.Deck.RemoveCard(c.Card)
                # don't remove the window from Parent.Cards because the Board
                # must be listening to the removal of the card from the Deck:
                # it must handle that itself
                # self.Parent.Cards.remove(c)


        ### callbacks

        def _on_set_focus(self, ev):
            self._active = True

        def _on_kill_focus(self, ev):
            self._active = False
            
        def _on_key_down(self, ev):
            if not self.Active or not self.Selection:
                ev.Skip()
                return
    
            key = ev.GetKeyCode()
    
            if ev.AltDown():
                bd = self.Parent
                if   key == wx.WXK_LEFT:
                    self.MoveSelection(-bd.SCROLL_STEP, 0)
                elif key == wx.WXK_RIGHT:
                    self.MoveSelection(bd.SCROLL_STEP, 0)
                elif key == wx.WXK_UP:
                    self.MoveSelection(0, -bd.SCROLL_STEP)
                elif key == wx.WXK_DOWN:
                    self.MoveSelection(0, bd.SCROLL_STEP)
                else:
                    ev.Skip()
    
            elif ev.ControlDown():
                if   key == ord("U"):
                    pass
                    # since collapsing takes away focus, store selection
                    windows = self.Selection[:]
    
                    # for the same reason, don't iterate over self.Selection
                    for c in [w.Card for w in windows]:
                        if isinstance(c, py5.Content):
                            c.collapsed = not c.collapsed
    
                    # restore selection
                    self.UnselectAll()
                    for w in windows:
                        self.Select(w)
                    
                elif key == ord("I"):
                    pass

                elif key == ord("G"):
                    self.Parent.GroupSelected()

                else:
                    ev.Skip()
    
            elif ev.MetaDown():
                ev.Skip()
    
            elif ev.ShiftDown():
                if   key == wx.WXK_LEFT:
                    self.SelectNearest(wx.WXK_LEFT, new_sel=False)
                elif key == wx.WXK_RIGHT:
                    self.SelectNearest(wx.WXK_RIGHT, new_sel=False)
                elif key == wx.WXK_UP:
                    self.SelectNearest(wx.WXK_UP, new_sel=False)
                elif key == wx.WXK_DOWN:
                    self.SelectNearest(wx.WXK_DOWN, new_sel=False)
                else:
                    ev.Skip()
    
            elif wxutils.IsFunctionKey(key):
                ev.Skip()
    
            else:
                if   key == wx.WXK_LEFT:
                    self.SelectNearest(wx.WXK_LEFT, new_sel=True)
                elif key == wx.WXK_RIGHT:
                    self.SelectNearest(wx.WXK_RIGHT, new_sel=True)
                elif key == wx.WXK_UP:
                    self.SelectNearest(wx.WXK_UP, new_sel=True)
                elif key == wx.WXK_DOWN:
                    self.SelectNearest(wx.WXK_DOWN, new_sel=True)
    
                elif key == wx.WXK_DELETE:
                    self.DeleteSelection()
                    
                # all other keys cancel selection
                else:
                    self.Ative = False



    ##############
    # Board
    ##############

    def __init__(self, parent, style=wx.BORDER_NONE):
        """Constructor.

        * `parent: ` the parent window.
        * `style: ` by default is `wx.BORDER_NONE`.
        """
        super(Board, self).__init__(parent, style=style)
        self.BackgroundColour = Board.BACKGROUND_CL
        self._init_accels()
        self._init_menu()

        self.Selector = Board.SelectionManager(self)
        """The `SelectionManager`."""

        self.Scale = 1.0
        """The current zoom scale."""

        self.Cards = []
        """The `CardWin`s in this `Board`."""

        # see the property Groups
        # self.Groups = []

        self._drag_init_pos = None
        """The position where we started dragging the mouse."""

        self._drag_cur_pos = None
        """The current position of the mouse, while dragging."""

        self._dragging = False
        """True when the user is dragging the mouse."""

        self._moving = False
        """True when the user is moving cards with the mouse."""

        self._moving_cards_pos = []
        """Stores position information while moving `Card`s."""

        self.Deck = py5.Deck()
        """The tracked `Deck`."""

        py5.subscribeList("cards", self._on_new_card, self._on_pop_card, self.Deck)

        self.Bind(wx.EVT_LEFT_DCLICK, self._on_left_double)
        self.Bind(wx.EVT_LEFT_DOWN, self._on_left_down)
        self.Bind(wx.EVT_LEFT_UP, self._on_left_up)
        self.Bind(wx.EVT_CHILD_FOCUS, self._on_child_focus)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, self._on_mouse_capture_lost)


    ### init methods

    def _init_accels(self):
        # we create an invisible menu so that we can bind its items to keystrokes
        accels = []
        ghost = wx.Menu()

        # new cards
        contr = wx.MenuItem(ghost, wx.ID_ANY, "New Card: Right")
        contb = wx.MenuItem(ghost, wx.ID_ANY, "New Card: Below")
        headr = wx.MenuItem(ghost, wx.ID_ANY, "New Header: Right")
        headb = wx.MenuItem(ghost, wx.ID_ANY, "New Header: Below")

        self.Bind(wx.EVT_MENU, self._on_ctrl_ret      , contr)
        self.Bind(wx.EVT_MENU, self._on_alt_ret       , headr)
        self.Bind(wx.EVT_MENU, self._on_ctrl_shft_ret , contb)
        self.Bind(wx.EVT_MENU, self._on_alt_shft_ret  , headb)

        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, wx.WXK_RETURN , contr.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_ALT,  wx.WXK_RETURN , headr.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_CTRL , wx.WXK_RETURN, contb.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_SHIFT|wx.ACCEL_ALT  , wx.WXK_RETURN, headb.GetId()))

        # copy/cut/paste: note these are different than the ones in _init_menu
        copy = wx.MenuItem(ghost, wx.ID_COPY, "Copy Selection")
        past = wx.MenuItem(ghost, wx.ID_PASTE, "Paste")
        
        self.Bind(wx.EVT_MENU, self._on_copy, copy)        
        self.Bind(wx.EVT_MENU, self._on_paste, past)

        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("C") , copy.GetId()))
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("V") , past.GetId()))

        # misc
        cycle = wx.MenuItem(ghost, wx.ID_ANY, "Cycle Selection")
        self.Bind(wx.EVT_MENU, self._on_esc, cycle)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, 27 , cycle.GetId()))

        selall = wx.MenuItem(ghost, wx.ID_ANY, "Select all")
        self.Bind(wx.EVT_MENU, self._on_ctrl_a, selall)
        accels.append(wx.AcceleratorEntry(wx.ACCEL_CTRL, ord("A") , selall.GetId()))

        self.SetAcceleratorTable(wx.AcceleratorTable(accels))

    def _init_menu(self):
        # note that none of these menu items have accelerators: see _init_accels
        menu = wx.Menu()
        self.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)

        # edit actions
        copy_it = wx.MenuItem(menu, wx.ID_COPY, "Copy Selection")
        self.Bind(wx.EVT_MENU, self._on_copy, copy_it)
        
        past_it = wx.MenuItem(menu, wx.ID_PASTE, "Paste")
        self.Bind(wx.EVT_MENU, self._on_paste, past_it)

        # # insert actions
        # cont_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Content")
        # self.Bind(wx.EVT_MENU, self._on_ctrl_ret, cont_it)
        # head_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Header")
        # self.Bind(wx.EVT_MENU, self._on_alt_ret, head_it)
        # img_it = wx.MenuItem(menu, wx.ID_ANY, "Insert Image")
        # self.Bind(wx.EVT_MENU, lambda ev: ImagePlaceHolder(self, pos=self._menu_pos), img_it)
        # # # tab actions
        # # close_it = wx.MenuItem(menu, wx.ID_ANY, "Close")
        # # self.Bind(wx.EVT_MENU, self.OnClose, close_it)

        menu.AppendItem(copy_it)
        menu.AppendItem(past_it)
        # menu.AppendItem(cont_it)
        # menu.AppendItem(head_it)
        # menu.AppendItem(img_it)
        # # menu.AppendSeparator()
        # # menu.AppendItem(close_it)

        self.menu = menu
        self._menu_pos = (0, 0)        


    ### properties

    @property
    def Groups(self):
        """The `CardGroup`s in this `Board`'s `Deck`."""
        return self.Deck.groups

    @property
    def Headers(self):
        """A list of all `HeaderWin`s in this `Board`."""
        return [h for h in self.Cards if isinstance(h, HeaderWin)]

    @property
    def Contents(self):
        """A list of all `ContentWin`s in this `Board`."""
        return [h for h in self.Cards if isinstance(h, ContentWin)]

    @property
    def Padding(self):
        """Returns `self.WIN_PADDING`, fixed for scale.

        `returns: ` the current scaled padding width in pixels, as a float.
        """
        return self.WIN_PADDING * self.Scale

    @property
    def Selection(self):
        """The `Card`s currently selected."""
        return self.Selector.Selection


    ### methods

    def GetCardById(self, id_):
        """Returns the `Card` with the specified id.

        * `id_: ` the id to look for.

        `returns: ` the requested `Card`, or None.
        """
        win = self.GetWindowById(id_)
        if win:
            return win.Card
        else:
            return None

    def GetWindowById(self, id_):
        """Returns the `CardWin` whose tracked `Card` has the specified id.

        * `id_: ` the id to look for.

        `returns: ` the requested `CardWin`, or None.
        """
        li = [win for win in self.Cards if win.Card._id == id_]
        if li: return li[0]
        else: return None

    def Nearest(self, card, direc):
        """Returns the nearest `Card` to `card` in the direction `direc`.

        * `card: ` a `Card` held by this object.
        * `direc: ` must be one of `wx.WXK_LEFT`, `wx.WXK_RIGHT`, `wx.WXK_UP`, or `wx.WXK_DOWN`.

        `returns: ` a `Card` or `None`.
        """
        # depending on the direction, we compare a different side
        # of the cards, as well as get the points whose distance
        # we're going to calculate in a different way
        if   direc == wx.WXK_LEFT:
            side  = lambda x: x.right
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetTopLeft()
        elif direc == wx.WXK_RIGHT:
            side  = lambda x: x.left
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetTopRight()
        elif direc == wx.WXK_UP:
            side  = lambda x: x.bottom
            getp1 = lambda x: x.GetTopLeft()
            getp2 = lambda x: x.GetBottomLeft()
        elif direc == wx.WXK_DOWN:
            side  = lambda x: x.top
            getp1 = lambda x: x.GetBottomLeft()
            getp2 = lambda x: x.GetTopLeft()

        # get those cards whose "side" is in the desired position with respect to card
        rect = card.Rect
        nxt = []
        if direc == wx.WXK_LEFT or direc == wx.WXK_UP:
            nxt = [c for c in self.Cards if side(c.Rect) < side(rect)]
        elif direc == wx.WXK_RIGHT or direc == wx.WXK_DOWN:
            nxt = [c for c in self.Cards if side(c.Rect) > side(rect)]
        else:
            return None

        # we're going to use getp2 to get a point in card and compare
        # it to the point got by getp1 on all the cards in nxt
        if nxt:
            # order them by distance and return the nearest one
            nxt.sort(key=lambda x: utils.dist2(getp1(x.Rect), getp2(rect)))
            return nxt[0]
        else:
            return None

    def ArrangeSelection(self, orient):
        """Arranges the selected cards according to `orient`. Don't use the _arrange_*
        methods directly, use this public method.

        * `orient: ` must be one of `wx.HORIZONTAL` or `wx.VERTICAL`.
        """
        if len(self.Selection) < 1:
            return

        if   orient == wx.HORIZONTAL:
            self._arrange_horizontally(self.Selection[:])
            self.FitToChildren()
            self.Selector.SetFocus()
        elif orient == wx.VERTICAL:
            self._arrange_vertically(self.Selection[:])
            self.FitToChildren()
            self.Selector.SetFocus()

    def GetContainingGroups(self, win):
        """Get a list of every `CardGroup` that contains the `Card` tracked by `win`.

        * `win: ` a `CardWin`.

        `returns: ` a list of `CardGroup`s.
        """
        return [g for g in self.Deck.groups if win.Card._id in g.members]

    def GroupSelected(self):
        """Creates a new `CardGroup` with the currently selected `Card`s."""
        sel = self.Selection
        if sel:
            self.Deck.AddGroup(py5.CardGroup([w.Card._id for w in sel]))

    def FindFocusOrSelection(self):
        """If there's a selection, returns the last selected `CardWin`. If there's no
        selection, returns the `CardWin` the cursor is currently in, or None."""
        result = None
        
        if self.Selection:
            result = self.Selector._last
        else:
            focus = self.FindFocus()
            if focus:
                ancestor = wxutils.GetCardAncestor(focus)
                if ancestor:
                    result = ancestor

        return result

    def CycleSelection(self):
        """After each call, a different object will be selected. Assuming the cursor
        is inside a `CardWin` child control, the first call will select that `CardWin`
        (and only that `CardWin`). The next call will select all windows in that
        `CardWin`'s `CardGroup`, if any. The next call, or if the original window wasn't
        member of any `CardGroup`, will select all the `CardWin`'s in the `Board`.
        The next call will again position the cursor where it was.

        `returns: ` `True` if the operation was successful (selection changed), or `False`.
        """
        result = True

        if len(self.Selection) > 1:
            # selecting a group: there's no more to select
            # so just cancel selection; when SelectionManager
            # is deactivated, it will return focus to the last
            # card that was selected
            self.Selector.UnselectAll()
            self.Selector.Active = False
            
        elif len(self.Selection) == 1:
            # selecting a card: select group (if any)
            win = self.Selection[0]
            if self.GetContainingGroups(win):
                self.Selector.SelectGroup(self.GetContainingGroups(win)[0], new_sel=True)
                
            # if no group, cancel selection
            else:
                self.Selector.UnselectAll()
                self.Selector.Active = False
                
        elif wxutils.GetCardAncestor(self.FindFocus()):
            # inside a card: select the card
            win = wxutils.GetCardAncestor(self.FindFocus())
            self.Selector.Select(win, True)

        else:
            # we didn't do anything!
            result = False

        return result

    def ScrollToCard(self, card):
        """Scroll in both directions so that `card` is fully in view.

        * `card: ` a `Card` to scroll to.
        """
        # call ScrollToPoint on opposite points of card
        rect = card.Rect
        pt = rect.BottomRight
        pt = self.CalcUnscrolledPosition(pt)
        self.ScrollToPoint(pt)

        # read Rect again since we may have scrolled the window
        rect = card.Rect
        pt = rect.TopLeft
        pt = self.CalcUnscrolledPosition(pt)
        self.ScrollToPoint(pt)

    def ScrollToPoint(self, pt):
        """Scroll in both directions so that `pt` is in view.

        * `pt: ` a (x, y) point.
        """
        view = self.GetViewStartPixels()
        sz = self.ClientSize
        rect = wx.Rect(view[0], view[1], sz.width, sz.height)

        if rect.Contains(pt):
            # nothing to do
            return

        scroll = False
        pad = self.Padding

        # if one of the argumets is wx.DefaultCoord,
        # we will not scroll in that direction
        ysc = wx.DefaultCoord
        xsc = wx.DefaultCoord
        
        # remember y coordinate grows downward
        if pt.x >= rect.right or pt.x <= rect.left:
            scroll = True
            xsc = pt.x - pad                  # where we want to go
            xsc /= self.SCROLL_STEP           # in scroll units
        if pt.y <= rect.top or pt.y >= rect.bottom:
            scroll = True
            ysc = pt.y - pad                  # where we want to go
            ysc /= self.SCROLL_STEP           # in scroll units

        if scroll:
            self.Scroll(xsc, ysc)

    def CopySelection(self):
        """Copies every selected `Card` to `wx.TheClipboard`."""
        if self.Selection and not wx.TheClipboard.IsOpened() and wx.TheClipboard.Open():
            data = []
            for c in self.Selection:
                data.append(c.Card.Dump())
    
            obj = wx.TextDataObject()
            obj.Text = str([json.dumps(d) for d in data])

            wx.TheClipboard.SetData(obj)
            wx.TheClipboard.Close()

    def PasteFromClipboard(self, pos=wx.DefaultPosition):
        """Pastes every `Card` currently in `wx.TheClipboard`."""
        if wx.TheClipboard.Open():
            obj = wx.TextDataObject()
            wx.TheClipboard.GetData(obj)

            # don't use eval()! Use ast.literal_eval() instead
            data = [json.loads(d) for d in literal_eval(obj.Text)]

            self.Selector.UnselectAll()
            for d in data:
                card = self.Deck.NewCard(d["class"])
                card.Load(d)
                self.Cards[-1].SetFocus()
                
                if pos == wx.DefaultPosition:
                    # default position: a step away from the original
                    card.Position = [i + self.Padding for i in d["pos"]]
                else:
                    card.Position = pos

                # the last window in self.Cards is the one tracking the
                # card we just created
                self.Selector.Select(self.Cards[-1])

            wx.TheClipboard.Close()

    def _arrange_horizontally(self, cards):
        """Arrange `cards` in a horizontal row, to the right of the left-most selected card.
        Don't use directly, use `ArrangeSelection`.
        """
        lefts = [c.Rect.left for c in cards]
        left = min(lefts)
        pivot = cards[lefts.index(left)]
        top = pivot.Rect.top
        cards.sort(key=lambda x: x.Rect.left)

        # note in every iteration we shift <left>
        for c in cards:
            c.Position = wx.Point(left, top)
            left = c.Rect.right + self.Padding

    def _arrange_vertically(self, cards):
        """Arrange `cards` in a vertical column, below of the top-most selected card.
        Don't use directly, use `ArrangeSelection`.
        """
        tops = [c.GetRect().top for c in cards]
        top = min(tops)
        pivot = cards[tops.index(top)]
        left = pivot.GetRect().left
        cards.sort(key=lambda x: x.GetRect().top)

        # note in every iteration we shift <top>
        for c in cards:
            c.Position = wx.Point(left, top)
            top = c.Rect.bottom + self.Padding

    def _paint_rect(self, rect, thick=MOVING_RECT_THICKNESS, style=wx.SOLID, refresh=True):
        """Paints a rectangle over this window. Used for click-dragging.

        * `rect: ` a `wx.Rect`.
        * `thick: ` line thickness. By default, is `Board.MOVING_RECT_THICKNESS`.
        * `style: ` a `dc.Pen` style. Use `wx.TRANSPARENT` to erase a rectangle.
        * `refresh: ` whether to call `Refresh` after the rectangle is painted.
        """
        dc = wx.ClientDC(self)
        dc.Brush = wx.Brush(self.GetBackgroundColour())      # background
        dc.Pen = wx.Pen("BLACK", thick, style)               # foreground
        dc.DrawRectangle(rect[0], rect[1], rect[2], rect[3])
        if refresh: self.RefreshRect(rect)

    def _paint_card_rect(self, card, pos, thick=MOVING_RECT_THICKNESS, style=wx.SOLID, refresh=True):
        """Paints a rectangle just big enough to encircle `card`.

        * `card: ` a `Card`.
        * `pos: ` where to paint the rectangle.
        * `thick: ` line thickness. By default, is `Board.MOVING_RECT_THICKNESS`.
        * `style: ` a `dc.Pen` style. Use `wx.TRANSPARENT` to erase a rectangle.
        * `refresh: ` whether to call `Refresh` after the rectangle is painted.
        """
        x, y, w, h = card.Rect
        rect = wx.Rect(pos[0], pos[1], w, h)
        rect = rect.Inflate(2 * thick, 2 * thick)
        self._paint_rect(rect, thick=thick, style=style, refresh=refresh)

    def _erase_card_rect(self, card, pos, thick=MOVING_RECT_THICKNESS, refresh=True):
        """Erases a rectangle drawn by PaintCardRect().

        * `card: ` a `Card`.
        * `pos: ` where to paint the rectangle.
        * `thick: ` line thickness. By default, is `Board.MOVING_RECT_THICKNESS`.
        * `refresh: ` whether to call `Refresh` after the rectangle is painted.
        """
        x, y, w, h = card.Rect
        rect = wx.Rect(pos[0], pos[1], w, h)
        rect = rect.Inflate(2 * thick, 2 * thick)
        self._paint_rect(rect, thick=thick, style=wx.TRANSPARENT, refresh=refresh)

    def _drag_init(self, pos):
        """Prepare for drag-select.

        * `pos: ` mouse click position, relative to the Board.
        """
        self.Selector.UnselectAll()
        self.Selector.SetFocus()

        self._drag_init_pos = pos
        self._drag_cur_pos = pos
        # note we don't set self._dragging to True until the user actually drags the
        # mouse, this is done in self._on_drag_motion
        
    def _drag_update(self, pos):
        """Called on every wx.EVT_MOTION while we are dragging."""
        self._dragging = True

        # erase the last one selection rect
        self._paint_rect(wx.Rect(self._drag_init_pos[0], self._drag_init_pos[1],
                                 self._drag_cur_pos[0],  self._drag_cur_pos[1]),
                         style = wx.TRANSPARENT,
                         refresh = False)

        # and draw the current one
        final_pos = pos - self._drag_init_pos
        self._paint_rect(wx.Rect(self._drag_init_pos[0], self._drag_init_pos[1],
                                 final_pos[0], final_pos[1]),
                         refresh = False)

        self._drag_cur_pos = final_pos

    def _drag_end(self, pos):
        """Clean up the drag-select task. Called on wx.EVT_LEFT_UP while we are dragging."""
        # erase the last selection rect
        final_rect = wxutils.MakeEncirclingRect(self._drag_init_pos, self._drag_init_pos + self._drag_cur_pos)
        self._paint_rect(final_rect, style=wx.TRANSPARENT)

        self._dragging = False
        self._drag_init_pos = None
        self._drag_cur_pos = None
        self.FitToChildren()
        self.Selector.SetFocus()

        selected = [c for c in self.Cards if c.Rect.Intersects(final_rect)]
        self.Selector.UnselectAll()
        for w in selected:
            self.Selector.Select(w)

    def _move_init(self, card, pos):
        """Prepare for moving the selected cards.

        * `card: ` the clicked card that will (probably) be moved.
        * `pos: ` mouse click position, relative to the Board.
        """
        self.Selector.Select(card)

        self._moving_cards_pos = []
        for c in self.Selection:
            # self._moving_cards_pos has tuple elements of the form:
            # (card, pos w.r.t. the original click, pos w.r.t. the board)
            self._moving_cards_pos.append((c, c.Position - pos, c.Position))

    def _move_update(self, cur_pos):
        """Called on every wx.EVT_MOTION while we are moving cards."""
        self._moving = True
        
        # draw a rectangle around each card while moving
        for c, orig, pos in self._moving_cards_pos:
            # order is important
            self._erase_card_rect(c, pos, refresh=False)
            self._paint_card_rect(c, cur_pos + orig)

    def _move_end(self, final_pos):
        """Clean up the move task. Called on wx.EVT_LEFT_UP while we are moving."""
        for c, orig, pos in self._moving_cards_pos:
            # erase the last floating rect
            self._erase_card_rect(c, pos)

            # set the `Card` position, not the `CardWin`!
            c.Card.Position = final_pos + orig - (c.BORDER_WIDTH, c.BORDER_WIDTH)

        self._moving = False            
        self._moving_cards_pos = []

        
    ### subscribers

    def _on_new_card(self, val):
        win = globals()[val.__class__.__name__ + "Win"](self, card=val)
        # win.Stretch(self.scale)

        win.Bind(wx.EVT_LEFT_DOWN, self._on_card_left_down)
        # win.Bind(card.Card.EVT_COLLAPSE, self.OnCardCollapse)
        # win.Bind(card.Card.EVT_REQUEST_VIEW, self.OnCardRequest)
        for ch in win.Children:
            ch.Bind(wx.EVT_LEFT_DOWN, self._on_card_child_left_down)

        # make enough space and breathing room for the new card
        self.FitToChildren(pad=self.Padding * 2)

        # make sure the new card is visible
        # if scroll:
        #     rect = win.Rect
        #     brd = self.Rect
        #     if rect.bottom > brd.bottom or rect.right > brd.right or rect.left < 0 or rect.top < 0:
        #         self.ScrollToCard(win)

        self.Cards.append(win)
        # self.Selector.Active = False
        win.SetFocus()

    def _on_pop_card(self, val):
        win = [w for w in self.Cards if w.Card is val]
        for w in win:
            self.Cards.remove(w)
            w.Card = None
            w.Hide()
            w.Destroy()
        

    ### callbacks

    def _on_right_down(self, ev):
        self._menu_pos = ev.Position
        self.PopupMenu(self.menu, ev.Position)

    def _on_ctrl_ret(self, ev):
        pivot = self.FindFocusOrSelection()
        if pivot:
            self.Deck.NewCard("Content", pivot=pivot.Card, below=False)
        else:
            self.Deck.NewCard("Content", pivot=None, below=False)

    def _on_ctrl_shft_ret(self, ev):
        pivot = self.FindFocusOrSelection()
        if pivot:
            self.Deck.NewCard("Content", pivot=pivot.Card, below=True)
        else:
            self.Deck.NewCard("Content", pivot=None, below=True)
        
    def _on_alt_ret(self, ev):
        pivot = self.FindFocusOrSelection()
        if pivot:
            self.Deck.NewCard("Header", pivot=pivot.Card, below=False)
        else:
            self.Deck.NewCard("Header", pivot=None, below=False)
        
    def _on_alt_shft_ret(self, ev):
        pivot = self.FindFocusOrSelection()
        if pivot:
            self.Deck.NewCard("Header", pivot=pivot.Card, below=True)
        else:
            self.Deck.NewCard("Header", pivot=None, below=True)
        
    def _on_left_double(self, ev):
        pos = [i / self.Scale for i in ev.Position]
        self.Deck.NewCard("Content", pos=pos)

    def _on_left_down(self, ev):
        self._drag_init(ev.Position)
        self.Bind(wx.EVT_MOTION, self._on_drag_motion)

    def _on_drag_motion(self, ev):
        """Listens to `wx.EVT_MOTION` events from this object, only when the user is click-dragging."""
        if ev.Dragging() and not self._moving:
            self._drag_update(ev.Position)

    def _on_left_up(self, ev):
        if self._dragging:
            self._drag_end(ev.Position)
        self.Unbind(wx.EVT_MOTION)

    def _on_child_focus(self, ev):
        # important to avoid automatically scrolling to focused child
        pass 

    def _on_mouse_capture_lost(self, ev):
        self.ReleaseMouse()

    def _on_copy(self, ev):
        self.CopySelection()
        
    def _on_paste(self, ev):
        self.PasteFromClipboard(self._menu_pos)

    def _on_esc(self, ev):
        if not self.CycleSelection():
            ev.Skip()

    def _on_ctrl_a(self, ev):
        self.Selector.SelectAll()

    def _on_card_left_down(self, ev):
        """Listens to `wx.EVT_LEFT_DOWN` events from every `Card`."""
        # pass the position relative to the Board
        pos = ev.EventObject.Position + ev.Position
        self.Bind(wx.EVT_LEFT_UP, self._on_card_left_up)
        self.Bind(wx.EVT_MOTION, self._on_moving_motion)
        self.CaptureMouse()
        self._move_init(ev.EventObject, pos)

    def _on_card_child_left_down(self, ev):
        self.Selector.Active = False
        # ev.EventObject.SetFocus()
        ev.Skip()

    def _on_moving_motion(self, ev):
        """Listens to `wx.EVT_MOTION` events from this object, only when the user is moving cards."""
        if ev.Dragging() and not self._dragging:
            self._move_update(ev.Position)

    def _on_card_left_up(self, ev):
        if self._moving:
            self._move_end(ev.Position)
        self.Unbind(wx.EVT_LEFT_UP)
        self.Unbind(wx.EVT_MOTION)
        self.ReleaseMouse()
        

        


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
for field in dir(wx.Panel)   : __pdoc__['Selectable.%s' % field] = None
for field in dir(Selectable) : __pdoc__['CardWin.%s' % field] = None
for field in dir(CardWin)    : __pdoc__['HeaderWin.%s' % field] = None
for field in dir(CardWin)    : __pdoc__['ImageWin.%s' % field] = None
for field in dir(CardWin)    : __pdoc__['ContentWin.%s' % field] = None
for field in dir(Selectable) : __pdoc__['ImagePlaceHolder.%s' % field] = None


# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in Selectable.__dict__.keys():
    if 'Selectable.%s' % field in __pdoc__.keys():
        del __pdoc__['Selectable.%s' % field]
for field in CardWin.__dict__.keys():
    if 'CardWin.%s' % field in __pdoc__.keys():
        del __pdoc__['CardWin.%s' % field]
for field in HeaderWin.__dict__.keys():
    if 'HeaderWin.%s' % field in __pdoc__.keys():
        del __pdoc__['HeaderWin.%s' % field]
for field in ImageWin.__dict__.keys():
    if 'ImageWin.%s' % field in __pdoc__.keys():
        del __pdoc__['ImageWin.%s' % field]
for field in ContentWin.__dict__.keys():
    if 'ContentWin.%s' % field in __pdoc__.keys():
        del __pdoc__['ContentWin.%s' % field]
for field in ImagePlaceHolder.__dict__.keys():
    if 'ImagePlaceHolder.%s' % field in __pdoc__.keys():
        del __pdoc__['ImagePlaceHolder.%s' % field]
