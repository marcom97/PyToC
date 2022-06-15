#!/usr/bin/env python3
import sys

import SimplePythonAST as ast
from SimplePythonIRGen import IRGen, IRControl, TAC


def emit_headers():
    system_headers = ['stdio.h', 'stdlib.h', 'string.h']
    for header in system_headers:
        print('#include <{}>'.format(header))
    print()


class SPtoC(object):
    def __init__(self, IRGen):
        self.IRGen = IRGen

        self.binOps = {
            '+': '+',
            '-': '-',
            '*': '*',
            '/': '/',
            '%': '%',
            '==': '==',
            '<': '<',
            '<=': '<=',
            '>': '>',
            '>=': '>=',
            'and': '&&',
            'or': '||'
        }

        self.unaryOps = {
            '-': '-',
            'not': '!'
        }

        self.typeNames = {
            'int': 'int',
            'str': 'char*',
            'bool': 'int'
        }

        self.indentation = 0
        self.reg_to_expr = {}  # NOTE: The expr must be a fully valid C expr
        self.str_lens = {}

    def convert_operand(self, operand):
        """
        Returns the operand as a string suitable for C code gen
        """
        if operand.op_type == 'array':
            ops = ', '.join(map(self.convert_operand, operand.value))
            return '{' + ops + '}'
        elif operand.op_type == 'expr':  # Temporary
            return self.reg_to_expr[operand]

        # Constant
        # This may not always be C-compatible, we need to convert to a C constant!
        elif operand.op_type == 'str':
            return '"{}"'.format(operand.value.replace('"', '\\"'))
        elif operand.op_type == 'bool':
            return '1' if operand.value else '0'
        else:
            return str(operand.value)

    def emit_line(self, line):
        print('    ' * self.indentation, end='')
        print(line)

    def emitCcode(self, file):
        old_stdout = sys.stdout
        sys.stdout = file

        emit_headers()
        for element in self.IRGen.IR_lst:
            if element is None:
                continue

            if type(element) == IRControl:
                if element.ctl.startswith('END'):
                    self.emit_scope_end()
                    if element.ctl == 'ENDFUNC':
                        print()
                elif element.ctl == 'FUNC':
                    self.emit_func(element.data[0], element.data[1], element.data[2])
                elif element.ctl == 'IF':
                    self.emit_conditional('if', element.data)
                elif element.ctl == 'WHILE':
                    self.emit_conditional('while', element.data)
                elif element.ctl == 'ELSE':
                    self.emit_conditional('else', None)
                elif element.ctl == 'PRINT':
                    self.emit_print(element.data)
                elif element.ctl == 'RET':
                    self.emit_ret(element.data)
                elif element.ctl == 'BEGINLOOPCOND':
                    pass
                else:
                    self.emit_line(element)
            else:
                if element.op == 'DECL':
                    self.emit_decl(element.typeinfo, element.dest, element.src1, element.arr_depth)
                elif element.op == 'ASSIGN':
                    self.emit_assign(element.dest, element.src1, element.arr_depth)
                elif element.src2 is not None and element.op in self.binOps:
                    self.emit_binop(element.op, element.typeinfo, element.dest,
                                    element.src1, element.src2, element.arr_depth)
                elif element.src2 is None and element.op in self.unaryOps:
                    self.emit_unaryOp(element.op, element.dest, element.src1, element.arr_depth)
                elif element.op == 'CALL':
                    self.emit_call(element.dest, element.src1, element.src2)
                elif element.op == 'ARRAY_IDX':
                    self.emit_array_idx(element.dest, element.src1, element.src2)
                else:
                    self.emit_line(element)

        sys.stdout = old_stdout

    def emit_array_idx(self, dest, src1, src2):
        s1 = self.convert_operand(src1)
        s2 = self.convert_operand(src2)
        self.reg_to_expr[dest] = '{}[{}]'.format(s1, s2)

    def emit_call(self, dest, name, args_list):
        call_args = ''
        for call_idx, call_arg in enumerate(args_list):
            call_args += self.convert_operand(call_arg)

            if call_idx != len(args_list) - 1:
                call_args += ', '
        self.reg_to_expr[dest] = '{}({})'.format(name, call_args)

    def emit_unaryOp(self, operator, dest, src1, arr_depth):
        s1 = self.convert_operand(src1)
        op = self.unaryOps[operator]
        self.reg_to_expr[dest] = '{}{}'.format(op, s1)

    def get_str_len(self, string):
        if string.value in self.str_lens:
            return self.str_lens[string.value]

        if string.op_type == 'expr' or string.op_type == 'id':
            length_name = '{}_len'.format(string.value)
            value = self.convert_operand(string)
            self.emit_line('int {} = strlen({});'.format(length_name, value))
            self.str_lens[string.value] = length_name
            return length_name
        else:
            length = str(len(string.value))
            self.str_lens[string.value] = length
            return length

    def emit_binop(self, operator, type, dest, src1, src2, arr_depth):
        s1 = self.convert_operand(src1)
        s2 = self.convert_operand(src2)
        op = self.binOps[operator]

        if type == 'str':
            len1 = self.get_str_len(src1)
            len2 = self.get_str_len(src2)

            result_len = '{}_len'.format(dest.value)
            self.emit_line('int {} = {} + {};'.format(result_len, len1, len2))
            self.str_lens[dest.value] = result_len

            self.emit_line('char* {} = (char*) malloc({} + 1);'.format(dest.value, result_len))
            self.emit_line('strcpy({}, {});'.format(dest.value, s1))
            self.emit_line('strcat({}, {});'.format(dest.value, s2))

            self.reg_to_expr[dest] = dest.value
        else:
            if arr_depth > 0 and op == '+':
                
                loc = 'malloc('
                
                var1 = s1
                var2 = s2
                
                if s1.split(',')[0][0] == '{':
                    self.emit_line('{} {}{} = {};'.format(type, dest.value+'_1', '[]'*arr_depth, s1))
                    var1 = dest.value+'_1'
                
                sizeof_s1 = 'sizeof({})'.format(var1)
                sizeof_s1_0 = 'sizeof({}[0])'.format(var1)
                    
                loc += sizeof_s1+'+'
                
                if s2.split(',')[0][0] == '{':
                    self.emit_line('{} {}{} = {};'.format(type, dest.value+'_2', '[]'*arr_depth, s2))
                    var2 = dest.value+'_2'
                
                sizeof_s2 = 'sizeof({})'.format(var2)
                    
                loc += sizeof_s2 + ');\n'
                
                loc += '    ' * self.indentation
                loc += 'memcpy({}, {}, {});\n'.format(dest, var1, sizeof_s1)
                
                loc += '    ' * self.indentation
                loc += 'memcpy({}+{}/{}, {}, {})'.format(dest, sizeof_s1, sizeof_s1_0, var2, sizeof_s2)
                    
                self.reg_to_expr[dest] = loc
            else:
                self.reg_to_expr[dest] = '({} {} {})'.format(s1, op, s2)

    def emit_assign(self, dest, value, depth):
        assign_val = self.convert_operand(value)
        if dest is None:
            self.emit_line(assign_val + ';')
        else:
            if depth > 0:
                if assign_val[0] != 'm':
                    self.emit_line('{} = {};'.format(dest.value, assign_val))
                else:
                    array_ind = '*' * depth
                    lines = assign_val.split('\n')
                    lines[1] = lines[1][:11] + str(dest)[1:] + lines[1][11+len(str(value)):]
                    lines[2] = lines[2][:11] + str(dest)[1:] + lines[2][11+len(str(value)):]
                    self.emit_line('{}{} {} = {};'.format(self.typeNames[type], array_ind, dest.value, '\n'.join(lines)))
            else:    
                self.emit_line('{} = {};'.format(dest.value, assign_val))

    def emit_ret(self, expr):
        ret_expr = self.convert_operand(expr)
        self.emit_line('return {};'.format(ret_expr))

    def emit_func(self, name, ret_type, params):
        param_str = ''
        for idx, param in enumerate(params):
            param_str += '{} {}'.format(self.typeNames[param[1]], param[0])
            if idx != len(params) - 1:
                param_str += ', '
        loc = '{} {}({})'.format(self.typeNames[ret_type], name, param_str)
        self.emit_line(loc+' {')
        self.indentation += 1

    def emit_decl(self, type, dest, value, arr_depth=0):
        assign_val = self.convert_operand(value)
        if arr_depth > 0:
            if assign_val[0] != 'm':
                array_ind = '[]' * arr_depth
                self.emit_line('{} {}{} = {};'.format(self.typeNames[type], dest.value, array_ind, assign_val))
            else:
                array_ind = '*' * arr_depth
                lines = assign_val.split('\n')
                lines[1] = lines[1][:11] + str(dest)[1:] + lines[1][11+len(str(value)):]
                lines[2] = lines[2][:11] + str(dest)[1:] + lines[2][11+len(str(value)):]
                self.emit_line('{}{} {} = {};'.format(self.typeNames[type], array_ind, dest.value, '\n'.join(lines)))
                
        else:
            self.emit_line('{} {} = {};'.format(self.typeNames[type], dest.value, assign_val))

    def emit_conditional(self, name, condition):
        cond = '({}) '.format(self.convert_operand(condition)) if condition is not None else ''
        self.emit_line('{} {}'.format(name, cond) + '{')
        self.indentation += 1

    def emit_scope_end(self):
        self.indentation -= 1
        self.emit_line('}')

    def emit_print(self, args_lst):
        fmt_spec = ''
        print_args = ''
        for print_idx, print_var in enumerate(args_lst):
            if print_var[1] == 'int':
                fmt_spec += '%d'
            elif print_var[1] == 'str':
                fmt_spec += '%s'
            elif print_var[1] == 'bool':
                fmt_spec += '%d'

            print_args += self.convert_operand(print_var[0])

            if print_idx != len(args_lst) - 1:
                fmt_spec += ' '
                print_args += ', '

        self.emit_line('printf("{}\\n", {});'.format(fmt_spec, print_args))
