# -*- coding: utf-8 -*-
"""
Data model for note taking application `threepy5`.
"""

from wx.lib.pubsub import pub
import classfactory as fac


######################
# Card classes
######################

CardBase = fac.class_prop_creator("CardBase", id=-1, rect=(0,0,-1,-1))
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

        
HeaderBase = fac.class_prop_creator("HeaderBase", base=Card, header="")                
class Header(HeaderBase):
    """`Card` that holds a title or header."""

    def __init__(self, **kwargs):
        """Constructor.

        * `id: ` identification number. 
        * `rect: ` (x, y, w, h), accepts floats.
        * `header: ` the title or header.
        """
        super(Header, self).__init__(**kwargs)
Header = fac.pub_class(Header, pub)


ImageBase = fac.class_prop_creator("ImageBase", base=Card, path="", scale=1.0)                        
class Image(ImageBase):
    """A `Card` that holds a single image. Note that this class doesn't
    actually load the image from disk. If the application needs to display
    the image, it must load it by itself.
    """

    def __init__(self, **kwargs):
        """Constructor.

        * `id: ` identification number. 
        * `rect: ` (x, y, w, h), accepts floats.
        * `path: ` the path to the image on disk.
        * `scale: ` the scale at which we show the image. This is the float by which we need
        to resize the original image so that it fits in `self.rect`.
        """
        super(Image, self).__init__(**kwargs)
Image = fac.pub_class(Image, pub)



######################
# Annotation class
######################

LineBase = fac.class_prop_creator("LineBase", base=object, colour=(0,0,0,0), thickness=1, pts=[])                        
class Line(LineBase):
    """A `Line` represents a single stroke of the annotations or doodles the user draws in the
    infinite surface that the `Card`s are drawn on. These are drawn on top of the `Card`s.
    """
    DEFAULT_COLOUR = (0,0,0,0)
    DEFAULT_THICKNESS = 1

    def __init__(self, **kwargs):
        """Constructor.

        * `colour: ` a (r,g,b,alpha) tuple.
        * `thickness: ` an int representing the thickness of this stroke.
        * `pts: ` the points defining this polyline.
        """
        super(Line, self).__init__(**kwargs)
Line = fac.pub_class(Line, pub)

    

AnnotationBase = fac.class_prop_creator("AnnotationBase", lines=[])                        
class Annotation(AnnotationBase):
    """`Annotation` is the set of all `Line`s over an `AnnotatedDeck` of `Card`s."""

    def __init__(self, **kwargs):
        """Constructor.

        * `lines: ` a list of `Line`s.
        """
        super(Annotation, self).__init__(**kwargs)
Annotation = fac.pub_class(Annotation, pub)



##########################
# Collections of Cards
##########################        


CardGroupBase = fac.class_prop_creator("CardGroupBase", id=-1, members=[])                        
class CardGroup(object):
    """A list of `Card`s. Grouped `Card`s have meaning together. A `Card` may
    belong to more than one group. If all the `Card`s in one group are also in
    another group, the smaller group is considered nested in the larger one.
    """

    def __init__(self, **kwargs):
        """Constructor.

        * `id: ` idenfitication number.
        * `members: ` a list of identification numbers from `Card`s.
        """
        super(CardGroup, self).__init__(**kwargs)
CardGroup = fac.pub_class(CardGroup, pub)



DeckBase = fac.class_prop_creator("DeckBase", name="", id=-1, members=[])                        
class Deck(DeckBase):
    """It's a collection of `Card`s that share a common topic. It can also hold
    many `CardGroup`s. A `Card` from a `Deck` may have the same id as a `CardGroup`
    but not the same id as another `Card` from the same `Deck`.
    """

    def __init__(self, **kwargs):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        """
        super(Deck, self).__init__(**kwargs)
Deck = fac.pub_class(Deck, pub)



AnnotatedDeckBase = fac.class_prop_creator("AnnotatedDeckBase", base=Deck, name="", cards=[], groups=[], lines=[])                        
class AnnotatedDeck(AnnotatedDeckBase):
    """A collection of `Card`s that can be annotated on."""

    def __init__(self, **kwargs):
        """Constructor.

        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        * `lines: ` a list of `Line`s.
        """
        super(AnnotatedDeck, self).__init__(**kwargs)
        self.annotation = Annotation(lines)
AnnotatedDeck = fac.pub_class(AnnotatedDeck, pub)
    


BoxBase = fac.class_prop_creator("BoxBase", name="", path="", decks=[])                                
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
        super(Box, self).__init__(**kwargs)
Box = fac.pub_class(Box, pub)

