# -*- coding: utf-8 -*-

register_table = {}

# decorators:
# example of usage
# @register_event
# class MyEvent(Event):
#   ...
# @register_callback(MyEvent)
# def my_callback(info, args, kwargs):
#   ...
# @register_trigger(MyEvent)
# def my_trigger(*args, **kwargs):
#  ...
# then just call my_trigger and callbacks will be automatically
# called

from functools import wraps

class Event: pass

class Stop(BaseException):
    pass

def register_callback(event):
    def decorator(function):
        register_table[event].append(function)
        return function
    return decorator


def register_event(event):
    if not issubclass(event, Event):
        raise TypeError("%s is not an event (it doesn't subclass Event)" % str(event))
    register_table[event] = []
    return event

# callbacks should

def register_trigger(event):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            if event not in register_table:
                raise TypeError("Event %s isn't registered" % str(event))
            for callback in register_table[event]:
                try:
                    callback((event, False, None), *args, **kwargs)
                except Stop:
                    return
            result = function(*args, **kwargs)
            for callback in register_table[event]:
                try:
                    callback((event, True, result), *args, **kwargs)
                except Stop:
                    return result
            return result
        return wrapper
    return decorator
        
