# File name: test_structures.py
# Author: Nupur Garg
# Date created: 2/22/2017
# Python Version: 3.5


import unittest
import ast
import copy

from src.globals import *
from src.generatecfg import CFGGenerator
from src.models.slice import *
from src.models.block import BlockList
from src.models.instruction import Instruction
from src.models.structures import Queue, QueueInt


# Tests Queue class.
class TestQueue(unittest.TestCase):

    def setUp(self):
        self.queue = Queue()

    def test_empty(self):
        self.assertEqual(self.queue._items, [])
        self.assertTrue(self.queue.empty())
        self.assertEqual(self.queue.size(), 0)

    def test_init(self):
        self.assertTrue(self.queue.empty())
        self.queue.init([5, 10, 20])
        self.assertEqual(self.queue.size(), 3)

        self.assertEqual(self.queue.dequeue(), 5)
        self.assertEqual(self.queue.size(), 2)
        self.assertEqual(self.queue.dequeue(), 10)
        self.assertEqual(self.queue.size(), 1)
        self.assertEqual(self.queue.dequeue(), 20)
        self.assertTrue(self.queue.empty())

    def test_enqueue(self):
        self.assertTrue(self.queue.empty())
        self.queue.enqueue(5)
        self.assertEqual(self.queue.size(), 1)
        self.queue.enqueue(10)
        self.assertEqual(self.queue.size(), 2)
        self.queue.enqueue(20)
        self.assertEqual(self.queue.size(), 3)

    def test_dequeue(self):
        self.assertTrue(self.queue.empty())
        self.queue.enqueue(5)
        self.queue.enqueue(10)
        self.queue.enqueue(20)
        self.assertEqual(self.queue.size(), 3)

        self.assertEqual(self.queue.dequeue(), 5)
        self.assertEqual(self.queue.size(), 2)
        self.assertEqual(self.queue.dequeue(), 10)
        self.assertEqual(self.queue.size(), 1)
        self.assertEqual(self.queue.dequeue(), 20)
        self.assertTrue(self.queue.empty())


# Tests QueueInt class.
class TestQueueInt(unittest.TestCase):

    def setUp(self):
        self.queue = QueueInt()

    def test_min(self):
        self.assertTrue(self.queue.empty())
        self.queue.enqueue(10)
        self.assertEqual(self.queue.min(), 10)
        self.queue.enqueue(5)
        self.assertEqual(self.queue.min(), 5)
        self.queue.enqueue(20)
        self.assertEqual(self.queue.min(), 5)
        self.assertEqual(self.queue.size(), 3)

        self.assertEqual(self.queue.dequeue(), 10)
        self.assertEqual(self.queue.min(), 5)
        self.assertEqual(self.queue.dequeue(), 5)
        self.assertEqual(self.queue.min(), 5)
        self.assertEqual(self.queue.dequeue(), 20)
        self.assertEqual(self.queue.min(), 5)
        self.assertTrue(self.queue.empty())
