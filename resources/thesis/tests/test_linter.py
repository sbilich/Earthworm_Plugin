# File name: test_linter.py
# Author: Nupur Garg
# Date created: 5/2/2017
# Python Version: 3.5


import unittest

from src.globals import *
from src.linter import *
from src.models.error import *


class TestLinter(unittest.TestCase):

    def _generate_suggestions(self, source):
        node = ast.parse(source)
        suggestions = get_linter_suggestions(node, source)
        return suggestions

    def test_add_suggestions(self):
        linter = LinterTokenParser(debug=True)
        linter.generate(source='')
        self.assertFalse(linter.suggestions)

        linter._add_suggestion(lineno=1, message="hi")
        self.assertEqual(set(linter.suggestions.keys()), set([1]))
        self.assertEqual(len(linter.suggestions[1]), 1)
        self.assertEqual(linter.suggestions[1][0], "hi")

        linter._add_suggestion(lineno=1, message="hi")
        self.assertEqual(set(linter.suggestions.keys()), set([1]))
        self.assertEqual(len(linter.suggestions[1]), 1)
        self.assertEqual(linter.suggestions[1][0], "hi")

        linter._add_suggestion(lineno=1, message="how are you")
        self.assertEqual(set(linter.suggestions.keys()), set([1]))
        self.assertEqual(len(linter.suggestions[1]), 2)
        self.assertEqual(linter.suggestions[1][0], "hi")
        self.assertEqual(linter.suggestions[1][1], "how are you")

    def test_get_lines(self):
        linter = LinterTokenParser(debug=True)
        source = ('def funcA(num):\n'               # line 1
                  '    """\n'                       # line 2
                  '    multiline comment"""\n'      # line 3
                  '    """ small line """\n'        # line 4
                  '    if num > 5:\n'               # line 5
                  '        return num\n'            # line 6
                  '    # comment\n'                 # line 7
                  '    return 0\n')                 # line 8
        linter.generate(source)

        expected = [(1, 'def funcA(num):\n'),
                    (2, '    """\n'),
                    (3, '    multiline comment"""\n'),
                    (4, '    """ small line """\n'),
                    (5, '    if num > 5:\n'),
                    (6, '        return num\n'),
                    (7, '    # comment\n'),
                    (8, '    return 0\n')]
        self.assertEqual(linter.all_lines, expected)

    def test_get_lines_code(self):
        linter = LinterTokenParser(debug=True)
        source = ('def funcA(num):\n'               # line 1
                  '    """\n'                       # line 2
                  '    multiline comment"""\n'      # line 3
                  '    \'\'\' small line \'\'\'\n'  # line 4
                  '    if num > 5:\n'               # line 5
                  '        return num\n'            # line 6
                  '    # comment\n'                 # line 7
                  '    return 0\n')                 # line 8
        linter.generate(source)

        expected = [(1, 'def funcA(num):\n'),
                    (5, '    if num > 5:\n'),
                    (6, '        return num\n'),
                    (8, '    return 0\n')]
        self.assertEqual(linter.lines, expected)

    def test_has_indent(self):
        linter = LinterTokenParser(debug=True)
        linter.generate(source='')

        self.assertTrue(linter._has_indent('\tvar = 5'))
        self.assertTrue(linter._has_indent('   var = 5'))
        self.assertTrue(linter._has_indent('    var = 5'))

        self.assertFalse(linter._has_indent('var = 5'))
        self.assertFalse(linter._has_indent('var = 5'))

    def test_is_return_bool(self):
        linter = LinterTokenParser(debug=True)
        linter.generate(source='')

        # Check "True" case.
        self.assertTrue(linter._is_return_bool('return True\n'))
        self.assertTrue(linter._is_return_bool('return   True'))
        self.assertTrue(linter._is_return_bool('return\tTrue'))

        # Check "False" case.
        self.assertTrue(linter._is_return_bool('return False '))
        self.assertTrue(linter._is_return_bool('return   False  '))
        self.assertTrue(linter._is_return_bool('return\tFalse  \n'))

        # Check generate case.
        self.assertFalse(linter._is_return_bool('return False or False'))
        self.assertFalse(linter._is_return_bool('return\tfalse'))
        self.assertFalse(linter._is_return_bool('return\tTrue or x > 5'))

    def test_is_if(self):
        linter = LinterTokenParser(debug=True)
        linter.generate(source='')

        self.assertTrue(linter._is_if('\tif   x < 5:\n'))
        self.assertTrue(linter._is_if('\tif   (x  < 5) :\n'))
        self.assertTrue(linter._is_if('\tif   (x  \n'))

        self.assertFalse(linter._is_if('\tif'))
        self.assertFalse(linter._is_if('\tift'))

    def test_is_else(self):
        linter = LinterTokenParser(debug=True)
        linter.generate(source='')

        self.assertTrue(linter._is_else('\telse:\n'))
        self.assertTrue(linter._is_else('\telse :\n'))
        self.assertTrue(linter._is_else('\telse\t  :\n'))

        self.assertFalse(linter._is_else('\telse'))
        self.assertFalse(linter._is_else('\telif'))

    def test_is_func_def(self):
        linter = LinterTokenParser(debug=False)
        linter.generate(source='')

        # Valid function headers.
        self.assertEqual(linter._get_function_def('def funcA('), 'funcA')
        self.assertEqual(linter._get_function_def('def funcA():'), 'funcA')
        self.assertEqual(linter._get_function_def('def funcA\t():'), 'funcA')
        self.assertEqual(linter._get_function_def('def funcA (func, params):'), 'funcA')
        self.assertEqual(linter._get_function_def('def func_1('), 'func_1')
        self.assertEqual(linter._get_function_def('def func_A__1('), 'func_A__1')

        # Invalid function headers.
        self.assertFalse(linter._get_function_def('#def funcA (func, params):'))
        self.assertFalse(linter._get_function_def('def funcA'))

    def test_for__no_suggestions(self):
        source = ('def funcA(listA):\n'
                  '    for x in listA:\n'
                  '        print(x)\n')
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_for__has_suggestions(self):
        source = ('def funcA(listA):\n'
                  '    for x in listA:\n'
                  '        print(x)\n'
                  '    else:\n'
                  '        print("No values")\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([5]))
        self.assertEqual(len(suggestions[5]), 1)
        self.assertEqual(suggestions[5][0], 'Do not use else with for loops.')

    def test_while__no_suggestions(self):
        source = ('def funcA(maximum):\n'
                  '    while x < range(maximum):\n'
                  '        print(x)\n'
                  '        x += 1\n')
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_while__has_suggestions(self):
        source = ('def funcA(maximum):\n'
                  '    while x < range(maximum):\n'
                  '        print(x)\n'
                  '        x += 1\n'
                  '    else:\n'
                  '        print("No values")\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([6]))
        self.assertEqual(len(suggestions[6]), 1)
        self.assertEqual(suggestions[6][0], 'Do not use else with while loops.')

    def test_try_except__no_suggestions(self):
        source = ('def funcA(num):\n'
                  '    try:\n'
                  '        int(num)\n'
                  '    except:\n'
                  '        print("EXCEPTION")\n')
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_try_except__has_suggestions(self):
        source = ('def funcA(num):\n'
                  '    try:\n'
                  '        int(num)\n'
                  '    except:\n'
                  '        print("EXCEPTION")\n'
                  '    else:\n'
                  '        print("No values")\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([7]))
        self.assertEqual(len(suggestions[7]), 1)
        self.assertEqual(suggestions[7][0], 'Do not use else with exceptions.')

    def test_conditional_true_false__no_suggestion(self):
        source = ('def funcA(num):\n'
                  '    result = 0\n'
                  '    if num > 5:\n'
                  '        result += 1\n'
                  '    else:\n'
                  '        result -= 1\n'
                  '    print(result)\n')
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_conditional_true_false__return_if_else(self):
        source = ('def funcA(num):\n'
                  '    if num > 5:\n'
                  '        return True\n'
                  '    else:\n'
                  '        return False\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([2]))
        self.assertEqual(len(suggestions[2]), 1)
        message = 'Rewrite conditional as a single line return statement: \'return <conditional>\'.'
        self.assertEqual(suggestions[2][0], message)

    def test_conditional_true_false__return_only_if(self):
        source = ('def funcA(num):\n'
                  '    if(num > 5):\n'
                  '        return   True\n'
                  '    return False\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([2]))
        self.assertEqual(len(suggestions[2]), 1)
        message = 'Rewrite conditional as a single line return statement: \'return <conditional>\'.'
        self.assertEqual(suggestions[2][0], message)

    def test_conditional_true_false__return_if_if_else(self):
        source = ('def funcA(num):\n'
                  '    if(num > 5):\n'
                  '        return   False\n'
                  '    if num > 5:\n'
                  '        return False\n'
                  '    # comment\n'
                  '    else:\n'
                  '        return True\n')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([4]))
        self.assertEqual(len(suggestions[4]), 1)
        message = 'Rewrite conditional as a single line return statement: \'return <conditional>\'.'
        self.assertEqual(suggestions[4][0], message)

    def test_func_inside_func(self):
        source = ('def funcA(num):\n'
                  '    def funcB(num):\n'
                  '        return False\n'
                  '    return True\n')

        with self.assertRaises(FuncInsideFuncError) as context:
            suggestions = self._generate_suggestions(source)

    def test_over_80_line__has_suggestion_comment(self):
        source = ('def funcA(num):\n'
                  '    # this line is a very long line of comment and'
                  '     should be condensed into one line of comment\n'
                  '    pass')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([2]))
        self.assertEqual(len(suggestions[2]), 1)
        message = 'Line length over 80 characters.'
        self.assertEqual(suggestions[2][0], message)


    def test_over_80_line__has_suggestion_string(self):
        source = ('def funcA(num):\n'
                  '    string = ("this line is a very long line of string and'
                  '              should be condensed into one line of string")\n'
                  '    pass')
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([2]))
        self.assertEqual(len(suggestions[2]), 1)
        message = 'Line length over 80 characters.'
        self.assertEqual(suggestions[2][0], message)

    def test_over_80_line__has_no_suggestion(self):
        source = ('def funcA(num):\n'
                  '    # this line is medium line of code\n'
                  '    if num > 5:\n'
                  '        return num\n'
                  '    return 0\n')
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_tabbing__change_in_tabbing_tab_vs_4(self):
        source = ('def funcA(num):\n'       # line 1
                  '\tif num > 5:\n'         # line 2
                  '\t\treturn num\n'        # line 3
                  '\treturn 0\n'            # line 4
                  '\t\n'                    # line 5
                  '\n'                      # line 6
                  'def funcB(num):\n'       # line 7
                  '    if num > 5:\n'       # line 8
                  '        return num\n'    # line 9
                  '    return 0\n')         # line 10
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([1, 7]))

        self.assertEqual(len(suggestions[1]), 1)
        message = 'Indentation should be either 3 or 4 spaces.'
        self.assertEqual(suggestions[1][0], message)

        self.assertEqual(len(suggestions[7]), 1)
        message = '\'funcB\' has different indentation than \'funcA\'.'
        self.assertEqual(suggestions[7][0], message)

    def test_tabbing__change_in_tabbing_2_vs_4(self):
        source = ('def funcA(num):\n'       # line 1
                  '  if num > 5:\n'         # line 2
                  '    return num\n'        # line 3
                  '  return 0\n'            # line 4
                  '  \n'                    # line 5
                  'def funcB(num):\n'       # line 6
                  '  # comment\n'           # line 7
                  '    if num > 5:\n'       # line 8
                  '        return num\n'    # line 9
                  '    return 0\n')         # line 8
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([1, 6]))

        self.assertEqual(len(suggestions[1]), 1)
        message = 'Indentation should be either 3 or 4 spaces.'
        self.assertEqual(suggestions[1][0], message)

        self.assertEqual(len(suggestions[6]), 1)
        message = '\'funcB\' has different indentation than \'funcA\'.'
        self.assertEqual(suggestions[6][0], message)

    def test_tabbing__change_in_tabbing_4_vs_tab(self):
        source = ('def funcA(num):\n'       # line 1
                  '    if num > 5:\n'       # line 2
                  '        return num\n'    # line 3
                  '    return 0\n'          # line 4
                  'def funcB(num):\n'       # line 5
                  '\tif num > 5:\n'         # line 6
                  '\t\treturn num\n'        # line 7
                  '\treturn 0\n')           # line 8
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([5]))
        self.assertEqual(len(suggestions[5]), 1)
        message = '\'funcB\' has different indentation than \'funcA\'.'
        self.assertEqual(suggestions[5][0], message)

    def test_tabbing__change_in_tabbing_in_func(self):
        source = ('  # comment\n'           # line 1
                  'def funcA(num):\n'       # line 2
                  '    if num > 5:\n'       # line 3
                  '      print(num)\n'      # line 4
                  '      return num\n'      # line 5
                  '    return 0\n')         # line 6
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([2]))
        message = 'Indentation within \'funcA\' changes between indentation levels.'
        self.assertEqual(len(suggestions[2]), 1)
        self.assertEqual(suggestions[2][0], message)

    def test_tabbing__no_change_in_tabbing_in_func(self):
        source = ('  # comment\n'           # line 1
                  'def funcA(num):\n'       # line 2
                  '    if num > 5:\n'       # line 3
                  '        print(num\n'     # line 4
                  '                 )\n'    # line 5
                  '    str = \'    \'\n'    # line 6
                  '    return 0\n')         # line 7
        suggestions = self._generate_suggestions(source)
        self.assertFalse(suggestions)

    def test_variable_names__inside_func(self):
        source = ('def funcA(num):\n'       # line 1
                  '    x = 5\n'             # line 2
                  '    if x > 5:\n'         # line 3
                  '        x = 0\n'         # line 4
                  '    return x\n')         # line 5
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([1]))
        message = 'Use descriptive variable name instead of \'x\' in \'funcA\'.'
        self.assertEqual(len(suggestions[1]), 1)
        self.assertEqual(suggestions[1][0], message)

    def test_variable_names__func_header(self):
        source = ('def funcA(x):\n'         # line 1
                  '    num = 5\n'           # line 2
                  '    if num > 5:\n'       # line 3
                  '        num = 0\n'       # line 4
                  '    return num\n')       # line 5
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([1]))
        message = 'Use descriptive variable name instead of \'x\' in \'funcA\'.'
        self.assertEqual(len(suggestions[1]), 1)
        self.assertEqual(suggestions[1][0], message)

    def test_variable_names__func_header(self):
        source = ('def funcA(XXX):\n'       # line 1
                  '    num = 5\n'           # line 2
                  '    if num > 5:\n'       # line 3
                  '        return True\n'   # line 4
                  '    return None\n')      # line 5
        suggestions = self._generate_suggestions(source)

        self.assertEqual(set(suggestions.keys()), set([1]))
        message = 'Use descriptive variable name instead of \'XXX\' in \'funcA\'.'
        self.assertEqual(len(suggestions[1]), 1)
        self.assertEqual(suggestions[1][0], message)
