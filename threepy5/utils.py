# -*- coding: utf-8 -*-
"""This module contains python classes and functions that could be
used outside of `threepy5`.
"""

#####################################################
#             General purpose classes               #
#####################################################

###########################
# listener class
###########################

from wx.lib.pubsub import pub

class listener(object):
    """Helper class that subscribes to pubsub messges. Used for debugging."""
    
    def __init__(self, topics=[]):
        """Constructor.

        * `topics: ` a list of topic names to subscribe.
        """
        self.calls = {}
        for t in topics:
            pub.subscribe(self.callback, t)
        
    def callback(self, topic=pub.AUTO_TOPIC, **kwargs):
        """The callback for all subscribed methods."""
        name = topic.getName()
        print name
        if not name in self.calls.keys():
            self.calls[name] = 0
        self.calls[name] += 1

    def addTopic(self, topic):
        """Add a new topic to subscribe to."""
        pub.subscribe(self.callback, topic)


###########################
# Rect recordtype
###########################

import recordtype

class Rect(recordtype.recordtype('Rect', [('left', 0), ('top', 0), ("width", 0), ("height", 0)])):
    """Minimal rectanble functionality. Used in `Card` classes."""
    
    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


###########################
# WithId class
###########################

import itertools

class WithId(object):
    """A class that automatically assigns a new, unique ID to each of
    its instances on construction."""
    _newid = itertools.count().next
    
    def __init__(self):
        """Constructor."""
        super(WithId, self).__init__()
        self._id = WithId._newid()
        


###########################
# Loud descriptor classes
###########################

from weakref import WeakKeyDictionary as weakdict
from wx.lib.pubsub import pub

class LoudObj(object):
    """Abstract class. An object that sends messages to pubsub."""

    def __init__(self, subtopic):
        """Constructor.

        * `subtopic: ` the subtopic for all messages from this object.
        """
        super(LoudObj, self).__init__()
        self._subtopic = subtopic
        self._loud = True

    def silently(self, call, *args, **kwargs):
        """Do something without publishing a message.

        * `call: ` callable to execute without sending message.
        * `args: ` arguments to pass to `call`.
        * `kwargs: ` keyword arguments to pass to `call`.
        """
        self._loud = False
        call(*args, **kwargs)
        self._loud = True

                
class LoudSetter(LoudObj):
    """A descriptor that publishes its updates, by calling `pub.sendMessage`
    every time `__set__` is called. Child classes *must* contain the name
    "LoudSetter" at the beginning of their name.

    The topic name we publish with is based on the last word of the name of the
    derived class. By default, if the class is called `LoudSetterFoo`, the topic
    will be named "UPDATE_FOO".

    However, `LoudSetter` also provides a method to specify the root topic for
    the message. If an instance with a `LoudSetterFoo` descriptor calls
    `LoudSetterFoo.setTopic(instance, owner, topic)`, the new topic name will be
    `topic.UPDATE_FOO`.
    """
    def __init__(self, default):
        """Constructor.

        * `default: ` the default value returned the first time `x.prop` is referenced.
        """
        name = self.__class__.__name__[10:]
        super(LoudSetter, self).__init__(subtopic = "UPDATE_" + name.upper())

        self._name = "_" + name.lower()
        self._default = default

    def __get__(self, instance, owner):
        """Get method.

        * `instance: ` the object referencing this descriptor.
        * `owner: ` the `instance`'s class.

        `returns: ` the data value of `instance` corresponding to this descriptor."""
        if instance is None:
            return self
        else:
            # print "getting"

            # we use __dict__ directly since we need to store the data in the instance
            # and we can't use getattr() because that's just going to call this method again
            if self._name in instance.__dict__.keys():
                attr = instance.__dict__[self._name]
            else:
                attr = self._default
                instance.__dict__[self._name] = attr
            return attr

    def __set__(self, instance, value):
        """Set method.

        * `instance: ` the instance whose data we're setting.
        * `value: ` the new value to set.
        """
        topic = instance._root + "." + self._subtopic
        # print "publishing %s for %s with topic: %s" % (str(value), str(instance), topic)

        # we use __dict__ directly since we need to store the data in the instance
        # and we can't use getattr() because that's just going to call this method again
        instance.__dict__[self._name] = value
        if self._loud:
            pub.sendMessage(topic, val=value)

    def silently(self, instance, value):
        """Overridden from `LoudObj`. Calls `__set__` without publishing a message."""
        super(LoudSetter, self).silently(self.__set__, instance=instance, value=value)



def makeLoudSetter(name, default):
    """Creates a `LoudSetter` class. The new class will be called "LoudSetter'Name'",
    and it will publish its calls with the subtopic "UPDATE_'NAME'".

    * `name: ` the name of the new `LoudSetter` subclass.
    * `default: ` the default value for the attributes created with the new `LoudSetter` class.

    `returns: ` a `LoudSetter` class.
    """
    class newLoudSetter(LoudSetter):
        def __init__(self, default=default):
            super(newLoudSetter, self).__init__(default=default)
    newLoudSetter.__name__ = "LoudSetter" + name
    return newLoudSetter



########################
# Publisher class
########################

NO_ID = -1
LoudSetterID = makeLoudSetter("ID", NO_ID)

class Publisher(WithId):
    """A class that holds `LoudObj`s. Manages the root topic for all its attributes. """
    _id = LoudSetterID()

    def __init__(self):
        """Constructor."""
        # let WithId.__init__ set our id
        super(Publisher, self).__init__()

        # listen to whenever our _id changes, so that we can set topics again
        pub.subscribe(self._on_set_id, self._root + "." + "UPDATE_ID")

    def __del__(self):
        """Publishes a "DESTROY" message. Called automatically on destruction."""
        # since we are not touching an attribute, we need to set the full topic
        # print "destroy!", self._root
        pub.sendMessage(self._root + "." + "DESTROY")

    @property
    def _root(self):
        """Returns the root topic name for all messages coming from this object."""
        return ".".join([self.__class__.__name__, str(self._id)])

    def _on_set_id(self, val):
        """Called when the _id of this object changes loudly."""
        pub.subscribe(self._on_set_id, self._root + "." + "UPDATE_ID")

        

#########################
# LoudMethod class
#########################

class LoudMethod(LoudObj):
    """Descriptor class for a method that publishes its calls. Assumes the
    owner has a `_root` attribute (e.g. a `Publisher`) that will be used as
    the root topic for the messages.

    For example, if foo is a `Publisher` object with a list attribute called `li`
    and `LoudAppend` is a subclass of `LoudMethod`, then any call of the form
    `foo.li.append(...)` will publish a message with a root topic taken from the
    `Publisher` object and a subtopic taken from this class.
    """
    
    def __init__(self, attr, method, subtopic):
        """Constructor.

        * `attr: ` the name of the attribute on which `method` is called.
        * `method: ` the `method` whose calls are published.
        * `subtopic: ` subtopic to publish the calls with.
        """
        super(LoudMethod, self).__init__(subtopic=subtopic)
        self._attr = attr
        self._method = method
        self._name = self.__class__.__name__[4:]

    def __get__(self, instance, owner):
        """Get the modified method.

        * `instance: ` the `Publisher` object.
        * `owner: ` the class of `instance`.

        * `returns: ` a function that calls the usual method and publishes it afterward.
        """
        if instance is None:
            return self
            
        def func(val):
            call = getattr(getattr(instance, self._attr), self._method)
            call(val)

            topic = instance._root + "." + self._subtopic
            if self._loud:
                pub.sendMessage(topic, val=val)

        func.__name__ = self._name + self._attr.capitalize()
        return func

class LoudAppend(LoudMethod):
    """A `LoudMethod` class for the `append` method in a list attribute.
    Publishes the calls with the topic "NEW_<ATTR>" where <ATTR> is the name
    of the list attribute in uppercase."""
    def __init__(self, attr):
        super(LoudAppend, self).__init__(attr, "append", "NEW_" + attr[:-1].upper())

class LoudRemove(LoudMethod):
    """A `LoudMethod` class for the `remove` method in a list attribute.
    Publishes the calls with the topic "POP_<ATTR>" where <ATTR> is the name
    of the list attribute in uppercase."""
    def __init__(self, attr):
        super(LoudRemove, self).__init__(attr, "remove", "POP_" + attr[:-1].upper())

    
#####################################################
#             General purpose functions             #
#####################################################

from math import sqrt

def isnumber(s):
    """Return True of the argument is a string representing a number.
    
    * `s: ` a string.
    
    `returns: ` `True` if `s` is a number, or `False`.
    """
    try:
        float(s)
        return True
    except ValueError:
        return False

def dist2(p1, p2):
    """Returns the squared euclidean distance between two points.

    * `p1: ` any object with two fields addressable as `p1[0]` and `p1[1]`.
    * `p2: ` idem.

    `returns: ` the squared distance, always a `float`.
    """
    return float(sum([i**2 for i in p1 - p2]))

def dist(p1, p2):
    """Returns the euclidean distance betwen two points.

    * `p1: ` any object with two fields addressable as `p1[0]` and `p1[1]`.
    * `p2: ` idem.

    `returns: ` the distance, always a `float`.
    """
    return float(sqrt(dist2(p1, p2)))





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
for field in dir(object):
    __pdoc__['listener.%s' % field] = None
for field in dir(recordtype.recordtype):
    __pdoc__['Rect.%s' % field] = None
for field in dir(object):
    __pdoc__['WithId.%s' % field] = None
for field in dir(object):
    __pdoc__['LoudObj.%s' % field] = None    
for field in dir(LoudObj):
    __pdoc__['LoudSetter.%s' % field] = None
for field in dir(WithId):
    __pdoc__['Publisher.%s' % field] = None
for field in dir(LoudObj):
    __pdoc__['LoudMethod.%s' % field] = None    
for field in dir(LoudMethod):
    __pdoc__['LoudAppend.%s' % field] = None
for field in dir(LoudMethod):
    __pdoc__['LoudRemove.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in listener.__dict__.keys():
    if 'listener.%s' % field in __pdoc__.keys():
        del __pdoc__['listener.%s' % field]
for field in Rect.__dict__.keys():
    if 'Rect.%s' % field in __pdoc__.keys():
        del __pdoc__['Rect.%s' % field]
for field in WithId.__dict__.keys():
    if 'WithId.%s' % field in __pdoc__.keys():
        del __pdoc__['WithId.%s' % field]
for field in LoudObj.__dict__.keys():
    if 'LoudObj.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudObj.%s' % field]        
for field in LoudSetter.__dict__.keys():
    if 'LoudSetter.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudSetter.%s' % field]
for field in Publisher.__dict__.keys():
    if 'Publisher.%s' % field in __pdoc__.keys():
        del __pdoc__['Publisher.%s' % field]
for field in LoudMethod.__dict__.keys():
    if 'LoudMethod.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudMethod.%s' % field]
for field in LoudAppend.__dict__.keys():
    if 'LoudAppend.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudAppend.%s' % field]
for field in LoudRemove.__dict__.keys():
    if 'LoudRemove.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudRemove.%s' % field]
