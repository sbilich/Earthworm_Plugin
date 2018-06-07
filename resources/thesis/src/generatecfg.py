# File name: generatecfg.py
# Author: Nupur Garg
# Date created: 12/25/2016
# Python Version: 3.5


import ast
import _ast
import re
from enum import Enum

from src.globals import *
from src.models.error import *
from src.models.block import BlockList, Block, FunctionBlock
from src.models.instruction import Instruction, InstructionType


_LIST_COMPREHENSION_FUNCTIONS = ['append', 'insert', 'extend', 'pop']


class TypeVariable(Enum):
    """
    Enumerator that states type of the variable.
    """
    __order__ = 'LOAD, STORE'
    LOAD = 1
    STORE = 2


class TokenGenerator(object):
    """
    Generates and retains tokens.

    source: str
        Text source.
    include_conditional: bool
        Whether or not not include the conditional in the multiline groups.
    """

    def __init__(self, source, include_conditional=True):
        # Generates lines and line types.
        self.lines = source.splitlines(True)
        self.blank_lines = self._get_blank_lines()
        self.comments = self._get_commented_lines()

        # Generates extra information about the lines.
        self.indentation = self._get_indentation()
        self.line_indent = self._get_line_indentation()
        self.multiline = self._get_multiline_instructions()
        self.conditionals = self._get_conditionals()
        self.exceptions = self._get_try_except()

        if include_conditional:
            for lineno, group in self.conditionals.items():
                if lineno not in self.multiline:
                    self.multiline[lineno] = set()
                self.multiline[lineno] |= group
            for lineno, group in self.exceptions.items():
                if lineno not in self.multiline:
                    self.multiline[lineno] = set()
                self.multiline[lineno] |= group

    def _get_blank_lines(self):
        blank_lines = set()
        for lineno, line in enumerate(self.lines, 1):
            if not line.strip():
                blank_lines.add(lineno)
        return blank_lines

    def _get_commented_lines(self):
        comments = set()
        inside_comment_block = False

        for lineno, line in enumerate(self.lines, 1):
            stripped_line = line.strip()
            # Check if current line is a comment or inside a comment.
            if ((stripped_line and stripped_line[0] == '#') or
                inside_comment_block):
                comments.add(lineno)

            # Check if inside comment block.
            matches = re.findall(r'"""[^"]', line)
            for block_comment in range(len(matches)):
                inside_comment_block = not inside_comment_block
                if inside_comment_block:
                    comments.add(lineno)
        return comments

    def _get_multiline_instructions(self):
        multiline = {}
        brackets = []

        inside_str = False
        last_slash = None
        start = 1

        # Get actual multiline instructions.
        for lineno, line in enumerate(self.lines, 1):
            # New statement if no slash at end.
            if not brackets and not last_slash:
                start = lineno

            # Analyze the line if not blank line or comment.
            if (lineno not in self.blank_lines and
                lineno not in self.comments):
                idx_char = 0
                idx_prev_char = None
                exit = False

                # Checks for multiline parenthesis.
                while idx_char < len(line) and not exit:
                    character = line[idx_char]
                    prev_char = line[idx_prev_char] if idx_prev_char else None
                    if self._is_quotation(character, prev_char):
                        inside_str = not inside_str
                    if not inside_str:
                        if character == '(':
                            brackets.append('(')
                        elif character == ')':
                            brackets.pop()
                        elif character == '#':
                            exit = True
                    idx_char += 1
                    idx_prev_char = idx_char - 1

                # Store range in dict if multiline.
                multiline_group = range(start, lineno+1)
                if (start != lineno and (last_slash or not brackets)):
                    for grouped_lineno in multiline_group:
                        multiline[grouped_lineno] = set(multiline_group)

                # Initialize multiline \ for next iteration.
                last_slash = lineno if self._is_end_slash(line) else None

        return multiline

    # Gets the indentation for a program.
    def _get_indentation(self):
        if not self.lines:
            return None

        lineno = 1
        line = self.lines[lineno-1]

        while (lineno < len(self.lines) and
               (lineno in self.comments or
                line == line.lstrip() or not line.strip())):
            lineno += 1
            line = self.lines[lineno-1]

        return self._get_space_start(line)

    # Gets the indentation for each line in the program.
    def _get_line_indentation(self):
        line_indent = {}
        for lineno, line in enumerate(self.lines, 1):
            start_line = self._get_space_start(line)
            count = len(tuple(re.finditer(self.indentation, start_line)))
            line_indent[lineno] = count
        return line_indent

    # Returns the groups of conditionals.
    def _get_conditionals(self):
        groups = {}
        conditionals = {}
        for lineno, line in enumerate(self.lines, 1):
            if lineno not in self.comments:
                line_indentation = self.line_indent[lineno]
                if re.search(r'elif |elif \(|else\:', line):
                    if line_indentation in conditionals:
                        conditionals[line_indentation].append(lineno)
                        for grouped_lineno in conditionals[line_indentation]:
                            groups[grouped_lineno] = set(conditionals[line_indentation])
                elif re.search(r'if |if\(', line):
                    conditionals[line_indentation] = [lineno]
        return groups

    # Returns the groups of try/except.
    def _get_try_except(self):
        groups = {}
        exceptions = {}
        for lineno, line in enumerate(self.lines, 1):
            if lineno not in self.comments:
                line_indentation = self.line_indent[lineno]
                if re.search(r'except |except:|finally:|finally ', line):
                    if line_indentation in exceptions:
                        exceptions[line_indentation].append(lineno)
                        for grouped_lineno in exceptions[line_indentation]:
                            groups[grouped_lineno] = set(exceptions[line_indentation])
                elif re.search(r'try |try:', line):
                    exceptions[line_indentation] = [lineno]
        return groups

    # Checks if the character is a quotation that starts or ends a string.
    def _is_quotation(self, character, prev_char):
        return (character == '\"' or character == '\'') and prev_char != '\\'

    # Determines if the line ends in a backslash.
    def _is_end_slash(self, line):
        return len(line) >= 2 and line[-2] == '\\' and line[-1] == '\n'

    # Returns the space at the start of the line.
    def _get_space_start(self, line):
        return re.search(r'(\s*)[^\s]*', line).group(1)


class CFGGenerator(ast.NodeVisitor):
    """
    Generates a CFG from an AST.

    debug: bool
        Whether to print debug messages.
    """

    def __init__(self, debug):
        self.debug = debug
        self._init_variables()

    def _init_variables(self):
        self.block_list = BlockList()
        self.func_block = None
        self.current_block = None
        self.guard_block = None
        self.after_block = None
        self.exit_block = None
        self.current_control = None
        self.tokens = None
        self.last_lineno = None

    # Generates CFG.
    def generate(self, node, source):
        self._init_variables()
        self.tokens = TokenGenerator(source)
        self.visit(node)
        return self.block_list

    # Adds information about an instruction to the current block at lineno.
    def _add_instruction_info(self, lineno, var=None, action=None, instr_type=None):
        if self.current_block:
            # Adds variables to instruction.
            if var:
                if action == TypeVariable.LOAD:
                    self.current_block.add_reference(lineno, var)
                if action == TypeVariable.STORE:
                    self.current_block.add_definition(lineno, var)

            # Adds control to instruction.
            if self.current_control:
                self.current_block.add_instr_control(lineno, self.current_control)

            # Adds instruction type to instruction.
            if instr_type:
                self.current_block.add_instruction_type(lineno, instr_type)

            # Adds multiline to instructions.
            if lineno in self.tokens.multiline:
                self.current_block.add_multiline_instructions(
                    lineno, self.tokens.multiline[lineno])

            # Adds indentation level to instruction.
            indent = self.tokens.line_indent[lineno]
            self.current_block.add_instr_indent(lineno, indent)

            # Stores last line number visited.
            if not self.last_lineno or lineno > self.last_lineno:
                self.last_lineno = lineno

    # Adds a successor to the block if it is not null.
    def _add_successor(self, block, successor):
        if block:
            block.add_successor(successor)

    # Visits element within node.
    def _visit_item(self, value):
        if isinstance(value, list):
            items = []
            for item in value:
                if isinstance(item, ast.AST):
                    result = self.visit(item)
                    if isinstance(result, list):
                        items.extend(result)
                    elif result:
                        items.append(result)
            return items
        elif isinstance(value, ast.AST):
            return self.visit(value)

    # input: Module(stmt* body)
    # output: None
    def visit_Module(self, node):
        if 'body' in vars(node):
            for child_node in vars(node)['body']:
                if (isinstance(child_node, _ast.FunctionDef) or
                    isinstance(child_node, _ast.ClassDef)):
                    self._visit_item(child_node)

    # # Interactive(stmt* body)
    # def visit_Interactive(self, node):
    #     print('visit_Interactive')
    #     self.generic_visit(node)

    # # Expression(expr body)
    # def visit_Expression(self, node):
    #     print('visit_Expr')
    #     self.generic_visit(node)

    # # Suite(stmt* body)
    # def visit_Suite(self, node):
    #     print('visit_Suite')
    #     self.generic_visit(self, node)

    # input: FunctionDef(identifier name, arguments args,
    #                    stmt* body, expr* decorator_list)
    # output: None
    def visit_FunctionDef(self, node):
        prev_block = self.current_block

        # Create FunctionBlock.
        self.func_block = self.current_block = FunctionBlock(node.name)
        self._add_instruction_info(node.lineno, instr_type=InstructionType.FUNCTION_HEADER)

        # Create exit block.
        self.exit_block = Block()
        self.block_list.add(self.current_block)

        # Visit function information.
        self.generic_visit(node)
        self._add_successor(self.current_block, self.exit_block)

        # Add blank linenos and comments.
        linenos = set(range(node.lineno, self.last_lineno+1))
        self.func_block.blank_lines = linenos.intersection(self.tokens.blank_lines)
        self.func_block.comments = linenos.intersection(self.tokens.comments)
        self.func_block.unimportant |= self.func_block.blank_lines
        self.func_block.unimportant |= self.func_block.comments
        self.current_block = prev_block

    # # ClassDef(identifier name, expr* bases, stmt* body, expr* decorator_list)
    # def visit_ClassDef(self, node):
    #     print('visit_ClassDef')
    #     self.generic_visit(node)

    # input: Return(expr? value)
    # output: None
    def visit_Return(self, node):
        self._add_instruction_info(node.lineno, instr_type=InstructionType.RETURN)
        self._add_successor(self.current_block, self.exit_block)
        self.generic_visit(node)
        self.current_block = None

    # # Delete(expr* targets)
    # def visit_Delete(self, node):
    #     print('visit_Delete')
    #     self.generic_visit(node)

    # # Assign(expr* targets, expr value)
    # def visit_Assign(self, node):
    #     print('visit_Assign')
    #     self.generic_visit(node)

    # input: AugAssign(expr target, expr value, operator op)
    # output: None
    def visit_AugAssign(self, node):
        var = self._visit_item(node.target)
        self._add_instruction_info(node.lineno, var=var, action=TypeVariable.LOAD)

        self._visit_item(node.value)
        self._visit_item(node.op)

    # input: Print(expr? dest, expr* values, bool nl)
    # output: None
    def visit_Print(self, node):
        # Compatible with Python 2 print.
        self._add_instruction_info(node.lineno, var='print', action=TypeVariable.LOAD)
        self.generic_visit(node)

    # Visits a loop. Returns None.
    def _visit_loop(self, instr_type, conditional_nodes, conditional_lineno, body):
        start_block = self.current_block
        prev_control = self.current_control
        prev_guard_block = self.guard_block
        prev_after_block = self.after_block

        guard_block = Block()
        start_body_block = Block()
        after_block = Block()

        # Add successors/predcessors.
        start_block.add_successor(guard_block)
        guard_block.add_successor(start_body_block)
        guard_block.add_successor(after_block)

        # Add conditional to guard block.
        self.current_block = guard_block
        for node in conditional_nodes:
            self._visit_item(node)
        self._add_instruction_info(lineno=conditional_lineno, instr_type=instr_type)
        self.current_control = conditional_lineno

        # Add body to body block.
        self.current_block = start_body_block
        self.guard_block = guard_block
        self.after_block = after_block

        self._visit_item(body)

        self.guard_block = prev_guard_block
        self.after_block = prev_after_block
        self._add_successor(self.current_block, guard_block)

        self.current_control = prev_control
        self.current_block = after_block

    # input: For(expr target, expr iter, stmt* body, stmt* orelse)
    # output: None
    def visit_For(self, node):
        self._visit_loop(InstructionType.FOR, [node.target, node.iter],
                         node.target.lineno, node.body)

    # input: While(expr test, stmt* body, stmt* orelse)
    # output: None
    def visit_While(self, node):
        self._visit_loop(InstructionType.WHILE, [node.test],
                         node.test.lineno, node.body)

    # input: If(expr test, stmt* body, stmt* orelse)
    # output: None
    def visit_If(self, node):
        prev_control = self.current_control
        start_block = self.current_block

        # Add conditional to current block.
        self._visit_item(node.test)
        self.current_control = node.test.lineno

        # Add body to if block.
        start_if_block = Block()
        start_block.add_successor(start_if_block)
        self.current_block = start_if_block

        self._visit_item(node.body)
        end_if_block = self.current_block

        # Add orelse to else block.
        if node.orelse:
            start_else_block = Block()
            start_block.add_successor(start_else_block)
            self.current_block = start_else_block

            # If else block then add instruction type ELSE as a placeholder.
            if not isinstance(node.orelse[0], _ast.If):
                # Gets line number of else.
                lineno = node.orelse[0].lineno - 1
                while (lineno in self.tokens.comments or
                       lineno in self.tokens.blank_lines):
                    lineno -= 1

                # Adds ELSE instruction.
                self._add_instruction_info(lineno, instr_type=InstructionType.ELSE)
                self.current_control = lineno

            self._visit_item(node.orelse)
            end_else_block = self.current_block
        else:
            end_else_block = start_block

        # Add after block if all paths don't have a return.
        if end_if_block or end_else_block:
            after_block = Block()
            self._add_successor(end_if_block, after_block)
            self._add_successor(end_else_block, after_block)
            self.current_block = after_block
        self.current_control = prev_control

    # # With(expr context_expr, expr? optional_vars, stmt* body)
    # def visit_With(self, node):
    #     print('visit_With')
    #     self.generic_visit(node)

    # input: Raise(expr? type, expr? inst, expr? tback)
    # output: None
    def visit_Raise(self, node):
        self._add_instruction_info(node.lineno, instr_type=InstructionType.RAISE)
        self._add_successor(self.current_block, self.exit_block)
        self.generic_visit(node)
        self.current_block = None

    # Visits an exception. Returns None.
    def _visit_exception(self, lineno, body, handlers):
        prev_control = self.current_control
        start_block = self.current_block
        end_except_block = None

        # Add TRY statement to current block.
        self._add_instruction_info(lineno, instr_type=InstructionType.TRY)
        self.current_control = lineno

        # Add body to try block.
        start_try_block = Block()
        start_block.add_successor(start_try_block)
        self.current_block = start_try_block

        self._visit_item(body)
        end_try_block = self.current_block

        # Add except data.
        for handler in handlers:
            # Add body to except block.
            start_except_block = Block()
            start_block.add_successor(start_except_block)
            self.current_block = start_except_block

            # Visit handler header (ex. except Exception as e).
            if isinstance(handler.name, str):
                self._add_instruction_info(handler.lineno, var='e', action=TypeVariable.STORE)
            else:
                self._visit_item(handler.name)
            self._visit_item(handler.type)
            self._add_instruction_info(handler.lineno, instr_type=InstructionType.EXCEPT)
            self.current_control = handler.lineno

            # Visit handler body.
            self._visit_item(handler.body)
            end_except_block = self.current_block

        # Add after block if all paths don't have a return.
        if end_try_block or end_except_block:
            after_block = Block()
            self._add_successor(end_try_block, after_block)
            self._add_successor(end_except_block, after_block)
            self.current_block = after_block
        self.current_control = prev_control

    # Visits finalbody (finally of try/except).
    def _visit_finally(self, finalbody):
        if finalbody:
            lineno = finalbody[0].lineno - 1
            while (lineno in self.tokens.comments or
                   lineno in self.tokens.blank_lines):
                lineno -= 1
            self._add_instruction_info(lineno, instr_type=InstructionType.FINALLY)
            self._visit_item(finalbody)

    # input: TryExcept(stmt* body, excepthandler* handlers, stmt* orelse)
    # output: None
    def visit_TryExcept(self, node):
        self._visit_exception(node.lineno, node.body, node.handlers)

    # input: Try(stmt* body, excepthandler* handlers, stmt* orelse, stmt* finalbody)
    # output: None
    def visit_Try(self, node):
        self._visit_exception(node.lineno, node.body, node.handlers)
        self._visit_finally(node.finalbody)

    # input: TryFinally(stmt* body, stmt* finalbody)
    # output: None
    def visit_TryFinally(self, node):
        self._visit_item(node.body)
        self._visit_finally(node.finalbody)

    # # Exec(expr body, expr? globals, expr? locals)
    # def visit_Exec(self, node):
    #     print('visit_Exec')
    #     self.generic_visit(node)

    # # Global(identifier* names)
    # def visit_Global(self, node):
    #     print('visit_Global')
    #     self.generic_visit(node)

    # # Expr(expr value)
    # def visit_Expr(self, node):
    #     print('visit_Expr')
    #     self.generic_visit(node)

    # input: Pass()
    # output: None
    def visit_Pass(self, node):
        self._add_instruction_info(node.lineno, instr_type=InstructionType.PASS)
        self.generic_visit(node)

    # input: Break()
    # output: None
    def visit_Break(self, node):
        self._add_instruction_info(node.lineno, instr_type=InstructionType.BREAK)
        self._add_successor(self.current_block, self.after_block)
        self.generic_visit(node)
        self.current_block = None

    # input: Continue()
    # output: None
    def visit_Continue(self, node):
        self._add_instruction_info(node.lineno, instr_type=InstructionType.CONTINUE)
        self._add_successor(self.current_block, self.guard_block)
        self.generic_visit(node)
        self.current_block = None

    # # BoolOp(boolop op, expr* values)
    # def visit_BoolOp(self, node):
    #     print('visit_BoolOp')
    #     self.generic_visit(node)

    # # BinOp(expr left, operator op, expr right)
    # def visit_BinOp(self, node):
    #     print('visit_BinOp')
    #     self.generic_visit(node)

    # # UnaryOp(unaryop op, expr operand)
    # def visit_UnaryOp(self, node):
    #     print('visit_UnaryOp')
    #     self.generic_visit(node)

    # # Lambda(arguments args, expr body)
    # def visit_Lambda(self, node):
    #     print('visit_Lambda')
    #     self.generic_visit(node)

    # # IfExp(expr test, expr body, expr orelse)
    # def visit_IfExp(self, node):
    #     print('visit_IfExp')
    #     self.generic_visit(node)

    # # Dict(expr* keys, expr* values)
    # def visit_Dict(self, node):
    #     print('visit_Dict')
    #     self.generic_visit(node)

    # # Set(expr* elts)
    # def visit_Set(self, node):
    #     print('visit_Set')
    #     self.generic_visit(node)

    # # ListComp(expr elt, comprehension* generators)
    # def visit_ListComp(self, node):
    #     print('visit_ListComp')
    #     self.generic_visit(node)

    # # SetComp(expr elt, comprehension* generators)
    # def visit_SetComp(self, node):
    #     print('visit_SetComp')
    #     self.generic_visit(node)

    # # DictComp(expr key, expr value, comprehension* generators)
    # def visit_DictComp(self, node):
    #     print('visit_DictComp')
    #     self.generic_visit(node)

    # # GeneratorExp(expr elt, comprehension* generators)
    # def visit_GeneratorExp(self, node):
    #     print('visit_GeneratorExp')
    #     self.generic_visit(node)

    # # Yield(expr? value)
    # def visit_Yield(self, node):
    #     print('visit_Yield')
    #     self.generic_visit(node)

    # # Compare(expr left, cmpop* ops, expr* comparators)
    # def visit_Compare(self, node):
    #     print('visit_Compare')
    #     self.generic_visit(node)

    # # Call(expr func, expr* args, keyword* keywords,
    # #      expr? starargs, expr? kwargs)
    # def visit_Call(self, node):
    #     print('visit_Call')
    #     self.generic_visit(node)

    # # Repr(expr value)
    # def visit_Repr(self, node):
    #     print('visit_Repr')
    #     self.generic_visit(node)

    # # Num(object n) -- a number as a PyObject.
    # def visit_Num(self, node):
    #     print('visit_Num')
    #     self.generic_visit(node)

    # # Str(string s) -- need to specify raw, unicode, etc?
    # def visit_Str(self, node):
    #     print('visit_Str')
    #     print('line %d: (str) "%s"' %(node.lineno, node.s))
    #     self.generic_visit(node)

    # input: Attribute(expr value, identifier attr, expr_context ctx)
    # output: None
    def visit_Attribute(self, node):
        self._visit_item(node.value)
        if node.attr in _LIST_COMPREHENSION_FUNCTIONS:
            var_name = self._visit_item(node.value)
            self._add_instruction_info(node.lineno, var=var_name, action=TypeVariable.STORE)
            self._add_instruction_info(node.lineno, var=node.attr, action=TypeVariable.LOAD)

    # input: Subscript(expr value, slice slice, expr_context ctx)
    # output: None
    def visit_Subscript(self, node):
        self._visit_item(node.slice)
        var_name = self._visit_item(node.value)
        action = self._visit_item(node.ctx)
        self._add_instruction_info(node.lineno, var=var_name, action=action)

    # input: Name(identifier id, expr_context ctx)
    # output: var_name str
    def visit_Name(self, node):
        action = self._visit_item(node.ctx)
        self._add_instruction_info(node.lineno, var=node.id, action=action)
        return node.id

    # input: NameConstant(identifier value)
    # output: var_name str
    def visit_NameConstant(self, node):
        var = str(node.value)
        self._add_instruction_info(node.lineno, var=var, action=TypeVariable.LOAD)
        return var

    # input: arg(identifier arg, expr? annotation)
    # output: None
    def visit_arg(self, node):
        # Compatible with Python 3 arguments.
        self._add_instruction_info(node.lineno, var=node.arg, action=TypeVariable.STORE)

    # # List(expr* elts, expr_context ctx)
    # def visit_List(self, node):
    #     print('visit_List')
    #     self.generic_visit(node)

    # # Tuple(expr* elts, expr_context ctx)
    # def visit_Tuple(self, node):
    #     print('visit_Tuple')
    #     self.generic_visit(node)

    # # arguments(expr* args, identifier? vararg,
    # #           identifier? kwarg, expr* defaults)
    # def visit_arguments(self, node):
    #     # Compatible with Python 3 arguments.
    #     print('visit_arguments')
    #     self.generic_visit(node)

    # input: Load()
    # output: TypeVariable
    def visit_Load(self, node):
        return TypeVariable.LOAD

    # input: Store()
    # output: TypeVariable
    def visit_Store(self, node):
        return TypeVariable.STORE

    # # ???
    # def visit_Del(self, node):
    #     print('visit_Del')
    #     self.generic_visit(node)

    # # ???
    # def visit_AugLoad(self, node):
    #     print('visit_AugLoad')
    #     self.generic_visit(node)

    # # ???
    # def visit_AugStore(self, node):
    #     print('visit_AugStore')
    #     self.generic_visit(node)

    # input: Param()
    # output: TypeVariable
    def visit_Param(self, node):
        return TypeVariable.STORE

    # # Ellipsis
    # def visit_Ellipsis(self, node):
    #     print('visit_Ellipsis')
    #     self.generic_visit(node)

    # # Slice(expr? lower, expr? upper, expr? step)
    # def visit_Slice(self, node):
    #     print('visit_Slice')
    #     self.generic_visit(node)

    # # ExtSlice(slice* dims)
    # def visit_ExtSlice(self, node):
    #     print('visit_ExtSlice')
    #     self.generic_visit(node)

    # # Index(expr value)
    # def visit_Index(self, node):
    #     print('visit_Index')
    #     self.generic_visit(node)

    # # ???
    # def visit_And(self, node):
    #     print('visit_And')
    #     self.generic_visit(node)

    # # ???
    # def visit_Or(self, node):
    #     print('visit_Or')
    #     self.generic_visit(node)

    # # ???
    # def visit_Add(self, node):
    #     print('visit_Add')
    #     self.generic_visit(node)

    # # ???
    # def visit_Sub(self, node):
    #     print('visit_Sub')
    #     self.generic_visit(node)

    # # ???
    # def visit_Mult(self, node):
    #     print('visit_Mult')
    #     self.generic_visit(node)

    # # ???
    # def visit_Div(self, node):
    #     print('visit_Div')
    #     self.generic_visit(node)

    # # ???
    # def visit_Mod(self, node):
    #     print('visit_Mod')
    #     self.generic_visit(node)

    # # ???
    # def visit_Pow(self, node):
    #     print('visit_Pow')
    #     self.generic_visit(node)

    # # ???
    # def visit_LShift(self, node):
    #     print('visit_LShift')
    #     self.generic_visit(node)

    # # ???
    # def visit_RShift(self, node):
    #     print('visit_RShift')
    #     self.generic_visit(node)

    # # ???
    # def visit_BitOr(self, node):
    #     print('visit_BitOr')
    #     self.generic_visit(node)

    # # ???
    # def visit_BitXor(self, node):
    #     print('visit_BitXor')
    #     self.generic_visit(node)

    # # ???
    # def visit_BitAnd(self, node):
    #     print('visit_BitAnd')
    #     self.generic_visit(node)

    # # ???
    # def visit_FloorDiv(self, node):
    #     print('visit_FloorDiv')
    #     self.generic_visit(node)

    # # ???
    # def visit_Invert(self, node):
    #     print('visit_Invert')
    #     self.generic_visit(node)

    # # ???
    # def visit_Not(self, node):
    #     print('visit_Not')
    #     self.generic_visit(node)

    # # ???
    # def visit_UAdd(self, node):
    #     print('visit_UAdd')
    #     self.generic_visit(node)

    # # ???
    # def visit_USub(self, node):
    #     print('visit_USub')
    #     self.generic_visit(node)

    # # ???
    # def visit_Eq(self, node):
    #     print('visit_Eq')
    #     self.generic_visit(node)

    # # ???
    # def visit_NotEq(self, node):
    #     print('visit_NotEq')
    #     self.generic_visit(node)

    # # ???
    # def visit_Lt(self, node):
    #     print('visit_Lt')
    #     self.generic_visit(node)

    # # ???
    # def visit_Lte(self, node):
    #     print('visit_Lte')
    #     self.generic_visit(node)

    # # ???
    # def visit_Gt(self, node):
    #     print('visit_Gt')
    #     self.generic_visit(node)

    # # ???
    # def visit_Gte(self, node):
    #     print('visit_Gte')
    #     self.generic_visit(node)

    # # ???
    # def visit_Is(self, node):
    #     print('visit_Is')
    #     self.generic_visit(node)

    # # ???
    # def visit_IsNot(self, node):
    #     print('visit_IsNot')
    #     self.generic_visit(node)

    # # ???
    # def visit_In(self, node):
    #     print('visit_In')
    #     self.generic_visit(node)

    # # ???
    # def visit_NotIn(self, node):
    #     print('visit_NotIn')
    #     self.generic_visit(node)
