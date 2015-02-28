# -*- coding: utf-8 -*-
"""Data model for note taking application `threepy5`."""

from wx.lib.pubsub import pub
from weakref import WeakKeyDictionary as weakdict
from collections import namedtuple


######################
# Default values
######################

# There are global constants because we need to set the default value
# for the *Publisher classes before creating the classes themselves.

NO_ID = -1
"""Default ID for a `Card`."""

NO_RECT = [0,0,-1,-1]
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


######################
# Publisher classes
######################

class Publisher(object):
    """A descriptor that publishes its updates, by calling `pub.sendMessage`
    every time `__set__` is called.  Child classes *must* contain the word
    "Publisher" at the end of their name.

    The topic name we publish with is based on the first word of the name of the
    derived class. By default, if the class is called `FooPublisher`, the topic
    will be named "UPDATE_FOO".

    However, `Publisher` also provides a method to specify the root topic for
    the message. If an instance with a `FooPublisher` descriptor calls
    `FooPublisher.setTopic(instance, owner, topic)`, the new topic name will be
    `topic.UPDATE_FOO`.
    """
    def __init__(self, default):
        """Constructor.

        * `default: ` the default value returned the first time x.prop is referenced.
        * `topic_path: ` the path to the topic that we will send messages with.
        """
        self._publish = True
        self._default = default
        self._data = weakdict()
        self._topics = weakdict()
        self._subtopic = "UPDATE_" + self.__class__.__name__[:-9].upper()

    def __get__(self, instance, owner):
        """Get method.

        * `instance: ` the object referencing this descriptor.
        * `owner: ` the `instance`'s class.

        `returns: ` the data value of `instance` corresponding to this descriptor."""
        # print "getting"
        if instance is None:
            return self
        else:
            return self._data.get(instance, self._default)

    def __set__(self, instance, value):
        """Set method.

        * `instance: ` the instance whose data we're setting.
        * `value: ` the new value to set.
        """
        topic = self._topics.get(instance, _make_topic_name(instance))
        topic += "." + self._subtopic
        # print "publishing %s for %s with topic: %s" % (str(value), str(instance), topic)
        
        self._data[instance] = value
        if self._publish:
            pub.sendMessage(topic, val=value)

    def setTopic(self, instance, topic):
        """Set the root topic to send messages with.

        * `instance: ` the instance whose topic root is being set.
        * `topic: ` the string to prepended to the default subtopic.
        """
        self._topics[instance] = topic

    def silent(self, instance, value):
        """Calls __set__ without publishing."""
        self._publish = False
        self.__set__(instance, value)
        self._publish = True

        

def makePublisher(name, default):
    """Function that creates a `Publisher` class. The new class will
    be called "'Name'Publisher", and it will publish its calls with the
    message "UPDATE_'NAME'". All derived `*Publisher` classed in this module
    are created with this function.
    """
    class newPublisher(Publisher):
        def __init__(self, default=default):
            super(newPublisher, self).__init__(default=default)
    newPublisher.__name__ = name + "Publisher"
    return newPublisher

IDPublisher        = makePublisher("ID", NO_ID)
RectPublisher      = makePublisher("Rect", NO_RECT)
HeaderPublisher    = makePublisher("Header", "")
TitlePublisher     = makePublisher("Title", "")
KindPublisher      = makePublisher("Kind", DEFAULT_KIND)
RatingPublisher    = makePublisher("Rating", DEFAULT_RATING)
ContentPublisher   = makePublisher("Content", "")
CollapsedPublisher = makePublisher("Collapsed", False)
PathPublisher      = makePublisher("Path", "")
ScalePublisher     = makePublisher("Scale", DEFAULT_SCALE)
ColourPublisher    = makePublisher("Colour", DEFAULT_COLOUR)
ThicknessPublisher = makePublisher("Thickness", DEFAULT_THICKNESS)
PtsPublisher       = makePublisher("Pts", [])
LinesPublisher     = makePublisher("Lines", [])
MembersPublisher   = makePublisher("Members", [])
NamePublisher      = makePublisher("Name", "")
CardsPublisher     = makePublisher("Cards", [])
GroupsPublisher    = makePublisher("Groups", [])
DecksPublisher     = makePublisher("Decks", [])
        


#########################
# Add/Remove descriptors
#########################

class AddDesc(object):
    """A descriptor that adds a member to a list.

    For example, if a class `foo` is created as:

        class foo(object):
            addThing = AddDesc("thing")
            removeThing = RemoveDesc("thing")
            def __init__(...):
                self.things = []
                ...

    then an instance `x` of class `foo` will be able to do

        >>> x = foo()
        >>> x.things            -> []
        >>> x.addThing(1)
        >>> x.things            -> [1]
        >>> x.removeThing(1)
        >>> x.things            -> []
    """
    def __init__(self, name):
        """Constructor.

        * `name: ` the name of the attribute we are going to append to.
        """
        self.name = name

    def __get__(self, instance, owner):
        """Set method.

        * `instance: ` the object whose attribute we will append to.
        * `owner: ` the `instance`'s class.

        `returns: ` a method called `Add'Thing'` that takes one argument
        which it appends to instance.'name'.
        """
        def func(new_val):
            if instance is None:
                return self

            li = getattr(instance, self.name)[:]
            li.append(new_val)
            setattr(instance, self.name, li)
        func.__name__ = "Add" + self.name.capitalize()
        return func



class RemoveDesc(object):
    """A descriptor that removes a member from a list.

    For example, if a class `foo` is created as:

        class foo(object):
            addThing = AddDesc("thing")
            removeThing = RemoveDesc("thing")
            def __init__(...):
                self.things = []
                ...

    then an instance `x` of class `foo` will be able to do

        >>> x = foo()
        >>> x.things            -> []
        >>> x.addThing(1)
        >>> x.things            -> [1]
        >>> x.removeThing(1)
        >>> x.things            -> []
    """
    def __init__(self, name):
        """Constructor.

        * `name: ` the name of the attribute we are going to append to.
        """
        self.name = name

    def __get__(self, instance, owner):
        """Get method.

        * `instance: ` the object whose attribute we will remove from.
        * `owner: ` the `instance`'s class.

        `returns: ` a method called `Remove'Thing'` that takes one argument
        which it removes from instance.'name'.
        """
        def func(val):
            li = getattr(instance, self.name)[:]
            if val in li:
                li.remove(val)
            setattr(instance, self.name, li)
        func.__name__ = "Remove" + self.name.capitalize()
        return func


        
###################################
# Publisher convinience functions
###################################

def _make_topic_name(obj):
    """Returns the root topic name for all messages coming from `obj`."""
    return ".".join([obj.__class__.__name__, str(obj.id)])

def subscribe(attr, call, obj):
    """Call to tell `threpy5` to call `call` when `obj` changes its `attr`.

    * `attr: ` the name of the attribute to listen to (a string).
    * `call: ` a callable object to call when `attr` is updated.
    * `obj: ` the object whose attribute `attr` we want to track.
    """
    topic = ".".join([_make_topic_name(obj), "UPDATE_" + attr.upper()])
    pub.subscribe(call, topic)



######################
# Card classes
######################

class Card(object):
    """`Card` is a "virtual 3x5 index card". They are assumed to lie on a
    surface and relative position to one another is very important.

    As an abstract class, its inheritors specialize in handling text
    (`Content`), titles (`Header`), or images (`Image`).

    Always create a `Card` with its final id (don't use the default id) and
    never change it. Weird things happend when you change ids, though it
    could be possible if done carefully.
    """

    id = IDPublisher()
    rect = RectPublisher()

    def __init__(self, id=NO_ID, rect=NO_RECT):
        """Constructor.

        * `id: ` this `Card`'s identification number.
        * `rect: ` (x, y, w, h), accepts floats.
        """
        Card.id.setTopic(self, _make_topic_name(self))
        subscribe("id", self._on_set_id, self)
        self.id = id
        
        self.rect = rect

        
    ### properties

    @property
    def Position(self):
        """The position of this `Card`.

        `returns: ` a (x, y) tuple of floats.
        """
        return namedtuple("Point", "x y")(self.rect[0], self.rect[1])

    @Position.setter
    def Position(self, pt):
        """Set the position of this `Card`."""
        self.rect[0], self.rect[1] = pt[0], pt[1]

    @property
    def Size(self):
        """The size of this `Card`.

        `returns: ` a (x, y) tuple of floats.
        """
        return namedtuple("Size", "w h")(self.rect[2], self.rect[3])

    @Size.setter
    def Size(self, sz):
        """Set the position of this `Card`."""
        self.rect[2], self.rect[3] = sz[0], sz[1]

        
    ### methods

    def _register_topic(self):
        """Sets the topic name with which this `Card` will publish its property
        updates. The topic name for a property "foo" is "id.UPDATE_FOO".
        
        Called automatically in __init__ for all properties, including the ones
        defined in child classes, so there's no need to register again. Called
        automatically every time the id is set.
        """
        for attr in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr), Publisher):
                getattr(self.__class__, attr).setTopic(self, str(self.id))
    
    def MoveBy(self, dx, dy):
        """Move the card relateive to its current position.

        * `dx: ` amount to move in the horizontal direction.
        * `dy: ` amount to move in the vertical direction.
        """
        self.Position = (self.rect[0] + dx, self.rect[1] + dy)

    def Dump(self):
        """Return a dict holding all this `Card`'s data. When overriding,
        call this method and append all adittional data to the object returned.
        
        `returns: ` an object holding data. Generally, a `dict`.
        """
        return {"id": self.id, "rect": self.rect}

    def Load(self, data):
        """Read data from an object and load it into this `Card`.

        * `obj: ` must be a dict in the format returned by `Card.Dump`.
        """
        self.id = data["id"]
        self.rect = data["rect"]

        
    ### subscribers

    def _on_set_id(self, val):
        for attr in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr), Publisher):
                getattr(self.__class__, attr).setTopic(self, _make_topic_name(self))



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
    KIND_LBL_CONCEPT    = "Concept"
    KIND_LBL_RESEARCH   = "Research"
    KIND_LBL_ASSUMPTION = "Assumption"
    KIND_LBL_FACT       = "Fact"
    KIND_LBLS = [KIND_LBL_CONCEPT, KIND_LBL_RESEARCH, KIND_LBL_ASSUMPTION, KIND_LBL_FACT]
    
    RATING_MAX = 3
    DEFAULT_RECT_CONT = (0,0,250,150)

    title = TitlePublisher()
    kind = KindPublisher()
    rating = RatingPublisher()
    content = ContentPublisher()
    collapsed = CollapsedPublisher()

    def __init__(self, id=NO_ID, rect=DEFAULT_RECT_CONT, title="", kind=DEFAULT_KIND, rating=DEFAULT_RATING, content="", collapsed=False):
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



class Header(Card):
    """`Card` that holds a title or header."""

    header = HeaderPublisher()

    def __init__(self, id=NO_ID, rect=NO_RECT, header=""):
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

    def __init__(self, id=NO_ID, rect=NO_RECT, path="", scale=DEFAULT_SCALE):
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

    Add = AddDesc("pts")
    Remove = RemoveDesc("pts")

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

    Add = AddDesc("lines")
    Remove = RemoveDesc("lines")

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

    Add = AddDesc("members")
    Remove = RemoveDesc("members")

    def __init__(self, id=NO_ID, members=[]):
        """Constructor.

        * `id: ` idenfitication number.
        * `members: ` a list of identification numbers from `Card`s.
        """
        self.id = id
        self.members = members



class Deck(object):
    """It's a collection of `Card`s that share a common topic. It can also hold
    many `CardGroup`s. A `Card` from a `Deck` may have the same id as a `CardGroup`
    but not the same id as another `Card` from the same `Deck`.
    """

    id = IDPublisher()
    name = NamePublisher()
    cards = CardsPublisher()
    groups = GroupsPublisher()

    AddCard = AddDesc("cards")
    RemoveCard = RemoveDesc("cards")
    AddGroup = AddDesc("groups")
    RemoveGroup = RemoveDesc("groups")

    def __init__(self, id=NO_ID, name="", cards=[], groups=[]):
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

class AnnotatedDeck(Deck):
    """A collection of `Card`s that can be annotated on."""

    def __init__(self, id=NO_ID, name="", cards=[], groups=[], lines=[]):
        """Constructor.

        * `id: ` identification number.
        * `name: ` the name of this `Deck`.
        * `cards: ` a list of `Card`s.
        * `groups: ` a list of `CardGroup`s.
        * `lines: ` a list of `Line`s.
        """
        super(AnnotatedDeck, self).__init__(id=id, name=name, cards=cards, groups=groups)
        self.annotation = Annotation(lines=lines)




class Box(object):
    """A `Box` holds various `Deck`s. It is the equivalent of a file at
    application level: every `Box` is stored in one file and every file
    loads one `Box`.
    """

    name = NamePublisher()
    path = PathPublisher()
    decks = DecksPublisher()

    AddDeck = AddDesc("decks")
    RemoveDeck = RemoveDesc("decks")

    def __init__(self, name="", path="", decks=[]):
        """Constructor.

        * `name: ` the name of this `Box`.
        * `path: ` the path to the file on disk.
        * `decks: ` a list of `Deck`s (or `AnnotatedDeck`s).
        """
        self.name = name
        self.path = path
        self.decks = decks
