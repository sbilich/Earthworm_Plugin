from __future__ import print_function
import ast
import sys


# Visitor to generate CFG.
class CFGVisitor(ast.NodeVisitor):

   temp = None

   # Generates CFG.
   def generate(self, node):
      self.visit(node)
      print("returned: ", self.temp)
      return "TEMP"

   def visit_Str(self, node):
      self.temp = "testing"
      print('Found string on line %d: "%s"' %(1, node.s))


# Opens and reads file.
def readfile(filename):
   f = open(filename)
   return f.read()


# Prints AST structure.
def print_node(node, tabs):
   tab_str = '    '

   if not isinstance(node, ast.AST):
      return

   print('%s%s' %(tab_str*tabs, type(node)))
   for key, attr in node.__dict__.items():
      print('%s%s  ~~~  %s' %(tab_str*(tabs+1), key, attr))
      if isinstance(attr, list):
         for item in attr:
            print_node(item, tabs+2)
      else:
         print_node(attr, tabs+2)


# Prints AST structure.
def print_ast(node):
   for child_node in node.__dict__['body']:
      print_node(child_node, tabs=0)
      print('')


# Processes commandline arguments.
def process_args():
   if len(sys.argv) != 2:
      print('Usage: python test-parser.py <filename>')
   return sys.argv[1]


def main():
   filename = process_args()
   source = readfile(filename)
   node = ast.parse(source)
   # print_ast(node)

   # Call MyVisitor.
   visitor = CFGVisitor()
   cfg = visitor.generate(node)
   print(cfg)

   # Evaluates the AST structure.
   # exec compile(node, '<string>', 'exec')
   # print eval(compile(node, '<string>', mode='eval'))


if __name__ == '__main__':
   main()

