# File name: slice.py
# Author: Nupur Garg
# Date created: 2/20/2017
# Python Version: 3.5


from src.globals import *
from numpy import array, diff, where, split
from enum import Enum
import copy
import itertools

from src.models.block import FunctionBlock, Block, BlockList
from src.models.blockinfo import FunctionBlockInformation, ReachingDefinitions
from src.models.dataflowanalysis import *
from src.models.structures import Queue, QueueInt
from src.models.instruction import InstructionType



class SuggestionType(Enum):
    __order__ = 'REMOVE_VAR, SIMILAR_REF, DIFF_REF_LIVAR_BLOCK, DIFF_REF_LIVAR_INSTR'
    REMOVE_VAR = 1
    SIMILAR_REF = 2
    DIFF_REF_LIVAR_BLOCK = 3
    DIFF_REF_LIVAR_INSTR = 4

    def __str__(self):
        if self == SuggestionType.REMOVE_VAR:
            return ('Removing these instructions decreases number of paths of '
                    'execution in this function - making the code more '
                    'readable and testable.')
        elif self == SuggestionType.SIMILAR_REF:
            return ('The same set of variables are referenced in all '
                    'instructions in the given line numbers.')
        elif (self == SuggestionType.DIFF_REF_LIVAR_BLOCK or
              self == SuggestionType.DIFF_REF_LIVAR_INSTR):
            return ('Multiple variables defined prior to these instructions '
                    'are not used in these line numbers.')
        else:
            raise TypeError(self)


class Suggestion(object):
    """
    Represents a suggestion to be made to the user.
    """

    def __init__(self, ref_vars, ret_vars, types, func_name,
                 start_lineno, end_lineno=None):
        self.func_name = func_name
        self.start_lineno = start_lineno
        self.end_lineno = end_lineno if end_lineno else start_lineno
        self.ref_vars = ref_vars
        self.ret_vars = ret_vars
        self.types = types

    def __lt__(self, other):
        if self.start_lineno == other.start_lineno:
            return self.end_lineno > other.end_lineno
        return self.start_lineno < other.start_lineno

    def __str__(self):
        message = ''

        # Gets message header.
        if self.end_lineno == self.start_lineno:
            message += 'line {} ({}):\n'.format(self.start_lineno, self.func_name)
        else:
            message += 'line {}-{} ({}):\n'.format(self.start_lineno, self.end_lineno, self.func_name)

        # Add suggestion parameters.
        if self.ref_vars:
            message += '\tparameters: {}\n'.format(', '.join(self.ref_vars))

        # Adds suggestion return value.
        if self.ret_vars:
            message += '\treturns: {}\n'.format(', '.join(self.ret_vars))

        # Add suggestion types to message.
        # names = [suggestion_type.name.lower() for suggestion_type in self.types]
        names = ' '.join([str(suggestion_type) for suggestion_type in self.types])
        message += '\treason: {}\n'.format(names)

        return message


class Slice(object):
    """
    Generates a slice for a function block.

    func: obj
        FunctionBlock for the current function.
    info: obj
        FunctionBlockInformation containg ReachingDefinitions for current block.
    slow: bool
        Whether to generate the full report.
    """

    def __init__(self, func, config, slow=False):
        self.func = func
        self.config = config
        self.slow = slow

        # Condense functions and generate analysis methods.
        self.func = self.condense_cfg(self.func)
        analysismethod = ReachingDefinitionsAnalysis()
        self.reaching_def_info = analysismethod.analyze(self.func)

        analysismethod = LiveVariableAnalysis()
        self.live_var_info = analysismethod.analyze(self.func)

        # Caches data about func_block.
        self.sorted_blocks = self.func.get_sorted_blocks()
        self.linenos = self.func.get_linenos_in_func()
        self.variables = self._get_variables_in_func()
        self.controls = self._get_map_control_linenos_in_func()
        self.multiline = self._get_map_multiline_in_func()
        self.block_map = self._get_block_map_in_func()
        self.instrs_block_map = self._get_instrs_block_map_in_func()

        # Creates variable groups.
        defined = self._get_defined_variables_in_func()
        self.variable_groups = [[var] for var in self.variables] # 6m21.758s
        if self.slow:
            self.variable_groups.extend([list(var)
                for var in self._get_groups_variables(size=3, defined=defined)])
            self.variable_groups.extend([list(var)
                for var in self._get_groups_variables(size=4, defined=defined)])

        # Global caches.
        self._SLICE_CACHE = {}
        self._SUGGESTION_CACHE = {}

    # Gets the variables in a function.
    def _get_variables_in_func(self):
        variables = set()
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                for var in instr.defined:
                    variables.add(var)
        return variables

    # Generates a map of lineno of control to the linenos it controls.
    def _get_map_control_linenos_in_func(self):
        controls = {}
        for lineno in self.linenos:
            instr = self.reaching_def_info.get_instruction(lineno)
            if instr and instr.control:
                if instr.control not in controls:
                    controls[instr.control] = set()
                controls[instr.control].add(lineno)
        return controls

    # Generates a map of lineno of multiline to the multiline linenos.
    def _get_map_multiline_in_func(self):
        multiline_map = {}
        for lineno in self.linenos:
            instr = self.reaching_def_info.get_instruction(lineno)
            if instr and instr.multiline:
                multiline = instr.multiline | set([lineno])
                for lineno in multiline:
                    multiline_map[lineno] = multiline
        return multiline_map

    # Generates a map of block labels to block.
    def _get_block_map_in_func(self):
        return {block.label: block for block in self.sorted_blocks}

    # Generates a map of instructions to block.
    def _get_instrs_block_map_in_func(self):
        instrs_block_map = {}
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                instrs_block_map[instr.lineno] = block
        return instrs_block_map

    def _get_defined_variables_in_func(self):
        defined = set()
        for lineno in self.linenos:
            instr_info = self.live_var_info.get_instruction_info(lineno)
            defined |= instr_info.defined
        return defined

    # Gets the variables in groups.
    def _get_groups_variables(self, size, defined):
        groups = set()
        variables = []
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                instr_variables = instr.defined | instr.referenced
                for var in instr_variables:
                    if var in defined:
                        variables.append(var)
                        if len(frozenset(variables)) == size:
                            groups.add(frozenset(variables))
                        if len(variables) == size:
                            variables.pop(0)
        return groups

    # -------------------------------------
    # ---------- GENERATES SLICE ----------
    # -------------------------------------

    # Gets set of line numbers in a slice.
    def _get_instructions_in_slice(self, start_lineno, **kwargs):
        visited = set()
        queue = QueueInt()
        queue.enqueue(start_lineno)

        # Parse keyword arguments.
        include_control = kwargs.get('include_control', True)
        exclude_vars = kwargs.get('exclude_vars', {})

        while not queue.empty():
            # Get instruction.
            cur_lineno = queue.dequeue()
            instr = self.reaching_def_info.get_instruction(cur_lineno)

            # Process instruction if it has not been visited.
            if instr and cur_lineno not in visited:
                instr_info = self.reaching_def_info.get_instruction_info(cur_lineno)

                # Trace line numbers of referenced variables except:
                #   - Variables only referenced in func (e.g. function names).
                #   - Variables in exclude_vars.
                for var in instr.referenced:
                    if var in instr_info.in_node and var not in exclude_vars:
                        for _, lineno in instr_info.in_node[var]:
                            queue.enqueue(lineno)

                # Add line wraps.
                for lineno in instr.multiline:
                    queue.enqueue(lineno)

                # Add control if include_control or a line before control is referenced.
                if instr.control and (include_control or instr.control > queue.min()):
                    queue.enqueue(instr.control)

            # Mark current instruction as visited.
            visited.add(cur_lineno)

        # Returns set of line numbers instructions.
        return visited

    # Creates a FunctionBlock representing a CFG from a set of instruction linenos.
    def _generate_cfg_slice(self, slice_instrs):
        block_map = {} # function block number : slice block number
        slice_func = FunctionBlock(self.func.label)

        for block in self.sorted_blocks:
            # Get all instructions in this block that are in the slice.
            linenos = block.get_instruction_linenos().intersection(slice_instrs)

            # Create a copy of the block.
            if not block_map:
                curr_bloc = slice_func
            else:
                curr_bloc = Block()
            block_map[block.label] = curr_bloc

            # Copy instructions in the block to block copy.
            for lineno in linenos:
                instruction = block.get_instruction(lineno)
                curr_bloc.add_instruction(instruction)

            # Copy the block's successors.
            for successor in block.successors:
                if successor in block_map:
                    curr_bloc.add_successor(block_map[successor])

            # Copy the block's predecessors.
            for predecessor in block.predecessors:
                if predecessor in block_map:
                    curr_bloc.add_predecessor(block_map[predecessor])

        return slice_func

    # ----------------------------------------
    # ---------- CONDENSES CFG ---------------
    # ----------------------------------------

    # Condenses successors into one block if they are equal.
    def _condense_cfg_fold_redundant_branch(self, block):
        successors = list(block.successors.values())

        if len(successors) > 1 and block.check_successor_equality():
            for successor in successors[1:]:
                successor.destroy()

    # Removes empty block if block is empty and isn't a function block.
    def _condense_cfg_remove_empty_block(self, block, func):
        successor = block.get_first_successor()

        # If block is empty and isn't a function block, remove block.
        if (len(block.successors) == 1 and block != func and
            len(block.get_instruction_linenos()) == 0):
            # Remove predecessors.
            while block.predecessors:
                predecessor = block.get_first_predecessor()
                predecessor.replace_successor(block, successor)

            # Remove successor.
            successor.remove_predecessor(block)
            block.set_successors([])

    # Combines block if single successor has one predecessor.
    def _condense_cfg_combine_blocks(self, block):
        successor = block.get_first_successor()

        # If successor has one predecessor, merge blocks.
        if len(block.successors) == 1 and len(successor.predecessors) == 1:
            # Add instructions to current block.
            for instruction in successor.get_instructions():
                block.add_instruction(instruction)

            # Change block's successors and successor's predecessors.
            block.remove_successor(successor)
            while successor.successors:
                new_successor = successor.get_first_successor()
                new_successor.replace_predecessor(successor, block)

    # Skips successors if successor is empty and leads to a branch.
    def _condense_cfg_hoist_branch(self, block):
        successor = block.get_first_successor()

        # If successor is empty and ends in a branch, skip successor.
        if (len(block.successors) == 1 and len(successor.successors) > 1 and
            len(successor.get_instruction_linenos()) == 0):
            successors = successor.successors.values()
            block.set_successors(successors)

    # Runs through one pass of condensing a FunctionBlock representing a CFG.
    def _condense_cfg_helper(self, func):
        visited = set()
        queue = [func]

        while queue:
            block = queue.pop()
            visited.add(block.label)

            # Run optimization functions on the block.
            self._condense_cfg_fold_redundant_branch(block)
            self._condense_cfg_remove_empty_block(block, func)
            self._condense_cfg_combine_blocks(block)
            self._condense_cfg_hoist_branch(block)

            # Add successors to queue if not visited.
            for label, successor in block.successors.items():
                if label not in visited:
                    queue.append(successor)
        return func

    # Condenses a FunctionBlock representing a CFG.
    def condense_cfg(self, func):
        func = copy.deepcopy(func)
        func_copy = None
        while func != func_copy:
            func_copy = copy.deepcopy(func)
            func = self._condense_cfg_helper(func)
        return func

    # ------------------------------------------------------------------
    # ---------- GENERATES CONDENSED SLICE AND SLICE MAP ---------------
    # ------------------------------------------------------------------

    # Gets a slice for the function block for the given line number.
    def _get_slice(self, instrs):
        slice_func = self._generate_cfg_slice(instrs)
        slice_func = self.condense_cfg(slice_func)
        return slice_func

    # Gets a slice for the function block from the cache.
    def get_slice(self, instrs):
        instrs = frozenset(instrs)
        if instrs not in self._SLICE_CACHE:
            slice_cfg = self._get_slice(instrs)
            slice_complexity = slice_cfg.get_cyclomatic_complexity()
            self._SLICE_CACHE[instrs] = {'complexity': slice_complexity,
                                         'cfg': slice_cfg}
        return self._SLICE_CACHE[instrs]

    # Gets map of line number to slice.
    # Parameter kwargs is arguments to _get_instructions_in_slice().
    def get_slice_map(self, **kwargs):
        slice_map = {}
        for lineno in self.linenos:
            instrs = self._get_instructions_in_slice(lineno, **kwargs)
            if instrs:
                slice_map[lineno] = self.get_slice(instrs)
        return slice_map

    # -------------------------------------------
    # ---------- GENERATES GROUPS ---------------
    # -------------------------------------------

    # Groups line numbers with greater than max diff between slices.
    def _group_suggestions(self, linenos):
        linenos = sorted(list(linenos))
        groups = split(linenos, where(diff(linenos) >= 2)[0] + 1)
        return set([(min(linenos), max(linenos))
                    for linenos in groups if linenos.size > 1])

    # Adds multiline statements where there are no instructions.
    def _add_multiline_statements(self, linenos):
        final_linenos = copy.copy(linenos)
        for lineno in linenos:
            instr = self.reaching_def_info.get_instruction(lineno)
            if instr:
                for multiline in instr.multiline:
                    if multiline not in self.linenos:
                        final_linenos.add(multiline)
        return final_linenos

    # Splits the groups of line numbers if indentation goes out.
    def _split_groups_linenos_indentation(self, groups):
        suggestions = set()
        for min_lineno, max_lineno in groups:
            index = 0
            linenos = range(min_lineno, max_lineno + 1)
            start_indent = cur_indent = None
            start_lineno = min_lineno

            # Splits group based on indentation.
            while index < len(linenos):
                lineno = linenos[index]
                instr = self.reaching_def_info.get_instruction(lineno)
                if instr:
                    cur_indent = instr.indentation
                    if start_indent is None:
                        start_indent = cur_indent
                        start_lineno = lineno
                    elif cur_indent < start_indent:
                        suggestions.add((start_lineno, linenos[index - 1]))
                        start_indent = cur_indent
                        start_lineno = lineno
                index += 1
            suggestions.add((start_lineno, linenos[index - 1]))
        return suggestions

    # Removes line numbers if all multiline instrs aren't included.
    def _adjust_multiline_groups(self, groups):
        suggestions = set()
        for min_lineno, max_lineno in groups:
            linenos = range(min_lineno, max_lineno + 1)
            final_linenos = set()

            for cur_lineno in linenos:
                # Add lineno if all lines within multiline group are valid.
                if cur_lineno in self.multiline:
                    multiline = self.multiline[cur_lineno]
                    valid_lines = [lineno in linenos for lineno in multiline]
                    if all(valid_lines):
                        final_linenos.add(cur_lineno)
                else:
                    final_linenos.add(cur_lineno)
            suggestions |= self._group_suggestions(final_linenos)
        return suggestions

    # Removes control flow where body is not included.
    def _adjust_control_groups(self, groups):
        suggestions = set()
        for min_lineno, max_lineno in groups:
            linenos = range(min_lineno, max_lineno + 1)
            final_linenos = set()

            for lineno in linenos:
                if lineno in self.controls:
                    controls = self.controls[lineno]
                    intersection = controls.intersection(linenos)
                    if len(intersection) == len(controls):
                        final_linenos.add(lineno)
                else:
                    final_linenos.add(lineno)
            suggestions |= self._group_suggestions(final_linenos)

        return suggestions

    # Trims the ends of the suggestion to remove unimportant lines.
    def _trim_unimportant(self, groups):
        suggestions = set()
        for min_lineno, max_lineno in groups:
            final_max_lineno = max_lineno
            final_min_lineno = min_lineno
            while final_max_lineno in self.func.unimportant:
                final_max_lineno -= 1
            while final_min_lineno in self.func.unimportant:
                final_min_lineno += 1
            if final_min_lineno < final_max_lineno:
                suggestions.add((final_min_lineno, final_max_lineno))
        return suggestions

    # Splits the groups of line numbers to make them valid.
    def _split_groups_linenos(self, groups):
        final_suggestions = set()
        for min_lineno, max_lineno in groups:
            key = frozenset((min_lineno, max_lineno))
            if key not in self._SUGGESTION_CACHE:
                suggestions = set([(min_lineno, max_lineno)])
                prev_suggestion = None

                # Run suggestions multiple times.
                while prev_suggestion != suggestions:
                    prev_suggestion = suggestions
                    suggestions = self._split_groups_linenos_indentation(suggestions)
                    suggestions = self._adjust_multiline_groups(suggestions)
                    suggestions = self._adjust_control_groups(suggestions)
                suggestions = self._trim_unimportant(suggestions)
                self._SUGGESTION_CACHE[key] = suggestions
            final_suggestions |= self._SUGGESTION_CACHE[key]
        return final_suggestions

    # Generates groups from line numbers.
    def _group_suggestions_with_unimportant(self, linenos):
        if not linenos:
            return set([])
        linenos = self._add_multiline_statements(linenos)
        linenos |= self.func.unimportant
        suggestions = self._group_suggestions(linenos)
        return self._split_groups_linenos(suggestions)

    # -----------------------------------------------------------------
    # ---------- HELPER METHODS TO GENERATE SUGGESTIONS ---------------
    # -----------------------------------------------------------------

    # Gets the length of the range of the line numbers.
    def _range(self, min_lineno, max_lineno):
        return max_lineno - min_lineno + 1

    # -----------------------------------------------------
    # ---------- GENERATES SUGGESTION TYPES ---------------
    # -----------------------------------------------------

    # Gets groups of line numbers with greater than max diff between slices.
    def _compare_slice_maps(self, slice_map, reduced_slice_map,
                            min_diff_complexity):
        linenos = set()
        cur_control = set()
        excluded_control = set()

        # Get line numbers with reduced complexity.
        for lineno in self.linenos:
            if lineno in slice_map and lineno not in excluded_control:
                slice_complexity = slice_map[lineno]['complexity']
                reduced_slice_complexity = reduced_slice_map[lineno]['complexity']
                diff_complexity = slice_complexity - reduced_slice_complexity

                # If enough decrease in complexity, add line and grouped lines.
                if diff_complexity >= min_diff_complexity:
                    linenos.add(lineno)

        return self._group_suggestions_with_unimportant(linenos)

    # Gets suggestions based on removing variables.
    def _get_suggestions_remove_variables(self, slice_map, debug=False):
        suggestions = set()

        # Gets map of linenos to variables to generate suggestions.
        for var in self.variable_groups:
            reduced_slice_map = self.get_slice_map(exclude_vars=var)
            linenos = self._compare_slice_maps(slice_map, reduced_slice_map,
                                               self.config.min_diff_complexity_between_slices)

            # Adds groups of linenos.
            for min_lineno, max_lineno in linenos:
                if self._range(min_lineno, max_lineno) >= self.config.min_lines_in_suggestion:
                    suggestions.add((min_lineno, max_lineno))

        return suggestions, SuggestionType.REMOVE_VAR

    # Gets suggestions based on similar references in consequtive instructions.
    def _get_suggestions_similar_reference_instrs(self, debug=False):
        suggestions = set()
        prev_ref_set = set()
        min_lineno = None
        max_lineno = None

        # Finds similar references in consequtive lines within a block.
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                info = self.live_var_info.get_instruction_info(instr.lineno)
                if not info.referenced or info.referenced != prev_ref_set:
                    if (min_lineno and (self._range(min_lineno, max_lineno) >=
                                        self.config.min_lines_in_suggestion)):
                        suggestions.add((min_lineno, max_lineno))
                    min_lineno = instr.lineno
                max_lineno = instr.lineno
                prev_ref_set = info.referenced

        suggestions = self._split_groups_linenos(suggestions)
        return suggestions, SuggestionType.SIMILAR_REF

    """
    # TODO: Either remove or finish.
    # Gets suggestions based on similar references in consequtive instructions.
    # Treats mutliline instructions as a single instruction.
    def _get_suggestions_similar_reference_instrs_multiline(self, debug=False):
        suggestions = set()
        prev_ref_set = set()
        min_lineno = None
        max_lineno = None

        # Finds similar references in consequtive lines within a block.
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                # Get referenced in multiline
                info = self.live_var_info.get_instruction_info(instr.lineno)
                if not info.referenced or info.referenced != prev_ref_set:
                    if (min_lineno and (self._range(min_lineno, max_lineno) >=
                                        self.config.min_lines_in_suggestion)):
                        suggestions.add((min_lineno, max_lineno))
                    min_lineno = instr.lineno
                max_lineno = instr.lineno
                prev_ref_set = info.referenced

        suggestions = self._split_groups_linenos(suggestions)
        return suggestions, SuggestionType.SIMILAR_REF_MULTILINE
    """

    # Gets suggestions from differences in live var and referenced in a block.
    def _get_suggestions_diff_reference_livevar_block(self, debug=False):
        linenos = set()

        # Get instructions from blocks.
        for block in self.sorted_blocks:
            info = self.live_var_info.get_block_info(block)
            # Add instructions of less than equal to min difference required.
            if ((len(info.in_node) - len(info.referenced)) >=
                 self.config.min_diff_ref_and_live_var):
                linenos |= block.get_instruction_linenos()

        suggestions = self._group_suggestions_with_unimportant(linenos)
        return suggestions, SuggestionType.DIFF_REF_LIVAR_BLOCK

    # Gets suggestions from differences in live var and referenced in an instr.
    def _get_suggestions_diff_reference_livevar_instr(self, debug=False):
        linenos = set()

        # Get instructions from blocks.
        for block in self.sorted_blocks:
            for instr in block.get_instructions():
                info = self.live_var_info.get_instruction_info(instr.lineno)
                # Add instructions of less than equal to min difference required.
                if ((len(info.in_node) - len(info.referenced)) >=
                     self.config.min_diff_ref_and_live_var):
                    linenos.add(instr.lineno)

        suggestions = self._group_suggestions_with_unimportant(linenos)

        # Only add suggestion if there are enough actual instructions.
        final_suggestions = set()
        for min_lineno, max_lineno in suggestions:
            linenos = set(range(self._range(min_lineno, max_lineno)))
            num_linenos = len(linenos - self.func.unimportant)
            if num_linenos > self.config.min_linenos_diff_reference_livevar_instr:
                final_suggestions.add((min_lineno, max_lineno))

        return final_suggestions, SuggestionType.DIFF_REF_LIVAR_INSTR

    """
    # TODO: Either remove or finish.
    # Gets suggestions if all paths in a conditional define the same variables.
    def _get_suggestions_conditional_branches(self, debug=False):
        linenos = set()

        # For all the blocks.
        # If there are multiple successors
        # Then see if the multiple successors have similar definitions

        suggestions = self._group_suggestions_with_unimportant(linenos)
        return final_suggestions, SuggestionType.SIMILAR_CONDITIONALS
    """

    # ------------------------------------------------
    # ---------- GENERATES SUGGESTIONS ---------------
    # ------------------------------------------------

    # Determines if the suggestion is valid.
    def _is_valid_suggestion(self, ref_vars, ret_vars, min_lineno, max_lineno):
        ref_vars = set(ref_vars)
        ret_vars = set(ret_vars)
        linenos = set(range(min_lineno, max_lineno + 1))
        linenos_instrs = linenos - self.func.unimportant
        lines_func = len(self.linenos) - len(linenos_instrs)

        return (len(ref_vars) >= self.config.min_variables_parameter_in_suggestion and
                len(ret_vars) <= self.config.max_variables_return_in_suggestion and
                len(linenos_instrs) >= self.config.min_lines_in_suggestion and
                lines_func >= self.config.min_lines_func_not_in_suggestion and
                ref_vars != self.func.get_function_parameters())

    # Gets the variables referenced in range of line numbers.
    def _get_referenced_variables(self, min_lineno, max_lineno):
        variables = set()
        defined = set()
        for lineno in range(min_lineno, max_lineno+1):
            instr_info = self.live_var_info.get_instruction_info(lineno)
            if instr_info:
                for var in instr_info.referenced:
                    if var not in defined:
                        variables.add(var)
                for var in instr_info.defined:
                    defined.add(var)
        return sorted(list(variables))

    # Gets the variables defined in range of line numbers.
    # Returns variables defined, variables returned, and successors to visit.
    def _get_defined_variables(self, min_lineno, max_lineno):
        variables = set()   # Variables to be returned.
        defined = set()     # Variables defined in range.
        successors = set()  # Successors to visit.

        # Gets all variables defined in range.
        for lineno in range(min_lineno, max_lineno+1):
            instr_info = self.live_var_info.get_instruction_info(lineno)
            if instr_info:
                # Track variables defined.
                for var in instr_info.defined:
                    defined.add(var)

                # Add successors.
                block = self.instrs_block_map[lineno]
                block_last_lineno = block.get_last_instruction()
                if defined:
                    successors.add(block.label)
                if block.label in successors and block_last_lineno == lineno:
                    successors.remove(block.label)
                if defined:
                    successors |= set(block.successors.keys())

                # Adds variables referenced in RETURN to 'variables'.
                instr = self.live_var_info.get_instruction(lineno)
                if instr.instruction_type == InstructionType.RETURN:
                    variables |= instr_info.referenced
        return defined, variables, successors

    # Gets the return values in the range of the line numbers.
    def _get_return_variables(self, min_lineno, max_lineno):
        visited = set()
        queue = Queue()

        defined_tuple = self._get_defined_variables(min_lineno, max_lineno)
        defined, variables, successors = defined_tuple

        # Follow all of the block's successors.
        queue.init(successors)
        while not queue.empty():
            label = queue.dequeue()

            # Gets linenos in block if block has not been visited.
            if label not in visited:
                block = self.block_map[label]
                for lineno in block.get_instruction_linenos():
                    instr_info = self.live_var_info.get_instruction_info(lineno)

                    # Analyze instruction if exists and is not part of the slice.
                    if instr_info and (lineno < min_lineno or lineno > max_lineno):
                        variables |= defined.intersection(instr_info.referenced)
                        for var in instr_info.defined:
                            if var in defined:
                                defined.remove(var)

                # Add successors to queue.
                for successor in block.successors:
                    queue.enqueue(successor)
            visited.add(label)
        return sorted(list(variables))

    # Generates suggestions from a map of range of lineno to list of variables.
    def _generate_suggestions(self, suggestion_map):
        suggestions = []
        for key, types in suggestion_map.items():
            min_lineno, max_lineno = key
            ref_vars = self._get_referenced_variables(min_lineno, max_lineno)
            ret_vars = self._get_return_variables(min_lineno, max_lineno)

            # Generate message if the number of vars within max vars in func.
            if self._is_valid_suggestion(ref_vars, ret_vars, min_lineno, max_lineno):
                suggestions.append(Suggestion(ref_vars, ret_vars, types,
                                              self.func.label,
                                              min_lineno, max_lineno))

        return suggestions

    # Adds suggestions to suggestion map.
    def _add_suggestion_map(self, suggestion_map, suggestions, suggestion_type):
        for suggestion in suggestions:
            if suggestion not in suggestion_map:
                suggestion_map[suggestion] = set()
            suggestion_map[suggestion].add(suggestion_type)

    # Adds suggestions of function type to suggestion map.
    def _add_suggestions(self, suggestion_map, func, **kwargs):
        suggestions, suggestion_type = func(**kwargs)
        self._add_suggestion_map(suggestion_map, suggestions, suggestion_type)

    # Gets the suggestions on how to improve the function.
    def get_suggestions(self, debug=False):
        suggestion_map = {}
        slice_map = self.get_slice_map()

        # Get the suggestions through various methods.
        self._add_suggestions(suggestion_map,
                              func=self._get_suggestions_remove_variables,
                              slice_map=slice_map, debug=debug)
        self._add_suggestions(suggestion_map,
                              func=self._get_suggestions_similar_reference_instrs,
                              debug=debug)
        self._add_suggestions(suggestion_map,
                              func=self._get_suggestions_diff_reference_livevar_block,
                              debug=debug)
        self._add_suggestions(suggestion_map,
                              func=self._get_suggestions_diff_reference_livevar_instr,
                              debug=debug)

        # Generate list of final suggestions.
        final_suggestions = self._generate_suggestions(suggestion_map)
        return sorted(final_suggestions)

    # Gets the complexity of the slice at each line for each line
    # multiplied by line number.
    def get_avg_lineno_slice_complexity(self):
        slice_map = self.get_slice_map()
        total_complexity = 0

        # Gets complexity of the slice at each line.
        for func_lineno, lineno in enumerate(sorted(slice_map.keys())):
            reduced_slice_complexity = slice_map[lineno]['complexity']
            total_complexity += (reduced_slice_complexity * func_lineno)

        # Gets average complexity.
        func_length = len(slice_map.keys()) + 1
        avg_complexity = float(total_complexity) / func_length
        return avg_complexity
