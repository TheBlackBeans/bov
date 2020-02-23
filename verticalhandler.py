### Vertical Handler module
# Defines classes, events and exceptions used to transmit signals
# vertically

import heapq

class QuitGame(BaseException):
    pass

def iterate_heap(heap, disabled):
    heap = heap.copy()
    while heap:
        priority, value = heapq.heappop(heap)
        if priority not in disabled:
            yield value

class KeyHandler:
    def __init__(self):
        self.callbacks = []
        self.disabled = set()
    def add_handler(self, priority):
        def decorator(function):
            heapq.heappush(self.callbacks, (-priority, function))
            return function
        return decorator
    def dispatch_key(self, key):
        for function in iterate_heap(self.callbacks, self.disabled):
            if function(key):
                break
    def disable_handler(self, priority):
        self.disabled.add(-priority)
    def enable_handler(self, priority):
        if -priority in self.disabled:
            self.disabled.remove(-priority)
    def remove_handler(self, priority):
        i = 0
        while i < len(self.callbacks):
            if self.callbacks[i][0] == -priority:
                self.callbacks.pop(i)
            else:
                i += 1
        heapq.heapify(self.callbacks)
