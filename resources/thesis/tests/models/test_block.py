# File name: test_block.py
# Author: Nupur Garg
# Date created: 12/25/2016
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.models.block import BlockList, Block, FunctionBlock
from src.models.instruction import Instruction, InstructionType
from src.generatecfg import CFGGenerator


# Test BlockList class.
class TestBlockList(unittest.TestCase):

    def setUp(self):
        self.block_list1 = BlockList()  # funcA
        self.block_list2 = BlockList()  # funcA
        self.block_list3 = BlockList()  # funcB
        self.block_list4 = BlockList()  # no funcs
        self.block_list5 = BlockList()  # funcA, funcB

        self.funcA = FunctionBlock('funcA')
        self.funcB = FunctionBlock('funcB')
        self.block_list1.add(self.funcA)
        self.block_list2.add(self.funcA)
        self.block_list3.add(self.funcB)
        self.block_list5.add(self.funcA)
        self.block_list5.add(self.funcB)

    def test_to_string(self):
        result = ('funcA | \n'
                  '      | successors()\n'
                  '      | predecessors()\n\n\n')
        self.assertEqual(str(self.block_list1), result)
        self.assertEqual(str(self.block_list4), '')

        result = ('funcA | \n'
                  '      | successors()\n'
                  '      | predecessors()\n\n\n'
                  'funcB | \n'
                  '      | successors()\n'
                  '      | predecessors()\n\n\n')
        self.assertEqual(str(self.block_list5), result)

    def test_equals(self):
        self.assertFalse(self.block_list1 == None)
        self.assertFalse(self.block_list1 == 1)
        self.assertEqual(self.block_list1, self.block_list2)
        self.assertFalse(self.block_list1 == self.block_list3)
        self.assertFalse(self.block_list1 == self.block_list4)
        self.assertFalse(self.block_list1 == self.block_list5)

    def test_not_equals(self):
        self.assertTrue(self.block_list1 != None)
        self.assertTrue(self.block_list1 != 1)
        self.assertTrue(self.block_list1 != self.block_list3)

    def test_get_func(self):
        self.assertEqual(self.block_list1.get_func('funcA'), self.funcA)
        self.assertEqual(self.block_list1.get_func('funcB'), None)

    def test_funcs(self):
        self.assertEqual(self.block_list1.get_funcs(), [self.funcA])

    def test_get_num_funcs(self):
        self.assertEqual(self.block_list1.get_num_funcs(), 1)
        self.assertEqual(self.block_list2.get_num_funcs(), 1)
        self.assertEqual(self.block_list3.get_num_funcs(), 1)
        self.assertEqual(self.block_list4.get_num_funcs(), 0)
        self.assertEqual(self.block_list5.get_num_funcs(), 2)


# Test Block class.
class TestBlock(unittest.TestCase):

    def setUp(self):
        self.block1 = Block()
        self.block2 = Block()
        self.block3 = Block()
        self.block4 = Block()

    def assertSuccessorsEqual(self, block, successors):
        actual = set(block.successors.keys())
        if successors is None:
            self.assertFalse(actual)
        else:
            expected = [successor.label for successor in successors]
            self.assertEqual(actual, set(expected))

    def assertPredecessorsEqual(self, block, predecessors):
        actual = set(block.predecessors.keys())
        if predecessors is None:
            self.assertFalse(actual)
        else:
            expected = [predecessor.label for predecessor in predecessors]
            self.assertEqual(actual, set(expected))

    def test_to_string(self):
        instr = Instruction(lineno=1)
        instr.referenced.add('varA')
        instr.defined.add('varB')
        self.block1.add_instruction(instr)

        label = self.block1.label
        spaces = ' ' * len(label)
        result = ('{} | \n'
                  '{} | successors()\n'
                  '{} | predecessors()\n'
                  '\t#1 | REF(varA) DEF(varB)\n').format(label, spaces, spaces)
        self.assertEqual(str(self.block1), result)


    def test_labels(self):
        block_label1 = int(self.block1.label[1:])
        block_label2 = int(self.block2.label[1:])
        self.assertEqual(block_label2 - block_label1, 1)

        # Ensure error when trying to reset label.
        with self.assertRaises(ValueError) as context:
            self.block1.label = 'error_label'

    def test_equals(self):
        self.block2.add_predecessor(self.block1)
        self.block3.add_predecessor(self.block1)
        self.block2.add_successor(self.block4)
        self.block3.add_successor(self.block4)

        self.assertFalse(self.block2 == None)
        self.assertFalse(self.block2 == 1)
        self.assertFalse(self.block2 == self.block3)
        self.assertTrue(self.block2.equals(self.block3))

        instrA = Instruction(lineno=1)
        instrB = Instruction(lineno=1)
        instrB.referenced.add('varA')
        self.block2.add_instruction(instrA)
        self.block3.add_instruction(instrB)
        self.assertFalse(self.block2.equals(self.block3))

    def test_check_successor_equality(self):
        # Checks block with less than 2 successors.
        self.assertTrue(self.block1.check_successor_equality())
        self.block1.add_successor(self.block2)
        self.assertTrue(self.block1.check_successor_equality())

        # Checks block with successors.
        self.block1.add_successor(self.block3)
        self.block1.add_successor(self.block4)
        self.assertTrue(self.block1.check_successor_equality())

        # Checks block with different successors.
        instr = Instruction(lineno=1)
        self.block4.add_instruction(instr)
        self.assertFalse(self.block1.check_successor_equality())

    def test_add_reference(self):
        self.block1.add_reference(lineno=1, variable='varA')
        self.assertEqual(self.block1._instructions[1].referenced, set(['varA']))
        self.assertFalse(self.block1._instructions[1].defined)
        self.assertEqual(len(self.block1.get_instructions()), 1)
        self.assertEqual(set(self.block1._instructions.keys()), set([1]))

        self.block1.add_reference(lineno=2, variable='varA')
        self.block1.add_reference(lineno=2, variable='varB')
        self.assertEqual(self.block1._instructions[2].referenced, set(['varA', 'varB']))
        self.assertFalse(self.block1._instructions[2].defined)
        self.assertEqual(len(self.block1.get_instructions()), 2)
        self.assertEqual(set(self.block1._instructions.keys()), set([1, 2]))

    def test_add_definition(self):
        self.block1.add_definition(lineno=1, variable='varB')
        self.assertFalse(self.block1._instructions[1].referenced)
        self.assertEqual(self.block1._instructions[1].defined, set(['varB']))
        self.assertEqual(len(self.block1.get_instructions()), 1)
        self.assertEqual(set(self.block1._instructions.keys()), set([1]))

        self.block1.add_definition(lineno=2, variable='varA')
        self.block1.add_definition(lineno=2, variable='varC')
        self.assertFalse(self.block1._instructions[2].referenced)
        self.assertEqual(self.block1._instructions[2].defined, set(['varA', 'varC']))
        self.assertEqual(len(self.block1.get_instructions()), 2)
        self.assertEqual(set(self.block1._instructions.keys()), set([1, 2]))

    def test_add_instruction_type(self):
        self.block1.add_reference(lineno=1, variable='varA')
        self.assertEqual(self.block1._instructions[1].referenced, set(['varA']))
        self.assertEqual(self.block1._instructions[1].instruction_type, None)

        self.block1.add_instruction_type(lineno=1, instruction_type=InstructionType.RETURN)
        self.assertEqual(self.block1._instructions[1].instruction_type, InstructionType.RETURN)

    def test_add_instr_control(self):
        self.block1.add_reference(lineno=1, variable='varA')
        self.block1.add_reference(lineno=2, variable='varA')
        self.assertEqual(self.block1._instructions[1].referenced, set(['varA']))
        self.assertEqual(self.block1._instructions[2].referenced, set(['varA']))
        self.assertEqual(self.block1._instructions[2].control, None)

        self.block1.add_instr_control(lineno=2, control=1)
        self.assertEqual(self.block1._instructions[2].control, 1)

    def test_add_instr_indent(self):
        self.block1.add_reference(lineno=1, variable='varA')
        self.block1.add_reference(lineno=2, variable='varA')
        self.assertEqual(self.block1._instructions[1].referenced, set(['varA']))
        self.assertEqual(self.block1._instructions[2].referenced, set(['varA']))
        self.assertEqual(self.block1._instructions[2].indentation, None)

        self.block1.add_instr_indent(lineno=2, indentation=1)
        self.assertEqual(self.block1._instructions[2].indentation, 1)

    def test_method_add_instruction(self):
        instr = Instruction(lineno=1)
        instr.referenced.add('varA')
        instr.defined.add('varB')
        self.block1.add_instruction(instr)
        self.assertEqual(len(self.block1.get_instructions()), 1)
        self.assertEqual(set(self.block1._instructions.keys()), set([1]))

    def test_add_multiline_instructions(self):
        instr = Instruction(lineno=1)
        self.block1.add_instruction(instr)
        self.assertFalse(self.block1._instructions[1].multiline)

        self.block1.add_multiline_instructions(lineno=1, linenos=[2, 3])
        self.assertEqual(self.block1._instructions[1].multiline, set([1, 2, 3]))

    def test_add_successor(self):
        self.block1.add_successor(self.block1)
        self.block1.add_successor(self.block2)
        self.block1.add_successor(self.block3)
        self.assertSuccessorsEqual(self.block1, [self.block2, self.block3])
        self.assertPredecessorsEqual(self.block2, [self.block1])
        self.assertPredecessorsEqual(self.block3, [self.block1])

    def test_add_predecessor(self):
        self.block1.add_predecessor(self.block1)
        self.block1.add_predecessor(self.block2)
        self.block1.add_predecessor(self.block3)
        self.assertPredecessorsEqual(self.block1, [self.block2, self.block3])
        self.assertSuccessorsEqual(self.block2, [self.block1])
        self.assertSuccessorsEqual(self.block3, [self.block1])

    def test_set_successors(self):
        self.block1.add_successor(self.block1)
        self.block1.add_successor(self.block2)
        self.block1.add_successor(self.block3)
        self.assertSuccessorsEqual(self.block1, [self.block2, self.block3])
        self.assertPredecessorsEqual(self.block2, [self.block1])
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.set_successors([self.block1, self.block2])
        self.assertSuccessorsEqual(self.block1, [self.block2])
        self.assertPredecessorsEqual(self.block2, [self.block1])
        self.assertPredecessorsEqual(self.block3, None)

        self.block1.set_successors([self.block3])
        self.assertSuccessorsEqual(self.block1, [self.block3])
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.set_successors([])
        self.assertSuccessorsEqual(self.block1, None)
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, None)

    def test_replace_successor(self):
        self.block1.add_successor(self.block1)
        self.block1.add_successor(self.block2)
        self.assertSuccessorsEqual(self.block1, [self.block2])
        self.assertPredecessorsEqual(self.block2, [self.block1])
        self.assertPredecessorsEqual(self.block3, None)

        self.block1.replace_successor(self.block2, self.block3)
        self.assertSuccessorsEqual(self.block1, [self.block3])
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.replace_successor(self.block3, self.block1)
        self.assertSuccessorsEqual(self.block1, None)
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, None)

        # Ensure error when trying to replace non-existant successor.
        with self.assertRaises(ValueError) as context:
            self.block1.replace_successor(self.block3, self.block1)

        # Before: Block 1 --> Block2 --> Block3
        # After: Block1 --> Block3 and Block2 --> Block3
        self.block1.add_successor(self.block2)
        self.block2.add_successor(self.block3)
        self.block1.replace_successor(self.block2, self.block3)
        self.assertSuccessorsEqual(self.block1, [self.block3])
        self.assertPredecessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block2, [self.block3])
        self.assertPredecessorsEqual(self.block3, [self.block1, self.block2])

    def test_replace_predecessor(self):
        self.block1.add_predecessor(self.block1)
        self.block1.add_predecessor(self.block2)
        self.assertPredecessorsEqual(self.block1, [self.block2])
        self.assertSuccessorsEqual(self.block2, [self.block1])
        self.assertSuccessorsEqual(self.block3, None)

        self.block1.replace_predecessor(self.block2, self.block3)
        self.assertPredecessorsEqual(self.block1, [self.block3])
        self.assertSuccessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block3, [self.block1])

        self.block1.replace_predecessor(self.block3, self.block1)
        self.assertPredecessorsEqual(self.block1, None)
        self.assertSuccessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block3, None)

        # Ensure error when trying to replace non-existant predecessor.
        with self.assertRaises(ValueError) as context:
            self.block1.replace_predecessor(self.block3, self.block1)

        # Before: Block 1 <-- Block2 <-- Block3
        # After: Block1 <-- Block3 and Block2 <-- Block3
        self.block1.add_predecessor(self.block2)
        self.block2.add_predecessor(self.block3)
        self.block1.replace_predecessor(self.block2, self.block3)
        self.assertPredecessorsEqual(self.block1, [self.block3])
        self.assertSuccessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block2, [self.block3])
        self.assertSuccessorsEqual(self.block3, [self.block1, self.block2])

    def test_remove_successor(self):
        self.block1.add_successor(self.block1)
        self.block1.add_successor(self.block2)
        self.block1.add_successor(self.block3)
        self.assertSuccessorsEqual(self.block1, [self.block2, self.block3])
        self.assertPredecessorsEqual(self.block2, [self.block1])
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.remove_successor(self.block2)
        self.assertSuccessorsEqual(self.block1, [self.block3])
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.remove_successor(self.block1)
        self.assertSuccessorsEqual(self.block1, [self.block3])
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, [self.block1])

        self.block1.remove_successor(self.block3)
        self.assertSuccessorsEqual(self.block1, None)
        self.assertPredecessorsEqual(self.block2, None)
        self.assertPredecessorsEqual(self.block3, None)

    def test_remove_predecessor(self):
        self.block1.add_predecessor(self.block1)
        self.block1.add_predecessor(self.block2)
        self.block1.add_predecessor(self.block3)
        self.assertPredecessorsEqual(self.block1, [self.block2, self.block3])
        self.assertSuccessorsEqual(self.block2, [self.block1])
        self.assertSuccessorsEqual(self.block3, [self.block1])

        self.block1.remove_predecessor(self.block2)
        self.assertPredecessorsEqual(self.block1, [self.block3])
        self.assertSuccessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block3, [self.block1])

        self.block1.remove_predecessor(self.block1)
        self.assertPredecessorsEqual(self.block1, [self.block3])
        self.assertSuccessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block3, [self.block1])

        self.block1.remove_predecessor(self.block3)
        self.assertPredecessorsEqual(self.block1, None)
        self.assertSuccessorsEqual(self.block2, None)
        self.assertSuccessorsEqual(self.block3, None)

    def test_destroy(self):
        self.block1.set_successors([self.block2, self.block3])
        self.block2.add_successor(self.block4)
        self.block3.add_successor(self.block4)

        self.block3.destroy()
        self.assertSuccessorsEqual(self.block1, [self.block2])
        self.assertPredecessorsEqual(self.block3, None)
        self.assertSuccessorsEqual(self.block3, None)
        self.assertPredecessorsEqual(self.block4, [self.block2])

        self.block2.destroy()
        self.assertSuccessorsEqual(self.block1, None)
        self.assertPredecessorsEqual(self.block3, None)
        self.assertSuccessorsEqual(self.block3, None)
        self.assertPredecessorsEqual(self.block4, None)

    def test_get_instruction(self):
        instr = Instruction(lineno=1)
        instr.referenced.add('varA')
        instr.defined.add('varB')
        self.block1.add_instruction(instr)

        result = self.block1.get_instruction(lineno=1)
        self.assertEqual(result.lineno, instr.lineno)
        self.assertEqual(result.referenced, instr.referenced)
        self.assertEqual(result.defined, instr.defined)
        self.assertFalse(self.block1.get_instruction(lineno=2))

    def test_get_instruction_linenos(self):
        self.assertFalse(self.block1.get_instruction_linenos())
        self.block1.add_definition(lineno=1, variable='varB')
        self.block1.add_definition(lineno=2, variable='varA')
        self.assertEqual(self.block1.get_instruction_linenos(), set([1, 2]))

    def test_get_instructions(self):
        self.block1.add_reference(lineno=2, variable='varA')
        self.block1.add_definition(lineno=1, variable='varA')

        instructions = self.block1.get_instructions()
        self.assertEqual(instructions[0].lineno, 1)
        self.assertEqual(instructions[1].lineno, 2)

    def test_get_last_instruction(self):
        self.assertFalse(self.block1.get_instruction_linenos())
        self.block1.add_definition(lineno=1, variable='varB')
        self.block1.add_definition(lineno=2, variable='varA')
        self.assertEqual(self.block1.get_last_instruction(), 2)

    def test_get_first_successor(self):
        self.block1.set_successors([self.block2, self.block3])
        successor = self.block1.get_first_successor()
        self.assertEqual(successor, self.block2)

        self.block1.remove_successor(successor)
        successor = self.block1.get_first_successor()
        self.assertEqual(successor, self.block3)

        self.block1.remove_successor(successor)
        successor = self.block1.get_first_successor()
        self.assertEqual(successor, None)

    def test_get_first_predecessor(self):
        self.block1.add_predecessor(self.block2)
        self.block1.add_predecessor(self.block3)
        predecessor = self.block1.get_first_predecessor()
        self.assertEqual(predecessor, self.block2)

        self.block1.remove_predecessor(predecessor)
        predecessor = self.block1.get_first_predecessor()
        self.assertEqual(predecessor, self.block3)

        self.block1.remove_predecessor(predecessor)
        predecessor = self.block1.get_first_predecessor()
        self.assertEqual(predecessor, None)


# Tests FunctionBlock class.
class TestFunctionBlock(unittest.TestCase):

    def setUp(self):
        Block._label_counter.reset()
        self.func_block1 = FunctionBlock('func1')
        self.generator = CFGGenerator(False)

    def _generate_cfg(self, source):
        node = ast.parse(source)
        cfg = self.generator.generate(node, source)
        return cfg

    def test_labels(self):
        self.assertEqual(self.func_block1.label, 'func1')
        with self.assertRaises(ValueError) as context:
            self.func_block1.label = 'error_label'

    def test_to_string(self):
        result = ('func1 | \n'
                  '      | successors()\n'
                  '      | predecessors()\n\n')
        self.assertEqual(str(self.func_block1), result)

        block = Block()
        self.func_block1.add_successor(block)

        label = block.label
        spaces = ' ' * len(label)
        result = ('func1 | \n'
                  '      | successors({})\n'
                  '      | predecessors()\n\n'
                  '{} | \n'
                  '{} | successors()\n'
                  '{} | predecessors(func1)\n\n').format(label, label, spaces, spaces)
        self.assertEqual(str(self.func_block1), result)

    def test_get_sorted_blocks(self):
        source = ('def funcA():\n'
                  '    integers = [[1, 2], [3, 4]]\n'
                  '    for numbers in integers:\n'
                  '        for integer in numbers:\n'
                  '            print("%d " %integer)')

        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')
        sorted_blocks = funcA.get_sorted_blocks()

        self.assertEqual(sorted_blocks[0].label, 'funcA')
        self.assertEqual(sorted_blocks[1].label, 'L2')
        self.assertEqual(sorted_blocks[2].label, 'L3')
        self.assertEqual(sorted_blocks[3].label, 'L5')
        self.assertEqual(sorted_blocks[4].label, 'L6')
        self.assertEqual(sorted_blocks[5].label, 'L7')
        self.assertEqual(sorted_blocks[6].label, 'L4')
        self.assertEqual(sorted_blocks[7].label, 'L1')

    def test_get_cyclomatic_complexity(self):
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

        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')
        sorted_blocks = funcA.get_sorted_blocks()

        self.assertEqual(funcA._get_num_nodes(sorted_blocks), 7)
        self.assertEqual(funcA._get_num_edges(sorted_blocks), 8)
        self.assertEqual(funcA._get_num_exits(sorted_blocks, 6), 3)
        self.assertEqual(funcA.get_cyclomatic_complexity(), 7)

    def test_get_lineno_in_func(self):
        source = ('def funcA():\n'              # line 1
                  '     i = 3\n'                # line 2
                  '     i = j = i + 1\n'        # line 3
                  '     a = j + 2\n'            # line 4
                  '     while a > 0:\n'         # line 5
                  '         i = i + 1\n'        # line 6
                  '         j = j - 1\n'        # line 7
                  '\n'                          # line 8
                  '         if i != j:\n'       # line 9
                  '             a = a - 1\n'    # line 10
                  '         i = i + 1')         # line 11

        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')

        linenos = funcA.get_linenos_in_func()
        self.assertEqual(len(linenos), 10)
        self.assertEqual(linenos, [1, 2, 3, 4, 5, 6, 7, 9, 10, 11])

    def test_get_function_parameters(self):
        # No instruction in function.
        self.assertEqual(self.func_block1.get_function_parameters(), None)

        # Function without parameters.
        source = ('def funcA():\n'
                  '    pass\n')
        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')
        self.assertEqual(funcA.get_function_parameters(), None)

        # Function with 1 parameter.
        source = ('def funcA(x):\n'
                  '    pass\n')
        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')
        self.assertEqual(funcA.get_function_parameters(), set(['x']))

        # Function with parameters.
        source = ('def funcA(x, y):\n'
                  '    pass\n')
        cfg = self._generate_cfg(source)
        funcA = cfg.get_func('funcA')
        self.assertEqual(funcA.get_function_parameters(), set(['x', 'y']))


if __name__ == '__main__':
    unittest.main()
