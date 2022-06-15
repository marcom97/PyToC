import sys
from SimplePythonIRGen import TAC, IRControl, Operand


class SimplePythonOptimizer(object):
    def __init__(self, irlst):
        self.irlst = irlst

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

    def optimize(self):
        for i, ir in enumerate(self.irlst):
            if ir is None:
                continue

            new_ir = self.optimize_line(ir)
            self.irlst[i] = new_ir

    def optimize_line(self, ir):
        """
        Given a single IR line, this function returns either an optimized line to replace it
         or None to remove the line
        """
        pass


class ConstOptimizer(SimplePythonOptimizer):
    def __init__(self, irlst):
        super().__init__(irlst)
        self.var_to_value = {}
        self.constant_types = {'int', 'str', 'bool', 'array'}
        self.unknown_context_depth = 0
        self.foldable_context_depth = 0
        self.should_eliminate = False

    def fold_operand(self, operand):
        # Disable all folding if we're currently in an unpredictable context
        if self.unknown_context_depth > 0:
            return operand

        if operand.op_type == 'id' and operand.value in self.var_to_value:
            return self.var_to_value[operand.value]
        return operand

    def optimize_line(self, ir):
        # Immediately eliminate if we're in a false if context
        if self.should_eliminate and (not isinstance(ir, IRControl) or (not ir.ctl.endswith('IF') and
                                                                        not ir.ctl.endswith('ELSE'))):
            return None

        if isinstance(ir, IRControl):
            if ir.ctl == 'RET':
                ir.data = self.fold_operand(ir.data)
            elif ir.ctl == 'IF':
                ir = self.optimize_if(ir, False)
            elif ir.ctl == 'ENDIF' or ir.ctl == 'ENDELSE':
                ir = self.optimize_endif(ir)
            elif ir.ctl == 'ELSE':
                ir = self.optimize_if(ir, True)
            elif ir.ctl == 'BEGINLOOPCOND':
                self.unknown_context_depth += 1
            elif ir.ctl == 'ENDWHILE':
                self.unknown_context_depth -= 1
            elif ir.ctl == 'PRINT':
                ir.data = [(self.fold_operand(tup[0]), tup[1]) for tup in ir.data]
            elif ir.ctl == 'ENDFUNC':
                self.var_to_value = {}
            return ir
        else:
            # Check if we're currently in an unpredictable context and if so,
            # stop any further folding/propagation on this variable
            if self.unknown_context_depth > 0:
                if ir.dest is not None and ir.dest.value in self.var_to_value:
                    del self.var_to_value[ir.dest.value]
            elif ir.op == 'DECL':
                ir = self.optimize_assign(ir)
            elif ir.op == 'ASSIGN':
                ir = self.optimize_assign(ir)
            elif ir.src2 is not None and ir.op in self.binOps:
                ir = self.optimize_binop(ir)
            elif ir.src2 is None and ir.op in self.unaryOps:
                ir = self.optimize_unaryOp(ir)
            elif ir.op == 'CALL':
                ir.src2 = [self.fold_operand(x) for x in ir.src2]
            elif ir.op == 'ARRAY_IDX':
                ir = self.optimize_array_idx(ir)
            return ir

    def optimize_assign(self, ir):
        value = self.fold_operand(ir.src1)
        ir.src1 = value
        if ir.dest is not None:
            if value.op_type in self.constant_types:
                self.var_to_value[ir.dest.value] = value
        return ir

    def optimize_binop(self, ir):
        s1 = self.fold_operand(ir.src1)
        s2 = self.fold_operand(ir.src2)

        if s1.op_type not in self.constant_types or s2.op_type not in self.constant_types:
            ir.src1 = s1
            ir.src2 = s2
            return ir

        ir.dest.value = eval('s1 {} s2'.format(ir.op), {}, {'s1': s1.value, 's2': s2.value})
        ir.dest.op_type = 'array' if isinstance(ir.dest.value, list) else ir.typeinfo
        return None

    def optimize_unaryOp(self, ir):
        expr = self.fold_operand(ir.src1)

        if expr.op_type not in self.constant_types:
            return ir

        ir.dest.value = eval('{} {}'.format(ir.op, expr.value))
        ir.dest.op_type = ir.typeinfo
        return None

    def optimize_array_idx(self, ir):
        array = self.fold_operand(ir.src1)
        idx = self.fold_operand(ir.src2)

        if idx.op_type not in self.constant_types:
            return ir

        ir.src2 = idx

        # Raise warning if index is negative
        if idx.value < 0:
            print()
            error = 'The array "{}" was accessed with a negative index of {}'
            raise IndexError(error.format(ir.src1.value, idx.value))

        if array.op_type not in self.constant_types:
            return ir

        # Check for potential out-of-bounds access
        if idx.value >= len(array.value):
            print()
            error = 'The array "{}" was accessed with an index of {}, but it has a size of {}'
            raise IndexError(error.format(ir.src1.value, idx.value, len(array.value)))

        result = array.value[idx.value]
        if result.op_type not in self.constant_types:
            return ir
        ir.dest.value = result.value
        ir.dest.op_type = result.op_type
        return None

    def optimize_if(self, ir, is_else):
        cond = self.fold_operand(ir.data)
        ir.data = cond
        if cond.op_type not in self.constant_types:
            self.unknown_context_depth += 1
            if self.should_eliminate:
                return None
        else:
            self.foldable_context_depth += 1
            real_cond = cond.value if not is_else else not cond.value
            if not real_cond:
                self.should_eliminate = True
            return None

        return ir

    def optimize_endif(self, ir):
        cond = self.fold_operand(ir.data)
        ir.data = cond
        if cond.op_type not in self.constant_types:
            self.unknown_context_depth -= 1
            if self.should_eliminate:
                return None
        else:
            self.foldable_context_depth -= 1
            if self.foldable_context_depth == 0:
                self.should_eliminate = False
            return None

        return ir
