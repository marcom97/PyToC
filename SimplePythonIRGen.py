#!/usr/bin/env python3

def convert_to_string(obj):
    if isinstance(obj, list) or isinstance(obj, tuple):
        return '(' + ', '.join(map(convert_to_string, obj)) + ')'
    return str(obj)

class IRControl(object):
    """
    Represents a 'control' statement in the IR. For example, this can be
    a function declaration, while/if statement, or scope end marker.
    """

    def __init__(self, ctl, data=None):
        self.ctl = ctl
        self.data = data

    def __str__(self):
        return self.ctl + ' ' + convert_to_string(self.data)


class TAC(object):
    """
    Represents a single 3AC
    """

    def __init__(self, op, typeinfo, dest, src1, src2=None, arr_depth=0):
        self.op = op
        self.typeinfo = typeinfo
        self.dest = dest
        self.src1 = src1
        self.src2 = src2
        self.arr_depth=arr_depth

    def __str__(self):
        if self.arr_depth != 0:
            result = '{}({}, array_depth={}) {}, {}'.format(self.op, self.typeinfo, self.arr_depth, self.dest, self.src1)
        else:
            result = '{}({}) {}, {}'.format(self.op, self.typeinfo, self.dest, self.src1)
        if self.src2 is not None:
            result = result + ', ' + convert_to_string(self.src2)
        return result


class Operand(object):
    def __init__(self, op_type, value):
        self.op_type = op_type
        self.value = value

    def __str__(self):
        if self.op_type == 'array':
            return '[' + ', '.join(map(str, self.value)) + ']'

        string = str(self.value)
        if self.op_type == 'id' or self.op_type == 'expr':
            string = '%' + string
        elif self.op_type == 'str':
            string = "'" + string + "'"
        return string


class IRGen(object):
    """
    This Intermediate Representation converts Python code into
    a sequence of methods and main-method calls.
    """

    def __init__(self):
        """
        method_lst: list of IR code
        """
        self.IR_lst = []
        self.register_count = 0

    def generate(self, node):
        """
        Similar to 'typecheck' method from TypeChecker object
        """
        method = 'gen_' + node.__class__.__name__
        return getattr(self, method)(node)

    ################################
    ## Helper functions
    ################################
    def add_code(self, code):
        """
        Add 'code' to the IR_lst with correct spacing
        """
        self.IR_lst.append(code)

    def inc_var(self):
        """
        Increase the register count and return its value for use
        """
        self.register_count += 1
        return Operand('expr', '_t%d' % self.register_count)

    def reset_var(self):
        """
        Can reset the register_count to reuse them
        """
        self.register_count = 0

    def print_ir(self):
        """
        Loop through the generated IR code and print them out to stdout
        """
        for ir in self.IR_lst:
            print(ir)

    def gen_AssignStmt(self, node):
        expr = self.generate(node.expr)
        op = 'DECL' if node.isDecl else 'ASSIGN'
        tac = TAC(op, node.type.name, Operand('id', node.name), expr, None, node.type.arr_depth)
        self.add_code(tac)

    def gen_UnaryOp(self, node):
        expr = self.generate(node.expr)

        var = self.inc_var()
        self.add_code(TAC(node.op, node.type.name, var, expr, None, node.type.arr_depth))

        return var

    def gen_BinOp(self, node):
        # Left operand
        left = self.generate(node.left)
        # Right operand
        right = self.generate(node.right)

        reg = self.inc_var()
        self.add_code(TAC(node.op, node.type.name, reg, left, right, node.type.arr_depth))

        return reg

    def gen_Constant(self, node):
        return Operand(node.const_type, node.value)

    def gen_FunctionCall(self, node):
        # Generate all args
        args = node.children()
        parameters = []
        for (i, arg) in args:
            parameters.append(self.generate(arg))

        # call the function
        reg = self.inc_var()
        self.add_code(TAC('CALL', node.type.name, reg, node.name, parameters, node.type.arr_depth))

        return reg

    def gen_ExprStmt(self, node):
        expr = self.generate(node.expr)
        self.add_code(TAC('ASSIGN', 'void', None, expr))

    def gen_PrintStmt(self, node):
        args = []
        for arg in node.args_list:
            args.append((self.generate(arg), arg.type.name))

        self.add_code(IRControl('PRINT', args))

    def gen_IfStmt(self, node):
        cond = self.generate(node.cond)

        if node.true_body is not None:
            self.add_code(IRControl('IF', cond))
            self.generate(node.true_body)
            self.add_code(IRControl('ENDIF', cond))

        if node.false_body is not None:
            self.add_code(IRControl('ELSE', cond))
            self.generate(node.false_body)
            self.add_code(IRControl('ENDELSE', cond))

    def gen_WhileStmt(self, node):
        if node.body is not None:
            self.add_code(IRControl('BEGINLOOPCOND'))
            cond = self.generate(node.cond)

            self.add_code(IRControl('WHILE', cond))
            self.generate(node.body)
            self.add_code(IRControl('ENDWHILE', cond))


    def gen_MethodDecl(self, node):
        self.reset_var()

        params = [(param.name, param.type.name) for param in node.params.params]
        self.add_code(IRControl('FUNC', (node.name, node.ret_type.name, params)))

        self.generate(node.body)

        self.add_code(IRControl('ENDFUNC', node.name))

    def gen_Program(self, node):
        for decl in node.func_decl:
            self.generate(decl)

        self.generate(node.main_func)

    def gen_RetStmt(self, node):
        expr = self.generate(node.expr)
        self.add_code(IRControl('RET', expr))

    def gen_StmtList(self, node):
        for stmt in node.stmt_lst:
            self.generate(stmt)
            
    def gen_Array(self, node):
        avals = []
        for aval in node.array_vals:
            avals.append(self.generate(aval))
        return Operand('array', avals)

    def gen_ArrayIndexing(self, node):
        array_name = self.generate(node.array_name)
        array_index = self.generate(node.array_index)
        reg = self.inc_var()
        self.add_code(TAC('ARRAY_IDX', node.type.name, reg, array_name, array_index, node.type.arr_depth))
        return reg