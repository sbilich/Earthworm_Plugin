# File name: test_instruction.py
# Author: Nupur Garg
# Date created: 3/16/2017
# Python Version: 3.5


import unittest

from src.globals import *
from src.models.instruction import Instruction, InstructionType


# Test Instruction class.
class TestInstruction(unittest.TestCase):

    def test_to_string(self):
        instr1 = Instruction(lineno=1)
        instr2 = Instruction(lineno=3)
        instr3 = Instruction(lineno=4)

        # Initial string.
        self.assertEqual(str(instr1), '#1 |')
        self.assertEqual(str(instr2), '#3 |')
        self.assertEqual(str(instr3), '#4 |')

        # Test instruction 1: Multiline statement equating to y = (x + z).
        instr1.referenced.add('x')
        instr1.referenced.add('z')
        instr1.defined.add('y')
        instr1.multiline.add(1)
        instr1.multiline.add(2)
        self.assertEqual(str(instr1), '#1 | REF(x, z) DEF(y) MULTI(1, 2)')

        # Test instruction 3 (return x) with control line 1.
        instr3.control = 1
        instr3.referenced.add('x')
        instr3.instruction_type = InstructionType.RETURN
        self.assertEqual(str(instr3), '#4 | (#1) REF(x) - return')

    def test_equality(self):
        instr1 = Instruction(lineno=1)
        instr2 = Instruction(lineno=2)

        # Starting equality.
        self.assertFalse(instr1 == None)
        self.assertFalse(instr1 == 1)
        self.assertFalse(instr1 == instr2)

        # Tests line number equality.
        instr2.lineno = 1
        self.assertEqual(instr1, instr2)

        # Test instruction type equality.
        instr2.instruction_type = InstructionType.RETURN
        self.assertFalse(instr1 == instr2)
        instr2.instruction_type = None
        self.assertEqual(instr1, instr2)

        # Test reference equality.
        instr2.referenced.add('x')
        self.assertFalse(instr1 == instr2)
        instr2.referenced = set()
        self.assertEqual(instr1, instr2)

        # Test defined equality.
        instr2.defined.add('x')
        self.assertFalse(instr1 == instr2)
        instr2.defined = set()
        self.assertEqual(instr1, instr2)

        # Test control equality.
        instr2.control = 1
        self.assertFalse(instr1 == instr2)
        instr2.control = None
        self.assertEqual(instr1, instr2)

        # Test multiline equality.
        instr2.multiline.add(2)
        instr2.multiline.add(3)
        self.assertFalse(instr1 == instr2)
        instr2.multiline = set()
        self.assertEqual(instr1, instr2)


if __name__ == '__main__':
     unittest.main()
