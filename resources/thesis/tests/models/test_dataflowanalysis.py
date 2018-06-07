# File name: test_dataflowanalysis.py
# Author: Nupur Garg
# Date created: 2/1/2017
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.generatecfg import CFGGenerator
from src.models.block import Block
from src.models.dataflowanalysis import *
from src.models.blockinfo import FunctionBlockInformation, ReachingDefinitions


# Base class for testing IterativeDataflowAnalysis.
class TestIterativeDataflowAnalysis(unittest.TestCase):

    def _generate_cfg(self, source=None):
        if not source:
            source = ('def funcA():\n'              # line 1
                      '     i = 3\n'                # line 2
                      '     i = j = i + 1\n'        # line 3
                      '     a = j + 2\n'            # line 4
                      '     while a > 0:\n'         # line 5
                      '         i = i + 1\n'        # line 6
                      '         j = j - 1\n'        # line 7
                      '         if i != j:\n'       # line 8
                      '             a = a - 1\n'    # line 9
                      '         i = i + 1')         # line 10

        node = ast.parse(source)
        generator = CFGGenerator(False)
        self.cfg = generator.generate(node, source)
        self.funcA = self.cfg.get_func('funcA')

    def setUp(self):
        Block._label_counter.reset()


# Test ReachingDefinitionsAnalysis class.
class TestReachingDefinitionsAnalysis(TestIterativeDataflowAnalysis):

    def test_abstract(self):
        with self.assertRaises(TypeError) as context:
            IterativeDataflowAnalysis(ReachingDefinitions)
        self.assertIsNotNone(context.exception)

    def test_compute_func_gen(self):
        self._generate_cfg()
        analysismethod = ReachingDefinitionsAnalysis()
        info = FunctionBlockInformation()
        info.init(self.funcA, ReachingDefinitions)

        func_gen = analysismethod._compute_func_gen(info)
        self.assertEqual(func_gen, {'i': set([('funcA', 2), ('funcA', 3), ('L3', 6), ('L6', 10)]),
                                    'j': set([('funcA', 3), ('L3', 7)]),
                                    'a': set([('funcA', 4), ('L5', 9)])})

    def test_compute_block_info_func(self):
        self._generate_cfg()
        analysismethod = ReachingDefinitionsAnalysis()
        info = FunctionBlockInformation()

        info.init(self.funcA, ReachingDefinitions)
        func_gen = analysismethod._compute_func_gen(info)
        analysismethod._compute_block_info(info, func_gen)

        # funcA block.
        cur_block_info = info.get_block_info(self.funcA)
        self.assertEqual(cur_block_info.gen, {'i': set([('funcA', 3)]),
                                              'j': set([('funcA', 3)]),
                                              'a': set([('funcA', 4)])})
        self.assertEqual(cur_block_info.kill, {'i': set([('funcA', 2), ('L3', 6), ('L6', 10)]),
                                               'j': set([('L3', 7)]),
                                               'a': set([('L5', 9)])})

        # L2 block.
        guard_block = self.funcA.successors['L2']
        cur_block_info = info.get_block_info(guard_block)
        self.assertEqual(len(cur_block_info.gen), 0)
        self.assertEqual(len(cur_block_info.kill), 0)

        # L3 block.
        loop_body_start_block = guard_block.successors['L3']
        cur_block_info = info.get_block_info(loop_body_start_block)
        self.assertEqual(cur_block_info.gen, {'i': set([('L3', 6)]),
                                              'j': set([('L3', 7)])})
        self.assertEqual(cur_block_info.kill, {'i': set([('funcA', 2), ('funcA', 3), ('L6', 10)]),
                                               'j': set([('funcA', 3)])})

        # L5 block.
        if_body_block = loop_body_start_block.successors['L5']
        cur_block_info = info.get_block_info(if_body_block)
        self.assertEqual(cur_block_info.gen, {'a': set([('L5', 9)])})
        self.assertEqual(cur_block_info.kill, {'a': set([('funcA', 4)])})

        # L6 block.
        loop_body_end_block = loop_body_start_block.successors['L6']
        cur_block_info = info.get_block_info(loop_body_end_block)
        self.assertEqual(cur_block_info.gen, {'i': set([('L6', 10)])})
        self.assertEqual(cur_block_info.kill, {'i': set([('funcA', 2), ('funcA', 3), ('L3', 6)])})

        # L4 block.
        after_block = guard_block.successors['L4']
        cur_block_info = info.get_block_info(after_block)
        self.assertEqual(len(cur_block_info.gen), 0)
        self.assertEqual(len(cur_block_info.kill), 0)

        # L1 block.
        exit_block = after_block.successors['L1']
        cur_block_info = info.get_block_info(exit_block)
        self.assertEqual(len(cur_block_info.gen), 0)
        self.assertEqual(len(cur_block_info.kill), 0)

    def test_compute_block_info_instr(self):
        self._generate_cfg()
        analysismethod = ReachingDefinitionsAnalysis()
        info = FunctionBlockInformation()

        info.init(self.funcA, ReachingDefinitions)
        func_gen = analysismethod._compute_func_gen(info)
        analysismethod._compute_block_info(info, func_gen)

        # Line 2.
        cur_instr_info = info.get_instruction_info(2)
        self.assertEqual(cur_instr_info.gen, {'i': set([('funcA', 2)])})
        self.assertEqual(cur_instr_info.kill, {'i': set([('funcA', 3), ('L3', 6), ('L6', 10)])})

        # Line 3.
        cur_instr_info = info.get_instruction_info(3)
        self.assertEqual(cur_instr_info.gen, {'i': set([('funcA', 3)]),
                                              'j': set([('funcA', 3)])})
        self.assertEqual(cur_instr_info.kill, {'i': set([('funcA', 2), ('L3', 6), ('L6', 10)]),
                                               'j': set([('L3', 7)])})

        # Line 4.
        cur_instr_info = info.get_instruction_info(4)
        self.assertEqual(cur_instr_info.gen, {'a': set([('funcA', 4)])})
        self.assertEqual(cur_instr_info.kill, {'a': set([('L5', 9)])})

        # Line 5.
        cur_instr_info = info.get_instruction_info(5)
        self.assertFalse(cur_instr_info.gen)
        self.assertFalse(cur_instr_info.kill)

        # Line 6.
        cur_instr_info = info.get_instruction_info(6)
        self.assertEqual(cur_instr_info.gen, {'i': set([('L3', 6)])})
        self.assertEqual(cur_instr_info.kill, {'i': set([('funcA', 2), ('funcA', 3), ('L6', 10)])})

        # Line 7.
        cur_instr_info = info.get_instruction_info(7)
        self.assertEqual(cur_instr_info.gen, {'j': set([('L3', 7)])})
        self.assertEqual(cur_instr_info.kill, {'j': set([('funcA', 3)])})

        # Line 9.
        cur_instr_info = info.get_instruction_info(9)
        self.assertEqual(cur_instr_info.gen, {'a': set([('L5', 9)])})
        self.assertEqual(cur_instr_info.kill, {'a': set([('funcA', 4)])})

        # Line 10.
        cur_instr_info = info.get_instruction_info(10)
        self.assertEqual(cur_instr_info.gen, {'i': set([('L6', 10)])})
        self.assertEqual(cur_instr_info.kill, {'i': set([('funcA', 2), ('funcA', 3), ('L3', 6)])})

    def test_compute_info_func(self):
        self._generate_cfg()
        analysismethod = ReachingDefinitionsAnalysis()
        info = analysismethod.analyze(self.funcA)

        # funcA block.
        cur_block_info = info.get_block_info(self.funcA)
        self.assertEqual(len(cur_block_info.in_node), 0)
        self.assertEqual(cur_block_info.out_node, {'i': set([('funcA', 3)]),
                                                   'j': set([('funcA', 3)]),
                                                   'a': set([('funcA', 4)])})

        # L2 block.
        guard_block = self.funcA.successors['L2']
        cur_block_info = info.get_block_info(guard_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                   'j': set([('funcA', 3), ('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # L3 block.
        loop_body_start_block = guard_block.successors['L3']
        cur_block_info = info.get_block_info(loop_body_start_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('L3', 6)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # L5 block.
        if_body_block = loop_body_start_block.successors['L5']
        cur_block_info = info.get_block_info(if_body_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('L3', 6)]),
                                                  'j': set([('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('L3', 6)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('L5', 9)])})

        # L6 block.
        loop_body_end_block = loop_body_start_block.successors['L6']
        cur_block_info = info.get_block_info(loop_body_end_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('L3', 6)]),
                                                  'j': set([('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('L6', 10)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # L4 block.
        after_block = guard_block.successors['L4']
        cur_block_info = info.get_block_info(after_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                   'j': set([('funcA', 3), ('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # L2 block.
        exit_block = after_block.successors['L1']
        cur_block_info = info.get_block_info(exit_block)
        self.assertEqual(cur_block_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_block_info.out_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                   'j': set([('funcA', 3), ('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

    def test_compute_info_instr(self):
        self._generate_cfg()
        analysismethod = ReachingDefinitionsAnalysis()
        info = analysismethod.analyze(self.funcA)

        # Line 2.
        cur_instr_info = info.get_instruction_info(2)
        self.assertEqual(cur_instr_info.in_node, {})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('funcA', 2)])})

        # Line 3.
        cur_instr_info = info.get_instruction_info(3)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('funcA', 2)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('funcA', 3)]),
                                                   'j': set([('funcA', 3)])})

        # Line 4.
        cur_instr_info = info.get_instruction_info(4)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('funcA', 3)]),
                                                  'j': set([('funcA', 3)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('funcA', 3)]),
                                                   'j': set([('funcA', 3)]),
                                                   'a': set([('funcA', 4)])})

        # Line 5.
        cur_instr_info = info.get_instruction_info(5)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                   'j': set([('funcA', 3), ('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # Line 6.
        cur_instr_info = info.get_instruction_info(6)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('funcA', 3), ('L6', 10)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('L3', 6)]),
                                                   'j': set([('funcA', 3), ('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})
        # Line 7.
        cur_instr_info = info.get_instruction_info(7)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('L3', 6)]),
                                                  'j': set([('funcA', 3), ('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('L3', 6)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})

        # Line 9.
        cur_instr_info = info.get_instruction_info(9)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('L3', 6)]),
                                                  'j': set([('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('L3', 6)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('L5', 9)])})

        # Line 10.
        cur_instr_info = info.get_instruction_info(10)
        self.assertEqual(cur_instr_info.in_node, {'i': set([('L3', 6)]),
                                                  'j': set([('L3', 7)]),
                                                  'a': set([('funcA', 4), ('L5', 9)])})
        self.assertEqual(cur_instr_info.out_node, {'i': set([('L6', 10)]),
                                                   'j': set([('L3', 7)]),
                                                   'a': set([('funcA', 4), ('L5', 9)])})


# Test LiveVariableAnalysis class.
class TestLiveVariableAnalysis(TestIterativeDataflowAnalysis):

    def test_compute_block_info_func(self):
        self._generate_cfg()
        analysismethod = LiveVariableAnalysis()
        info = FunctionBlockInformation()

        info.init(self.funcA, LiveVariables)
        func_gen = analysismethod._compute_func_gen(info)
        analysismethod._compute_block_info(info, func_gen)

        # funcA block.
        cur_block_info = info.get_block_info(self.funcA)
        self.assertFalse(cur_block_info.referenced)
        self.assertEqual(cur_block_info.defined, set(['a', 'i', 'j']))

        # L2 block.
        guard_block = self.funcA.successors['L2']
        cur_block_info = info.get_block_info(guard_block)
        self.assertEqual(cur_block_info.referenced, set(['a']))
        self.assertFalse(cur_block_info.defined)

        # L3 block.
        loop_body_start_block = guard_block.successors['L3']
        cur_block_info = info.get_block_info(loop_body_start_block)
        self.assertEqual(cur_block_info.referenced, set(['i', 'j']))
        self.assertEqual(cur_block_info.defined, set(['i', 'j']))

        # L5 block.
        if_body_block = loop_body_start_block.successors['L5']
        cur_block_info = info.get_block_info(if_body_block)
        self.assertEqual(cur_block_info.referenced, set(['a']))
        self.assertEqual(cur_block_info.defined, set(['a']))

        # L6 block.
        loop_body_end_block = loop_body_start_block.successors['L6']
        cur_block_info = info.get_block_info(loop_body_end_block)
        self.assertEqual(cur_block_info.referenced, set(['i']))
        self.assertEqual(cur_block_info.defined, set(['i']))

        # L4 block.
        after_block = guard_block.successors['L4']
        cur_block_info = info.get_block_info(after_block)
        self.assertFalse(cur_block_info.referenced)
        self.assertFalse(cur_block_info.defined)

        # L1 block.
        exit_block = after_block.successors['L1']
        cur_block_info = info.get_block_info(exit_block)
        self.assertFalse(cur_block_info.referenced)
        self.assertFalse(cur_block_info.defined)

    def test_compute_block_info_instr(self):
        self._generate_cfg()
        analysismethod = LiveVariableAnalysis()
        info = FunctionBlockInformation()

        info.init(self.funcA, LiveVariables)
        func_gen = analysismethod._compute_func_gen(info)
        analysismethod._compute_block_info(info, func_gen)

        # Line 2.
        cur_instr_info = info.get_instruction_info(2)
        self.assertFalse(cur_instr_info.referenced)
        self.assertEqual(cur_instr_info.defined, set(['i']))

        # Line 3.
        cur_instr_info = info.get_instruction_info(3)
        self.assertEqual(cur_instr_info.referenced, set(['i']))
        self.assertEqual(cur_instr_info.defined, set(['i', 'j']))

        # Line 4.
        cur_instr_info = info.get_instruction_info(4)
        self.assertEqual(cur_instr_info.referenced, set(['j']))
        self.assertEqual(cur_instr_info.defined, set(['a']))

        # Line 5.
        cur_instr_info = info.get_instruction_info(5)
        self.assertEqual(cur_instr_info.referenced, set(['a']))
        self.assertFalse(cur_instr_info.defined)

        # Line 6.
        cur_instr_info = info.get_instruction_info(6)
        self.assertEqual(cur_instr_info.referenced, set(['i']))
        self.assertEqual(cur_instr_info.defined, set(['i']))

        # Line 7.
        cur_instr_info = info.get_instruction_info(7)
        self.assertEqual(cur_instr_info.referenced, set(['j']))
        self.assertEqual(cur_instr_info.defined, set(['j']))

        # Line 8.
        cur_instr_info = info.get_instruction_info(8)
        self.assertEqual(cur_instr_info.referenced, set(['i', 'j']))
        self.assertFalse(cur_instr_info.defined)

        # Line 9.
        cur_instr_info = info.get_instruction_info(9)
        self.assertEqual(cur_instr_info.referenced, set(['a']))
        self.assertEqual(cur_instr_info.defined, set(['a']))

        # Line 10.
        cur_instr_info = info.get_instruction_info(10)
        self.assertEqual(cur_instr_info.referenced, set(['i']))
        self.assertEqual(cur_instr_info.defined, set(['i']))

    def test_compute_info_func(self):
        self._generate_cfg()
        analysismethod = LiveVariableAnalysis()
        info = analysismethod.analyze(self.funcA)

        # funcA block.
        cur_block_info = info.get_block_info(self.funcA)
        self.assertFalse(cur_block_info.in_node)
        self.assertEqual(cur_block_info.out_node, set(['a', 'i', 'j']))

        # L2 block.
        guard_block = self.funcA.successors['L2']
        cur_block_info = info.get_block_info(guard_block)
        self.assertEqual(cur_block_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_block_info.out_node, set(['a', 'i', 'j']))

        # L3 block.
        loop_body_start_block = guard_block.successors['L3']
        cur_block_info = info.get_block_info(loop_body_start_block)
        self.assertEqual(cur_block_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_block_info.out_node, set(['a', 'i', 'j']))

        # L5 block.
        if_body_block = loop_body_start_block.successors['L5']
        cur_block_info = info.get_block_info(if_body_block)
        self.assertEqual(cur_block_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_block_info.out_node, set(['a', 'i', 'j']))

        # L6 block.
        loop_body_end_block = loop_body_start_block.successors['L6']
        cur_block_info = info.get_block_info(loop_body_end_block)
        self.assertEqual(cur_block_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_block_info.out_node, set(['a', 'i', 'j']))

        # L4 block.
        after_block = guard_block.successors['L4']
        cur_block_info = info.get_block_info(after_block)
        self.assertFalse(cur_block_info.in_node)
        self.assertFalse(cur_block_info.out_node)

        # L1 block.
        exit_block = after_block.successors['L1']
        cur_block_info = info.get_block_info(exit_block)
        self.assertFalse(cur_block_info.in_node)
        self.assertFalse(cur_block_info.out_node)

    def test_compute_info_instr(self):
        self._generate_cfg()
        analysismethod = LiveVariableAnalysis()
        info = analysismethod.analyze(self.funcA)

        # Line 2.
        cur_instr_info = info.get_instruction_info(2)
        self.assertFalse(cur_instr_info.in_node)
        self.assertEqual(cur_instr_info.out_node, set(['i']))

        # Line 3.
        cur_instr_info = info.get_instruction_info(3)
        self.assertEqual(cur_instr_info.in_node, set(['i']))
        self.assertEqual(cur_instr_info.out_node, set(['i', 'j']))

        # Line 4.
        cur_instr_info = info.get_instruction_info(4)
        self.assertEqual(cur_instr_info.in_node, set(['i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 5.
        cur_instr_info = info.get_instruction_info(5)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 6.
        cur_instr_info = info.get_instruction_info(6)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 7.
        cur_instr_info = info.get_instruction_info(7)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 8.
        cur_instr_info = info.get_instruction_info(8)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 9.
        cur_instr_info = info.get_instruction_info(9)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

        # Line 10.
        cur_instr_info = info.get_instruction_info(10)
        self.assertEqual(cur_instr_info.in_node, set(['a', 'i', 'j']))
        self.assertEqual(cur_instr_info.out_node, set(['a', 'i', 'j']))

    def test_compute_info_func_complex(self):
        source = ('def funcA(x, y, z, c, d):\n' # line 1
                  '     while c < 5:\n'         # line 2
                  '         x = y + 1\n'        # line 3
                  '         y = mult_2(z)\n'    # line 4
                  '         if d:\n'            # line 5
                  '             x = y + z\n'    # line 6
                  '         z = 1\n'            # line 7
                  '     z = x\n')               # line 8
        self._generate_cfg(source)

        analysismethod = LiveVariableAnalysis()
        info = analysismethod.analyze(self.funcA)

        # funcA block.
        cur_block_info = info.get_block_info(self.funcA)
        self.assertFalse(cur_block_info.in_node)
        self.assertEqual(cur_block_info.out_node, set(['x', 'y', 'z', 'c', 'd']))

        # L2 block.
        guard_block = self.funcA.successors['L2']
        cur_block_info = info.get_block_info(guard_block)
        self.assertEqual(cur_block_info.in_node, set(['x', 'y', 'z', 'c', 'd']))
        self.assertEqual(cur_block_info.out_node, set(['x', 'y', 'z', 'c', 'd']))

        # L3 block.
        loop_body_start_block = guard_block.successors['L3']
        cur_block_info = info.get_block_info(loop_body_start_block)
        self.assertEqual(cur_block_info.in_node, set(['y', 'z', 'c', 'd']))
        self.assertEqual(cur_block_info.out_node, set(['x', 'y', 'z', 'c', 'd']))

        # L5 block.
        if_body_block = loop_body_start_block.successors['L5']
        cur_block_info = info.get_block_info(if_body_block)
        self.assertEqual(cur_block_info.in_node, set(['y', 'z', 'c', 'd']))
        self.assertEqual(cur_block_info.out_node, set(['x', 'y', 'c', 'd']))

        # L6 block.
        loop_body_end_block = loop_body_start_block.successors['L6']
        cur_block_info = info.get_block_info(loop_body_end_block)
        self.assertEqual(cur_block_info.in_node, set(['x', 'y', 'c', 'd']))
        self.assertEqual(cur_block_info.out_node, set(['x', 'y', 'z', 'c', 'd']))

        # L4 block.
        after_block = guard_block.successors['L4']
        cur_block_info = info.get_block_info(after_block)
        self.assertEqual(cur_block_info.in_node, set(['x']))
        self.assertFalse(cur_block_info.out_node)

        # L1 block.
        exit_block = after_block.successors['L1']
        cur_block_info = info.get_block_info(exit_block)
        self.assertFalse(cur_block_info.in_node)
        self.assertFalse(cur_block_info.out_node)


if __name__ == '__main__':
     unittest.main()
