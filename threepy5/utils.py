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

class LoudObj(object):

    def __init__(self, subtopic):
        super(LoudObj, self).__init__()
        self._subtopic = subtopic
        self._loud = True

    def silently(self, call, *args, **kwargs):
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
        super(LoudSetter, self).silently(self.__set__, instance=instance, value=value)



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
# Add/Remove descriptors
#########################

class LoudMethod(LoudObj):
    """Assumes the owner is a Publisher with a _root."""
    def __init__(self, attr, method, subtopic):
        """Constructor.

        * `name: ` the name of the attribute we are going to append to.
        """
        super(LoudMethod, self).__init__(subtopic=subtopic)
        self._attr = attr
        self._method = method
        self._name = self.__class__.__name__[4:]

    def __get__(self, instance, owner):
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
    def __init__(self, attr):
        super(LoudAppend, self).__init__(attr, "append", "NEW_" + attr[:-1].upper())

class LoudRemove(LoudMethod):
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
# for field in LoudAppend.__dict__.keys():
#     if 'LoudAppend.%s' % field in __pdoc__.keys():
#         del __pdoc__['LoudAppend.%s' % field]
# for field in LoudRemove.__dict__.keys():
#     if 'LoudRemove.%s' % field in __pdoc__.keys():
#         del __pdoc__['LoudRemove.%s' % field]
