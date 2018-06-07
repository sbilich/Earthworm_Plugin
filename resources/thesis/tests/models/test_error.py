# File name: test_error.py
# Author: Nupur Garg
# Date created: 4/13/2017
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.models.error import *


class Test_DecomposerError(unittest.TestCase):

    def test_config_file_not_found_error(self):
        error = FileNotFoundError("test.json")
        self.assertEqual(error.message, "FileNotFoundError: File 'test.json' not found.")

    def test_func_inside_func_error(self):
        error = FuncInsideFuncError(lineno=10)
        self.assertEqual(error.message, "FuncInsideFuncError: Function inside function on line 10.")
