# File name: test_blockinfo.py
# Author: Nupur Garg
# Date created: 3/16/2017
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.generatecfg import CFGGenerator
from src.models.block import Block
from src.models.blockinfo import *


# Test ReachingDefinitions class.
class TestReachingDefinitions(unittest.TestCase):

    def test_is_dict_equal(self):
        reachingdef = ReachingDefinitions()

        dictA = {'a': 'test'}
        dictB = {'b': 'test'}
        self.assertFalse(reachingdef._is_dict_equal(dictA, dictB))

        dictA = {'a': 'test'}
        dictB = {'a': 'test2'}
        self.assertFalse(reachingdef._is_dict_equal(dictA, dictB))

        dictA = {'a': 'test'}
        dictB = {'a': 'test'}
        self.assertTrue(reachingdef._is_dict_equal(dictA, dictB))

    def test_equality(self):
        reachingdef1 = ReachingDefinitions()
        reachingdef2 = ReachingDefinitions()
        self.assertFalse(reachingdef1 == None)
        self.assertFalse(reachingdef1 == 1)

        # Checks gen sets equality.
        reachingdef1.gen['a'] = set([('L2', 6)])
        self.assertFalse(reachingdef1 == reachingdef2)
        reachingdef2.gen['a'] = set([('L2', 6)])
        self.assertEqual(reachingdef1, reachingdef1)

        # Checks kill sets equality.
        reachingdef1.kill['a'] = set([('L2', 6)])
        self.assertFalse(reachingdef1 == reachingdef2)
        reachingdef2.kill['a'] = set([('L2', 6)])
        self.assertEqual(reachingdef1, reachingdef1)

        # Checks in_node sets equality.
        reachingdef1.in_node['a'] = set([('L2', 6)])
        self.assertFalse(reachingdef1 == reachingdef2)
        reachingdef2.in_node['a'] = set([('L2', 6)])
        self.assertEqual(reachingdef1, reachingdef1)

        # Checks out_node sets equality.
        reachingdef1.out_node['a'] = set([('L2', 6)])
        self.assertFalse(reachingdef1 == reachingdef2)
        reachingdef2.out_node['a'] = set([('L2', 6)])
        self.assertEqual(reachingdef1, reachingdef1)


# Test LiveVariables class.
class TestLiveVariables(unittest.TestCase):

    def test_equality(self):
        livevar1 = LiveVariables()
        livevar2 = LiveVariables()
        self.assertFalse(livevar1 == None)
        self.assertFalse(livevar1 == 1)

        # Checks defined set equality.
        livevar1.defined = set(['a'])
        self.assertFalse(livevar1 == livevar2)
        livevar2.defined = set(['a'])
        self.assertEqual(livevar1, livevar2)

        # Checks referenced set equality.
        livevar1.referenced = set(['a'])
        self.assertFalse(livevar1 == livevar2)
        livevar2.referenced = set(['a'])
        self.assertEqual(livevar1, livevar2)

        # Checks in_node set equality.
        livevar1.in_node = set(['a'])
        self.assertFalse(livevar1 == livevar2)
        livevar2.in_node = set(['a'])
        self.assertEqual(livevar1, livevar2)

        # Checks out_node set equality.
        livevar1.out_node = set(['a'])
        self.assertFalse(livevar1 == livevar2)
        livevar2.out_node = set(['a'])
        self.assertEqual(livevar1, livevar2)


# Test FunctionBlockInformation class.
class TestFunctionBlockInformation(unittest.TestCase):

    def setUp(self):
        Block._label_counter.reset()

    def _get_func_block(self):
        source = ('def funcA():\n'                      # line 1
                  '     a = 5\n'                        # line 2
                  '     hpixels = 5\n'                  # line 3
                  '     wpixels = 10\n'                 # line 4
                  '     for y in range(5):\n'           # line 5
                  '         for x in range(2):\n'       # line 6
                  '             hpixels += 1\n'         # line 7
                  '             new_var = 0\n'          # line 8
                  '         wpixels += 1\n'             # line 9
                  '     print(hpixels)\n')              # line 10
        node = ast.parse(source)
        generator = CFGGenerator(False)
        cfg = generator.generate(node, source)
        func = cfg.get_func('funcA')
        return func

    def test_equality(self):
        info1 = FunctionBlockInformation()
        info2 = FunctionBlockInformation()
        func = self._get_func_block()
        self.assertNotEqual(info1, None)
        self.assertNotEqual(info1, 1)

        # Test equality of blockinfo type blocks.
        info1.init(func, LiveVariables)
        info2.init(func, ReachingDefinitions)
        self.assertNotEqual(info1, info2)
        info2.init(func, LiveVariables)
        self.assertEqual(info1, info2)

    def test_init(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        # Checks general information equal.
        self.assertEqual(info._block_info_class, LiveVariables)

        # Checks keys for block info.
        keys = set(['funcA', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7'])
        self.assertEqual(set(info._block_info.keys()), keys)

        # Checks keys for instructions.
        keys = set(range(1, 11))
        self.assertEqual(set(info._instructions.keys()), keys)
        self.assertEqual(set(info._instruction_info.keys()), keys)

    def test_blocks(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        blocks = info.blocks()
        self.assertEqual(blocks[0][0].label, 'funcA')
        self.assertEqual(blocks[1][0].label, 'L2')
        self.assertEqual(blocks[2][0].label, 'L3')
        self.assertEqual(blocks[3][0].label, 'L5')
        self.assertEqual(blocks[4][0].label, 'L6')
        self.assertEqual(blocks[5][0].label, 'L7')
        self.assertEqual(blocks[6][0].label, 'L4')
        self.assertEqual(blocks[7][0].label, 'L1')

    def test_instructions(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        instructions = info.instructions()
        linenos = [instr.lineno for instr, info in instructions]
        self.assertEqual(linenos, list(range(1, 11)))

    def test_get_block_info(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        block_info = info.get_block_info(func)
        self.assertEqual(type(block_info), LiveVariables)

    def test_get_instruction(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        instr = info.get_instruction(1)
        self.assertEqual(instr.lineno, 1)
        self.assertFalse(info.get_instruction(13))

    def test_get_instruction_info(self):
        info = FunctionBlockInformation()
        func = self._get_func_block()
        info.init(func, LiveVariables)

        instr_info = info.get_instruction_info(1)
        self.assertEqual(type(instr_info), LiveVariables)
        self.assertFalse(info.get_instruction_info(13))


if __name__ == '__main__':
    unittest.main()
