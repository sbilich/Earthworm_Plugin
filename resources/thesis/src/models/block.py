# File name: block.py
# Author: Nupur Garg
# Date created: 12/25/2016
# Python Version: 3.5


import collections
import copy

from src.globals import *
from src.models.counter import Counter
from src.models.instruction import Instruction, InstructionType


class BlockList(object):
    """
    List of blocks.

    _block_list: list(Block)
        List of blocks.
    """

    def __init__(self):
        self._block_list = []

    def __str__(self):
        string = ''
        for func_block in self._block_list:
            string += '%s\n' %str(func_block)
        return string

    def __eq__(self, other):
        if (not other or not isinstance(other, self.__class__) or
            not self.get_num_funcs() == other.get_num_funcs()):
            return False

        for func_block in self.get_funcs():
            if func_block != other.get_func(func_block.label):
                return False
        return True

    def __ne__(self, other):
        return not self == other

    # Adds block to block list.
    def add(self, block):
        self._block_list.append(block)

    # Gets the block with the function name.
    def get_func(self, func_name):
        for block in self._block_list:
            if block.label == func_name:
                return block
        return None

    # Returns functions in the block list.
    def get_funcs(self):
        return self._block_list

    # Returns number of functions in the block list.
    def get_num_funcs(self):
        return len(self._block_list)


class BlockInterface(ABC):
    """
    Abstract class BlockInterface.

    successors: list(Block)
        Successors to block.
    predecessors: list(Block)
        Predecessors to block.
    _instructions: list(Instruction)
        Instructions in the block.
    label: str
        Label identifying the block.
    """

    _label_counter = Counter()

    def __init__(self, label):
        self.successors = collections.OrderedDict()
        self.predecessors = collections.OrderedDict()
        self._instructions = {}
        self.label = label

    def __str__(self):
        len_tab = len(self.label)

        # Adds block header.
        string = '%s | \n' %str(self.label)

        # Adds predecessors and successors.
        successors = ' | successors(%s)\n' %(', '.join(self.successors.keys()))
        string += successors.rjust(len_tab + len(successors))
        predecessors = ' | predecessors(%s)\n' %(', '.join(self.predecessors.keys()))
        string += predecessors.rjust(len_tab + len(predecessors))

        # Adds instructions.
        for instruction in self.get_instructions():
            string += '\t%s\n' %str(instruction)
        return string

    def __eq__(self, other):
        if not other or not isinstance(other, self.__class__):
            return False
        return self.label == other.label and self.equals(other)

    def __ne__(self, other):
        return not self == other

    # Getter method for label. Sets label if it hasn't been set.
    @property
    def label(self):
        return self.__label

    # Setter for label.
    @label.setter
    def label(self, label):
        if hasattr(self, '_BlockInterface__label'):
            raise ValueError('\'label\' is immutable')
        self.__label = label

    # Checks if blocks are equal excluding the labels.
    def equals(self, block):
        # Check successors and predecessors and number of instructions.
        if (self.successors.keys() != block.successors.keys() or
            self.predecessors.keys() != block.predecessors.keys() or
            self.get_instruction_linenos() != block.get_instruction_linenos()):
            return False

        # Check instructions.
        for instruction in self.get_instructions():
            if block.get_instruction(instruction.lineno) != instruction:
                return False
        return True

    # Checks if all successors are equal.
    def check_successor_equality(self):
        # Returns True if number of successors is less than 2.
        if len(self.successors) < 2:
            return True

        # Checks for equality of remaining successors.
        successors = list(self.successors.values())
        for idx in range(len(self.successors)-1):
            if not successors[idx].equals(successors[idx+1]):
                return False
        return True

    # Gets an instruction from the block.
    def _get_instruction(self, lineno):
        if lineno not in self._instructions:
            self._instructions[lineno] = Instruction(lineno)
        return self._instructions[lineno]

    # Adds variable reference at line number.
    def add_reference(self, lineno, variable):
        instruction = self._get_instruction(lineno)
        instruction.referenced.add(variable)

    # Adds variable defined at line number.
    def add_definition(self, lineno, variable):
        instruction = self._get_instruction(lineno)
        instruction.defined.add(variable)

    # Adds instruction type at line number.
    def add_instruction_type(self, lineno, instruction_type):
        instruction = self._get_instruction(lineno)
        instruction.instruction_type = instruction_type

    # Adds control at the line number.
    def add_instr_control(self, lineno, control):
        instruction = self._get_instruction(lineno)
        instruction.control = control

    # Adds indentation at the line number.
    def add_instr_indent(self, lineno, indentation):
        instruction = self._get_instruction(lineno)
        instruction.indentation = indentation

    # Adds instruction to instruction list.
    def add_instruction(self, instruction):
        self._instructions[instruction.lineno] = copy.deepcopy(instruction)

    # Adds instruction to multiline.
    def add_multiline_instructions(self, lineno, linenos):
        instruction = self._get_instruction(lineno)
        instruction.multiline.add(lineno)
        for group_lineno in linenos:
            instruction.multiline.add(group_lineno)

    # Adds a block as a successor and this block as its predecessor.
    def add_successor(self, block):
        if block != self:
            self.successors[block.label] = block
            block.predecessors[self.label] = self

    # Adds a block as a predecessor and this block as its successor.
    def add_predecessor(self, block):
        block.add_successor(self)

    # Sets successsors list to the provided successors list.
    def set_successors(self, successors):
        # Remove successors reference to this block.
        while self.successors:
            successor = self.get_first_successor()
            if self.label in successor.predecessors:
                successor.remove_predecessor(self)

        # Set new successors.
        self.successors = collections.OrderedDict()
        for successor in successors:
            self.add_successor(successor)

    # Returns new OrderedDict with block replaced.
    def _replace_block(self, blocklist, cur_block, new_block):
        new_blocklist = [(new_block.label, new_block)
                         if label == cur_block.label else (label, block)
                         for label, block in blocklist.items()]
        return collections.OrderedDict(new_blocklist)

    # Replaces a successor block with the provided block.
    def replace_successor(self, cur_block, new_block):
        if cur_block.label not in self.successors:
            raise ValueError('Successor not found')

        # Removes/replaces cur block from successors list.
        if self != new_block:
            self.successors = self._replace_block(self.successors, cur_block, new_block)
        else:
            self.remove_successor(cur_block)

        # Adds new predecessor to new block and removes from cur block.
        new_block.add_predecessor(self)
        cur_block.remove_predecessor(self)

    # Replaces a predecessor block with the provided block.
    def replace_predecessor(self, cur_block, new_block):
        if cur_block.label not in self.predecessors:
            raise ValueError('Predecessor not found')

        # Removes/replaces cur block from predecessor list.
        if self != new_block:
            self.predecessors = self._replace_block(self.predecessors, cur_block, new_block)
        else:
            self.remove_predecessor(cur_block)

        # Adds new successor to new block and removes from cur block.
        new_block.add_successor(self)
        cur_block.remove_successor(self)

    # Removes item from the OrderedDict.
    def _remove_item(self, blocklist, block):
        if blocklist and block.label in blocklist:
            return blocklist.pop(block.label)
        return None

    # Removes successor from successors if the successor exists.
    def remove_successor(self, block):
        self._remove_item(block.predecessors, self)
        self._remove_item(self.successors, block)

    # Removes predecessor from predecessors if the predecessor exists.
    def remove_predecessor(self, block):
        self._remove_item(block.successors, self)
        self._remove_item(self.predecessors, block)

    # Destroys the block by removing itself from successors and predecessors.
    def destroy(self):
        for predecessor in self.predecessors.values():
            predecessor.remove_successor(self)
        for successor in self.successors.values():
            successor.remove_predecessor(self)

    # Returns instruction at line number. Returns None if no instruction.
    def get_instruction(self, lineno):
        if lineno in self._instructions:
            return self._instructions[lineno]
        return None

    # Returns line numbers of instructions in a block.
    def get_instruction_linenos(self):
        return set(self._instructions.keys())

    # Returns instructions.
    def get_instructions(self):
        sorted_instructions = iter(sorted(self._instructions.items()))
        return [instruction for lineno, instruction in sorted_instructions]

    # Returns last instruction.
    def get_last_instruction(self):
        return max(self._instructions.keys())

    # Returns top successor.
    def get_first_successor(self):
        if self.successors:
            return list(self.successors.values())[0]
        return None

    # Returns top predecessor.
    def get_first_predecessor(self):
        if self.predecessors:
            return list(self.predecessors.values())[0]
        return None


class Block(BlockInterface):
    """
    Block representing body of the function within a CFG.
    """

    def __init__(self):
        super(self.__class__, self).__init__(self._get_label())

    # Returns next available label.
    def _get_label(self):
        return 'L%d' %Block._label_counter.increment()


class FunctionBlock(BlockInterface):
    """
    Block representing start of a function within a CFG.
    """

    def __init__(self, label):
        super(self.__class__, self).__init__(label)
        self.unimportant = set()
        self.blank_lines = set()
        self.comments = set()

    def __str__(self):
        string = '%s\n' %super(FunctionBlock, self).__str__()
        for sorted_block in self.get_sorted_blocks()[1:]:
            string += '%s\n' %str(sorted_block)
        return string

    def __eq__(self, other):
        # Check equality for the function block.
        if not super(FunctionBlock, self).__eq__(other):
            return False

        # Check equality for all blocks in the function.
        self_blocks = self.get_sorted_blocks()[1:]
        other_blocks = other.get_sorted_blocks()[1:]
        for self_block, other_block in zip(self_blocks, other_blocks):
            if self_block != other_block:
                return False
        return True

    # Returns the number of instructions.
    def get_linenos_in_func(self):
        instrs = []
        for block in self.get_sorted_blocks():
            instrs.extend(sorted(block.get_instruction_linenos()))
        return instrs

    # Gets function parameters.
    def get_function_parameters(self):
        if self._instructions:
            instr = self._instructions[sorted(list(self._instructions.keys()))[0]]
            if instr.instruction_type == InstructionType.FUNCTION_HEADER and instr.defined:
                return instr.defined
        return None

    # Gets topologically sorted blocks.
    def get_sorted_blocks(self):
        visited = set()
        sorted_blocks = []
        self._topological_sort_helper(sorted_blocks, visited, self)
        return sorted_blocks

    # Helper method to topologically sort blocks.
    def _topological_sort_helper(self, sorted_blocks, visited, current):
        visited.add(current.label)
        for key in reversed(list(current.successors.keys())):
            successor = current.successors[key]
            if successor.label not in visited:
                self._topological_sort_helper(sorted_blocks, visited, successor)
        sorted_blocks.insert(0, current)

    # Gets number of nodes.
    def _get_num_nodes(self, sorted_blocks):
        return len(sorted_blocks)

    # Gets the number of edges.
    def _get_num_edges(self, sorted_blocks):
        edges = 0
        for idx, block in enumerate(sorted_blocks):
            for successor in block.successors:
                edges += 1
        return edges

    # Gets the number of exits.
    def _get_num_exits(self, sorted_blocks, nodes):
        exits = 0
        for idx, block in enumerate(sorted_blocks):
            if len(block.predecessors) > 1 or (idx == nodes - 1):
                exits += 1
        return exits

    # Returns the cyclomatic complexity.
    def get_cyclomatic_complexity(self):
        sorted_blocks = self.get_sorted_blocks()
        nodes = self._get_num_nodes(sorted_blocks)
        edges = self._get_num_edges(sorted_blocks)
        exits = self._get_num_exits(sorted_blocks, nodes)
        return edges - nodes + 2 * exits
