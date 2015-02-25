# -*- coding: utf-8 -*-
"""
Data model for note taking application `threepy5`.
"""

from wx.lib.pubsub import pub
from weakref import WeakKeyDictionary as weakdict
import classfactory as fac



######################
# Default values
######################

# Card defaults
DEFAULT_ID   = -1
DEFAULT_RECT = (0,0,-1,-1)

# Content defaults
DEFAULT_KIND      = "kind"
DEFAULT_RATING    = 0
DEFAULT_COLLAPSED = False

# Image defaults
DEFAULT_SCALE = 1.0

# Line defaults
DEFAULT_COLOUR    = (0,0,0,0)
DEFAULT_THICKNESS = 1



######################
# Descriptors classes
######################

class Publisher(object):
    """A descriptor that publishes its updates.

    The topic name we publish is based on the first word of the name of the
    derived class. If the class is called `FooPublisher`, the topic will be named
    "UPDATE_FOO"."""

    def __init__(self, default):
        self.default = default
        self.data = weakdict()

    def __get__(self, instance, owner):
        return self.data.get(instance, self.default)

    def __set__(self, instance, value):
        # print "setting %s for: %s" % (str(value), str(instance))
        self.data[instance] = value
        name = self.__class__.__name__[:-9]
        pub.sendMessage("UPDATE_" + name.upper())

            
class IDPublisher(Publisher):
    def __init__(self, default=DEFAULT_ID):
        super(IDPublisher, self).__init__(default=default)

class RectPublisher(Publisher):
    def __init__(self, default=DEFAULT_RECT):
        super(RectPublisher, self).__init__(default=default)

class HeaderPublisher(Publisher):
    def __init__(self, default=""):
        super(HeaderPublisher, self).__init__(default=default)

class TitlePublisher(Publisher):
    def __init__(self, default=""):
        super(TitlePublisher, self).__init__(default=default)

class KindPublisher(Publisher):
    def __init__(self, default=DEFAULT_KIND):
        super(KindPublisher, self).__init__(default=default)

class RatingPublisher(Publisher):
    def __init__(self, default=DEFAULT_RATING):
        super(RatingPublisher, self).__init__(default=default)

class ContentPublisher(Publisher):
    def __init__(self, default=""):
        super(ContentPublisher, self).__init__(default=default)

class CollapsedPublisher(Publisher):
    def __init__(self, default=False):
        super(CollapsedPublisher, self).__init__(default=default)

class PathPublisher(Publisher):
    def __init__(self, default=""):
        super(PathPublisher, self).__init__(default=default)

class ScalePublisher(Publisher):
    def __init__(self, default=DEFAULT_SCALE):
        super(ScalePublisher, self).__init__(default=default)

class ColourPublisher(Publisher):
    def __init__(self, default=DEFAULT_COLOUR):
        super(ColourPublisher, self).__init__(default=default)

class ThicknessPublisher(Publisher):
    def __init__(self, default=DEFAULT_THICKNESS):
        super(ThicknessPublisher, self).__init__(default=default)

class PtsPublisher(Publisher):
    def __init__(self, default=[]):
        super(PtsPublisher, self).__init__(default=default)

class LinesPublisher(Publisher):
    def __init__(self, default=[]):
        super(LinesPublisher, self).__init__(default=default)

class MembersPublisher(Publisher):
    def __init__(self, default=[]):
        super(MembersPublisher, self).__init__(default=default)

class NamePublisher(Publisher):
    def __init__(self, default=""):
        super(NamePublisher, self).__init__(default=default)

class CardsPublisher(Publisher):
    def __init__(self, default=[]):
        super(CardsPublisher, self).__init__(default=default)

class GroupsPublisher(Publisher):
    def __init__(self, default=[]):
        super(GroupsPublisher, self).__init__(default=default)

class DecksPublisher(Publisher):
    def __init__(self, default=[]):
        super(DecksPublisher, self).__init__(default=default)


######################
# Card classes
######################

class Card(object):
    """`Card` is a "virtual 3x5 index card". They are assumed to lie on a
    surface and relative position to one another is very important.

    As an abstract class, its inheritors specialize in handling text
    (`Content`), titles (`Header`), or images (`Image`).
    """

    id = IDPublisher()
    rect = RectPublisher()

    def __init__(self, id=DEFAULT_ID, rect=DEFAULT_RECT):
        """Constructor.

        * `id: ` this `Card`'s identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        """
        self.id = id
        self.rect = rect



class Content(Card):
    """
    A `Card` which holds text contents. Features: title, kind, rating, content.

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
    KIND_CONCEPT    = "C"
    KIND_RESEARCH   = "R"
    KIND_ASSUMPTION = "A"
    KIND_FACT       = "F"
    RATING_MAX = 3

    title = TitlePublisher()
    kind = KindPublisher()
    rating = RatingPublisher()
    content = ContentPublisher()
    collapsed = CollapsedPublisher()

    def __init__(self, id=DEFAULT_ID, rect=DEFAULT_RECT, title="", kind=DEFAULT_KIND, rating=DEFAULT_RATING, content="", collapsed=DEFAULT_COLLAPSED):
        """Constructor.

        * `id: ` identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        * `kind: ` one of `Content.KIND_*`.
        * `content: ` the content text.
        * `rating: ` a measure of the importance of this `Content`. Must be an
        int from 0 to `RATING_MAX`, inclusive.
        * `collapsed: ` if `True`, we ignore the contents. In that case, this
        `Content` would funtion sort of like a `Header` with a kind and a rating.
        """
        super(Content, self).__init__(id=id, rect=rect)
        self.title = title
        self.kind = kind
        self.rating = rating
        self.content = content
        self.collapsed = collapsed



class Header(Card):
    """`Card` that holds a title or header."""

    header = HeaderPublisher()

    def __init__(self, id=DEFAULT_ID, rect=DEFAULT_RECT, header=""):
        """Constructor.

        * `id: ` identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        * `header: ` the title or header.
        """
        super(Header, self).__init__(id=id, rect=rect)
        self.header = header



class Image(Card):
    """A `Card` that holds a single image. Note that this class doesn't
    actually load the image from disk. If the application needs to display
    the image, it must load it by itself.
    """

    path = PathPublisher()
    scale = ScalePublisher()

    def __init__(self, id=DEFAULT_ID, rect=DEFAULT_RECT, path="", scale=DEFAULT_SCALE):
        """Constructor.

        * `id: ` identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        * `path: ` the path to the image on disk.
        * `scale: ` the scale at which we show the image. This is the float by which we need
        to resize the original image so that it fits in `self.rect`.
        """
        super(Image, self).__init__(id=id, rect=rect)
        self.path = path
        self.scale = scale



######################
# Annotation class
######################

class Line(object):
    """A `Line` represents a single stroke of the annotations or doodles the user draws in the
    infinite surface that the `Card`s are drawn on. These are drawn on top of the `Card`s.
    """

    colour = ColourPublisher()
    thickness = ThicknessPublisher()
    pts = PtsPublisher()

    def __init__(self, colour=DEFAULT_COLOUR, thickness=DEFAULT_THICKNESS, pts=[]):
        """Constructor.

        * `colour: ` a (r,g,b,alpha) tuple.
        * `thickness: ` an int representing the thickness of this stroke.
        * `pts: ` the points defining this polyline.
        """
        self.colour = colour
        self.thickness = thickness
        self.pts = pts



class Annotation(object):
    """`Annotation` is the set of all `Line`s over an `AnnotatedDeck` of `Card`s."""

    lines = LinesPublisher()

    def __init__(self, lines=[]):
        """Constructor.

        * `lines: ` a list of `Line`s.
        """
        self.lines = lines



##########################
# Collections of Cards
##########################

class CardGroup(object):
    """A list of `Card`s. Grouped `Card`s have meaning together. A `Card` may
    belong to more than one group. If all the `Card`s in one group are also in
    another group, the smaller group is considered nested in the larger one.
    """

    id = IDPublisher()
    members = MembersPublisher()

    def __init__(self, id=DEFAULT_ID, members=[]):
        """Constructor.

        * `id: ` idenfitication number.
        * `members: ` a list of identification numbers from `Card`s.
        """
        self.id = id
        self.members = members



# DeckBase = fac.class_prop_creator("DeckBase", id=DEFAULT_ID, name="", cards=[], groups=[])
class Deck(object):
    """It's a collection of `Card`s that share a common topic. It can also hold
    many `CardGroup`s. A `Card` from a `Deck` may have the same id as a `CardGroup`
    but not the same id as another `Card` from the same `Deck`.
    """

    id = IDPublisher()
    name = NamePublisher()
    cards = CardsPublisher()
    groups = GroupsPublisher()

    def __init__(self, id=DEFAULT_ID, name="", cards=[], groups=[]):
        """Constructor.

        * `id: ` identification number.
        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        """
        self.id = id
        self.name = name
        self.cards = cards
        self.groups = groups



##################################
# Collections of mixed objects
##################################

class AnnotatedDeck(object):
    """A collection of `Card`s that can be annotated on."""

    id = IDPublisher()
    name = NamePublisher()
    cards = CardsPublisher()
    groups = GroupsPublisher()

    def __init__(self, id=DEFAULT_ID, name="", cards=[], groups=[], lines=[]):
        """Constructor.

        * `id: ` identification number.
        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        * `lines: ` a list of `Line`s.
        """
        self.id = id
        self.name = name
        self.cards = cards
        self.groups = groups
        self.annotation = Annotation(lines=lines)




# BoxBase = fac.class_prop_creator("BoxBase", name="", path="", decks=[])
class Box(object):
    """A `Box` holds various `Deck`s. It is the equivalent of a file at
    application level: every `Box` is stored in one file and every file
    loads one `Box`.
    """

    name = NamePublisher()
    path = PathPublisher()
    decks = DecksPublisher()

    def __init__(self, name="", path="", decks=[]):
        """Constructor.

        * `name: ` the name of this `Box`.
        * `path: ` the path to the file on disk.
        * `decks: ` a list of `Deck`s (or `AnnotatedDeck`s).
        """
        self.name = name
        self.path = path
        self.decks = decks
