# File name: counter.py
# Author: Nupur Garg
# Date created: 1/12/2017
# Python Version: 3.5


from src.globals import *


class Counter(object):
    """
    Represents a Counter.

    counter: int
        Integer as a counter.
    """

    def __init__(self, start=0, step=1):
        self.start = start
        self.step = step
        self.reset()

    def reset(self):
        self.counter = self.start

    def increment(self):
        self.counter += self.step
        return self.counter

