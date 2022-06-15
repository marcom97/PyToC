#!/usr/bin/env python3

import sys

class Node(object):
    """
    Abstract base class for AST nodes

    Things to implement:
        __init__: Initialize attributes / children

        children: Method to return list of children. Alternatively, you can
                  look into __iter__ method, which allow nodes to be
                  iterable.
    """

    def children(self):
        """
        A sequence of all children that are Nodes
        """
        pass

    # Set of attributes for a given node
    attr_names = ()

class NodeVisitor(object):
    """
    A base NodeVisitor class for visiting MiniJava nodes.
    Define your own visit_X methods to, where X is the class
    name you want to visit with these methods.

    Refer to visit_Program, for example
    """

    def visit(self, node, offset=0):
        """
        Your compiler can call this method to traverse through your AST
        """
        method = 'visit_' + node.__class__.__name__
        node_type = (getattr(self, method, self.generic_visit)(node, offset))
        node.type = node_type
        return node_type

    def generic_visit(self, node, offset=0):
        """
        Default visit method that simply prints out given node's attributes,
        then traverses through its children. This is called if no explicit
        visitor function exists for a node.

        NOTE: A method within Node object with similar behaviour might be
              useful when debugging your project
        """
        lead = ' ' * offset

        output = lead + node.__class__.__name__ + ': '
        #print(node)
        #print(node.children())
        if node.attr_names:
            vlist = [getattr(node, n) for n in node.attr_names]
            output += ', '.join('%s' % v for v in vlist)

        print(output)

        for (child_name, child) in node.children():
            self.visit(child, offset=offset + 2)

    def visit_Program(self, node, offset=0):
        """
        Custom visit method for "Program" node
        """
        print("====== PROGRAM START ======")
        if node.func_decl != None:
            for func in node.func_decl[::-1]:
                self.visit(func, offset=2)
        self.visit(node.main_func, offset=2)
        print("====== PROGRAM END ======")

class AssignStmt(Node):
    def __init__(self, name, expr, coord=None):
        self.name = name
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('name', )

class PrintStmt(Node):
    def __init__(self, args_list, coord=None):
        self.args_list = args_list
        self.coord = coord

    def children(self):
        nodelist = []
        for i, arg in enumerate(self.args_list or []):
            nodelist.append(('args[%d]' % i, arg))
        return tuple(nodelist)

    attr_names = ()

class ExprStmt(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        return tuple([('expr', self.expr)])

class BinOp(Node):
    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None:
            nodelist.append(('left', self.left))
        if self.right is not None:
            nodelist.append(('right', self.right))
        return tuple(nodelist)

    attr_names = ('op', )

class Array(Node):
    def __init__(self, array_vals, coord=None):
        self.array_vals = array_vals
        self.coord = coord

    def children(self):
        nodelist = []
        for i, array_val in enumerate(self.array_vals or []):
            nodelist.append(('Array Value [%d]' % i, array_val))
        return nodelist

    attr_names = ()

class ArrayIndexing(Node):
    def __init__(self, array_name, array_index, coord=None):
        self.array_name = array_name
        self.array_index = array_index
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.array_name is not None:
            nodelist.append(('array_name', self.array_name))
        if self.array_index is not None:
            nodelist.append(('array_index', self.array_index))
        return tuple(nodelist)

    attr_names = ()

class Constant(Node):
    def __init__(self, type, value, coord=None):
        self.const_type = type
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('const_type', 'value')

class DeclStmt(Node):
    def __init__(self, name, type, expr=None):
        self.name = name
        self.type = type
        self.expr = expr

    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('name', )

class Formal(Node):
    def __init__(self, name, type, coord=None):
        self.name = name
        self.type = type
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None:
            nodelist.append(('type', self.type))
        return tuple(nodelist)

    attr_names = ('name', )

class IfStmt(Node):
    def __init__(self, cond, true_body, false_body, coord=None):
        self.cond = cond
        self.true_body = true_body
        self.false_body = false_body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None:
            nodelist.append(('cond', self.cond))
        if self.true_body is not None:
            nodelist.append(('true_body', self.true_body))
        if self.false_body is not None:
            nodelist.append(('false_body', self.false_body))
        return tuple(nodelist)

    attr_names = ()

class MethodDecl(Node):
    def __init__(self, name, ret_type, params, body, coord=None):
        self.name = name
        self.ret_type = ret_type
        self.params = params
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.ret_type is not None:
            nodelist.append(('ret_type', self.ret_type))
        if self.body is not None:
            nodelist.append(('body', self.body))
        if self.params is not None:
            nodelist.append(('params', self.params))
        return tuple(nodelist)

    attr_names = ('name', )

class ParamList(Node):
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.params or []):
            nodelist.append(('params[%d]' % i, child))
        return tuple(nodelist)

    attr_names = ()

class Program(Node):
    def __init__(self, main_func, func_decl, coord=None):
        self.main_func = main_func
        self.func_decl = func_decl

    def children(self):
        nodelist = []
        if self.func_decl is not None and len(self.func_decl) > 0:
            nodelist.append(('func_decl', self.func_decl))
        if self.main_func is not None:
            nodelist.append(('main_func', self.main_func))
        return tuple(nodelist)

    attr_names = ()

class RetStmt(Node):
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ()

class StmtList(Node):
    def __init__(self, stmt_lst, coord=None):
        self.stmt_lst = stmt_lst

    def children(self):
        nodelist = []
        for i, stmt in enumerate(self.stmt_lst or []):
            nodelist.append(('stmt[%d]' % i, stmt))
        return nodelist

    attr_names = ()

class FunctionCall(Node):
    def __init__(self, name, args_list, coord=None):
        self.name = name
        self.args_list = args_list
        self.coord = coord

    def children(self):
        nodelist = []
        for i, arg in enumerate(self.args_list or []):
            nodelist.append(('args[%d]' % i, arg))
        return tuple(nodelist)

    attr_names = ('name', )

class Type(Node):
    def __init__(self, name, arr_depth=0, coord=None):
        self.name = name
        self.coord = coord
        self.arr_depth = arr_depth

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('name', )

class UnaryOp(Node):
    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.expr is not None:
            nodelist.append(('expr', self.expr))
        return tuple(nodelist)

    attr_names = ('op', )

class WhileStmt(Node):
    def __init__(self, cond, body, coord=None):
        self.cond = cond
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None:
            nodelist.append(('cond', self.cond))
        if self.body is not None:
            nodelist.append(('body', self.body))
        return tuple(nodelist)

    attr_names = ()
