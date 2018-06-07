# File name: blockinfo.py
# Author: Nupur Garg
# Date created: 2/1/2017
# Python Version: 3.5


from src.globals import *


class NodeInformation(ABC):
    """
    Abstract class containing NodeInformation.
    """

    def __ne__(self, other):
        return not self == other

    @abstractmethod
    def __eq__(self, other):
        pass

    # Determines if two dictionaries are equal to each other.
    def _is_dict_equal(self, dictA, dictB):
        if sorted(dictA.keys()) != sorted(dictB.keys()):
            return False

        for key in dictA.keys():
            if dictA[key] != dictB[key]:
                return False
        return True

    # Finds dictA DIFF dictB for the common keys.
    @staticmethod
    def diff_common_keys(dictA, dictB):
        result = {}
        for key, valueset in dictA.items():
            if key in dictB:
                result[key] = valueset.symmetric_difference(dictB[key])
        return result

    # Finds diffA - diffB.
    @staticmethod
    def sub(dictA, dictB):
        result = {}
        for key, valueset in dictA.items():
            result[key] = valueset
            if key in dictB:
                result[key] = valueset - dictB[key]
        return result

    # Finds dictA UNION dictB.
    @staticmethod
    def union(dictA, dictB):
        result = {}
        keys = set().union(*[dictA, dictB])
        for key in keys:
            result[key] = set()
            if key in dictA:
                result[key] = result[key].union(dictA[key])
            if key in dictB:
                result[key] = result[key].union(dictB[key])
        return result


class ReachingDefinitions(NodeInformation):
    """
    Reaching definitions for node (either Block or Instruction).
    """

    def __init__(self):
        self.gen = {}
        self.kill = {}
        self.in_node = {}
        self.out_node = {}

    def __eq__(self, other):
        if other is None or type(other) != type(self):
            return False

        return (self._is_dict_equal(self.gen, other.gen) and
                self._is_dict_equal(self.kill, other.kill) and
                self._is_dict_equal(self.in_node, other.in_node) and
                self._is_dict_equal(self.out_node, other.out_node))


class LiveVariables(NodeInformation):
    """
    Live variables for node (either Block or Instruction).
    """

    def __init__(self):
        self.defined = set()
        self.referenced = set()
        self.in_node = set()
        self.out_node = set()

    def __eq__(self, other):
        if other is None or type(other) != type(self):
            return False

        return (self.defined == other.defined and
                self.referenced == other.referenced and
                self.in_node == other.in_node and
                self.out_node == other.out_node)


class FunctionBlockInformation(object):
    """
    Information for a function block.
    """

    def __init__(self):
        self._block_info_class = None   # Type of NodeInformation child class.
        self._blocks = None             # List of blocks.
        self._block_info = None         # Map {Block : NodeInformation}.
        self._instructions = None       # Map {lineno: Instruction}
        self._instruction_info = None   # Map {lineno: NodeInformation}.

    def __ne__(self, other):
        return not self == other

    def __eq__(self, other):
        if other is None or type(other) != type(self):
            return False

        if (type(other._block_info_class) != type(other._block_info_class) or
            len(other._blocks) != len(other._blocks) or
            other._block_info.keys() != other._block_info.keys()):
            return False

        for block, block_info in self.blocks():
            if block_info != other.get_block_info(block):
                return False

        for instr, block_info in self.instructions():
            if block_info != other.get_instruction_info(instr.lineno):
                return False

        return True

    # Initializes FunctionBlockInformation.
    def init(self, func_block, block_info_class):
        assert issubclass(type(block_info_class()), NodeInformation)

        self._blocks = []
        self._block_info = {}
        self._instructions = {}
        self._instruction_info = {}
        self._block_info_class = block_info_class

        for block in func_block.get_sorted_blocks():
            self._blocks.append(block)
            self._block_info[block.label] = block_info_class()
            for instr in block.get_instructions():
                self._instructions[instr.lineno] = instr
                self._instruction_info[instr.lineno] = block_info_class()

    # Returns ordered list of (Block, NodeInformation) tuples.
    def blocks(self):
        return [(block, self._block_info[block.label])
                for block in self._blocks]

    # Returns ordered list of (Instruction, NodeInformation) in tuples.
    def instructions(self):
        return [(instr, self._instruction_info[lineno])
                for lineno, instr in self._instructions.items()]

    # Returns NodeInformation for a given Block.
    def get_block_info(self, block):
        return self._block_info[block.label]

    # Gets instruction for a given line number.
    def get_instruction(self, lineno):
        if lineno in self._instructions:
            return self._instructions[lineno]
        return None

    # Returns NodeInformation for a given line number.
    def get_instruction_info(self, lineno):
        if lineno in self._instruction_info:
            return self._instruction_info[lineno]
        return None
