# -*- coding: utf-8 -*-
"""This module contains python classes and functions that could be
used outside of `threepy5`.
"""


###########################
# General purpose classes
###########################




###########################
# General purpose functions
###########################

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
for field in dir(wx.ScrolledWindow):
    __pdoc__['AutoSize.%s' % field] = None
for field in dir(wx.TextCtrl):
    __pdoc__['ColouredText.%s' % field] = None
for field in dir(ColouredText):
    __pdoc__['EditText.%s' % field] = None

# Then, we have to add again the methods that we have
# overriden. See https://github.com/BurntSushi/pdoc/issues/15.
for field in AutoSize.__dict__.keys():
    if 'AutoSize.%s' % field in __pdoc__.keys():
        del __pdoc__['AutoSize.%s' % field]
for field in ColouredText.__dict__.keys():
    if 'ColouredText.%s' % field in __pdoc__.keys():
        del __pdoc__['ColouredText.%s' % field]
for field in EditText.__dict__.keys():
    if 'EditText.%s' % field in __pdoc__.keys():
        del __pdoc__['EditText.%s' % field]
