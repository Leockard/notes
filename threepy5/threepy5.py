# -*- coding: utf-8 -*-
"""Data model for note taking application `threepy5`."""

from wx.lib.pubsub import pub
from collections import namedtuple
import utils
import Image as imglib


######################
# Default values
######################

# There are global constants because we need to set the default value
# for the LoudSetter* classes before creating the classes themselves.

# NO_ID = -1
# """Default ID for a `Card`."""

NO_POS = (-1,-1)
"""Magic value for position arguments."""

NO_RECT = utils.Rect(0,0,-1,-1)
"""Default rect for a `Card`."""

# Content defaults
DEFAULT_KIND      = "kind"
"""Default kind name for a `Content`."""

DEFAULT_RATING    = 0
"""Default rating for a `Content`."""

DEFAULT_SCALE = 1.0
"""Default scale for an `Image`."""

# Line defaults
DEFAULT_COLOUR    = (0,0,0,0)
"""Default colour for a `Line`"""

DEFAULT_THICKNESS = 1
"""Default thickness for a `Line`"""



###################################
# utils.Publisher classes
###################################

# LoudSetterID        = utils.makeLoudSetter("ID", NO_ID)
# LoudSetterID        = utils.LoudSetterID
LoudSetterRect      = utils.makeLoudSetter("Rect", NO_RECT)
LoudSetterHeader    = utils.makeLoudSetter("Header", "")
LoudSetterTitle     = utils.makeLoudSetter("Title", "")
LoudSetterKind      = utils.makeLoudSetter("Kind", DEFAULT_KIND)
LoudSetterRating    = utils.makeLoudSetter("Rating", DEFAULT_RATING)
LoudSetterContent   = utils.makeLoudSetter("Content", "")
LoudSetterCollapsed = utils.makeLoudSetter("Collapsed", False)
LoudSetterPath      = utils.makeLoudSetter("Path", "")
LoudSetterScale     = utils.makeLoudSetter("Scale", DEFAULT_SCALE)
LoudSetterLines     = utils.makeLoudSetter("Lines", [])
LoudSetterMembers   = utils.makeLoudSetter("Members", [])
LoudSetterName      = utils.makeLoudSetter("Name", "")
LoudSetterCards     = utils.makeLoudSetter("Cards", [])
LoudSetterGroups    = utils.makeLoudSetter("Groups", [])
LoudSetterDecks     = utils.makeLoudSetter("Decks", [])


def subscribe(attr, call, obj):
    """Call to tell `threpy5` to call `call` when `obj` changes its `attr`.

    * `attr: ` the name of the attribute to listen to (a string).
    * `call: ` a callable object to call when `attr` is updated.
    * `obj: ` the object whose attribute `attr` we want to track.
    """
    topic = ".".join([obj._root, "UPDATE_" + attr.upper()])
    pub.subscribe(call, topic)

def track(call, obj):
    """Call to subscribe to the DESTROY message from an object.

    * `call: ` the callable for the `DESTROY` message.
    * `obj: ` the object to track."""
    topic = ".".join([obj._root, "DESTROY"])
    pub.subscribe(call, topic)

def subscribeList(attr, new, pop, obj):
    """Call to subscribe to the new and remove messages from a `LoudSetter` list.

    * `attr: ` the name of the list attribute.
    * `new: ` the callable for the `NEW_*` message.
    * `pop: ` the callable for the `POP_*` message.
    * `obj: ` the object whose list we're subscribing to.
    """
    topic = ".".join([obj._root, "NEW_" + attr[:-1].upper()])
    pub.subscribe(new, topic)
    topic = ".".join([obj._root, "POP_" + attr[:-1].upper()])
    pub.subscribe(pop, topic)


######################
# Card classes
######################

class Card(utils.Publisher):
    """`Card` is a "virtual 3x5 index card". They are assumed to lie on a
    surface, in which relative position to other `Card`s is very important.

    As an abstract class, its inheritors specialize in handling text
    (`Content`), titles (`Header`), images (`Image`), etc.

    After creating a `Card`, do what's possible to never change its _id.
    Weird things happen when you change _id, though it could be possible
    if done carefully.
    """
    rect = LoudSetterRect()

    def __init__(self, rect=NO_RECT):
        """Constructor.

        * `rect: ` (x, y, w, h), accepts floats.
        """
        super(Card, self).__init__()
        self.rect = rect

        
    ### properties

    @property
    def Position(self):
        """The position of this `Card`.

        `returns: ` a (x, y) tuple of floats.
        """
        return namedtuple("Point", "x y")(self.rect.left, self.rect.top)

    @Position.setter
    def Position(self, pt):
        """Set the position of this `Card`."""
        new_rect = self.rect
        new_rect.left, new_rect.top = pt[0], pt[1]
        # force an update on Rect by using setter
        self.rect = utils.Rect(*new_rect)

    @property
    def Size(self):
        """The size of this `Card`.

        `returns: ` a (x, y) tuple of floats.
        """
        return namedtuple("Size", "w h")(self.rect.width, self.rect.height)

    @Size.setter
    def Size(self, sz):
        """Set the position of this `Card`."""
        new_rect = self.rect
        new_rect.width, new_rect.height = sz[0], sz[1]
        # force an update on Rect by using setter
        self.rect = utils.Rect(*new_rect)


    ### methods

    def MoveBy(self, dx, dy):
        """Move the card relateive to its current position.

        * `dx: ` amount to move in the horizontal direction.
        * `dy: ` amount to move in the vertical direction.
        """
        self.Position = (self.rect.left + dx, self.rect.top + dy)

    def Dump(self):
        """Return a dict holding all this `Card`'s data. When overriding,
        call this method and append all adittional data to the object returned.

        `returns: ` a dict holding data.
        """
        return {"id": self._id, "rect": list(self.rect), "class": self.__class__.__name__}

    def Load(self, data):
        """Read data from an object and load it into this `Card`. Does not change
        this object's id, only copies the data.

        * `obj: ` must be a dict in the format returned by `Card.Dump`.
        """
        self.rect = utils.Rect(*data["rect"])

    def Clone(self, data):
        """Read data from an object and load it into this `Card`, including id.

        * `obj: ` must be a dict in the format returned by `Card.Dump`.
        """
        self.Load(data)
        self._id = data["id"]



class Content(Card):
    """A `Card` which holds text contents. Features: title, kind, rating, content.

    In its content text field, the user may input "tags". Any line of the form
        ^my-tag: foo bar baz$
    is considered to define the tag "my-tag". Tag names (before the colon) must
    be single words, and their content (after the colon) may be any string,
    until a newline.

    A tag can be anything, though they usually describe facts about concepts:

        Content Card "Protein"
        kind: concept
        rating: 2 stars
            Proteins are chains of amino-acids which...
            Number: there are x types of proteins.
            Kinds: transmembrane proteins, integral membrane proteins.

    This `Content` has two tags: "number" and "kinds".

    A `Content` can be "collapsed". This means that its content text is hidden
    and we only wish to display its title.
    """
    KIND_LBL_CONCEPT    = "Concept"
    KIND_LBL_RESEARCH   = "Research"
    KIND_LBL_ASSUMPTION = "Assumption"
    KIND_LBL_FACT       = "Fact"
    KIND_LBLS = [KIND_LBL_CONCEPT, KIND_LBL_RESEARCH, KIND_LBL_ASSUMPTION, KIND_LBL_FACT]

    RATING_MAX = 3
    DEFAULT_SZ = (250, 150)
    DEFAULT_RECT = (0,0,250,150)

    title = LoudSetterTitle()
    kind = LoudSetterKind()
    rating = LoudSetterRating()
    content = LoudSetterContent()
    collapsed = LoudSetterCollapsed()

    def __init__(self, rect=DEFAULT_RECT, title="", kind=DEFAULT_KIND, rating=DEFAULT_RATING, content="", collapsed=False):
        """Constructor.

        * `rect: ` (x, y, w, h), accepts floats.
        * `kind: ` one of `Content.KIND_*`.
        * `content: ` the content text.
        * `rating: ` a measure of the importance of this `Content`. Must be an
        int from 0 to `RATING_MAX`, inclusive.
        * `collapsed: ` if `True`, we ignore the contents. In that case, this
        `Content` would funtion sort of like a `Header` with a kind and a rating.
        """
        super(Content, self).__init__(rect=rect)
        self.title = title
        self.kind = kind
        self.rating = rating
        self.content = content
        self.collapsed = collapsed


    ### methods

    def IncreaseRating(self, wrap=True):
        """Set the rating to be one more than its current value.

        * `wrap: ` if `True`, and we increase to more than the maximum rating, we set it to zero.
        if `False` and the new rating is more than `self.MAX`, don't do anything."""
        new = self.rating + 1
        if wrap and new > self.RATING_MAX:
            new = 0
        elif new > self.RATING_MAX:
            return

        self.rating = new

    def Dump(self):
        """Return a dict holding all this `Content`'s data.

        `returns: ` a dict holding data.
        """
        data = super(Content, self).Dump()
        data["title"]     = self.title
        data["kind"]      = self.kind
        data["rating"]    = self.rating
        data["content"]   = self.content
        data["collapsed"] = self.collapsed
        return data

    def Load(self, data):
        """Read data from an object and load it into this `Content`.

        * `obj: ` must be a dict in the format returned by `Content.Dump`.
        """
        super(Content, self).Load(data)
        self.title     = data["title"]
        self.kind      = data["kind"]
        self.rating    = data["rating"]
        self.content   = data["content"]
        self.collapsed = data["collapsed"]



class Header(Card):
    """`Card` that holds a title or header."""
    DEFAULT_SZ = (150, 32)
    header = LoudSetterHeader()

    def __init__(self, rect=NO_RECT, header=""):
        """Constructor.

        * `rect: ` (x, y, w, h), accepts floats.
        * `header: ` the title or header.
        """
        super(Header, self).__init__(rect=rect)
        self.header = header


    ### methods

    def Dump(self):
        """Return a dict holding all this `Header`'s data.

        `returns: ` a dict holding data.
        """
        data = super(Header, self).Dump()
        data["header"] = self.header
        return data

    def Load(self, data):
        """Read data from an object and load it into this `Header`.

        * `obj: ` must be a dict in the format returned by `Header.Dump`.
        """
        super(Header, self).Load(data)
        self.header = data["header"]



class Image(Card):
    """A `Card` that holds a single image. Note that this class doesn't
    hold a reference to the image. If the application needs to display
    the image, it must load it by itself. However, `Image` does handle
    its size according to the assigned image.
    """
    DEFAULT_SZ = (50, 50)
    path = LoudSetterPath()
    scale = LoudSetterScale()

    def __init__(self, path="", scale=DEFAULT_SCALE, rect=NO_RECT):
        """Constructor.

        * `path: ` the path to the image on disk.
        * `scale: ` the scale at which we show the image. This is the float by which we need
        to resize the original image so that it fits in `self.rect`.
        * `rect: ` any `rect` init argument will be overridden as soon as a `path` is provided.
        `Image` accepts a `rect` argument only for compatibility with its ancestor.
        """
        super(Image, self).__init__(rect=rect)
        subscribe("path", self._on_update_path, self)
        self.path = path
        self.scale = scale


    ### methods
    
    def Dump(self):
        """Return a dict holding all this `Image`'s data.

        `returns: ` a dict holding data.
        """
        data = super(Image, self).Dump()
        data["path"] = self.path
        data["scale"] = self.scale
        return data

    def Load(self, data):
        """Read data from an object and load it into this `Image`.

        * `obj: ` must be a dict in the format returned by `Image.Dump`.
        """
        super(Image, self).Load(data)
        data["path"] = self.path
        data["scale"] = self.scale

        
    ### subscribers

    def _on_update_path(self, val):
        if val:
            try:
                img = imglib.open(val)
                x, y = self.rect.left, self.rect.top
                self.rect = utils.Rect(x, y, img.size[0], img.size[1])
            except Exception as e:
                print e


######################
# Annotation class
######################

# class Line(object):
#     """A `Line` represents a single stroke of the annotations or doodles the user draws in the
#     infinite surface that the `Card`s are drawn on. These are drawn on top of the `Card`s.
#     """

#     # colour = LoudSetterColour()
#     # thickness = LoudSetterThickness()
#     # pts = LoudSetterPts()

#     Add = utils.LoudAppend("pts")
#     Remove = utils.LoudRemove("pts")

#     def __init__(self, colour=DEFAULT_COLOUR, thickness=DEFAULT_THICKNESS, pts=[]):
#         """Constructor.

#         * `colour: ` a (r,g,b,alpha) tuple.
#         * `thickness: ` an int representing the thickness of this stroke.
#         * `pts: ` the points defining this polyline.
#         """
#         super(Line, self).__init__()
#         self.colour = colour
#         self.thickness = thickness
#         self.pts = pts


import recordtype
Line = recordtype.recordtype('Line', [('colour', (0,0,0,0)), ('thickness', 1), ("pts", [])])
"""A `Line` represents a single stroke of the annotations or doodles the user draws in the
infinite surface that the `Card`s are drawn on. These are drawn on top of the `Card`s.

It is a `recordtype` (a mutable named tuple), with fields aliases for "colour", "thickness",
and "pts".
"""



class Annotation(utils.Publisher):
    """`Annotation` is the set of all `Line`s over an `AnnotatedDeck` of `Card`s."""
    lines = LoudSetterLines()
    Add = utils.LoudAppend("lines")
    Remove = utils.LoudRemove("lines")

    def __init__(self, lines=[]):
        """Constructor.

        * `lines: ` a list of `Line`s.
        """
        super(Annotation, self).__init__()
        self.lines = lines



##########################
# Collections of Cards
##########################

class CardGroup(utils.Publisher):
    """A list of `Card`s. Grouped `Card`s have meaning together. A `Card` may
    belong to more than one group. If all the `Card`s in one group are also in
    another group, the smaller group is considered nested in the larger one.
    """
    members = LoudSetterMembers()
    Add = utils.LoudAppend("members")
    Remove = utils.LoudRemove("members")

    def __init__(self, members=[]):
        """Constructor.

        * `members: ` a list of identification numbers from `Card`s.
        """
        super(CardGroup, self).__init__()
        self.members = members

    def Dump(self):
        """Returns a list holding all this `CardGroup`'s data.

        `returns: ` a list holding data.
        """
        return [m._id for m in self.members]



class Deck(utils.Publisher):
    """It's a collection of `Card`s that share a common topic. It can also hold
    many `CardGroup`s.
    """
    PADDING = 15
    
    name = LoudSetterName()
    cards = LoudSetterCards()
    groups = LoudSetterGroups()

    AddCard = utils.LoudAppend("cards")
    RemoveCard = utils.LoudRemove("cards")
    AddGroup = utils.LoudAppend("groups")
    RemoveGroup = utils.LoudRemove("groups")

    def __init__(self, name=""):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        """
        super(Deck, self).__init__()
        self.name = name
        self.cards = []  # cards
        self.groups = [] # groups


    ### methods

    def NewCard(self, class_, pos=NO_POS, pivot=None, below=False):
        cardclass = globals()[class_]
        sz = cardclass.DEFAULT_SZ

        if pos == NO_POS:
            pos = self._new_pos(pivot=pivot, below=below)

        card = cardclass(rect=utils.Rect(pos[0], pos[1], sz[0], sz[1]))
        self.AddCard(card)
        return card

    def _new_pos(self, pivot=None, below=False):
        """Returns the recommended position of the next `Card`.

        * `pivot: ` a reference `Card` around which to look for a suitable position.
        * `below: ` when `False`, looks for a suitable position to the right of the
        `pivot`, if any; when `True`, looks for the position below the `pivot`.

        `returns: ` the recommended position for a new `Card`.
        """
        pos = (0,0)
        pad = self.PADDING
        
        # if there are no cards, recommend the top left corner
        if len(self.cards) < 1:
            pos = (pad, pad)
    
        # if there's a pivot, recommend next to it
        elif pivot:
            rect = utils.Rect(*pivot.rect)
            if below:
                top = rect.bottom + pad
                left = rect.left
            else:
                top = rect.top
                left = rect.right + pad
            pos = (left, top)

        # otherwise, move it to the right of the last Card
        else: 
            rects = [utils.Rect(*c.rect) for c in self.cards]
            rights = [r.right for r in rects]
            top = min([r.top for r in rects])
            left = max(rights) + pad
            pos = (left, top)

        return pos

    def Dump(self):
        """Return a dict holding all this `Deck`'s data.

        `returns: ` a dict holding data.
        """
        return {"cards": [c.Dump() for c in self.cards],
                "groups": [g.Dump() for g in self.groups]}

    def Load(self, data):
        pass



##################################
# Collections of mixed objects
##################################

class AnnotatedDeck(Deck):
    """A collection of `Card`s that can be annotated on."""

    def __init__(self, name=""):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        * `lines: ` a list of `Line`s.
        """
        super(AnnotatedDeck, self).__init__(name=name)
        self.annotation = Annotation()




class Box(utils.Publisher):
    """A `Box` holds various `Deck`s. It is the equivalent of a file at
    application level: every `Box` is stored in one file and every file
    loads one `Box`.
    """
    name = LoudSetterName()
    path = LoudSetterPath()
    decks = LoudSetterDecks()

    AddDeck = utils.LoudAppend("decks")
    RemoveDeck = utils.LoudRemove("decks")

    def __init__(self, name="", path="", decks=[]):
        """Constructor.

        * `name: ` the name of this `Box`.
        * `path: ` the path to the file on disk.
        * `decks: ` a list of `Deck`s (or `AnnotatedDeck`s).
        """
        super(Box, self).__init__()
        self.name = name
        self.path = path
        self.decks = decks

    def NewDeck(self, name=""):
        self.AddDeck(AnnotatedDeck(name))






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
for field in dir(utils.Publisher):
    __pdoc__['Card.%s' % field] = None
for field in dir(Card):
    __pdoc__['Content.%s' % field] = None
for field in dir(Card):
    __pdoc__['Header.%s' % field] = None
for field in dir(Card):
    __pdoc__['Image.%s' % field] = None
for field in dir(utils.Publisher):
    __pdoc__['Annotation.%s' % field] = None
for field in dir(utils.Publisher):
    __pdoc__['CardGroup.%s' % field] = None
for field in dir(utils.Publisher):
    __pdoc__['Deck.%s' % field] = None
for field in dir(Deck):
    __pdoc__['AnnotatedDeck.%s' % field] = None
for field in dir(utils.Publisher):
    __pdoc__['Box.%s' % field] = None            

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in Card.__dict__.keys():
    if 'Card.%s' % field in __pdoc__.keys():
        del __pdoc__['Card.%s' % field]
for field in Content.__dict__.keys():
    if 'Content.%s' % field in __pdoc__.keys():
        del __pdoc__['Content.%s' % field]
for field in Header.__dict__.keys():
    if 'Header.%s' % field in __pdoc__.keys():
        del __pdoc__['Header.%s' % field]
for field in Image.__dict__.keys():
    if 'Image.%s' % field in __pdoc__.keys():
        del __pdoc__['Image.%s' % field]
for field in Annotation.__dict__.keys():
    if 'Annotation.%s' % field in __pdoc__.keys():
        del __pdoc__['Annotation.%s' % field]
for field in CardGroup.__dict__.keys():
    if 'CardGroup.%s' % field in __pdoc__.keys():
        del __pdoc__['CardGroup.%s' % field]
for field in Deck.__dict__.keys():
    if 'Deck.%s' % field in __pdoc__.keys():
        del __pdoc__['Deck.%s' % field]
for field in AnnotatedDeck.__dict__.keys():
    if 'AnnotatedDeck.%s' % field in __pdoc__.keys():
        del __pdoc__['AnnotatedDeck.%s' % field]
for field in Box.__dict__.keys():
    if 'Box.%s' % field in __pdoc__.keys():
        del __pdoc__['Box.%s' % field]
