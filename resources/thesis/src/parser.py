# File name: parser.py
# Author: Nupur Garg
# Date created: 4/13/2017
# Python Version: 3.5


import json

from src.globals import *
from src.models.error import *
from src.models.config import Config

import os

dir_path = os.path.dirname(os.path.realpath(__file__))
_DEFAULT_JSON_FILE = dir_path + '/config/default.json'


# Generates a Config object from a dictionary.
def generate_config_obj(info):
    config = Config()
    config.min_diff_complexity_between_slices = info['generating_suggestions']['min_diff_complexity_between_slices']
    config.min_diff_ref_and_live_var = info['generating_suggestions']['min_diff_ref_and_live_var']
    config.min_linenos_diff_reference_livevar_instr = info['generating_suggestions']['min_linenos_diff_reference_livevar_instr']

    config.min_lines_in_suggestion = info['validating_suggestions']['min_lines_in_suggestion']
    config.min_variables_parameter_in_suggestion = info['validating_suggestions']['min_variables_parameter_in_suggestion']
    config.max_variables_parameter_in_suggestion = info['validating_suggestions']['max_variables_parameter_in_suggestion']
    config.max_variables_return_in_suggestion = info['validating_suggestions']['max_variables_return_in_suggestion']
    config.min_lines_func_not_in_suggestion = info['validating_suggestions']['min_lines_func_not_in_suggestion']
    return config


# Parses a JSON file into a Config object.
def parse_json(filename=None):
    filename = filename if filename else _DEFAULT_JSON_FILE
    info = None

    # Opens file.
    try:
        data_file = open(filename, 'r')
    except EnvironmentError as e:
        cwd = os.getcwd()
        raise FileNotFoundError(filename)

    # Gets config object.
    obj_json = data_file.read()
    info = json.loads(obj_json)
    config = generate_config_obj(info)
    data_file.close()
    return config
