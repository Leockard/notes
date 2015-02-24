# -*- coding: utf-8 -*-
"""
Data model for note taking application `threepy5`.
"""

from wx.lib.pubsub import pub
import classfactory as fac


######################
# Card classes
######################

CardBase = fac.class_prop_creator("CardBase", base=object, id=-1, rect=(0,0,-1,-1))
class Card(CardBase):
    """`Card` is a "virtual 3x5 index card". They are assumed to lie on a
    surface and relative position to one another is very important.

    As an abstract class, its inheritors specialize in handling text
    (`Content`), titles (`Header`), or images (`Image`).
    """
    DEFAULT_ID = -1
    DEFAULT_RECT = (0,0,-1,-1)

    def __init__(self, **kwargs):
        """Constructor.
        
        * `id: ` this `Card`'s identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        """
        super(Card, self).__init__(**kwargs)
Card = fac.pub_class(Card, pub)



ContentBase = fac.class_prop_creator("ContentBase", base=Card, title="", kind="kind", rating=0, content="", collapsed=False)
class Content(ContentBase):
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
    KIND_DEFAULT    = "kind"
    KIND_CONCEPT    = "C"
    KIND_RESEARCH   = "R"
    KIND_ASSUMPTION = "A"
    KIND_FACT       = "F"

    RATING_MAX = 3

    UPDATE_TITLE     = "title updated"
    UPDATE_KIND      = "kind updated"
    UPDATE_CONTENT   = "content updated"
    UPDATE_RATING    = "rating updated"
    UPDATE_COLLAPSED =  "collapsed updated"

        
    def __init__(self, **kwargs):
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
        super(Content, self).__init__(**kwargs)
Content = fac.pub_class(Content, pub)

# class Content(Card):
#     """
#     A `Card` which holds text contents. Features: title, kind, rating, content.
    
#     In its content text field, the user may input "tags". Any line of the form
#     ^my-tag: foo bar baz$
#     is considered to define the tag "my-tag". Tag names (before the colon) must
#     be single words, and their content (after the colon) may be any string,
#     until a newline.
    
#     A tag can be anything, though they usually describe facts about concepts:

#         Content Card "Protein"
#         kind: concept
#         rating: 2 stars
#             Proteins are chains of amino-acids which...
#             Number: there are x types of proteins.
#             Kinds: transmembrane proteins, integral membrane proteins.

#     This `Content` has two tags: "number" and "kinds".

#     A `Content` can be "collapsed". This means that its content text is hidden
#     and we only wish to display its title.
#     """
#     KIND_DEFAULT    = "kind"
#     KIND_CONCEPT    = "C"
#     KIND_RESEARCH   = "R"
#     KIND_ASSUMPTION = "A"
#     KIND_FACT       = "F"

#     RATING_MAX = 3

#     UPDATE_TITLE     = "title updated"
#     UPDATE_KIND      = "kind updated"
#     UPDATE_CONTENT   = "content updated"
#     UPDATE_RATING    = "rating updated"
#     UPDATE_COLLAPSED =  "collapsed updated"
    
    
#     def __init__(self, id=Card.DEFAULT_ID, rect=Card.DEFAULT_RECT, title="",
#                  kind=KIND_DEFAULT, content="", rating=0, collapsed=False):
#         """Constructor.

#         * `id: ` identification number. 
#         * `rect: ` (x, y, w, h), accepts floats.
#         * `kind: ` one of `Content.KIND_*`.
#         * `content: ` the content text.
#         * `rating: ` a measure of the importance of this `Content`. Must be an
#         int from 0 to `RATING_MAX`, inclusive.
#         * `collapsed: ` if `True`, we ignore the contents. In that case, this
#         `Content` would funtion sort of like a `Header` with a kind and a rating.
#         """
#         super(Content, self).__init__(id, rect)
#         self._title = title
#         self._kind = kind
#         self._content = content
#         self._rating = rating
#         self._collapsed = collapsed

#     @property
#     def title(self):
#         return self._title

#     @title.setter
#     def title(self, val):
#         pub.sendMessage(self.UPDATE_TITLE)
#         self._title = val

#     @property
#     def kind(self):
#         return self._kind

#     @kind.setter
#     def kind(self, val):
#         pub.sendMessage(self.UPDATE_KIND)
#         self._kind = val

#     @property
#     def content(self):
#         return self._content

#     @content.setter
#     def content(self, val):
#         pub.sendMessage(self.UPDATE_CONTENT)
#         self._content = val

#     @property
#     def rating(self):
#         return self._rating

#     @rating.setter
#     def rating(self, val):
#         pub.sendMessage(self.UPDATE_RATING)
#         self._rating = val

#     @property
#     def collapsed(self):
#         return self._collapsed

#     @collapsed.setter
#     def collapsed(self, val):
#         pub.sendMessage(self.UPDATE_COLLAPSED)
#         self._collapsed = val

        
                
class Header(Card):
    """`Card` that holds a title or header."""

    UPDATE_HEADER = "header updated"

    def __init__(self, id=Card.DEFAULT_ID, rect=Card.DEFAULT_RECT, header=""):
        """Constructor.

        * `id: ` identification number. 
        * `rect: ` (x, y, w, h), accepts floats.
        * `header: ` the title or header.
        """
        super(Header, self).__init__(id, rect)
        self._header = header

    @property
    def header(self):
        return self._collapsed

    @header.setter
    def header(self, val):
        pub.sendMessage(self.UPDATE_HEADER)
        self._header = val

        
class Image(Card):
    """A `Card` that holds a single image. Note that this class doesn't
    actually load the image from disk. If the application needs to display
    the image, it must load it by itself.
    """

    UPDATE_PATH = "updated path"

    def __init__(self, id=Card.DEFAULT_ID, rect=Card.DEFAULT_RECT, path="", scale=1.0):
        """Constructor.

        * `id: ` identification number. 
        * `rect: ` (x, y, w, h), accepts floats.
        * `path: ` the path to the image on disk.
        * `scale: ` the scale at which we show the image. This is the float by which we need
        to resize the original image so that it fits in `self.rect`.
        """
        super(Image, self).__init__(id, rect)
        self._path = path
        self._scale = scale

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, val):
        pub.sendMessage(self.UPDATE_PATH)
        self._path = val

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, val):
        pub.sendMessage(self.UPDATE_SCALE)
        self._scale = val



######################
# Annotation class
######################

class Line(object):
    """A `Line` represents a single stroke of the annotations or doodles the user draws in the
    infinite surface that the `Card`s are drawn on. These are drawn on top of the `Card`s.
    """
    DEFAULT_COLOUR = (0,0,0,0)
    DEFAULT_THICKNESS = 1

    UPDATE_COLOUR = "updated colour"
    UPDATE_THICKNESS = "updated thickness"
    UPDATE_POINTS = "updated points"

    def __init__(self, colour=DEFAULT_COLOUR, thickness=DEFAULT_THICKNESS, pts=[]):
        """Constructor.

        * `colour: ` a (r,g,b,alpha) tuple.
        * `thickness: ` an int representing the thickness of this stroke.
        * `pts: ` the points defining this polyline.
        """
        self._colour = colour
        self._thickness = thickness
        self._pts = pts

    @property
    def colour(self):
        return self._colour

    @colour.setter
    def colour(self, val):
        self._colour = val
        pub.sendMessage(self.UPDATE_COLOUR)

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, val):
        self._thickness = val
        pub.sendMessage(self.UPDATE_THICKNESS)

    @property
    def pts(self):
        return self._pts

    @pts.setter
    def pts(self, val):
        self._pts = val
        pub.sendMessage(self.UPDATE_POINTS)

    def AddPoint(self, pt):
        self._pts.append(pt)
        pub.sendMessage(self.UPDATE_POINTS)

    

class Annotation(object):
    """`Annotation` is the set of all `Line`s over an `AnnotatedDeck` of `Card`s."""

    UPDATE_LINES = "updated lines"

    def __init__(self, lines = []):
        """Constructor.

        * `lines: ` a list of `Line`s.
        """
        self._lines = lines

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, val):
        self._lines = val
        pub.sendMessage(self.UPDATE_LINES)

    def AddLine(self, line):
        self._lines.append(line)
        pub.sendMessage(self.UPDATE_LINES)



##########################
# Collections of Cards
##########################        

class CardGroup(object):
    """A list of `Card`s. Grouped `Card`s have meaning together. A `Card` may
    belong to more than one group. If all the `Card`s in one group are also in
    another group, the smaller group is considered nested in the larger one.
    """

    UPDATE_MEMBERS = "updated members"

    def __init__(self, id=-1, members=[]):
        """Constructor.

        * `id: ` idenfitication number.
        * `members: ` a list of identification numbers from `Card`s.
        """
        self._id = id
        self._members = []

    @property
    def members(self):
        return self._members

    @members.setter
    def members(self, val):
        self._members = val
        pub.sendMessage(self.UPDATE_MEMBERS)

    def AddCard(self, card):
        self._members.append(card)
        pub.sendMessage(self.UPDATE_MEMBERS)

    def RemoveCard(self, card):
        if card in self._members:
            self._members.remove(card)
        pub.sendMessage(self.UPDATE_MEMBERS)



class Deck(object):
    """It's a collection of `Card`s that share a common topic. It can also hold
    many `CardGroup`s. A `Card` from a `Deck` may have the same id as a `CardGroup`
    but not the same id as another `Card` from the same `Deck`.
    """

    def __init__(self, name="", cards=[], groups=[]):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        """
        self.cards = cards
        self.groups = groups



class AnnotatedDeck(Deck):
    """A collection of `Card`s that can be annotated on."""

    def __init__(self, name="", cards=[], groups=[], lines=[]):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        * `lines: ` a list of `Line`s.
        """
        super(AnnotatedDeck, self).__init__(cards, groups)
        self.annotation = Annotation(lines)
    

class Box(object):
    """A `Box` holds various `Deck`s. It is the equivalent of a file at
    application level: every `Box` is stored in one file and every file
    loads one `Box`.
    """

    def __init__(self, name="", path="", decks=[]):
        """Constructor.

        * `name: ` the name of this `Box`.
        * `path: ` the path to the file on disk.
        * `decks: ` a list of `Deck`s (or `AnnotatedDeck`s).
        """
        self.name = name
        self.path = path
        self.decks = decks
