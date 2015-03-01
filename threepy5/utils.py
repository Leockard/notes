# -*- coding: utf-8 -*-
"""This module contains python classes and functions that could be
used outside of `threepy5`.
"""

#####################################################
#             General purpose classes               #
#####################################################

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

class LoudSetter(object):
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
        super(LoudSetter, self).__init__()
        self._publish = True
        self._default = default
        self._data = weakdict()
        self._topics = weakdict()
        self._subtopic = "UPDATE_" + self.__class__.__name__[10:].upper()

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
        topic = ""
        topic = self._topics.get(instance, "")

        if topic:
            topic += "."
        topic += self._subtopic

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


def makeLoudSetter(name, default):
    """Creates a `LoudSetter` class. The new class will be called "LoudSetter'Name'",
    and it will publish its calls with the subtopic "UPDATE_'NAME'".
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
    _id = LoudSetterID()

    def __init__(self):
        """Constructor."""
        # let WithId.__init__ set our id
        super(Publisher, self).__init__()

        # set the topics for all properties appropriately, including _id
        self._register_topics()

        # listen to whenever our _id changes, so that we can set topics again
        pub.subscribe(self._on_set_id, self._make_topic_name() + "." + "UPDATE_ID")

    def __del__(self):
        """Publishes a "DESTROY" message. Called automatically on destruction."""
        # since we are not touching an attribute, we need to set the full topic
        print "__del__"
        print "id: ", self._id
        print "topic: ", self._make_topic_name()
        # print self._make_topic_name() + "." + "DESTROY"
        pub.sendMessage(self._make_topic_name() + "." + "DESTROY")

    def _make_topic_name(self):
        """Returns the root topic name for all messages coming from this object."""
        return ".".join([self.__class__.__name__, str(self._id)])

    def _register_topics(self):
        """Registers the topic for all `Loud` attributes."""
        for attr in dir(self.__class__):
            if isinstance(getattr(self.__class__, attr), LoudSetter):
                # print "setting %s topic for %s" % (self._make_topic_name(), attr)
                getattr(self.__class__, attr).setTopic(self, self._make_topic_name())
                
        # since we allso changed the id, we need to subscribe to the new topic
        pub.subscribe(self._on_set_id, self._make_topic_name() + ".UPDATE_ID")

    def _on_set_id(self, val):
        """Called when the _id of this object changes loudly."""
        self._register_topics()



#########################
# Add/Remove descriptors
#########################

class AddDesc(object):
    """A descriptor that adds an object to a list.

    For example, if a class `foo` is created as:

        class foo(object):
            addThing = AddDesc("things")
            removeThing = RemoveDesc("things")
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
        super(AddDesc, self).__init__()
        self.name = name

    def __get__(self, instance, owner):
        """Set method.

        * `instance: ` the object whose attribute we will append to.
        * `owner: ` the `instance`'s class.

        `returns: ` a method called `Add'Thing'` that takes one argument
        which it appends to `instance.'name'`.
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
        super(RemoveDesc, self).__init__()
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
    __pdoc__['LoudSetter.%s' % field] = None
for field in dir(object):
    __pdoc__['AddDesc.%s' % field] = None
for field in dir(object):
    __pdoc__['RemoveDesc.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in LoudSetter.__dict__.keys():
    if 'LoudSetter.%s' % field in __pdoc__.keys():
        del __pdoc__['LoudSetter.%s' % field]
for field in AddDesc.__dict__.keys():
    if 'AddDesc.%s' % field in __pdoc__.keys():
        del __pdoc__['AddDesc.%s' % field]
for field in RemoveDesc.__dict__.keys():
    if 'RemoveDesc.%s' % field in __pdoc__.keys():
        del __pdoc__['RemoveDesc.%s' % field]
