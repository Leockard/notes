# -*- coding: utf-8 -*-
"""
Functions that create classes with properties
"""

from copy import deepcopy


######################
# Card classes
######################

def getter_creator(arg, pub=None):
    """Make a function that acts as a getter.

    * `arg: ` the attribute to get.
    * `pub: ` if pub is a `PyPubSub.Publisher`, every time the property
    is get, `pub.sendMessage` will be called, with the message "GET_<ARG>".

    `returns: ` a function with name "get_<arg>".
    """
    def get_template(self):
        return getattr(self, "_"+ arg)
    def get_pub_template(self):
        pub.sendMessage("GET_" + arg.upper())
        return getattr(self, "_"+ arg)
    get_template.__name__ = "get_" + arg
    get_pub_template.__name__ = "get_" + arg

    if pub is not None:
        return get_pub_template
    else:
        return get_template

def setter_creator(arg, pub=None):
    """Make a function that acts as a setter.

    * `arg: ` the attribute to set.
    * `pub: ` if pub is a `PyPubSub.Publisher`, every time the property
    is set, `pub.sendMessage` will be called, with the message "SET_<ARG>".

    `returns: ` a function with name "set_<arg>".
    """
    def set_template(self, new_val):
        setattr(self, "_"+ arg, new_val)
    def set_pub_template(self, new_val):
        pub.sendMessage("SET_" + arg.upper())
        return getattr(self, "_"+ arg)
    set_template.__name__ = "set_" + arg
    set_pub_template.__name__ = "set_" + arg

    if pub is not None:
        return set_pub_template
    else:
        return set_template


def class_prop_creator(class_name, base=object, **attrs):
    """Make a class with one property object for each keyword argument.

    For example,
    
        `class_prop_creator("myclass", base=object, x=10)`

    will return a class with the property `x` (it will have a setter and
    getter function for that attribute).

    * `class_name: ` the name of the new class.
    * `base: ` the base class to inherit from.
    * `attrs: ` for every `prop=init_val` in attrs, the new calss will have
    a property object with name "prop" and initial value "init_val".

    `returns: ` a class with properties.
    """
    def init(self, **kwargs):
        if base is not object:
            base.__init__(self, **kwargs)
        # init values
        for arg, val in attrs.iteritems():
            setattr(self, "_"+arg, val)
        # values passed to init
        for arg, val in kwargs.iteritems():
            if arg in attrs.keys():
                setattr(self, arg, val)
    newclass = type(class_name, (base,), dict(base.__dict__))
    di = dict(newclass.__dict__)
    di["__init__"] = init
    for arg in attrs.keys():
        getter = getter_creator(arg)
        setter = setter_creator(arg)
        di[arg] = deepcopy(getter)
        di[arg] = deepcopy(setter)
        di[deepcopy(arg)] = property(getter, setter)
    newclass = type(class_name, (base,), dict(di))
    return newclass


def prop_pub_decorator(class_, pub):
    """Inherits from class_ and decorates its property setters with calls to pub.

    For example,
    
        `prop_decorator(MyClass, pub)`

    will create a class with name "DecoMyClass" in whcih every one
    of its property setters calls pub.sendMessage after the value
    has been changed.

    * `class_: ` the class we want to inherit from.
    * `pub: ` a PyPubSub to publish messges to.

    `returns: ` a class that publishes the changes of its properties.
    """
    class newclass(class_):
        def __init__(self, **kwargs):
            class_.__init__(self, **kwargs)

    di = {k: v for k,v in class_.__dict__.items()}
    for k, v in newclass.__dict__.items():
        di[deepcopy(k)] = deepcopy(v)
    keys = dir(newclass)
    for arg in [name for name in keys if type(di[name]) is property]:
        getter = getter_creator(arg)
        setter = setter_creator(arg, pub=pub)
        di[arg] = deepcopy(getter)
        di[arg] = deepcopy(setter)
        di[deepcopy(arg)] = property(getter, setter)

    new_name = "Deco" + class_.__name__
    newclass = type(new_name, (class_,), dict(di))
    
    return newclass
