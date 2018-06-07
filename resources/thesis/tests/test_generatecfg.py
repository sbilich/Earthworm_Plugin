# File name: test_generatecfg.py
# Author: Nupur Garg
# Date created: 12/26/2016
# Python Version: 3.5


import unittest
import ast

from src.globals import *
from src.models.block import Block
from src.models.instruction import InstructionType
from src.generatecfg import TokenGenerator, CFGGenerator


class TestGenerateTokens(unittest.TestCase):

    def setUp(self):
        Block._label_counter.reset()

    def test_is_end_slash(self):
        tokens = TokenGenerator('')

        # No slash
        line = 'x = "testing\\n"\n'
        self.assertFalse(tokens._is_end_slash(line))

        # Slash withe newline.
        line = 'x = "testing\\n"\\\n'
        self.assertTrue(tokens._is_end_slash(line))

        # Slash with space then newline
        line = 'x = "testing\\n"\\ \n'
        self.assertFalse(tokens._is_end_slash(line))

        # Slash with only space.
        line = '   x = "testing\\n"\\ '
        self.assertFalse(tokens._is_end_slash(line))

    def test_get_space_start(self):
        tokens = TokenGenerator('')

        # No spaces.
        line = 'x = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '')

        # 2 spaces.
        line = '  x = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '  ')

        # 3 spaces.
        line = '   x = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '   ')

        # 4 spaces.
        line = '    x = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '    ')

        # Tab.
        line = '\tx = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '\t')

        # Tab with 2 spaces.
        line = '\t  x = "testing\\n"\n'
        self.assertEqual(tokens._get_space_start(line), '\t  ')

    def test_is_quotation(self):
        tokens = TokenGenerator('')

        # Single quotations.
        self.assertTrue(tokens._is_quotation('\'', None))
        self.assertFalse(tokens._is_quotation('\'', '\\'))
        self.assertTrue(tokens._is_quotation('\'', ' '))
        self.assertTrue(tokens._is_quotation('\'', '('))

        # Double quotations.
        self.assertTrue(tokens._is_quotation('"', None))
        self.assertFalse(tokens._is_quotation('\"', '\\'))
        self.assertTrue(tokens._is_quotation('\"', ' '))
        self.assertTrue(tokens._is_quotation('\"', '('))

    def test_get_blank_lines_spaces(self):
        source = ('string0 = "hi0"\n'                           # line 1
                  '\n'                                          # line 2
                  'def funcA():\n'                              # line 3
                  '    string1 = "hi1"\n'                       # line 4
                  '    \n'                                      # line 5
                  '                                       \n'   # line 6
                  '    string2, string3 = string1, "hello"\n'   # line 7
                  '             \n'                             # line 8
                  '    string4 = string5 = "hi3"\n'             # line 9
                  '\n'                                          # line 10
                  '    print(string1)')                         # line 11
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.blank_lines, set([2, 5, 6, 8, 10]))
        self.assertFalse(tokens.comments)
        self.assertFalse(tokens.multiline)

    def test_get_blank_lines_tabs(self):
        source = ('string0 = "hi0"\n'                           # line 1
                  '\n'                                          # line 2
                  'def funcA():\n'                              # line 3
                  '\tstring1 = "hi1"\n'                         # line 4
                  '\t\n'                                        # line 5
                  '\t\t\t\t\t\t\n'                              # line 6
                  '\tstring2, string3 = string1, "hello"\n'     # line 7
                  '\t\t\t\n'                                    # line 8
                  '\tstring4 = string5 = "hi3"\n'               # line 9
                  '\n'                                          # line 10
                  '\tprint(string1)')                           # line 11
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.blank_lines, set([2, 5, 6, 8, 10]))
        self.assertFalse(tokens.comments)
        self.assertFalse(tokens.multiline)

    def test_comments_single_line(self):
        source = ('string0 = "hi0"\n'                           # line 1
                  '# Function A.\n'                             # line 2
                  'def funcA():\n'                              # line 3
                  '    string1 = "hi1"\n'                       # line 4
                  '    # Initialize string1.\n'                 # line 5
                  '    # Also Initialize string2, string 3.\n'  # line 6
                  '    string2, string3 = string1, "hello"\n'   # line 7
                  '    # Initialize string4, string5.\n'        # line 8
                  '    string4 = string5 = ("hi3") #hi\n'       # line 9
                  '    # Print string1.\n'                      # line 10
                  '    print(string1)')                         # line 11
        tokens = TokenGenerator(source)
        self.assertFalse(tokens.blank_lines)
        self.assertEqual(tokens.comments, set([2, 5, 6, 8, 10]))
        self.assertFalse(tokens.multiline)

    def test_comments_multiline(self):
        source = ('string0 = "hi0"\n'                           # line 1
                  '# Regular comment for fun.\n'                # line 2
                  'def funcA():\n'                              # line 3
                  '    string1 = "hi1"\n'                       # line 4
                  '    """\n'                                   # line 5
                  '    Inside comment block"""\n'               # line 6
                  '    string2, string3 = string1, "hello"\n'   # line 7
                  '    """Single line comment block"""\n'       # line 8
                  '    string4 = string5 = "hi3"\n'             # line 9
                  '    """"""\n'                                # line 10
                  '    Last comment block.\n'                   # line 11
                  '    """\n'                                   # line 12
                  '    print(string1)')                         # line 13
        tokens = TokenGenerator(source)
        self.assertFalse(tokens.blank_lines)
        self.assertEqual(tokens.comments, set([2, 5, 6, 8, 10, 11, 12]))
        self.assertFalse(tokens.multiline)

    def test_multiline_parenthesis(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n"\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = (y\n'                    # line 5
                  '         + y)\n'                 # line 6
                  '    if (z\n'                     # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        return z\n'              # line 9
                  '    return (x +\n'               # line 10
                  '           "test")\n')           # line 11
        tokens = TokenGenerator(source)
        self.assertFalse(tokens.blank_lines)
        self.assertFalse(tokens.comments)

        keys = set([2, 3, 4, 5, 6, 7, 8, 10, 11])
        self.assertEqual(set(tokens.multiline.keys()), keys)

        self.assertEqual(tokens.multiline[2], set([2, 3, 4]))
        self.assertEqual(tokens.multiline[3], set([2, 3, 4]))
        self.assertEqual(tokens.multiline[4], set([2, 3, 4]))

        self.assertEqual(tokens.multiline[5], set([5, 6]))
        self.assertEqual(tokens.multiline[6], set([5, 6]))

        self.assertEqual(tokens.multiline[7], set([7, 8]))
        self.assertEqual(tokens.multiline[8], set([7, 8]))

        self.assertEqual(tokens.multiline[10], set([10, 11]))
        self.assertEqual(tokens.multiline[11], set([10, 11]))

    def test_multiline_parenthesis_with_strs(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = (\'(testing\\n\'\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = ("\\\"(y\\\n'                   # line 5
                  '         + y #")\n'                 # line 6
                  '    if (z # (\n'                 # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        return z\n'              # line 9
                  '    return (x +\n'               # line 10
                  '           "test")\n')           # line 11
        tokens = TokenGenerator(source)
        self.assertFalse(tokens.blank_lines)
        self.assertFalse(tokens.comments)

        keys = set([2, 3, 4, 5, 6, 7, 8, 10, 11])
        self.assertEqual(set(tokens.multiline.keys()), keys)

        self.assertEqual(tokens.multiline[2], set([2, 3, 4]))
        self.assertEqual(tokens.multiline[3], set([2, 3, 4]))
        self.assertEqual(tokens.multiline[4], set([2, 3, 4]))

        self.assertEqual(tokens.multiline[5], set([5, 6]))
        self.assertEqual(tokens.multiline[6], set([5, 6]))

        self.assertEqual(tokens.multiline[7], set([7, 8]))
        self.assertEqual(tokens.multiline[8], set([7, 8]))

        self.assertEqual(tokens.multiline[10], set([10, 11]))
        self.assertEqual(tokens.multiline[11], set([10, 11]))

    def test_multiline_slash(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n" \\\n'      # line 2
                  '     #"testing2 (\\n" \\\n'      # line 3
                  '\n'                              # line 4
                  '            "testing3")\n'       # line 5
                  '    z = y\\\n'                   # line 6
                  '         + y\n'                  # line 7
                  '    if z\\\n'                    # line 8
                  '     < 7 or len(x) < 2:\n'       # line 9
                  '        return z\n'              # line 10
                  '    # testing () \\\n'           # line 11
                  '    return x +\\\n'              # line 12
                  '           "test"\n')            # line 13
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.blank_lines, set([4]))
        self.assertEqual(tokens.comments, set([3, 11]))

        keys = set([2, 3, 4, 5, 6, 7, 8, 9, 12, 13])
        self.assertEqual(set(tokens.multiline.keys()), keys)

        self.assertEqual(tokens.multiline[2], set([2, 3, 4, 5]))
        self.assertEqual(tokens.multiline[3], set([2, 3, 4, 5]))
        self.assertEqual(tokens.multiline[4], set([2, 3, 4, 5]))
        self.assertEqual(tokens.multiline[5], set([2, 3, 4, 5]))

        self.assertEqual(tokens.multiline[6], set([6, 7]))
        self.assertEqual(tokens.multiline[7], set([6, 7]))

        self.assertEqual(tokens.multiline[8], set([8, 9]))
        self.assertEqual(tokens.multiline[9], set([8, 9]))

        self.assertEqual(tokens.multiline[12], set([12, 13]))
        self.assertEqual(tokens.multiline[13], set([12, 13]))

    def test_get_indentation(self):
        # No lines.
        source = ''
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.indentation, None)

        # No indentation.
        source = ('x = "testing\\n"\n'
                  'y = "argh\\n"\n')
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.indentation, '')

        # Indentation 3 spaces
        source = ('def funcA(y):\n'                 # line 1
                  '    x = "testing\\n"\n')         # line 2
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.indentation, '    ')

        # Indentation tab.
        source = ('def funcA(y):\n'                 # line 1
                  '\tx = "testing\\n"\n')           # line 2
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.indentation, '\t')

        # Indentation 4 spaces after comment block.
        source = ('  # testing\n'                   # line 1
                  'def funcA(y):\n'                 # line 2
                  '\tx = "testing\\n"\n')           # line 3
        tokens = TokenGenerator(source)
        self.assertEqual(tokens.indentation, '\t')

    def  test_get_line_indentation(self):
        source = ('def funcA():\n'                                      # line 1
                  '    x = int(input("enter test score:"))\n'           # line 2
                  '    if x < 70:\n'                                    # line 3
                  '        print("You need to retake the class.")\n'    # line 4
                  '    elif x < 85:\n'                                  # line 5
                  '        print("You have room for improvement.")\n'   # line 6
                  '    else:\n'                                         # line 7
                  '        print("Great job!")\n'                       # line 8
                  '        print("Testing multi-line else")\n')         # line 9
        tokens = TokenGenerator(source)

        self.assertEqual(tokens.line_indent[1], 0)
        self.assertEqual(tokens.line_indent[2], 1)
        self.assertEqual(tokens.line_indent[3], 1)
        self.assertEqual(tokens.line_indent[4], 2)
        self.assertEqual(tokens.line_indent[5], 1)
        self.assertEqual(tokens.line_indent[6], 2)
        self.assertEqual(tokens.line_indent[7], 1)
        self.assertEqual(tokens.line_indent[8], 2)
        self.assertEqual(tokens.line_indent[9], 2)

    def test_get_conditionals(self):
        source = ('def funcA():\n'                                      # line 1
                  '    x = int(input("enter test score:"))\n'           # line 2
                  '    if x < 70:\n'                                    # line 3
                  '        print("You need to retake the class.")\n'    # line 4
                  '    elif x < 85:\n'                                  # line 5
                  '        if x < 80:\n'                                # line 6
                  '            print("here")\n'                         # line 7
                  '        else:\n'                                     # line 8
                  '            print("here2")\n'                        # line 9
                  '    else:\n'                                         # line 10
                  '        print("Great job!")\n'                       # line 11
                  '        print("Testing multi-line else")\n')         # line 12
        tokens = TokenGenerator(source)
        self.assertEqual(set(tokens.conditionals.keys()), set([3, 5, 6, 8, 10]))

        self.assertEqual(tokens.conditionals[3], set([3, 5, 10]))
        self.assertEqual(tokens.conditionals[5], set([3, 5, 10]))
        self.assertEqual(tokens.conditionals[10], set([3, 5, 10]))

        self.assertEqual(tokens.conditionals[6], set([6, 8]))
        self.assertEqual(tokens.conditionals[8], set([6, 8]))


    def test_get_try_except(self):
        source = ('def funcA():\n'                                      # line 1
                  '    x = int(input("enter test score:"))\n'           # line 2
                  '    try:\n'                                          # line 3
                  '        print("You need to retake the class.")\n'    # line 4
                  '    except ValueError as e:\n'                       # line 5
                  '        try :\n'                                     # line 6
                  '            print("here")\n'                         # line 7
                  '        except ValueError as e:\n'                   # line 8
                  '            print("here2")\n'                        # line 9
                  '    finally:\n'                                      # line 10
                  '        print("Great job!")\n'                       # line 11
                  '        print("Testing multi-line else")\n')         # line 12
        tokens = TokenGenerator(source)
        self.assertEqual(set(tokens.exceptions.keys()), set([3, 5, 6, 8, 10]))

        self.assertEqual(tokens.exceptions[3], set([3, 5, 10]))
        self.assertEqual(tokens.exceptions[5], set([3, 5, 10]))
        self.assertEqual(tokens.exceptions[10], set([3, 5, 10]))

        self.assertEqual(tokens.exceptions[6], set([6, 8]))
        self.assertEqual(tokens.exceptions[8], set([6, 8]))


class TestGenerateCFG(unittest.TestCase):

    def setUp(self):
        Block._label_counter.reset()
        self.generator = CFGGenerator(False)

    def assertInstrEqual(self, actual, referenced=None, defined=None,
                         instruction_type=None, control=None, multiline=None):
        self.assertEqual(actual.referenced, set(referenced) if referenced else set())
        self.assertEqual(actual.defined, set(defined) if defined else set())
        self.assertEqual(actual.instruction_type, instruction_type)
        self.assertEqual(actual.control, control)
        self.assertEqual(actual.multiline, set(multiline) if multiline else set())

    def assertBlockSuccessorsEqual(self, block, successors=None):
        actual = set(block.successors.keys())
        if successors is None:
            self.assertFalse(actual)
        else:
            self.assertEqual(actual, set(successors))

    def assertBlockPredecessorsEqual(self, block, predecessors=None):
        actual = set(block.predecessors.keys())
        if predecessors is None:
            self.assertFalse(actual)
        else:
            self.assertEqual(actual, set(predecessors))

    def _generate_cfg(self, source):
        node = ast.parse(source)
        cfg = self.generator.generate(node, source)
        return cfg

    def test_no_code(self):
        source = ''
        cfg = self._generate_cfg(source)
        self.assertEqual(cfg.get_num_funcs(), 0)

    def test_simple_script(self):
        source = 'string = "hi"'
        cfg = self._generate_cfg(source)
        self.assertEqual(cfg.get_num_funcs(), 0)

    def test_instr_type_return(self):
        source = ('string0 = "hi"\n'
                  'def funcA():\n'
                  '    x = 5\n'
                  '    return x')
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(3), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(4), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_parameters_definitions(self):
        source = ('def funcA(y):\n'
                  '    x = 5\n'
                  '    return x')
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_assignment_simple(self):
        source = ('string0 = "hi"\n'
                  'def funcA():\n'
                  '    string1 = "hi"\n'
                  '    string2, string3 = string1, "hello"\n'
                  '    string4 = string5 = "hi"\n'
                  '    print(string1)')
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(3), defined=['string1'])
        self.assertInstrEqual(func_block.get_instruction(4), referenced=['string1'], defined=['string2', 'string3'])
        self.assertInstrEqual(func_block.get_instruction(5), defined=['string4', 'string5'])
        self.assertInstrEqual(func_block.get_instruction(6), referenced=['print', 'string1'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_conditional_only_if(self):
        source = ('def funcA():\n'
                  '    x = int(input("enter test score:"))\n'
                  '    if x < 70:\n'
                  '        print("You need to retake the class.")\n'
                  '    print("Done")\n')
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), referenced=['int', 'input'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['x'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['print'], control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L3'])

        after_block = func_block.successors['L3']
        self.assertInstrEqual(after_block.get_instruction(5), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2', 'funcA'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L3'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_conditional_simple_if_elif_else(self):
        source = ('def funcA():\n'                                      # line 1
                  '    x = int(input("enter test score:"))\n'           # line 2
                  '    if x < 70:\n'                                    # line 3
                  '        print("You need to retake the class.")\n'    # line 4
                  '    elif x < 85:\n'                                  # line 5
                  '        print("You have room for improvement.")\n'   # line 6
                  '    else:\n'                                         # line 7
                  '        print("Great job!")\n'                       # line 8
                  '        print("Testing multi-line else")\n')         # line 9
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), referenced=['int', 'input'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['x'], multiline=[3, 5, 7])
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block_1 = func_block.successors['L2']
        self.assertInstrEqual(if_block_1.get_instruction(4), referenced=['print'], control=3)
        self.assertBlockPredecessorsEqual(if_block_1, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block_1, ['L7'])

        else_block_1 = func_block.successors['L3']
        self.assertInstrEqual(else_block_1.get_instruction(5), referenced=['x'], control=3, multiline=[3, 5, 7])
        self.assertBlockPredecessorsEqual(else_block_1, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block_1, ['L4', 'L5'])

        if_block_2 = else_block_1.successors['L4']
        self.assertInstrEqual(if_block_2.get_instruction(6), referenced=['print'], control=5)
        self.assertBlockPredecessorsEqual(if_block_2, ['L3'])
        self.assertBlockSuccessorsEqual(if_block_2, ['L6'])

        else_block_2 = else_block_1.successors['L5']
        self.assertInstrEqual(else_block_2.get_instruction(7), instruction_type=InstructionType.ELSE, control=5, multiline=[3, 5, 7])
        self.assertInstrEqual(else_block_2.get_instruction(8), referenced=['print'], control=7)
        self.assertInstrEqual(else_block_2.get_instruction(9), referenced=['print'], control=7)
        self.assertBlockPredecessorsEqual(else_block_2, ['L3'])
        self.assertBlockSuccessorsEqual(else_block_2, ['L6'])

        after_block_2 = if_block_2.successors['L6']
        self.assertFalse(after_block_2._instructions)
        self.assertBlockPredecessorsEqual(after_block_2, ['L4', 'L5'])
        self.assertBlockSuccessorsEqual(after_block_2, ['L7'])

        after_block_1 = if_block_1.successors['L7']
        self.assertFalse(after_block_1._instructions)
        self.assertBlockPredecessorsEqual(after_block_1, ['L2', 'L6'])
        self.assertBlockSuccessorsEqual(after_block_1, ['L1'])

        exit_block = after_block_1.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L7'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_loop_single_for(self):
        source = ('def funcA():\n'                                  # line 1
                  '    favs = ["berry", "apple"]\n'                 # line 2
                  '    name = "peter"\n'                            # line 3
                  '    for item in favs:\n'                         # line 4
                  '        print("%s likes %s" % (name, item))')    # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), defined=['favs'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(4), referenced=['favs'], defined=['item'], instruction_type=InstructionType.FOR)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA', 'L3'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(5), referenced=['print', 'item', 'name'], control=4)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L2'])

        after_block = guard_block.successors['L4']
        self.assertFalse(after_block._instructions)
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_loop_nested_for(self):
        source = ('def funcA():\n'                          # line 1
                  '    integers = [[1, 2], [3, 4]]\n'       # line 2
                  '    for numbers in integers:\n'          # line 3
                  '        for integer in numbers:\n'       # line 4
                  '            print("%d " %integer)\n'     # line 5
                  '        print("argh")\n'                 # line 6
                  '    print("done")\n')                    # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), defined=['integers'])
        self.assertBlockPredecessorsEqual(func_block, None)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block_1 = func_block.successors['L2']
        self.assertInstrEqual(guard_block_1.get_instruction(3), referenced=['integers'], defined=['numbers'], instruction_type=InstructionType.FOR)
        self.assertBlockPredecessorsEqual(guard_block_1, ['funcA', 'L7'])
        self.assertBlockSuccessorsEqual(guard_block_1, ['L3', 'L4'])

        body_start_1 = guard_block_1.successors['L3']
        self.assertFalse(body_start_1._instructions)
        self.assertBlockPredecessorsEqual(body_start_1, ['L2'])
        self.assertBlockSuccessorsEqual(body_start_1, ['L5'])

        guard_block_2 = body_start_1.successors['L5']
        self.assertInstrEqual(guard_block_2.get_instruction(4), referenced=['numbers'], defined=['integer'], instruction_type=InstructionType.FOR, control=3)
        self.assertBlockPredecessorsEqual(guard_block_2, ['L3', 'L6'])
        self.assertBlockSuccessorsEqual(guard_block_2, ['L6', 'L7'])

        body_2 = guard_block_2.successors['L6']
        self.assertInstrEqual(body_2.get_instruction(5), referenced=['integer', 'print'], control=4)
        self.assertBlockPredecessorsEqual(body_2, ['L5'])
        self.assertBlockSuccessorsEqual(body_2, ['L5'])

        body_end_1 = guard_block_1.predecessors['L7']
        self.assertInstrEqual(body_end_1.get_instruction(6), referenced=['print'], control=3)
        self.assertBlockPredecessorsEqual(body_end_1, ['L5'])
        self.assertBlockSuccessorsEqual(body_end_1, ['L2'])

        after_block = guard_block_1.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(7), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_loop_single_while(self):
        source = ('def funcA():\n'              # line 1
                  '    i = 0\n'                 # line 2
                  '    while i < 5:\n'          # line 3
                  '        i += 1\n'            # line 4
                  '    print("done")\n')        # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), defined=['i'])
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(3), referenced=['i'], instruction_type=InstructionType.WHILE)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA', 'L3'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(4), referenced=['i'], defined=['i'], control=3)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L2'])

        after_block = guard_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(5), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_loop_single_list_comprehension(self):
        source = ('def funcA():\n'
                  '    x = [i for i in range(5)]\n'
                  '    print(x)\n')
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), referenced=['i', 'range'], defined=['x', 'i'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['x', 'print'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_mid_function(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    return x\n'                  # line 3
                  '    print(x)\n')                 # line 4
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_if(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        return y\n'              # line 4
                  '    return x\n')                 # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_block = func_block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(5), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L1'])

        exit_block = else_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_if_else(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        return y\n'              # line 4
                  '    else:\n'                     # line 5
                  '        return x\n'              # line 6
                  '    return "BAD"\n')             # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'], multiline=[3, 5])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_block = func_block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(5), instruction_type=InstructionType.ELSE, control=3, multiline=[3, 5])
        self.assertInstrEqual(else_block.get_instruction(6), referenced=['x'], instruction_type=InstructionType.RETURN, control=5)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L1'])

        exit_block = else_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_if_no_return(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        print(y)\n'              # line 4
                  '    else:\n'                     # line 5
                  '        return x\n'              # line 6
                  '    return y\n')                 # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'], multiline=[3, 5])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y', 'print'], control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L4'])

        else_block = func_block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(5), instruction_type=InstructionType.ELSE, control=3, multiline=[3, 5])
        self.assertInstrEqual(else_block.get_instruction(6), referenced=['x'], instruction_type=InstructionType.RETURN, control=5)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L1'])

        after_block = if_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(7), referenced=['y'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L3', 'L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_else_no_return(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        return y\n'              # line 4
                  '    else:\n'                     # line 5
                  '        print(x)\n'              # line 6
                  '    return x\n')                 # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'], multiline=[3, 5])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_block = func_block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(5), instruction_type=InstructionType.ELSE, control=3, multiline=[3, 5])
        self.assertInstrEqual(else_block.get_instruction(6), referenced=['x', 'print'], control=5)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L4'])

        after_block = else_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(7), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(after_block, ['L3'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_if_elif_else(self):
        source = ('def funcA(y, z):\n'              # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        return y\n'              # line 4
                  '    elif z < 4:\n'               # line 5
                  '        return z\n'              # line 6
                  '    else:\n'                     # line 7
                  '        return x\n'              # line 8
                  '    return "BAD"\n')             # line 9
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y', 'z'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'], multiline=[3, 5, 7])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_cond_block = func_block.successors['L3']
        self.assertInstrEqual(else_cond_block.get_instruction(5), referenced=['z'], control=3, multiline=[3, 5, 7])
        self.assertBlockPredecessorsEqual(else_cond_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_cond_block, ['L4', 'L5'])

        elif_block = else_cond_block.successors['L4']
        self.assertInstrEqual(elif_block.get_instruction(6), referenced=['z'], instruction_type=InstructionType.RETURN, control=5)
        self.assertBlockPredecessorsEqual(elif_block, ['L3'])
        self.assertBlockSuccessorsEqual(elif_block, ['L1'])

        else_block = else_cond_block.successors['L5']
        self.assertInstrEqual(else_block.get_instruction(7), instruction_type=InstructionType.ELSE, control=5, multiline=[3, 5, 7])
        self.assertInstrEqual(else_block.get_instruction(8), referenced=['x'], instruction_type=InstructionType.RETURN, control=7)
        self.assertBlockPredecessorsEqual(else_block, ['L3'])
        self.assertBlockSuccessorsEqual(else_block, ['L1'])

        exit_block = else_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L4', 'L5'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_if_elif(self):
        source = ('def funcA(y, z):\n'              # line 1
                  '    x = 5\n'                     # line 2
                  '    if y < 4:\n'                 # line 3
                  '        return y\n'              # line 4
                  '    elif z < 4:\n'               # line 5
                  '        return z\n'              # line 6
                  '    return "BAD"\n')             # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y', 'z'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['y'], multiline=[3, 5])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_cond_block = func_block.successors['L3']
        self.assertInstrEqual(else_cond_block.get_instruction(5), referenced=['z'], control=3, multiline=[3, 5])
        self.assertBlockPredecessorsEqual(else_cond_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_cond_block, ['L4', 'L5'])

        elif_block = else_cond_block.successors['L4']
        self.assertInstrEqual(elif_block.get_instruction(6), referenced=['z'], instruction_type=InstructionType.RETURN, control=5)
        self.assertBlockPredecessorsEqual(elif_block, ['L3'])
        self.assertBlockSuccessorsEqual(elif_block, ['L1'])

        else_block = else_cond_block.successors['L5']
        self.assertFalse(else_block.get_instructions())
        self.assertBlockPredecessorsEqual(else_block, ['L3'])
        self.assertBlockSuccessorsEqual(else_block, ['L6'])

        after_block = else_block.successors['L6']
        self.assertInstrEqual(after_block.get_instruction(7), instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(after_block, ['L5'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L4', 'L6'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_for_with_return(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    for i in range(5):\n'        # line 2
                  '        y -= 1\n'                # line 3
                  '        return y\n'              # line 4
                  '    print(y)\n')                 # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(2), referenced=['range'], defined=['i'], instruction_type=InstructionType.FOR)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(3), referenced=['y'], defined=['y'], control=2)
        self.assertInstrEqual(body_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=2)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L1'])

        after_block = guard_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(5), referenced=['y', 'print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L3', 'L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_while_with_return(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    while y > 4:\n'              # line 2
                  '        y -= 1\n'                # line 3
                  '        return y\n'              # line 4
                  '    print(y)\n')                 # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(2), referenced=['y'], instruction_type=InstructionType.WHILE)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(3), referenced=['y'], defined=['y'], control=2)
        self.assertInstrEqual(body_block.get_instruction(4), referenced=['y'], instruction_type=InstructionType.RETURN, control=2)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L1'])

        after_block = guard_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(5), referenced=['y', 'print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L3', 'L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_while_if_with_return(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    while y > 4:\n'              # line 2
                  '        y -= 1\n'                # line 3
                  '        if y < 4:\n'             # line 4
                  '            return y\n')         # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(2), referenced=['y'], instruction_type=InstructionType.WHILE)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA', 'L6'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(3), referenced=['y'], defined=['y'], control=2)
        self.assertInstrEqual(body_block.get_instruction(4), referenced=['y'], control=2)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L5', 'L6'])

        if_block = body_block.successors['L5']
        self.assertInstrEqual(if_block.get_instruction(5), referenced=['y'], instruction_type=InstructionType.RETURN, control=4)
        self.assertBlockPredecessorsEqual(if_block, ['L3'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        after_if_block = body_block.successors['L6']
        self.assertFalse(after_if_block.get_instructions())
        self.assertBlockPredecessorsEqual(after_if_block, ['L3'])
        self.assertBlockSuccessorsEqual(after_if_block, ['L2'])

        after_block = guard_block.successors['L4']
        self.assertFalse(after_if_block.get_instructions())
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4', 'L5'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_multiline(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = ("testing\\n"\n'         # line 2
                  '     "testing2\\n"\n'            # line 3
                  '            "testing3")\n'       # line 4
                  '    z = (y\n'                    # line 5
                  '         + y)\n'                 # line 6
                  '    if (z\n'                     # line 7
                  '     < 7 or len(x) < 2):\n'      # line 8
                  '        return z\n'              # line 9
                  '    return x\n')                 # line 10
        cfg = self._generate_cfg(source)
        block = cfg.get_func('funcA')

        self.assertInstrEqual(block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(block.get_instruction(2), defined=['x'], multiline=set([2, 3, 4]))
        self.assertInstrEqual(block.get_instruction(5), defined=['z'], referenced=['y'], multiline=set([5, 6]))
        self.assertInstrEqual(block.get_instruction(6), referenced=['y'], multiline=set([5, 6]))
        self.assertInstrEqual(block.get_instruction(7), referenced=['z'], multiline=set([7, 8]))
        self.assertInstrEqual(block.get_instruction(8), referenced=['x', 'len'], multiline=set([7, 8]))
        self.assertBlockPredecessorsEqual(block)
        self.assertBlockSuccessorsEqual(block, ['L2', 'L3'])

        if_block = block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(9), referenced=['z'], instruction_type=InstructionType.RETURN, control=7)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L1'])

        else_block = block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(10), referenced=['x'], instruction_type=InstructionType.RETURN)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L1'])

        exit_block = else_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_try_except(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    try :\n'                     # line 2
                  '        print(y)\n'              # line 3
                  '    except:\n'                   # line 4
                  '        print(e)\n')             # line 5
        cfg = self._generate_cfg(source)
        block = cfg.get_func('funcA')

        self.assertInstrEqual(block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(block.get_instruction(2), instruction_type=InstructionType.TRY, multiline=[2, 4])
        self.assertBlockPredecessorsEqual(block)
        self.assertBlockSuccessorsEqual(block, ['L2', 'L3'])

        try_block = block.successors['L2']
        self.assertInstrEqual(try_block.get_instruction(3), referenced=['print', 'y'], control=2)
        self.assertBlockPredecessorsEqual(try_block, ['funcA'])
        self.assertBlockSuccessorsEqual(try_block, ['L4'])

        except_block = block.successors['L3']
        self.assertInstrEqual(except_block.get_instruction(4), instruction_type=InstructionType.EXCEPT, control=2, multiline=[2, 4])
        self.assertInstrEqual(except_block.get_instruction(5), referenced=['print', 'e'], control=4)
        self.assertBlockPredecessorsEqual(except_block, ['funcA'])
        self.assertBlockSuccessorsEqual(except_block, ['L4'])

        after_block = try_block.successors['L4']
        self.assertFalse(after_block.get_instructions())
        self.assertBlockPredecessorsEqual(after_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_try_except_finally(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    try :\n'                     # line 2
                  '        print(y)\n'              # line 3
                  '    except:\n'                   # line 4
                  '        print(e)\n'              # line 5
                  '    # comment\n'                 # line 6
                  '    finally:\n'                  # line 7
                  '        print("here")\n')        # line 8
        cfg = self._generate_cfg(source)
        block = cfg.get_func('funcA')

        self.assertInstrEqual(block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(block.get_instruction(2), instruction_type=InstructionType.TRY, multiline=[2, 4, 7])
        self.assertBlockPredecessorsEqual(block)
        self.assertBlockSuccessorsEqual(block, ['L2', 'L3'])

        try_block = block.successors['L2']
        self.assertInstrEqual(try_block.get_instruction(3), referenced=['print', 'y'], control=2)
        self.assertBlockPredecessorsEqual(try_block, ['funcA'])
        self.assertBlockSuccessorsEqual(try_block, ['L4'])

        except_block = block.successors['L3']
        self.assertInstrEqual(except_block.get_instruction(4), instruction_type=InstructionType.EXCEPT, control=2, multiline=[2, 4, 7])
        self.assertInstrEqual(except_block.get_instruction(5), referenced=['print', 'e'], control=4)
        self.assertBlockPredecessorsEqual(except_block, ['funcA'])
        self.assertBlockSuccessorsEqual(except_block, ['L4'])

        after_block = try_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(7), instruction_type=InstructionType.FINALLY, multiline=[2, 4, 7])
        self.assertInstrEqual(after_block.get_instruction(8), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_try_except_as_e(self):
        source = ('def funcA(y):\n'                       # line 1
                  '    try:\n'                            # line 2
                  '        return y\n'                    # line 3
                  '    except SyntaxException as e:\n'    # line 4
                  '        return str(e)\n'               # line 5
                  '    except Exception as e:\n'          # line 6
                  '        return str(e)\n')              # line 7
        cfg = self._generate_cfg(source)
        block = cfg.get_func('funcA')

        self.assertInstrEqual(block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(block.get_instruction(2), instruction_type=InstructionType.TRY, multiline=[2, 4, 6])
        self.assertBlockPredecessorsEqual(block)
        self.assertBlockSuccessorsEqual(block, ['L2', 'L3', 'L4'])

        try_block = block.successors['L2']
        self.assertInstrEqual(try_block.get_instruction(3), referenced=['y'], instruction_type=InstructionType.RETURN, control=2)
        self.assertBlockPredecessorsEqual(try_block, ['funcA'])
        self.assertBlockSuccessorsEqual(try_block, ['L1'])

        except_block_1 = block.successors['L3']
        self.assertInstrEqual(except_block_1.get_instruction(4), referenced=['SyntaxException'], defined=['e'], instruction_type=InstructionType.EXCEPT, control=2, multiline=[2, 4, 6])
        self.assertInstrEqual(except_block_1.get_instruction(5), referenced=['str', 'e'], instruction_type=InstructionType.RETURN, control=4)
        self.assertBlockPredecessorsEqual(except_block_1, ['funcA'])
        self.assertBlockSuccessorsEqual(except_block_1, ['L1'])

        except_block_2 = block.successors['L4']
        self.assertInstrEqual(except_block_2.get_instruction(6), referenced=['Exception'], defined=['e'], instruction_type=InstructionType.EXCEPT, control=4, multiline=[2, 4, 6])
        self.assertInstrEqual(except_block_2.get_instruction(7), referenced=['str', 'e'], instruction_type=InstructionType.RETURN, control=6)
        self.assertBlockPredecessorsEqual(except_block_2, ['funcA'])
        self.assertBlockSuccessorsEqual(except_block_2, ['L1'])

        exit_block = try_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L2', 'L3', 'L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_list_functions(self):
        source = ('def funcA():\n'              # line 1
                  '    x = [1, 2, 3, 4, 5]\n'   # line 2
                  '    y = [6, 7]\n'            # line 3
                  '    x.append(2)\n'           # line 4
                  '    x.extend(y)\n'           # line 5
                  '    x.insert(3, 3)\n'        # line 6
                  '    x.pop()\n'               # line 7
                  '    x[1] = 4\n'              # line 8
                  '    print(x[0])\n')          # line 9
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), defined=['y'])
        self.assertInstrEqual(func_block.get_instruction(4), referenced=['x', 'append'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(5), referenced=['x', 'y', 'extend'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(6), referenced=['x', 'insert'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(7), referenced=['x', 'pop'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(8), referenced=['x'], defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(9), referenced=['x', 'print'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_pass(self):
        source = ('def funcA(x):\n'             # line 1
                  '    if x < 5:\n'             # line 2
                  '        pass\n'              # line 3
                  '    else:\n'                 # line 4
                  '        pass\n')             # line 5
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['x'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), referenced=['x'], multiline=[2, 4])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2', 'L3'])

        if_block = func_block.successors['L2']
        self.assertInstrEqual(if_block.get_instruction(3), instruction_type=InstructionType.PASS, control=2)
        self.assertBlockPredecessorsEqual(if_block, ['funcA'])
        self.assertBlockSuccessorsEqual(if_block, ['L4'])

        else_block = func_block.successors['L3']
        self.assertInstrEqual(else_block.get_instruction(4), instruction_type=InstructionType.ELSE, control=2, multiline=[2, 4])
        self.assertInstrEqual(else_block.get_instruction(5), instruction_type=InstructionType.PASS, control=4)
        self.assertBlockPredecessorsEqual(else_block, ['funcA'])
        self.assertBlockSuccessorsEqual(else_block, ['L4'])

        after_block = else_block.successors['L4']
        self.assertFalse(after_block.get_instructions())
        self.assertBlockPredecessorsEqual(after_block, ['L2', 'L3'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_raise_error(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    x = 5\n'                     # line 2
                  '    raise ValueError()\n'        # line 3
                  '    print(x)\n')                 # line 4
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.get_instruction_linenos(), set([1, 2, 3]))
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(2), defined=['x'])
        self.assertInstrEqual(func_block.get_instruction(3), referenced=['ValueError'], instruction_type=InstructionType.RAISE)
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['funcA'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_class(self):
        source = ('class Test(object):\n'           # line 1
                  '    def __init__(self):\n'       # line 2
                  '        pass\n'                  # line 3
                  '    def print_hi(self):\n'       # line 4
                  '        print("hi")\n')          # line 5
        cfg = self._generate_cfg(source)
        self.assertEqual(cfg.get_num_funcs(), 2)

        func_block = cfg.get_func('__init__')
        self.assertEqual(func_block.get_instruction_linenos(), set([2, 3]))
        self.assertInstrEqual(func_block.get_instruction(2), defined=['self'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(3), instruction_type=InstructionType.PASS)
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L1'])

        exit_block = func_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['__init__'])
        self.assertBlockSuccessorsEqual(exit_block)

        func_block = cfg.get_func('print_hi')
        self.assertEqual(func_block.get_instruction_linenos(), set([4, 5]))
        self.assertInstrEqual(func_block.get_instruction(4), defined=['self'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertInstrEqual(func_block.get_instruction(5), referenced=['print'])
        self.assertBlockPredecessorsEqual(func_block)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        exit_block = func_block.successors['L2']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['print_hi'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_while_if_with_break(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    while True:\n'               # line 2
                  '        if y < 4:\n'             # line 3
                  '            break\n'             # line 4
                  '        y -= 1\n'                # line 5
                  '    print("DONE")\n')            # line 6
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(2), referenced=['True'], instruction_type=InstructionType.WHILE)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA', 'L6'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(3), referenced=['y'], control=2)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L5', 'L6'])

        if_block = body_block.successors['L5']
        self.assertInstrEqual(if_block.get_instruction(4), instruction_type=InstructionType.BREAK, control=3)
        self.assertBlockPredecessorsEqual(if_block, ['L3'])
        self.assertBlockSuccessorsEqual(if_block, ['L4'])

        after_if_block = body_block.successors['L6']
        self.assertInstrEqual(after_if_block.get_instruction(5), referenced=['y'], defined=['y'], control=2)
        self.assertBlockPredecessorsEqual(after_if_block, ['L3'])
        self.assertBlockSuccessorsEqual(after_if_block, ['L2'])

        after_block = guard_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(6), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2', 'L5'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)

    def test_return_while_if_with_continue(self):
        source = ('def funcA(y):\n'                 # line 1
                  '    while y > 5:\n'              # line 2
                  '        y -= 1\n'                # line 3
                  '        if y < 4:\n'             # line 4
                  '            continue\n'          # line 5
                  '        print("inside")\n'       # line 6
                  '    print("DONE")\n')            # line 7
        cfg = self._generate_cfg(source)
        func_block = cfg.get_func('funcA')

        self.assertEqual(func_block.label, 'funcA')
        self.assertInstrEqual(func_block.get_instruction(1), defined=['y'], instruction_type=InstructionType.FUNCTION_HEADER)
        self.assertBlockSuccessorsEqual(func_block, ['L2'])

        guard_block = func_block.successors['L2']
        self.assertInstrEqual(guard_block.get_instruction(2), referenced=['y'], instruction_type=InstructionType.WHILE)
        self.assertBlockPredecessorsEqual(guard_block, ['funcA', 'L5', 'L6'])
        self.assertBlockSuccessorsEqual(guard_block, ['L3', 'L4'])

        body_block = guard_block.successors['L3']
        self.assertInstrEqual(body_block.get_instruction(3), referenced=['y'], defined=['y'], control=2)
        self.assertInstrEqual(body_block.get_instruction(4), referenced=['y'], control=2)
        self.assertBlockPredecessorsEqual(body_block, ['L2'])
        self.assertBlockSuccessorsEqual(body_block, ['L5', 'L6'])

        if_block = body_block.successors['L5']
        self.assertInstrEqual(if_block.get_instruction(5), instruction_type=InstructionType.CONTINUE, control=4)
        self.assertBlockPredecessorsEqual(if_block, ['L3'])
        self.assertBlockSuccessorsEqual(if_block, ['L2'])

        after_if_block = body_block.successors['L6']
        self.assertInstrEqual(after_if_block.get_instruction(6), referenced=['print'], control=2)
        self.assertBlockPredecessorsEqual(after_if_block, ['L3'])
        self.assertBlockSuccessorsEqual(after_if_block, ['L2'])

        after_block = guard_block.successors['L4']
        self.assertInstrEqual(after_block.get_instruction(7), referenced=['print'])
        self.assertBlockPredecessorsEqual(after_block, ['L2'])
        self.assertBlockSuccessorsEqual(after_block, ['L1'])

        exit_block = after_block.successors['L1']
        self.assertFalse(exit_block.get_instructions())
        self.assertBlockPredecessorsEqual(exit_block, ['L4'])
        self.assertBlockSuccessorsEqual(exit_block)


if __name__ == '__main__':
    unittest.main()
