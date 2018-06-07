# File name: test_slice.py
# Author: Nupur Garg
# Date created: 2/22/2017
# Python Version: 3.5


import unittest
import ast
import copy

from src.globals import *
from src.parser import parse_json
from src.generatecfg import CFGGenerator
from src.models.slice import *
from src.models.block import BlockList
from src.models.instruction import Instruction


# Tests Suggestion class.
class TestSuggestion(unittest.TestCase):

    def setUp(self):
        self.ref_vars = ['ref_var', 'ref_var']
        self.ret_vars = ['ret_var']
        self.types = [SuggestionType.REMOVE_VAR]

    def _generate_suggestions_list(self):
        self.suggestion1 = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=1)
        self.suggestion3 = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=3)
        self.suggestion35 = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=3, end_lineno=5)
        self.suggestion4 = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=4)
        self.suggestion4cpy = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=4)
        self.suggestions = [self.suggestion4cpy, self.suggestion1,
                            self.suggestion35, self.suggestion4, self.suggestion3]

    def test_init(self):
        suggestion = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=1)
        self.assertEqual(suggestion.ref_vars, self.ref_vars)
        self.assertEqual(suggestion.ret_vars, self.ret_vars)
        self.assertEqual(suggestion.types, self.types)
        self.assertEqual(suggestion.start_lineno, 1)
        self.assertEqual(suggestion.end_lineno, 1)

        suggestion = Suggestion(self.ref_vars, self.ret_vars, self.types, "funcA", start_lineno=1, end_lineno=3)
        self.assertEqual(suggestion.ref_vars, self.ref_vars)
        self.assertEqual(suggestion.ret_vars, self.ret_vars)
        self.assertEqual(suggestion.types, self.types)
        self.assertEqual(suggestion.start_lineno, 1)
        self.assertEqual(suggestion.end_lineno, 3)

    def test_sort(self):
        self._generate_suggestions_list()
        self.suggestions.sort()

        self.assertEqual(self.suggestions[0], self.suggestion1)
        self.assertEqual(self.suggestions[1], self.suggestion35)
        self.assertEqual(self.suggestions[2], self.suggestion3)
        self.assertEqual(self.suggestions[3], self.suggestion4cpy)
        self.assertEqual(self.suggestions[4], self.suggestion4)

    def test_sorted(self):
        self._generate_suggestions_list()
        self.suggestions = sorted(self.suggestions)

        self.assertEqual(self.suggestions[0], self.suggestion1)
        self.assertEqual(self.suggestions[1], self.suggestion35)
        self.assertEqual(self.suggestions[2], self.suggestion3)
        self.assertEqual(self.suggestions[3], self.suggestion4cpy)
        self.assertEqual(self.suggestions[4], self.suggestion4)

    def test_str(self):
        self.skipTest('TODO: Implement')


# Framework for testing Slice class.
class TestSlice(unittest.TestCase):

    def setUp(self):
        Block._label_counter.reset()

    def _generate_cfg(self, source):
        node = ast.parse(source)
        generator = CFGGenerator(False)
        return generator.generate(node, source)

    def _get_slice_class(self, source):
        cfg = self._generate_cfg(source)
        func = cfg.get_func('funcA')
        config = parse_json()
        return Slice(func, config)

    def _get_instrs_slice(self, source, lineno, **kwargs):
        slicemethod = self._get_slice_class(source)
        instrs = slicemethod._get_instructions_in_slice(lineno, **kwargs)
        return instrs

    def _get_cfg_slice(self, source, lineno):
        slicemethod = self._get_slice_class(source)
        instrs = slicemethod._get_instructions_in_slice(lineno)
        slice_cfg = slicemethod._generate_cfg_slice(instrs)
        return slice_cfg

    def _get_slice(self, source, lineno):
        slicemethod = self._get_slice_class(source)
        instrs = slicemethod._get_instructions_in_slice(lineno)
        return slicemethod.get_slice(instrs)['cfg']

    def assertBlockInstrsEqual(self, block, linenos):
        actual = block.get_instruction_linenos()
        if linenos is None:
            self.assertFalse(actual)
        else:
            self.assertEqual(actual, set(linenos))

    def assertBlockSuccessorsEqual(self, block, successors):
        actual = set(block.successors.keys())
        if successors is None:
            self.assertFalse(actual)
        else:
            self.assertEqual(actual, set(successors))

    def assertBlockPredecessorsEqual(self, block, predecessors):
        actual = set(block.predecessors.keys())
        if predecessors is None:
            self.assertFalse(actual)
        else:
            self.assertEqual(actual, set(predecessors))

    def assertBlockEqual(self, block, linenos=None, predecessors=None, successors=None):
        self.assertBlockInstrsEqual(block, linenos)
        self.assertBlockPredecessorsEqual(block, predecessors)
        self.assertBlockSuccessorsEqual(block, successors)


# Tests Slice generate CFG related helper functions.
class TestSliceGenerateCFGFuncs(TestSlice):

    def _get_source(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n"\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = (y\n'                    # line 5
                  '         + y)\n'                 # line 6
                  '    if (z\n'                     # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        temp = 5\n'              # line 9
                  '        return z\n'              # line 10
                  '    return x\n')                 # line 11
        return source

    def test_get_linenos_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        self.assertEqual(slicemethod.linenos, [1, 2, 5, 6, 7, 8, 9, 10, 11])

    def test_get_variables_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        self.assertEqual(slicemethod.variables, set(['x', 'y', 'z', 'temp']))

    def test_get_map_control_linenos_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        self.assertEqual(slicemethod.controls, {7: set([9, 10])})

    def test_get_block_map_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        self.assertEqual(set(slicemethod.block_map.keys()),
                         set(['funcA', 'L2', 'L3', 'L1']))

    def test_get_map_multiline_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        self.assertEqual(slicemethod.multiline, {2: set([2, 3, 4]), 3: set([2, 3, 4]), 4: set([2, 3, 4]),
                                                 5: set([5, 6]), 6: set([5, 6]),
                                                 7: set([7, 8]), 8: set([7, 8])})

    def test_get_instrs_block_map_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        self.assertEqual(slicemethod.instrs_block_map[1].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[2].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[5].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[6].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[7].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[8].label, 'funcA')
        self.assertEqual(slicemethod.instrs_block_map[9].label, 'L2')
        self.assertEqual(slicemethod.instrs_block_map[10].label, 'L2')
        self.assertEqual(slicemethod.instrs_block_map[11].label, 'L3')

    def test_get_instructions_in_slice_in_func(self):
        source = self._get_source()
        instrs = self._get_instrs_slice(source, 11)
        self.assertEqual(instrs, set([2, 3, 4, 11]))

        instrs = self._get_instrs_slice(source, 10)
        self.assertEqual(instrs, set([1, 2, 3, 4, 5, 6, 7, 8, 10]))

        instrs = self._get_instrs_slice(source, 9)
        self.assertEqual(instrs, set([1, 2, 3, 4, 5, 6, 7, 8, 9]))

    def test_get_instructions_in_slice__include_control(self):
        source = self._get_source()
        instrs = self._get_instrs_slice(source, 11, include_control=False)
        self.assertEqual(instrs, set([2, 3, 4, 11]))

        instrs = self._get_instrs_slice(source, 10, include_control=False)
        self.assertEqual(instrs, set([1, 2, 3, 4, 5, 6, 7, 8, 10]))

        instrs = self._get_instrs_slice(source, 9, include_control=False)
        self.assertEqual(instrs, set([9]))

    def test_get_instructions_in_slice__exclude_vars(self):
        source = self._get_source()

        # Line 11.
        instrs = self._get_instrs_slice(source, 11, exclude_vars=['x'])
        self.assertEqual(instrs, set([11]))

        # Line 10.
        instrs = self._get_instrs_slice(source, 10, exclude_vars=['x'])
        self.assertEqual(instrs, set([1, 5, 6, 7, 8, 10]))

        instrs = self._get_instrs_slice(source, 10, exclude_vars=['y'])
        self.assertEqual(instrs, set([2, 3, 4, 5, 6, 7, 8, 10]))

        instrs = self._get_instrs_slice(source, 10, exclude_vars=['z'])
        self.assertEqual(instrs, set([2, 3, 4, 7, 8, 10]))

        # Line 11.
        instrs = self._get_instrs_slice(source, 9, exclude_vars=['x'])
        self.assertEqual(instrs, set([1, 5, 6, 7, 8, 9]))

        instrs = self._get_instrs_slice(source, 9, exclude_vars=['z'])
        self.assertEqual(instrs, set([2, 3, 4, 7, 8, 9]))

    def _get_source(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n"\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = (y\n'                    # line 5
                  '         + y)\n'                 # line 6
                  '    if (z\n'                     # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        temp = 5\n'              # line 9
                  '        return z\n'              # line 10
                  '    return x\n')                 # line 11
        return source

    def test_get_defined_variables_in_func(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        defined = slicemethod._get_defined_variables_in_func()
        self.assertEqual(defined, set(['x', 'y', 'z', 'temp']))

    def test_get_groups_variables(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        defined = slicemethod._get_defined_variables_in_func()
        groups = slicemethod._get_groups_variables(2, defined)
        self.assertEqual(groups, set([frozenset(['y', 'x']),
                                      frozenset(['x', 'z']),
                                      frozenset(['y', 'z']),
                                      frozenset(['z', 'x']),
                                      frozenset(['x', 'temp']),
                                      frozenset(['temp', 'z'])]))


# Tests Slice condense algorithm related helper functions.
class TestSliceCondenseFuncs(TestSlice):

    def _get_block(self, predecessor=None, successor=None, instructions=None):
        block = Block()
        if predecessor:
            block.add_predecessor(predecessor)
        if successor:
            block.add_successor(successor)
        if instructions:
            for instruction in instructions:
                block.add_instruction(instruction)
        return block

    def test_condense_cfg_fold_redundant_branch__identical(self):
        start_block = FunctionBlock('funcA')
        exit_block = self._get_block()

        successor_block_1 = self._get_block(start_block, exit_block)
        successor_block_2 = self._get_block(start_block, exit_block)
        successor_block_3 = self._get_block(start_block, exit_block)

        self.assertFalse(start_block.predecessors)
        self.assertEqual(len(start_block.successors), 3)
        self.assertEqual(len(exit_block.predecessors), 3)
        self.assertFalse(exit_block.successors)

        config = parse_json()
        slicemethod = Slice(start_block, config)
        slicemethod._condense_cfg_fold_redundant_branch(start_block)

        # Check for change after calling function.
        self.assertFalse(start_block.predecessors)
        self.assertEqual(len(start_block.successors), 1)
        self.assertEqual(len(exit_block.predecessors), 1)
        self.assertFalse(exit_block.successors)

        self.assertTrue(successor_block_1.label in start_block.successors)
        self.assertTrue(successor_block_1.label in exit_block.predecessors)

        self.assertEqual(len(successor_block_1.successors), 1)
        self.assertEqual(len(successor_block_1.predecessors), 1)
        self.assertFalse(successor_block_2.predecessors)
        self.assertFalse(successor_block_2.successors)
        self.assertFalse(successor_block_3.predecessors)
        self.assertFalse(successor_block_3.successors)

    def test_condense_cfg_fold_redundant_branch__non_identical(self):
        instructions = [Instruction(lineno=1)]
        start_block = FunctionBlock('funcA')
        exit_block = self._get_block()

        successor_block_1 = self._get_block(start_block, exit_block)
        successor_block_2 = self._get_block(start_block, exit_block)
        successor_block_3 = self._get_block(start_block, exit_block, instructions)

        self.assertFalse(start_block.predecessors)
        self.assertEqual(len(start_block.successors), 3)
        self.assertEqual(len(exit_block.predecessors), 3)
        self.assertFalse(exit_block.successors)

        config = parse_json()
        slicemethod = Slice(start_block, config)
        slicemethod._condense_cfg_fold_redundant_branch(start_block)

        # Check for no change after calling function.
        self.assertFalse(start_block.predecessors)
        self.assertEqual(len(start_block.successors), 3)
        self.assertEqual(len(exit_block.predecessors), 3)
        self.assertFalse(exit_block.successors)

    def test_condense_cfg_remove_empty_block(self):
        # On line 218.
        self.skipTest('TODO: Implement (Important)')

    def test_condense_cfg_combine_blocks(self):
        # On line 234.
        self.skipTest('TODO: Implement (Important)')

    def test_condense_cfg_hoist_branch(self):
        # On line 250.
        self.skipTest('TODO: Implement (Important)')


# Tests Slice generating slice and slice map related helper functions.
class TestSliceGenerateSliceFuncs(TestSlice):

    def _get_source(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n"\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = (y\n'                    # line 5
                  '         + y)\n'                 # line 6
                  '    if (z\n'                     # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        temp = 5\n'              # line 9
                  '        return z\n'              # line 10
                  '    return x\n')                 # line 11
        return source

    def test_get_slice__check_cache(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        instrs = slicemethod._get_instructions_in_slice(10)
        slice_cfg = slicemethod.get_slice(instrs)

        instrs = frozenset(instrs)
        self.assertEqual(set(slicemethod._SLICE_CACHE.keys()), set([instrs]))
        self.assertEqual(slicemethod._SLICE_CACHE[instrs], slice_cfg)

    def test_get_slice_map__check_keys(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        slice_map = slicemethod.get_slice_map()

        self.assertEqual(set(slice_map.keys()), set([1, 2, 5, 6, 7, 8, 9, 10, 11]))
        self.assertTrue(len(slicemethod._SLICE_CACHE.keys()) > 0)

    def test_get_slice_map__kwargs_check_keys(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        slice_map = slicemethod.get_slice_map(include_control=False)

        self.assertEqual(set(slice_map.keys()), set([1, 2, 5, 6, 7, 8, 9, 10, 11]))
        self.assertTrue(len(slicemethod._SLICE_CACHE.keys()) > 0)


# Tests Slice comparing slice map related helper functions.
class TestSliceCompareSliceMapFuncs(TestSlice):

    def _get_source(self, var):
        source = ('def funcA():\n'                      # line 1
                  '     a = 5\n'                        # line 2
                  '     hpixels = 5\n'                  # line 3
                  '     wpixels = 10\n'                 # line 4
                  '     for y in range(5):\n'           # line 5
                  '         for x in range(2):\n'       # line 6
                  '             hpixels += 1\n'         # line 7
                  '             new_var = 0\n'          # line 8
                  '         wpixels += 1\n'             # line 9
                  '     print(%s)\n' %var)              # line 10
        return source

    def _get_source_complex(self):
        source = ('def funcA(a):\n'                    # line 1
                  '    idx = 0\n'                      # line 2
                  '    if a < 5:\n'                    # line 3
                  '        a = 5\n'                    # line 4
                  '    check_cond = True\n'            # line 5
                  '    while check_cond:\n'            # line 6
                  '        if (a <\n'                  # line 7
                  '               0):\n'               # line 8
                  '            check_cond = False\n'   # line 9
                  '\n'                                 # line 10
                  '        if (idx > 100 or\n'         # line 11
                  '             a == 243):\n'          # line 12
                  '            return a\n'             # line 13
                  '        idx += 1\n'                 # line 14
                  '        a -= 1\n'                   # line 15
                  '    print(idx)\n'                   # line 16
                  '    return 0\n')                    # line 17
        return source

    def test_generate_groups(self):
        source = self._get_source('hpixels') # Source not important for tests.
        slicemethod = self._get_slice_class(source)

        linenos = set([10, 8, 7, 5, 1, 2, 4])
        groups = slicemethod._group_suggestions(linenos)
        self.assertEqual(list(groups), [(1, 2), (4, 5), (7, 8)])

        linenos = set([1, 2, 3, 4, 7])
        groups = slicemethod._group_suggestions(linenos)
        self.assertEqual(list(groups), [(1, 4)])

    def test_add_multiline_statements(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # Change due to multiline.
        linenos = slicemethod._add_multiline_statements(set([7, 9]))
        self.assertEqual(linenos, set([7, 8, 9]))

        # No changes.
        linenos = slicemethod._add_multiline_statements(set([11, 12, 13, 14]))
        self.assertEqual(linenos, set([11, 12, 13, 14]))

    def test_split_groups_linenos_indentation(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # Change due to indentation.
        suggestions = slicemethod._split_groups_linenos_indentation(set([(13, 16)]))
        self.assertEqual(suggestions, set([(13, 13), (14, 15), (16, 16)]))

        # Change due to indentation.
        suggestions = slicemethod._split_groups_linenos_indentation(set([(12, 15)]))
        self.assertEqual(suggestions, set([(12, 13), (14, 15)]))

        # No changes.
        suggestions = slicemethod._split_groups_linenos_indentation(set([(7, 11)]))
        self.assertEqual(suggestions, set([(7, 11)]))

    def test_adjust_multiline_groups(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # Change due to if/else.
        suggestions = slicemethod._adjust_multiline_groups(set([(6, 7), (8, 9)]))
        self.assertEqual(suggestions, set())

        # Change due to if/else.
        suggestions = slicemethod._adjust_multiline_groups(set([(12, 14)]))
        self.assertEqual(suggestions, set([(13, 14)]))

        # No changes.
        suggestions = slicemethod._adjust_multiline_groups(set([(11, 15)]))
        self.assertEqual(suggestions, set([(11, 15)]))

    def test_adjust_control_groups(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # While loop header included.
        suggestions = slicemethod._adjust_control_groups(set([(5, 6)]))
        self.assertEqual(suggestions, set())

        # If conditional header included.
        suggestions = slicemethod._adjust_control_groups(set([(7, 8)]))
        self.assertEqual(suggestions, set())

        # While loop header with some body included.
        suggestions = slicemethod._adjust_control_groups(set([(5, 9)]))
        self.assertEqual(suggestions, set([(7, 9)]))

        # No changes.
        suggestions = slicemethod._adjust_control_groups(set([(11, 15)]))
        self.assertEqual(suggestions, set([(11, 15)]))

    def test_trim_unimportant(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # Space at top
        suggestions = slicemethod._trim_unimportant(set([(10, 13)]))
        self.assertEqual(suggestions, set([(11, 13)]))

        # Space at bottom
        suggestions = slicemethod._trim_unimportant(set([(7, 10)]))
        self.assertEqual(suggestions, set([(7, 9)]))

        # No changes.
        suggestions = slicemethod._trim_unimportant(set([(7, 13)]))
        self.assertEqual(suggestions, set([(7, 13)]))

    def test_split_groups_linenos(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # Trim due to control and multiline.
        suggestions = slicemethod._split_groups_linenos(set([(2, 7), (8, 10), (10, 15)]))
        self.assertEqual(suggestions, set([(2, 5), (11, 15)]))

        # Trim from control and empty line.
        suggestions = slicemethod._split_groups_linenos(set([(9, 15)]))
        self.assertEqual(suggestions, set([(11, 15)]))

    def test_group_suggestions_with_unimportant(self):
        source = self._get_source_complex()
        slicemethod = self._get_slice_class(source)

        # No linenos.
        suggestions = slicemethod._group_suggestions_with_unimportant([])
        self.assertEqual(suggestions, set())

        # Add unimportant.
        linenos = set([7, 9, 11, 12, 13, 14, 15])
        suggestions = slicemethod._group_suggestions_with_unimportant(linenos)
        self.assertEqual(suggestions, set([(7, 15)]))

        # Add unimportant.
        linenos = set([7, 8, 11, 12, 13, 14, 15])
        suggestions = slicemethod._group_suggestions_with_unimportant(linenos)
        self.assertEqual(suggestions, set([(11, 15)]))


# Tests Slice generating suggestions types related helper functions.
class TestSliceGenerateSuggestionTypeFuncs(TestSlice):

    def _get_source(self, var):
        source = ('def funcA():\n'                      # line 1
                  '     a = 5\n'                        # line 2
                  '     hpixels = 5\n'                  # line 3
                  '     wpixels = 10\n'                 # line 4
                  '     for y in range(5):\n'           # line 5
                  '         for x in range(2):\n'       # line 6
                  '             hpixels += 1\n'         # line 7
                  '             new_var = 0\n'          # line 8
                  '         wpixels += 1\n'             # line 9
                  '     print(%s)\n' %var)              # line 10
        return source

    def test_range(self):
        source = self._get_source('hpixels') # Source not important for tests.
        slicemethod = self._get_slice_class(source)

        length = slicemethod._range(min_lineno=3, max_lineno=5)
        self.assertEqual(length, 3)

    def test_compare_slice_maps(self):
        self.skipTest('TODO: Implement')

    def test_get_suggestions_remove_variables(self):
        self.skipTest('TODO: Implement')

    def test_get_suggestions_similar_ref_block(self):
        self.skipTest('TODO: Implement')

    def test_get_suggestions_diff_reference_livevar_block(self):
        self.skipTest('TODO: Implement')

    def test_get_suggestions_diff_reference_livevar_instr(self):
        self.skipTest('TODO: Implement')


# Test Slice generating suggestion related helper functions.
class TestSliceGenerateSuggestionFuncs(TestSlice):

    def _get_source(self):
        source = ('def funcA(a):\n'                     # line 1
                  '     idx = 0\n'                      # line 2
                  '     if a < 5:\n'                    # line 3
                  '         a = 5\n'                    # line 4
                  '     check_cond = True\n'            # line 5
                  '     while check_cond:\n'            # line 6
                  '         if a < 0:\n'                # line 7
                  '             check_cond = False\n'   # line 8
                  '\n'                                  # line 9
                  '         if idx > 100:\n'            # line 10
                  '             return a\n'             # line 11
                  '         idx += 1\n'                 # line 12
                  '         a -= 1\n'                   # line 13
                  '     print(idx)\n'                   # line 14
                  '     return 0\n')                    # line 15
        return source

    def assertValidSuggestion(self, slicemethod, min_lineno, max_lineno, is_valid):
        ref_vars = slicemethod._get_referenced_variables(min_lineno, max_lineno)
        ret_vars = slicemethod._get_return_variables(min_lineno, max_lineno)
        is_valid_actual = slicemethod._is_valid_suggestion(ref_vars, ret_vars, min_lineno, max_lineno)
        self.assertEqual(is_valid_actual, is_valid)

    def assertReferencedVariablesEqual(self, slicemethod, min_lineno, max_lineno, variables):
        defined = slicemethod._get_referenced_variables(min_lineno, max_lineno)
        self.assertEqual(set(defined), set(variables))

    def assertDefinedVariablesEqual(self, slicemethod, min_lineno, max_lineno,
                                    defined=None, variables=None, successors=None):
        defined_tuple = slicemethod._get_defined_variables(min_lineno, max_lineno)
        expected_defined, expected_variables, expected_successors = defined_tuple
        self.assertEqual(expected_defined, set(defined) if defined else set())
        self.assertEqual(expected_variables, set(variables) if variables else set())
        self.assertEqual(expected_successors, set(successors) if successors else set())

    def assertReturnVariablesEqual(self, slicemethod, min_lineno, max_lineno, variables):
        defined = slicemethod._get_return_variables(min_lineno, max_lineno)
        self.assertEqual(set(defined), set(variables))

    def assertSuggestionEqual(self, suggestion, min_lineno, max_lineno,
                              func_name, parameters, returns, reasons):
        self.assertEqual(suggestion.start_lineno, min_lineno)
        self.assertEqual(suggestion.end_lineno, max_lineno)
        self.assertEqual(suggestion.func_name, func_name)
        self.assertEqual(suggestion.ref_vars, parameters)
        self.assertEqual(suggestion.ret_vars, returns)
        self.assertEqual(suggestion.types, reasons)

    def test_is_valid_suggestion(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        # Check start.
        self.assertValidSuggestion(slicemethod, 2, 2, False)

        # Check conditional.
        self.assertValidSuggestion(slicemethod, 3, 4, False)

        # Check conditional with straight line.
        self.assertValidSuggestion(slicemethod, 2, 4, False)

        # Check condition in loop.
        self.assertValidSuggestion(slicemethod, 7, 8, False)

        # Check condition in loop with newline.
        self.assertValidSuggestion(slicemethod, 7, 9, False)

        # Check return type.
        self.assertValidSuggestion(slicemethod, 10, 11, False)

        # Check condition in loop with newline and return type.
        self.assertValidSuggestion(slicemethod, 7, 11, True)

        # Check end of loop.
        self.assertValidSuggestion(slicemethod, 12, 13, False)

        # Check full loop body.
        self.assertValidSuggestion(slicemethod, 7, 13, True)

        # Check full loop.
        self.assertValidSuggestion(slicemethod, 6, 13, True)

    def test_get_referenced_variables(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        # Check condition in loop.
        self.assertReferencedVariablesEqual(slicemethod, 7, 8, ['a'])

        # Check condition in loop with newline.
        self.assertReferencedVariablesEqual(slicemethod, 7, 9, ['a'])

        # Check return type.
        self.assertReferencedVariablesEqual(slicemethod, 10, 11, ['a', 'idx'])

        # Check condition in loop with newline and return type.
        self.assertReferencedVariablesEqual(slicemethod, 7, 11, ['a', 'idx'])

        # Check end of loop.
        self.assertReferencedVariablesEqual(slicemethod, 12, 13, ['a', 'idx'])

        # Check full loop body.
        self.assertReferencedVariablesEqual(slicemethod, 7, 13, ['a', 'idx'])

        # Check full loop.
        self.assertReferencedVariablesEqual(slicemethod, 6, 13, ['a', 'check_cond', 'idx'])

    def test_get_defined_variables(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        # Check start.
        self.assertDefinedVariablesEqual(slicemethod, 2, 2, defined=['idx'], successors=['funcA', 'L2', 'L3'])

        # Check conditional.
        self.assertDefinedVariablesEqual(slicemethod, 3, 4, defined=['a'], successors=['L3'])

        # Check conditional with straight line.
        self.assertDefinedVariablesEqual(slicemethod, 2, 4, defined=['a', 'idx'], successors=['L3'])

        # Check condition in loop.
        self.assertDefinedVariablesEqual(slicemethod, 7, 8, defined=['check_cond'], successors=['L8'])

        # Check condition in loop with newline.
        self.assertDefinedVariablesEqual(slicemethod, 7, 9, defined=['check_cond'], successors=['L8'])

        # Check return type.
        self.assertDefinedVariablesEqual(slicemethod, 10, 11, variables=['a'])

        # Check condition in loop with newline and return type.
        self.assertDefinedVariablesEqual(slicemethod, 7, 11, defined=['check_cond'], variables=['a'], successors=['L1', 'L10'])

        # Check end of loop.
        self.assertDefinedVariablesEqual(slicemethod, 12, 13, defined=['idx', 'a'], successors=['L4'])

        # Check full loop body.
        self.assertDefinedVariablesEqual(slicemethod, 7, 13, defined=['check_cond', 'idx', 'a'], variables=['a'], successors=['L1', 'L4'])


    def test_get_return_variables(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)

        # Check start.
        self.assertReturnVariablesEqual(slicemethod, 2, 2, ['idx'])

        # Check conditional.
        self.assertReturnVariablesEqual(slicemethod, 3, 4, ['a'])

        # Check conditional with straight line.
        self.assertReturnVariablesEqual(slicemethod, 2, 4, ['a', 'idx'])

        # Check condition in loop.
        self.assertReturnVariablesEqual(slicemethod, 7, 8, ['check_cond'])

        # Check condition in loop with newline.
        self.assertReturnVariablesEqual(slicemethod, 7, 9, ['check_cond'])

        # Check return type.
        self.assertReturnVariablesEqual(slicemethod, 10, 11, ['a'])

        # Check condition in loop with newline and return type.
        self.assertReturnVariablesEqual(slicemethod, 7, 11, ['a', 'check_cond'])

        # Check end of loop.
        self.assertReturnVariablesEqual(slicemethod, 12, 13, ['a', 'idx'])

        # Check full loop body.
        self.assertReturnVariablesEqual(slicemethod, 7, 13, ['a', 'check_cond', 'idx'])

    def test_generate_suggestions(self):
        source = self._get_source()
        slicemethod = self._get_slice_class(source)
        suggestion_map = {(2, 2): [SuggestionType.REMOVE_VAR],
                          (3, 4): [SuggestionType.REMOVE_VAR],
                          (2, 4): [SuggestionType.REMOVE_VAR],
                          (7, 8): [SuggestionType.REMOVE_VAR],
                          (7, 9): [SuggestionType.REMOVE_VAR],
                          (10, 11): [SuggestionType.REMOVE_VAR],
                          (7, 11): [SuggestionType.REMOVE_VAR],
                          (7, 13): [SuggestionType.SIMILAR_REF],
                          (10, 11): [SuggestionType.REMOVE_VAR],
                          (6, 13): [SuggestionType.DIFF_REF_LIVAR_BLOCK,
                                    SuggestionType.DIFF_REF_LIVAR_INSTR]}

        suggestions = slicemethod._generate_suggestions(suggestion_map)
        self.assertEqual(len(suggestions), 3)

        # Suggestion 1.
        suggestion = suggestions[0]
        self.assertSuggestionEqual(suggestion, 6, 13, 'funcA',
                                   parameters=['a', 'check_cond', 'idx'],
                                   returns=['a', 'idx'],
                                   reasons=[SuggestionType.DIFF_REF_LIVAR_BLOCK,
                                            SuggestionType.DIFF_REF_LIVAR_INSTR])

        # Suggestion 2.
        suggestion = suggestions[1]
        self.assertSuggestionEqual(suggestion, 7, 11, 'funcA',
                                   parameters=['a', 'idx'],
                                   returns=['a', 'check_cond'],
                                   reasons=[SuggestionType.REMOVE_VAR])

        # Suggestion 3.
        suggestion = suggestions[2]
        self.assertSuggestionEqual(suggestion, 7, 13, 'funcA',
                                   parameters=['a', 'idx'],
                                   returns=['a', 'check_cond', 'idx'],
                                   reasons=[SuggestionType.SIMILAR_REF])

    def test_add_suggestion_map(self):
        self.skipTest('TODO: Implement')

    def test_add_suggestions(self):
        source = self._get_source()
        self.skipTest('TODO: Implement')

    def test_get_suggestions(self):
        self.skipTest('TODO: Implement')

    def test_get_avg_lineno_slice_complexity(self):
        self.skipTest('TODO: Implement')


# Tests conditionals with Slice class.
class TestSliceConditional(TestSlice):

    def _get_source(self, var):
        source = ('def funcA(b):\n'             # line 1
                  '     unused = 1\n'           # line 2
                  '     c = 2\n'                # line 3
                  '     d = 3\n'                # line 4
                  '     a = d\n'                # line 5
                  '     if a > 2:\n'            # line 6
                  '         d = b + d\n'        # line 7
                  '         c = b + d\n'        # line 8
                  '     else:\n'                # line 9
                  '         b = b + 1\n'        # line 10
                  '         d = b + 1\n'        # line 11
                  '     a = %s\n'               # line 12
                  '     print(a)\n' %var)       # line 13
        return source

    # Test _get_variables_in_func.
    def test_get_variables_in_func(self):
        source = self._get_source('5')
        slicemethod = self._get_slice_class(source)
        variables = slicemethod._get_variables_in_func()
        self.assertEqual(variables, set(['a', 'b', 'c', 'd', 'unused']))

    # Test _get_instructions_in_slice with line 12 as 'a = 5'.
    def test_get_instructions_in_slice_5(self):
        source = self._get_source('5')
        instrs = self._get_instrs_slice(source, 13)
        self.assertEqual(instrs, set([13, 12]))

    # Test _get_instructions_in_slice with line 12 as 'a = a'.
    def test_get_instructions_in_slice_a(self):
        source = self._get_source('a')
        instrs = self._get_instrs_slice(source, 13)
        self.assertEqual(instrs, set([13, 12, 5, 4]))

    # Test _get_instructions_in_slice with line 12 as 'a = b'.
    def test_get_instructions_in_slice_b(self):
        source = self._get_source('b')
        instrs = self._get_instrs_slice(source, 13)
        self.assertEqual(instrs, set([1, 4, 5, 6, 9, 10, 12, 13]))

    # Test _get_instructions_in_slice with line 12 as 'a = c'.
    def test_get_instructions_in_slice_c(self):
        source = self._get_source('c')
        instrs = self._get_instrs_slice(source, 13)
        self.assertEqual(instrs, set([1, 3, 4, 5, 6, 7, 8, 9, 12, 13]))

    # Test _get_instructions_in_slice with line 12 as 'a = d'.
    def test_get_instructions_in_slice_d(self):
        source = self._get_source('d')
        instrs = self._get_instrs_slice(source, 13)
        self.assertEqual(instrs, set([1, 4, 5, 6, 7, 9, 10, 11, 12, 13]))

    # Test _generate_cfg_slice with line 12 as 'a = 5'.
    def test_generate_cfg_slice_5(self):
        source = self._get_source('5')
        funcA = self._get_cfg_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'])

        # After/exit block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test _generate_cfg_slice with line 12 as 'a = a'.
    def test_generate_cfg_slice_a(self):
        source = self._get_source('a')
        funcA = self._get_cfg_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[4, 5])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'])

        # After/exit block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test _generate_cfg_slice with line 12 as 'a = b'.
    def test_generate_cfg_slice_b(self):
        source = self._get_source('b')
        funcA = self._get_cfg_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[1, 4, 5, 6])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'], linenos=[9, 10])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test _generate_cfg_slice with line 12 as 'a = c'.
    def test_generate_cfg_slice_c(self):
        source = self._get_source('c')
        funcA = self._get_cfg_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[1, 3, 4, 5, 6])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'], linenos=[7, 8])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'], linenos=[9])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test get_slice with line 12 as 'a = d'.
    def test_generate_cfg_slice_d(self):
        source = self._get_source('d')
        funcA = self._get_cfg_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[1, 4, 5, 6])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'], linenos=[7])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, predecessors=['funcA'], successors=['L7'], linenos=[9, 10, 11])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test get_slice with line 12 as 'a = 5'.
    def test_get_slice_5(self):
        source = self._get_source('5')
        funcA = self._get_slice(source, lineno=13)
        self.assertBlockEqual(funcA, linenos=[12, 13])

    # Test get_slice with line 12 as 'a = a'.
    def test_get_slice_a(self):
        source = self._get_source('a')
        funcA = self._get_slice(source, lineno=13)
        self.assertBlockEqual(funcA, linenos=[4, 5, 12, 13])

    # Test get_slice with line 12 as 'a = b'.
    def test_get_slice_b(self):
        source = self._get_source('b')
        funcA = self._get_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L6', 'L7'], linenos=[1, 4, 5, 6])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, successors=['L7'], predecessors=['funcA'], linenos=[9, 10])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['funcA', 'L6'], linenos=[12, 13])

    # Test get_slice with line 12 as 'a = c'.
    def test_get_slice_c(self):
        source = self._get_source('c')
        funcA = self._get_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[1, 3, 4, 5, 6])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, successors=['L7'], predecessors=['funcA'], linenos=[7, 8])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, successors=['L7'], predecessors=['funcA'], linenos=[9])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])

    # Test get_slice with line 12 as 'a = d'.
    def test_get_slice_d(self):
        source = self._get_source('d')
        funcA = self._get_slice(source, lineno=13)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L5', 'L6'], linenos=[1, 4, 5, 6])

        # If conditional.
        block = funcA.successors['L5']
        self.assertBlockEqual(block, successors=['L7'], predecessors=['funcA'], linenos=[7])

        # Else conditional.
        block = funcA.successors['L6']
        self.assertBlockEqual(block, successors=['L7'], predecessors=['funcA'], linenos=[9, 10, 11])

        # After block.
        block = block.successors['L7']
        self.assertBlockEqual(block, predecessors=['L5', 'L6'], linenos=[12, 13])


# Tests loops with Slice class.
class TestSliceForLoops(TestSlice):

    def _get_source(self, var):
        source = ('def funcA():\n'                      # line 1
                  '     a = 5\n'                        # line 2
                  '     hpixels = 5\n'                  # line 3
                  '     wpixels = 10\n'                 # line 4
                  '     for y in range(5):\n'           # line 5
                  '         for x in range(2):\n'       # line 6
                  '             hpixels += 1\n'         # line 7
                  '             new_var = 0\n'          # line 8
                  '         wpixels += 1\n'             # line 9
                  '     print(%s)\n' %var)              # line 10
        return source

    # Test _get_variables_in_func.
    def test_get_variables_in_func(self):
        source = self._get_source('5')
        slicemethod = self._get_slice_class(source)
        variables = slicemethod._get_variables_in_func()
        self.assertEqual(variables, set(['a', 'hpixels', 'wpixels', 'x', 'y', 'new_var']))

    # Test _get_instructions_in_slice with line 10 as 'print(a)'.
    def test_get_instructions_in_slice_a(self):
        source = self._get_source('a')
        instrs = self._get_instrs_slice(source, 10)
        self.assertEqual(instrs, set([2, 10]))

        # Test without including extra control.
        instrs = self._get_instrs_slice(source, 10, include_control=False)
        self.assertEqual(instrs, set([2, 10]))

    # Test _get_instructions_in_slice with line 10 as 'print(wpixels)'.
    def test_get_instructions_in_slice_wpixels(self):
        source = self._get_source('wpixels')
        instrs = self._get_instrs_slice(source, 10)
        self.assertEqual(instrs, set([4, 5, 9, 10]))

        # Test without including extra control.
        instrs = self._get_instrs_slice(source, 10, include_control=False)
        self.assertEqual(instrs, set([4, 5, 9, 10]))

    # Test _get_instructions_in_slice with line 10 as 'print(hpixels)'.
    def test_get_instructions_in_slice_hpixels(self):
        source = self._get_source('hpixels')
        instrs = self._get_instrs_slice(source, 10)
        self.assertEqual(instrs, set([3, 5, 6, 7, 10]))

        # Test without including extra control.
        instrs = self._get_instrs_slice(source, 10, include_control=False)
        self.assertEqual(instrs, set([3, 5, 6, 7, 10]))

        # Test with excluding x.
        instrs = self._get_instrs_slice(source, 10, exclude_vars=['x'])
        self.assertEqual(instrs, set([3, 5, 6, 7, 10]))

    # Test _get_instructions_in_slice with line 8 as 'new_var = 0'.
    def test_get_instructions_in_slice_new_var_line8(self):
        source = self._get_source('"NA"')
        instrs = self._get_instrs_slice(source, 8)
        self.assertEqual(instrs, set([5, 6, 8]))

        # Test without including extra control.
        instrs = self._get_instrs_slice(source, 8, include_control=False)
        self.assertEqual(instrs, set([8]))

    # Test _get_instructions_in_slice with line 10 as 'print(new_var)'.
    def test_get_instructions_in_slice_new_var_line10(self):
        source = self._get_source('new_var')
        instrs = self._get_instrs_slice(source, 10)
        self.assertEqual(instrs, set([5, 6, 8, 10]))

        # Test without including extra control.
        instrs = self._get_instrs_slice(source, 10, include_control=False)
        self.assertEqual(instrs, set([8, 10]))

    # Test get_slice with line 10 as 'print(a)'.
    def test_get_slice_a(self):
        source = self._get_source('a')
        funcA = self._get_cfg_slice(source, lineno=10)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L8'], linenos=[2])

        # Guard block 1.
        guard_block_1 = funcA.successors['L8']
        self.assertBlockEqual(guard_block_1, predecessors=['funcA', 'L11'], successors=['L9', 'L12'])

        # Guard block 2.
        guard_block_2 = guard_block_1.successors['L9']
        self.assertBlockEqual(guard_block_2, predecessors=['L8', 'L10'], successors=['L10', 'L11'])

        # Body block 2.
        body_block_2 = guard_block_2.successors['L10']
        self.assertBlockEqual(body_block_2, predecessors=['L9'], successors=['L9'])

        # After block 2.
        after_block_2 = guard_block_2.successors['L11']
        self.assertBlockEqual(after_block_2, predecessors=['L9'], successors=['L8'])

        # After block 1.
        after_block_1 = guard_block_1.successors['L12']
        self.assertBlockEqual(after_block_1, predecessors=['L8'], linenos=[10])

    # Test _generate_cfg_slice with line 9 as 'print(wpixels)'.
    def test_generate_cfg_slice_wpixels(self):
        source = self._get_source('wpixels')
        funcA = self._get_cfg_slice(source, lineno=10)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L8'], linenos=[4])

        # Guard block 1.
        guard_block_1 = funcA.successors['L8']
        self.assertBlockEqual(guard_block_1, predecessors=['funcA', 'L11'], successors=['L9', 'L12'], linenos=[5])

        # Guard block 2.
        guard_block_2 = guard_block_1.successors['L9']
        self.assertBlockEqual(guard_block_2, predecessors=['L8', 'L10'], successors=['L10', 'L11'])

        # Body block 2.
        body_block_2 = guard_block_2.successors['L10']
        self.assertBlockEqual(body_block_2, predecessors=['L9'], successors=['L9'])

        # After block 2.
        after_block_2 = guard_block_2.successors['L11']
        self.assertBlockEqual(after_block_2, predecessors=['L9'], successors=['L8'], linenos=[9])

        # After block 1.
        after_block_1 = guard_block_1.successors['L12']
        self.assertBlockEqual(after_block_1, predecessors=['L8'], linenos=[10])

    # Test _generate_cfg_slice with line 10 as 'print(hpixels)'.
    def test_generate_cfg_slice_hpixels(self):
        source = self._get_source('hpixels')
        funcA = self._get_cfg_slice(source, lineno=10)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L8'], linenos=[3])

        # Guard block 1.
        guard_block_1 = funcA.successors['L8']
        self.assertBlockEqual(guard_block_1, predecessors=['funcA', 'L11'], successors=['L9', 'L12'], linenos=[5])

        # Guard block 2.
        guard_block_2 = guard_block_1.successors['L9']
        self.assertBlockEqual(guard_block_2, predecessors=['L8', 'L10'], successors=['L10', 'L11'], linenos=[6])

        # Body block 2.
        body_block_2 = guard_block_2.successors['L10']
        self.assertBlockEqual(body_block_2, predecessors=['L9'], successors=['L9'], linenos=[7])

        # After block 1.
        after_block_2 = guard_block_2.successors['L11']
        self.assertBlockEqual(after_block_2, predecessors=['L9'], successors=['L8'])

        # After/exit block.
        after_block = guard_block_1.successors['L12']
        self.assertBlockEqual(after_block, predecessors=['L8'], linenos=[10])

    # Test _generate_cfg_slice with line 10 as 'print(a)'.
    def test_generate_cfg_slice_a(self):
        source = self._get_source('a')
        funcA = self._get_slice(source, lineno=10)
        self.assertBlockEqual(funcA, linenos=[2, 10])

    # Test get_slice with line 10 as 'print(hpixels)'.
    def test_get_slice_wpixels(self):
        source = self._get_source('wpixels')
        funcA = self._get_slice(source, lineno=10)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L8'], linenos=[4])

        # Guard block 1.
        guard_block_1 = funcA.successors['L8']
        self.assertBlockEqual(guard_block_1, predecessors=['funcA', 'L11'], successors=['L11', 'L12'], linenos=[5])

        # Body block 1.
        body_block_1 = guard_block_1.successors['L11']
        self.assertBlockEqual(body_block_1, predecessors=['L8'], successors=['L8'], linenos=[9])

        # After block 1.
        after_block_1 = guard_block_1.successors['L12']
        self.assertBlockEqual(after_block_1, predecessors=['L8'], linenos=[10])

    # Test get_slice with line 10 as 'print(hpixels)'.
    def test_get_slice_hpixels(self):
        source = self._get_source('hpixels')
        funcA = self._get_slice(source, lineno=10)

        # Function block.
        self.assertBlockEqual(funcA, successors=['L8'], linenos=[3])

        # Guard block 1.
        guard_block_1 = funcA.successors['L8']
        self.assertBlockEqual(guard_block_1, predecessors=['funcA', 'L9'], successors=['L9', 'L12'], linenos=[5])

        # Guard block 2.
        guard_block_2 = guard_block_1.successors['L9']
        self.assertBlockEqual(guard_block_2, predecessors=['L8', 'L10'], successors=['L10', 'L8'], linenos=[6])

        # Body block 2.
        body_block_2 = guard_block_2.successors['L10']
        self.assertBlockEqual(body_block_2, predecessors=['L9'], successors=['L9'], linenos=[7])

        # After block 1.
        after_block_1 = guard_block_1.successors['L12']
        self.assertBlockEqual(after_block_1, predecessors=['L8'], linenos=[10])


# Tests conditionals with a return statement with Slice class.
class TestSliceConditionalReturn(TestSlice):

    # TODO: Decide code and make a test suite for code.
    def test_conditional_with_return(self):
        self.skipTest('TODO: Implement (Important)')


# Tests loops with Slice class.
class TestSliceWhileLoops(TestSlice):

    # TODO: Decide code and make a test suite for code.
    def test_while_loop(self):
        self.skipTest('TODO: Implement (Important)')


# Tests a recursive function.
class TestRecursiveFunction(TestSlice):

    # TODO: Decide code and make a test suite for code.
    def test_recursion(self):
        self.skipTest('TODO: Implement (Important)')


# Tests a exception with more than two successors.
class TestExceptionFunction(TestSlice):

    def get_source(self):
        source = ('def funcA(y):\n'                       # line 1
                  '    try:\n'                            # line 2
                  '        return y\n'                    # line 3
                  '    except SyntaxException as e:\n'    # line 4
                  '        return str(e)\n'               # line 5
                  '    except Exception as e:\n'          # line 6
                  '        return str(e)\n')              # line 7
        return source

    # TODO: Decide code and make a test suite for code.
    def test_exception(self):
        self.skipTest('TODO: Implement (Important)')


if __name__ == '__main__':
     unittest.main()
