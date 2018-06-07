# File name: test_parser.py
# Author: Nupur Garg
# Date created: 4/13/2017
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.parser import *
from src.models.error import *


class Test_Parser(unittest.TestCase):

    def test_generate_config_obj(self):
        info = {
                    "generating_suggestions": {
                        "min_diff_complexity_between_slices" : 3,
                        "min_diff_ref_and_live_var" : 4,
                        "min_linenos_diff_reference_livevar_instr" : 4
                    },
                    "validating_suggestions": {
                        "min_lines_in_suggestion" : 3,
                        "min_variables_parameter_in_suggestion" : 1,
                        "max_variables_parameter_in_suggestion" : 6,
                        "max_variables_return_in_suggestion" : 3,
                        "min_lines_func_not_in_suggestion" : 5
                    }
                }
        config = generate_config_obj(info)

        self.assertEqual(config.min_diff_complexity_between_slices, 3)
        self.assertEqual(config.min_diff_ref_and_live_var, 4)
        self.assertEqual(config.min_linenos_diff_reference_livevar_instr, 4)
        self.assertEqual(config.min_lines_in_suggestion, 3)
        self.assertEqual(config.min_variables_parameter_in_suggestion, 1)
        self.assertEqual(config.max_variables_parameter_in_suggestion, 6)
        self.assertEqual(config.max_variables_return_in_suggestion, 3)
        self.assertEqual(config.min_lines_func_not_in_suggestion, 5)

    def test_parse_json_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as context:
            parse_json(filename='no_such_file.json')

    def test_parse_json_file_found(self):
        config = parse_json(filename='src/config/default.json')

        self.assertEqual(config.min_diff_complexity_between_slices, 3)
        self.assertEqual(config.min_diff_ref_and_live_var, 4)
        self.assertEqual(config.min_linenos_diff_reference_livevar_instr, 4)
        self.assertEqual(config.min_lines_in_suggestion, 3)
        self.assertEqual(config.min_variables_parameter_in_suggestion, 1)
        self.assertEqual(config.max_variables_parameter_in_suggestion, 6)
        self.assertEqual(config.max_variables_return_in_suggestion, 3)
        self.assertEqual(config.min_lines_func_not_in_suggestion, 5)
