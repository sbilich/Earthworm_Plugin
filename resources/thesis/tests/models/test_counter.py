# File name: test_counter.py
# Author: Nupur Garg
# Date created: 1/12/2017
# Python Version: 3.5


import unittest

from src.globals import *
from src.models.counter import Counter


# Test Counter class.
class TestCounter(unittest.TestCase):

   def test_counter(self):
      counter = Counter()
      self.assertEqual(counter.increment(), 1)
      self.assertEqual(counter.increment(), 2)
      counter.reset()
      self.assertEqual(counter.increment(), 1)


if __name__ == '__main__':
    unittest.main()