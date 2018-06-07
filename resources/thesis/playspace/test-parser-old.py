import ast

symbol_table = []

class Block:
   def __init__(self):
      self.inst = []
      self.succ = [] # List of immediate successors (blocks that follow).
      self.pred = [] # List of immediate predecesors.

class MyVisitor(ast.NodeVisitor):
   def visit_Str(self, node):
      print 'Found string on line %d: "%s"' % (1, node.s)



class MyTransformer(ast.NodeTransformer):
    def visit_Str(self, node):
        return ast.Str('str: ' + node.s)


node = ast.parse('''
favs = ['berry', 'apple']
name = 'peter'

for item in favs:
    print '%s likes %s' % (name, item)
''')

MyTransformer().visit(node)
MyVisitor().visit(node)
print node.__class__
print node.__dict__

for elem in node.body:
   print elem.__class__
   print elem.lineno

node = ast.fix_missing_locations(node)
print node.__class__
print node.__dict__
exec compile(node, '<string>', 'exec')

#import codegen
#print codegen.to_source(node)