# File name: linter.py
# Author: Nupur Garg
# Date created: 5/2/2017
# Python Version: 3.5


import ast
import re
import textwrap

from src.globals import *
from src.generatecfg import TokenGenerator
from src.models.error import *


# Generates suggestions for the linter.
def get_linter_suggestions(node, source, debug=True):
    # Gets LinterTokenParser suggestions.
    parser = LinterTokenParser(source)
    suggestions_map = parser.generate(source)

    # Gets Linter suggestions.
    linter = Linter(debug)
    linter_suggestions_map = linter.generate(node)
    for lineno, suggestions in sorted(linter_suggestions_map.items()):
        if lineno not in suggestions_map:
            suggestions_map[lineno] = []
        suggestions_map[lineno].extend(suggestions)
    return suggestions_map


class LinterTokenParser(object):
    """
    Generates and retains tokens.
    """

    def __init__(self, debug):
        self.debug = debug

    def generate(self, source, line_limit=80):
        tokens = TokenGenerator(source, include_conditional=False)
        self.multiline = tokens.multiline

        self.suggestions = {}
        self.all_lines = self._get_lines(source)
        self.lines = self._get_lines_code()

        # Gets the suggestions.
        self._check_indentation()
        self._check_line_length()
        self._check_conditional_true_false()
        return self.suggestions

    # Gets all individual lines of code as tuple of (lineno, line).
    def _get_lines(self, source):
        return [(lineno, line)
                for lineno, line in enumerate(source.splitlines(True), 1)]

    # Gets the lines that are not commented.
    def _get_lines_code(self):
        final_lines = []
        inside_comment_block = False
        contains_block_comment = False

        for lineno, line in self.all_lines:
            stripped_line = line.strip()

            # Check if inside comment block.
            matches = re.findall(r'"""[^"]|\'\'\'[^\']', line)
            for block_comment in range(len(matches)):
                inside_comment_block = not inside_comment_block
                contains_block_comment = True

            # Check if current line is a comment or inside a comment.
            if (stripped_line and stripped_line[0] != '#' and
                not inside_comment_block and not contains_block_comment):
                final_lines.append((lineno, line))
            contains_block_comment = False
        return final_lines

    # Adds a suggestion.
    def _add_suggestion(self, lineno, message):
        if lineno not in self.suggestions:
            self.suggestions[lineno] = []
        if message not in self.suggestions[lineno]:
            self.suggestions[lineno].append(message)

    # Returns the space at the start of the line.
    def _get_space_start(self, line):
        return re.search(r'(\s*)[^\s]*', line).group(1)

    # Determines whether the line has an indent at the left.
    def _has_indent(self, line):
        return line.lstrip() != line

    # Checks if the return statement is a boolean.
    def _is_return_bool(self, line):
        return bool(re.match(r'return\s+(True|False)$', line.strip()))

    # Checks if statement.
    def _is_if(self, line):
        return re.search(r'^if |^if\(', line.strip())

    # Checks else statement.
    def _is_else(self, line):
        return re.search(r'^else\s*\:$', line.strip())

    # Checks if the line is function definition.
    def _get_function_def(self, line):
        match_obj = re.search(r'^def\s+([a-zA-Z0-9\_]+)\s*\(', line)
        if match_obj:
            return match_obj.group(1)
        return None

    # Checks the indentation for a program.
    def _check_indentation(self):
        indentation = cur_func_indent = None
        start_func = cur_func = None
        prev_lineno = cur_func_lineno = None

        for lineno, line in self.lines:
            # Initialize indentation.
            cur_indent = self._get_space_start(line)
            if not indentation and cur_indent:
                indentation = cur_indent
                if not (indentation == '   ' or indentation == '    '):
                    message = 'Indentation should be either 3 or 4 spaces.'
                    self._add_suggestion(cur_func_lineno, message)

            # Initialize function definitions.
            func_def = self._get_function_def(line)
            if func_def:
                cur_func = func_def
                cur_func_lineno = lineno
                cur_func_indent = None
                start_func = cur_func if not start_func else start_func
            elif prev_lineno == cur_func_lineno:
                cur_func_indent = cur_indent

            # Check for matching indentation if inside function.
            if (indentation and cur_func and lineno != cur_func_lineno):
                self._check_indentation_line(indentation, line, lineno, prev_lineno,
                                             start_func, cur_func, cur_func_lineno,
                                             cur_indent, cur_func_indent)

            # Reset variables for next line.
            prev_lineno = lineno

    # Gets indentation on a given line.
    def _check_indentation_line(self, indentation, line, lineno, prev_lineno,
                                start_func, cur_func, cur_func_lineno,
                                cur_indent, cur_func_indent):
        count = len(tuple(re.finditer(indentation, cur_indent)))
        count_func = len(tuple(re.finditer(cur_func_indent, cur_indent)))
        has_indent = self._has_indent(line)
        message = None

        # Checks indentation between functions.
        if prev_lineno == cur_func_lineno:
            # Checks tab vs spaces and different number of spaces/tabs.
            if (has_indent and not count) or indentation != cur_indent:
                message = ('\'{0}\' has different indentation than '
                           '\'{1}\'.'.format(cur_func, start_func))
        # Checks indentation within a function for non-multiline statements.
        else:
            count_func_indent = count_func * cur_func_indent
            if cur_indent != count_func_indent and lineno not in self.multiline:
                message = ('Indentation within \'{0}\' changes between '
                           'indentation levels.'.format(cur_func))

        # Adds the suggestion if a suggestion is found.
        if message:
            self._add_suggestion(cur_func_lineno, message)

    # Checks if line length is greater than specified.
    def _check_line_length(self, line_limit=80):
        message = 'Line length over {0} characters.'.format(line_limit)
        for lineno, line in self.all_lines:
            if len(line) > line_limit:
                self._add_suggestion(lineno, message)

    # Checks conditional that is done as a True/False statement
    def _check_conditional_true_false(self):
        message = 'Rewrite conditional as a single line return statement: \'return <conditional>\'.'
        start_lineno = None
        cond_incr = 0

        for lineno, line in self.lines:
            is_bool_return = self._is_return_bool(line)

            if self._is_if(line):
                start_lineno = lineno
                cond_incr = 1
            elif cond_incr == 1 and is_bool_return:
                cond_incr += 1
            elif cond_incr == 2:
                if self._is_else(line):
                    cond_incr += 1
                elif is_bool_return:
                    self._add_suggestion(start_lineno, message)
                else:
                    cond_incr = 0
            elif cond_incr == 3 and is_bool_return:
                self._add_suggestion(start_lineno, message)
                cond_incr = 0
            else:
                cond_incr = 0


class Linter(ast.NodeVisitor):
    """
    Generates Linter messages from an AST.

    debug: bool
        Whether to print debug messages.
    """

    def __init__(self, debug):
        self.debug = debug

    # Generates CFG.
    def generate(self, node):
        self._init_variables()
        self.visit(node)
        return self.suggestions

    # Initializes variables.
    def _init_variables(self):
        self.suggestions = {}
        self.func_name = None
        self.func_lineno = None

    # Adds suggestions.
    def _add_suggestion(self, lineno, message):
        if lineno not in self.suggestions:
            self.suggestions[lineno] = []
        if message not in self.suggestions[lineno]:
            self.suggestions[lineno].append(message)

    # input: FunctionDef(identifier name, arguments args,
    #                    stmt* body, expr* decorator_list)
    # output: None
    def visit_FunctionDef(self, node):
        if self.func_name:
            raise FuncInsideFuncError(node.lineno)

        # Start of function.
        self.func_name = node.name
        self.func_lineno = node.lineno

        # Visit function.
        self.generic_visit(node)

        # End of function.
        self.func_lineno = None
        self.func_name = None

    # Visits a orelse condition.
    def _visit_orelse(self, orelse, message):
        if orelse:
            lineno = orelse[0].lineno
            self._add_suggestion(lineno, message)

    # input: For(expr target, expr iter, stmt* body, stmt* orelse)
    # output: None
    def visit_For(self, node):
        self._visit_orelse(node.orelse, 'Do not use else with for loops.')

    # input: While(expr test, stmt* body, stmt* orelse)
    # output: None
    def visit_While(self, node):
        self._visit_orelse(node.orelse, 'Do not use else with while loops.')

    # input: TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
    # output: None
    def visit_TryExcept(self, node):
        self._visit_orelse(node.orelse, 'Do not use else with exceptions.')

    # input: Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
    # output: None
    def visit_Try(self, node):
        self._visit_orelse(node.orelse, 'Do not use else with exceptions.')

    # Handles suggestions based on bad identifier names.
    def _handle_identifier(self, identifier):
        # Create suggestion if the identifier is made up of single character.
        has_repeated_letters = len(set(list(identifier))) > 1
        if self.func_name and not has_repeated_letters:
            message = ('Use descriptive variable name instead of \'{0}\' in '
                       '\'{1}\'.'.format(identifier, self.func_name))
            self._add_suggestion(self.func_lineno, message)

    # input: Name(identifier id, expr_context ctx)
    # output: var_name str
    def visit_Name(self, node):
        self._handle_identifier(node.id)

    # input: arg(identifier arg, expr? annotation)
    # output: None
    def visit_arg(self, node):
        # Compatible with Python 3 arguments.
        self._handle_identifier(node.arg)
