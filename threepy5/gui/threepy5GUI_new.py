# -*- coding: utf-8 -*-

import wx
import wxutils
from os import getcwd as oscwd
from threepy5.threepy5 import pub
import threepy5.threepy5 as py5


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
        self.Rect = card.rect
        # pub.subscribe(self._update_rect, "UPDATE_RECT")
        py5.subscribe("rect", self._update_rect, card)


    ### methods

    def _navigate_out(self, forward):
        """Simulate TAB navigation.

        * `forward: ` if `True`, try to navigate forward. `False` for backward.
        """
        for p in wxutils.GetAncestors(self):
            if hasattr(p, "Navigate"):
                p.Navigate(forward)


    ### subscribers: listen to changes in the underlying Card object

    def _update_rect(self, val): self.Rect = val


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
    DEFAULT_SZ = (150, 32)

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
    DEFAULT_SZ = (50, 50)

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
    DEFAULT_SZ   = (250, 150)
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

    class TitleEditText(wxutils.ColouredText):
        """The window for the title field."""

        def __init__(self, parent):
            """Constructor.

            * `parent: ` the parent `Content`.
            """
            super(ContentWin.TitleEditText, self).__init__(parent)
            self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

        def _on_key_down(self, ev):
            key = ev.GetKeyCode()
            if key == 9:
                # On TAB: instead of writing a "\t" char, let the card handle it
                wxutils.GetCardAncestor(self)._on_tab(ev)
            else:
                ev.Skip()

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
        # controls
        title   = self.TitleEditText(self)
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
        self._kind    = kind
        self._title   = title
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
        # self.Bind(wx.EVT_MENU, self.OnCtrlU, coll)
        # self.Bind(wx.EVT_MENU, self.OnCtrlI, insp)
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
        self._collapsed      = card.collapsed

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

    def Collapse(self):
        """Hides the content text and displays only the title (and rating). A "minimization" of sorts.
        This will only work if `CollapseEnabled` is `True`.
        """
        if self.CollapseEnabled and not self._collapsed:
            self.content.Hide()
            self._collapsed = True
            self.Size = self.COLLAPSED_SZ

            # # raise the event
            # event = self.CollapseEvent(id=wx.ID_ANY, collapsed=True)
            # event.SetEventObject(self)
            # self.GetEventHandler().ProcessEvent(event)

    def Uncollapse(self):
        """Shows the content text and returns to normal size.
        This will only work if `CollapseEnabled` is `True`.
        """
        if self.CollapseEnabled and self._collapsed:
            self._content.Show()
            self.Size = self.DEFAULT_SZ

            # # raise the event
            # event = self.CollapseEvent(id=wx.ID_ANY, collapsed=False)
            # event.SetEventObject(self)
            # self.GetEventHandler().ProcessEvent(event)

    def ToggleCollapse(self):
        """If the window is collapsed, uncollapsed it, or the other way around."""
        if self._collapsed:
            self.Uncollapse()
        else:
            if self.FindFocus() == self._content:
                self.title.SetFocus()
            self.Collapse()

    def _set_colours(self):
        """Set all controls' colours according to the `kind`."""
        self.BackgroundColour = self.COLOURS[self.Card.kind]["strong"]
        # self._title.SetFirstColour(self.COLOURS[kind]["border"])
        # self._title.SetSecondColour(self.COLOURS[kind]["bg"])
        self._content.BackgroundColour = self.COLOURS[self.Card.kind]["soft"]


    ### subscribers: listen to changes in the underlying Card object

    def _update_title(self, val)     : self._title.Value = val
    def _update_rating(self, val)    : self._rating.Rating = val
    def _update_content(self, val)   : self._content.Value = val
    def _update_collapsed(self, val) : self._collapsed = val
    def _update_kind(self, val):
        self._kind.Label = val;
        self._set_colours()


    ### callbacks: listen to wx.EVT_* events


    ### controllers: callbacks that change the model's state

    def _on_kind_selected(self, ev): self.Card.kind = self._kind.menu.FindItemById(ev.Id).Label
    def _on_rating_pressed(self, ev): self.Card.IncreaseRating()

    # in the following callbacks, we need to set the value silently
    # otherwise, a new "UPDATE_*" message would be published and we would
    # generate a infinite recursion exception
    def _on_title_entry(self, ev): py5.Content.title.silent(self.Card, self._title.Value)
    def _on_content_entry(self, ev): py5.Content.content.silent(self.Card, self._content.Value)



######################
# Class AutoSize
######################

class AutoSize(wx.ScrolledWindow):
    """`AutoSize` is a `wx.ScrolledWindow` that automates the process of setting
    up a window which has a "virtual size". In `wx`, "virtual size" is the size of
    the underlying contents of the window, while "size" is the screen real estate
    it occupies). `AutoSize` also holds various methods to facilitate the management
    of virtual size.
    """
    SCROLL_STEP = 10

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(AutoSize, self).__init__(*args, **kwargs)
        self.Bind(wx.EVT_SIZE, self.__on_size)
        self.SetScrollRate(self.SCROLL_STEP, self.SCROLL_STEP)

        self._virtual_sz = wx.Size(0, 0)
        if "size" in kwargs.keys():
            sz = kwargs["size"]
            self._virtual_sz = wx.Size(sz[0], sz[1])


    ### methods

    def UpdateVirtualSize(self, sz):
        """Recompute the virtual size.

        * `sz: ` a `(width, height)` size tuple. If it contains a dimension that
        is bigger than the current virtual size, change the virtual size.
        """
        flag = False
        virt_sz = self._virtual_sz

        if sz.x > virt_sz.x:
            flag = True
            self._virtual_sz = wx.Size(sz.x, self._virtual_sz.y)
        if sz.y > virt_sz.y:
            flag = True
            self._virtual_sz = wx.Size(self._virtual_sz.x, sz.y)

        if flag:
            self.VirtualSize = self._virtual_sz

    def FitToChildren(self, pad=0):
        """Call to set the virtual size to fit the children. If there are
        no children, keeps the virtual size as it is (don't shrink). If the
        window is resized, the new size will be enough to fit all children,
        plus a padding.

        * `pad: ` additional padding in case the window is resized.
        """
        if len(self.Children) == 0:
            return

        # set view start at (0,0) to get absolute cordinates
        shown = self.IsShown()
        if shown: self.Hide()
        view = self.GetViewStart()
        self.Scroll(0, 0)

        # calculate children extension
        rects = [c.Rect for c in self.Children]
        right  = max(rects, key=lambda r: r.right).right
        bottom = max(rects, key=lambda r: r.bottom).bottom

        # compare and update
        sz = self._virtual_sz
        if right  > sz.x: sz = wx.Size(right + pad, sz.y)
        if bottom > sz.y: sz = wx.Size(sz.x, bottom + pad)
        self._virtual_sz = sz
        self.VirtualSize = self._virtual_sz

        # return to the previous scroll position
        self.Scroll(view[0], view[1])
        if shown: self.Show()

    def ExpandVirtualSize(self, dx, dy):
        """Enlarge the virtual size.

        * `dx: ` pixels to add in the X direction.
        * `dy: ` pixels to add in the Y direction.
        """
        size = wx.Size(self._virtual_sz.x + dx, self._virtual_sz.y + dy)
        self._virtual_sz = size
        self.VirtualSize = size

    def GetViewStartPixels(self):
        """Return the point at which the current view starts, ie, the absolute
        coordinates of the point that, due to the scrollbars, currently lies at `(0,0)`.
        """
        view = self.GetViewStart()
        return wx.Point(*[v * self.SCROLL_STEP for v in view])


    ### Callbacks

    def __on_size(self, ev):
        """Listens to `wx.EVT_SIZE`."""
        self.UpdateVirtualSize(ev.GetSize())
        ev.Skip()




######################
# Class Board
######################

class Board(AutoSize):
    """`Board` holds a `Deck` and is the parent window of all `CardWin`s that
    track `Card`s from that `Deck`. It handles position, selection, arrangement,
    and listens to individual Cards' events, so that `Box` only needs to listen
    to `Deck` events.
    """
    WIN_PADDING = 15
    BACKGROUND_CL = "#CCCCCC"


    ################################
    # maybe private!!!
    # AddCard     = AddDesc("Cards")
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
            # self.cards = []
            # self.last = None
            # self.active = False
            # self.SetBackgroundColour(self.GetParent().GetBackgroundColour())


                        
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
        
        self.Deck = py5.Deck()
        self.Cards = []
        self.Groups = []
        self.Scale = 1.0
        self.Selector = Board.SelectionManager(self)
        # self._moving_cards_pos = []
        # self._drag_select = False

        self.Bind(wx.EVT_LEFT_DCLICK, self._on_left_dclick)

        
    ### init methods

    def _init_accels(self):
        accels = []
    
    def _init_menu(self):
        self._menu_pos = (0, 0)

    
    ### properties

    @property
    def Headers(self):
        """Get a list of all `HeaderWin`s in this `Board`."""
        return [h for h in self.Cards if isinstance(h, HeaderWin)]

    @property
    def Contents(self):
        """Get a list of all `ContentWin`s in this `Board`."""
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

    def AddCard(self, subclass, pos=wx.DefaultPosition, scroll=False):
        """Create a new `CardWin` of type `subclass`.

        * `subclass` the `__name__` of a `CardWin` subclass.
        * `pos: ` the position of the new `CardWin`.
        * `scroll: ` if `True`, scroll the `Board` so that the new `CardWin` is in view.

        `returns: ` the new `CardWin`.
        """
        # create the new card with the unscaled position
        pos = [i / self.Scale for i in pos]

        # if   subclass == "Content" : new = card.Content(self, pos=pos)
        # elif subclass == "Header"  : new = card.Header(self, pos=pos)
        # elif subclass == "Image"   : new = card.Image(self, pos=pos)

        cardclass = getattr(py5, subclass)
        winclass  = globals()[subclass + "Win"]
        sz = winclass.DEFAULT_SZ
        
        card = cardclass(rect=(pos[0], pos[1], sz[0], sz[1]))
        win = winclass(self, card)
        
        #win.Stretch(self.scale)

        # set bindings for every card
        # win.Bind(wx.EVT_LEFT_DOWN, self.OnCardLeftDown)
        # win.Bind(wx.EVT_CHILD_FOCUS, self.OnCardChildFocus)
        # win.Bind(card.Card.EVT_DELETE, self.OnCardDelete)
        # win.Bind(card.Card.EVT_COLLAPSE, self.OnCardCollapse)
        # win.Bind(card.Card.EVT_REQUEST_VIEW, self.OnCardRequest)
        # for ch in win.GetChildren():
        #     ch.Bind(wx.EVT_LEFT_DOWN, self.OnCardChildLeftDown)

        # make enough space and breathing room for the new card
        self.FitToChildren(pad=self.Padding * 2)
        
        # make sure the new card is visible
        # if scroll:
        #     rect = win.Rect
        #     brd = self.Rect
        #     if rect.bottom > brd.bottom or rect.right > brd.right or rect.left < 0 or rect.top < 0:
        #         self.ScrollToCard(win)

        win.SetFocus()
        self.Cards.append(win)
        
        return win
        

    ### callbacks

    def _on_left_dclick(self, ev):
        self.AddCard("Content", pos=ev.GetPosition())


                


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
