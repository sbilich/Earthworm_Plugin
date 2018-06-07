# File name: structures.py
# Author: Nupur Garg
# Date created: 3/31/2017
# Python Version: 3.5


from src.globals import *


class Queue(object):
    """
    Represents a queue.
    """

    def __init__(self):
        self._items = []

    def empty(self):
        return self._items == []

    def init(self, items):
        for item in items:
            self.enqueue(item)

    def enqueue(self, item):
        self._items.insert(0, item)

    def dequeue(self):
        return self._items.pop()

    def size(self):
        return len(self._items)


class QueueInt(Queue):
    """
    Represents a queue of integers.
    """

    def __init__(self):
        super(self.__class__, self).__init__()
        self._min = None

    def enqueue(self, item):
        super(QueueInt, self).enqueue(item)
        if not self._min:
            self._min = item
        self._min = min(item, self._min)

    # Represents minimum visited at any point.
    def min(self):
        return self._min
