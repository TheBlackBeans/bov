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

def register_trigger(event, context=0):
    # context:
    #  0: no context
    #  1: auto-context: context filled with locals()
    #  2: given-context: context is the first argument (which won't
    #     be passed to the function
    if context not in {0, 1, 2}:
        raise ValueError("Context can be 0, 1 or 2 (%s given)" % context)
    def decorator(function):
        def wrapper(*args, **kwargs):
            if event not in register_table:
                raise TypeError("Event %s isn't registered" % str(event))
            if context == 0:
                c = {}
            elif context == 1:
                c = locals()
            elif context == 2:
                c = args[-1]
                args = args[:-1]
            
            for callback in register_table[event]:
                try:
                    callback((event, False, None, c), *args, *kwargs)
                except Stop:
                    return
                result = function(*args, **kwargs)
                for callback in register_table[event]:
                    try:
                        callback((event, True, result, c), args, kwargs)
                    except Stop:
                        return result
                return result
        return wrapper
    return decorator
        
