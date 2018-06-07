# File name: instruction.py
# Author: Nupur Garg
# Date created: 12/25/2016
# Python Version: 3.5


from enum import Enum

from src.globals import *


class InstructionType(Enum):
    __order__ = ('RETURN, ELSE, FUNCTION_HEADER, '
                 'TRY, EXCEPT, FINALLY, RAISE, '
                 'PASS, BREAK, CONTINUE, FOR, WHILE')
    RETURN = 1
    ELSE = 2
    FUNCTION_HEADER = 3
    TRY = 4
    EXCEPT = 5
    FINALLY = 6
    RAISE = 7
    PASS = 8
    BREAK = 9
    CONTINUE = 10
    FOR = 11
    WHILE = 12


class Instruction(object):
    """
    Instruction within a block.

    instruction_type: obj
        InstructionType of instruction to enable specific functionality.
    referenced: set(str)
        Variables referenced in the instruction.
    defined: set(str)
        Variables defined in the block.
    indentation: int
        Indentation level.
    lineno: int
        Line number.
    control: int
        Line number controling this instruction.
    """

    def __init__(self, lineno):
        self.instruction_type = None
        self.lineno = lineno
        self.referenced = set()
        self.defined = set()
        self.indentation = None
        self.control = None
        self.multiline = set()

    def __str__(self):
        string = '#%d |' %self.lineno
        if self.control:
            string += ' (#%d)' %(self.control)
        if self.referenced:
            string += ' REF(%s)' %(', '.join(sorted(self.referenced)))
        if self.defined:
            string += ' DEF(%s)' %(', '.join(sorted(self.defined)))
        if self.multiline:
            multiline_str = sorted([str(lineno) for lineno in self.multiline])
            string += ' MULTI(%s)' %(', '.join(multiline_str))
        if self.instruction_type:
            instr_name = ' '.join(self.instruction_type.name.lower().split('_'))
            string += ' - %s' %(instr_name)
        return string

    def __eq__(self, other):
        if not other or not isinstance(other, self.__class__):
            return False

        return (self.instruction_type == other.instruction_type and
                self.lineno == other.lineno and
                self.referenced == other.referenced and
                self.defined == other.defined and
                self.control == other.control and
                self.multiline == other.multiline)

    def __ne__(self, other):
        return not self == other
