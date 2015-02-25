# -*- coding: utf-8 -*-
"""
Functions that create classes with properties
"""

def getter_creator(arg):
    """Make a function that acts as a getter.

    * `arg: ` the attribute to get.

    `returns: ` a function with name "get_'arg'>".
    """
    def get_template(self):
        return getattr(self, "_"+ arg)
    get_template.__name__ = "get_" + arg
    return get_template


def setter_creator(arg):
    """Make a function that acts as a setter.

    * `arg: ` the attribute to set.

    `returns: ` a function with name "set_'arg'".
    """
    def set_template(self, new_val):
        print "setter ", arg, " : ", new_val
        setattr(self, "_"+ arg, new_val)
    set_template.__name__ = "set_" + arg
    return set_template


def class_prop_creator(class_name, base=object, **attrs):
    """Make a class with one property object for each keyword argument.

    For example,
    
        class_prop_creator("myclass", base=object, x=10)

    will return a class with the property `x` (it will have a setter and
    getter function for that attribute) whose initial value is 10.

    * `class_name: ` the name of the new class.
    * `base: ` the base class to inherit from.
    * `attrs: ` for every `prop=init_val` in `attrs`, the new calss will have
    a property object with name "prop" and initial value "init_val".

    `returns: ` a class with properties.
    """
    # create a new class
    class newclass(base):
        pass
    setattr(newclass, "__name__", class_name)

    # create the new init function and assign it to the new class
    def init(self, **kwargs):
        if base is not object:
            base.__init__(self, **kwargs)
        # default values
        for arg, val in attrs.iteritems():
            setattr(self, "_"+arg, val)
        # values passed to init
        for arg, val in kwargs.iteritems():
            if arg in attrs.keys():
                setattr(self, "_"+arg, val)
    setattr(newclass, "__init__", init)

    # for every keyword argument, create a property and add it to the new class
    for arg in attrs.keys():
        getter = getter_creator(arg)
        setter = setter_creator(arg)
        setattr(newclass, arg, property(getter, setter))

    return newclass


def pub_func(func, pub, msg):
    """Decorates `func` to publish its calls to a PubSub.Publisher object.
    After each call of the decorated function, it will call `pub.sendMessage` with
    the message `msg` and the keyword argument "data" which it will take from the first
    argument to the decorated function.

    * `pub: ` a PubSub.Publisher to publish to.
    + `msg: ` the message to publish.

    `returns: ` a decorated function.
    """
    def decorated(self, *args, **kwargs):
        print func.__name__, args
        # pub.sendMessage(msg, data=args[0])
        return func(self, *args, **kwargs)
    setattr(decorated, "__name__", func.__name__)
    return decorated


def pub_class(class_, pub):
    """Decorates `class_` so that all its properties' setters publish their calls.
    For example, if `class_` has a property `x` and we decorate it, every time the
    property `x` is assigned to a new value, it will publish to `pub` with the
    message "UPDATE_X".
    
    The returned class has a magic variable `__decorated__` which is a list of all
    decorated methods of the class. `pub_class` checks this variable before decorating
    a class, to avoid double decorating.

    * `class_: ` the class to decorate.
    * `pub: ` a PubSub.Publisher to publish to.

    `returns: ` a decorated class.
    """
    to_decorate = {attr_name: getattr(class_, attr_name)
                   for attr_name in dir(class_)
                   if type(getattr(class_, attr_name)) is property}

    # remove the previously decorated properties
    if hasattr(class_, "__decorated__"):
        for key in to_decorate.keys():
            if key in class_.__decorated__:
                del to_decorate[key]
    
    decorated = []                
    for name, prop in to_decorate.items():
        setter = pub_func(prop.fset, pub, "UPDATE_" + name.upper())
        setattr(class_, name, property(prop.fget, setter))
        decorated.append(name)
        
    if hasattr(class_, "__decorated__"):
        decorated.extend(class_.__decorated__)
    setattr(class_, "__decorated__", decorated)
    return class_
