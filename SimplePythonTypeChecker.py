#!/usr/bin/env python3

from SimplePythonSymbolTable import SymbolTable, GlobalSymbolTable, FunctionSymbolTable, ParseError
import SimplePythonAST as ast
import sys

sys.tracebacklimit = 0

class TypeChecker(object):
    """
    Uses the same visitor pattern as ast.NodeVisitor, but modified to
    perform type checks, as well as to generate the symbol table.

    This TypeChecker is setup in a way that Program and FuncDecl visitors
    will return its symbol table, while other visitor functions will
    return the type of the associated object. This is so that we can use
    the return value of typecheck directly to check its type. If the object
    is not associated with either symbol table or a type, then it will return
    None.

    Alternatively, you could implement a method which returns the
    type of the object in question into the Node object.

    Additionally, this is not the only way of implementing visitor either.
    You could implement visitor design pattern straight into Node object
    rather than having a separate visitor.

    Finally, IR (Intermediate Representation) generators use the similar
    visitor pattern, and it may also require the symbol table which is
    being generated here. You should bare this in mind for sprint2 as you
    design your compiler to support type-checking and IR generator.

    NOTE: This Typechecker is as incomplete as the miniJava Parser -- meaning
          lack of features from parsers will impact this typechecker as well!
          (i.e., no method call, can only declare one method at a time, etc...)
    """

    def __init__(self):
        self.current_func = None

    def typecheck(self, node, st=None):
        method = 'check_' + node.__class__.__name__
        node.type = getattr(self, method, self.generic_typecheck)(node, st)
        return node.type

    def generic_typecheck(self, node, st=None):
        if node is None:
            return ast.Type('None')
        else:
            return ast.Type(''.join(self.typecheck(c, st).name for c_name, c in node.children()))

    def eq_type(self, t1, t2):
        """
        Helper function to check if two given type node is that of the
        same type. Precondition is that both t1 and t2 are that of class Type
        """
        if not isinstance(t1, ast.Type) or not isinstance(t2, ast.Type):
            raise ParseError("eq_type invoked on non-type objects")
        return t1.name == t2.name

    def check_AssignStmt(self, node, st):
        var_type = st.lookup_variable(node.name, node.coord)
        expr_type = self.typecheck(node.expr, st)

        if var_type is None:
            st.declare_variable(node.name, expr_type, node.coord)
            node.isDecl = True
        elif not self.eq_type(var_type, expr_type):
            raise ParseError("Variable \"" + node.name + "\" has the type",
                             var_type.name, "but is being assigned the type",
                             expr_type.name)
        else:
            node.isDecl = False

        return expr_type

    def check_BinOp(self, node, st):
        """
        NOTE
        You should also check if the type of the left and right operation
        makes sense in the context of the operator (ie., you should not be
        able to add/subtract/multiply/divide strings or booleans). In this
        example, it only checks if the left and right expressions are of the
        same type, but that won't be sufficient for your project.
        """

        left_type = self.typecheck(node.left, st)
        right_type = self.typecheck(node.right, st)
        if not self.eq_type(left_type, right_type):
            raise ParseError("Left and right expressions are of different type", node.coord)
        elif node.op in ['-', '*', '/', '%'] and left_type.name != "int":
            raise ParseError(node.op + " is only valid for integer operands", node.coord)
        elif node.op == '+' and (left_type.arr_depth > 0 or right_type.arr_depth > 0) and left_type.arr_depth != right_type.arr_depth:
            print(left_type.arr_depth)
            print(right_type.arr_depth)
            raise ParseError(node.op + " is only valid for arrays of same depth and type", node.coord)
        elif node.op == '+' and (left_type.name != "int" and left_type.name != "str"):
            raise ParseError(node.op + " is only valid for integer operands or string operands", node.coord)
        elif node.op in ['<', '<=', '>', '>=', '=='] and left_type.name != "int":
            raise ParseError(node.op + " is only valid for integer operands", node.coord)
        elif node.op in ['and', 'or'] and left_type.name != "bool":
            raise ParseError(node.op + " is only valid for boolean operands", node.coord)

        if node.op in ['-', '*', '/', '%']:
            return ast.Type("int")
        elif node.op == '+' and left_type.arr_depth > 0:
            return left_type
        elif node.op == '+' and left_type.name == 'int':
            return ast.Type("int")
        elif node.op == '+' and left_type.name == 'str':
            return ast.Type("str")
        elif node.op in ['!', '<', '<=', '>', '>=', '==', 'and', 'or']:
            return ast.Type("bool")

    def check_MethodDecl(self, node, st):
        st.declare_func(node.name, ([param.type for param in node.params.params], node.ret_type), node.coord)

        # Store the return type, so we can check against it when we encounter a return statement
        self.current_func = node.name

        # We might want to find a cleaner way of separating parameters from other function scopes.
        # Right now, we're already creating a scope for each StmtList, so we
        # end up creating two scopes.
        st.push_scope()
        # Go through the parameters
        if node.params is not None:
            self.typecheck(node.params, st)
        # Go through the method body and type check each statements
        if node.body is not None:
            self.typecheck(node.body, st)
        st.pop_scope()

        return ast.Type('None')

    def check_FunctionCall(self, node, st):
        """
        Type-check all args and make sure that they all match with the parameters
        of the function. Then return the type for its return statement.
        """
        param_types, ret_type = st.lookup_func(node.name, node.coord)
        if len(param_types) != len(node.args_list):
            raise ParseError('The function "' + node.name + '" was called with ',
                             len(node.args_list), ' args, but it expected ',
                             len(param_types), node.coord)
        for i in range(len(node.args_list)):
            arg_type = self.typecheck(node.args_list[i], st)
            if not self.eq_type(arg_type, param_types[i]):
                raise ParseError('Mismatch of argument types when calling "' + node.name + '" ', node.coord)

        return ret_type


    def check_Constant(self, node, st):
        """
        Returns the type of the constant. If the constant refers to
        some kind of id, then we need to find if the id has been declared.
        """
        if node.const_type == 'id':
            res = st.lookup_variable(node.value, node.coord)
            if res is None:
                raise ParseError("Referencing undefined variable \"" + node.value + "\"", node.coord)
            else:
                return res
        return ast.Type(node.const_type)

    def check_DeclStmt(self, node, st):
        st.declare_variable(node.name, node.type, node.coord)
        if node.expr is not None:
            expr_type = self.typecheck(node.expr, st)
            if not self.eq_type(expr_type, node.type):
                raise ParseError("Mismatch of declaration type", node.coord)

        return node.type

    def check_IfStmt(self, node, st):
        """
        Check if the condition expression is a boolean type, then
        recursively typecheck all of if statement body.

        Note that most of the programming languages, such as C, Java, and
        Python, all accepts ints/floats for conditions as well. That is
        something you should consider for your project.
        """

        cond_type = self.typecheck(node.cond, st)
        if not self.eq_type(ast.Type('bool'), cond_type):
            raise ParseError("If statement requires boolean as its condition", node.coord)

        if node.true_body is not None:
            self.typecheck(node.true_body, st)
        if node.false_body is not None:
            self.typecheck(node.false_body, st)

        return ast.Type('None')

    def check_ParamList(self, node, st):
        """
        Add all of the parameters to the symbol table
        """
        # Alternatively, you could have a separate check method for
        # "Formal" class, instead of declaring them as a variable here.
        for param in node.params:
            st.declare_variable(param.name, param.type, param.coord)
        return ast.Type('None')

    def check_Program(self, node, st=None):
        """
        Generate global symbol table. Recursively typecheck its classes and
        add its class symbol table to itself.
        """
        # Generate global symbol table
        global_st = GlobalSymbolTable()

        # Iterate through the declared functions, perform typecheck on them
        # and add them to the global symbol table
        for decl in node.func_decl:
            self.typecheck(decl, global_st)

        self.typecheck(node.main_func, global_st)

        return global_st

    def check_RetStmt(self, node, st):
        # Check if the type of the return statement matches the return type
        # of the method
        expr_type = self.typecheck(node.expr, st)
        curr_ret_type = st.lookup_func(self.current_func, node.coord)
        if not self.eq_type(expr_type, curr_ret_type[1]):
            raise ParseError("Mismatch of return type within method \"" +
                             self.current_func + "\"", node.coord)
        return expr_type

    def check_StmtList(self, node, st):
        """
        Iterate through all the statements and perform typecheck on them.
        StmtList acts similarily to a new scope -- it should push additional
        scope to the scope_stack and pop the scope when done.
        """
        st.push_scope()
        for stmt in node.stmt_lst:
            self.typecheck(stmt, st)
        st.pop_scope()

        # List itself does not have any type
        return ast.Type('None')

    def check_Type(self, node, st):
        return node

    def check_UnaryOp(self, node, st):
        """
        NOTE
        Similar to BinOp, you should check if the unary operator is
        applicable with the type returned by the expression
        (i.e., '-' could only make sense if the expression is an integer)
        """
        type = self.typecheck(node.expr, st)
        if node.op == 'not' and type.name != 'bool':
            raise ParseError(node.op + " is only valid for boolean operands", node.coord)
        elif node.op == '-' and type.name != 'int':
            raise ParseError(node.op + " is only valid for integer operands", node.coord)

        return type

    def check_WhileStmt(self, node, st):
        """
        First, check if the condition returns the type boolean.
        Then, push another scope into the scope stack and perform typecheck
        within the while statement body.
        """

        cond_type = self.typecheck(node.cond, st)
        if not self.eq_type(ast.Type('bool'), cond_type):
            raise ParseError("While statement requires boolean as its condition", node.coord)

        if node.body is not None:
            self.typecheck(node.body, st)

        return ast.Type('None')
        
    def check_Array(self, node, st):
    
        arr_type = None
        
        if node.array_vals != []:
            arr_type = self.typecheck(node.array_vals[0], st)
            
            for aval in node.array_vals:
                aval_type = self.typecheck(aval, st)
                if not self.eq_type(aval_type, arr_type):
                    raise ParseError("Array is not of a homogenous type", node.coord)
                    
            #arr_type.name = "Array: " + arr_type.name
            
            return ast.Type(arr_type.name, arr_type.arr_depth+1)
        else:
            return ast.Type('int', 1)
        
    def check_ArrayIndexing(self, node, st):

        arr_type = None
        idx_type = None
        
        try:
            arr_type = st.lookup_variable(node.array_name.value, node.coord)
            idx_type = self.typecheck(node.array_index, st)
        except:
            pass
            
        if arr_type == None or arr_type.arr_depth == 0:
            raise ParseError(node.array_name + " is not an array", node.coord)
            
        if idx_type == None or not self.eq_type(ast.Type('int'), idx_type) or idx_type.arr_depth > 0:
            raise ParseError(node.array_index + " is not an integer", node.coord)
            
        return ast.Type(arr_type.name, arr_type.arr_depth-1)
