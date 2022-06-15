#!/usr/bin/env python3

import argparse
from ply import yacc
from SimplePythonLexer import SimplePythonLexer
import SimplePythonAST as ast

# Get the token map from the lexer. This is required.
from SimplePythonLexer import tokens

class SimplePythonParser:
    """
    SimplePythonParser follows similar language defined in the grammar.txt file on our repository
    (https://mcsscm.utm.utoronto.ca/csc488_20221/group15/project/-/blob/master/sprint0/grammar.txt).
    """

    precedence = (
        ('left', 'AND'),
        ('left', 'EQOP', 'NEQ'),
        ('left', 'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ', 'MOD'),
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('right', 'UNARY')
    )

    # Let the parser know that symbol "program" is the starting point
    start = 'program'

    ################################
    ## Program (starting point)
    ################################

    def p_program(self, p):
        '''
        program : main_func_decl
                | func_decl_list main_func_decl
        '''
        if len(p) == 2:
            p[0] = ast.Program(p[1], [])
        else:
            p[0] = ast.Program(p[2], p[1])
        
    ################################
    ## Main Function
    ################################

    def p_main_func_decl(self, p):
        '''
        main_func_decl : DEF MAIN LPAREN RPAREN COLON NEWLINE block
        '''
        int_type = ast.Type("int")
        p[0] = ast.MethodDecl("main", int_type, ast.ParamList([]), p[7])

    ################################
    ## Function Declarations
    ################################

    def p_func_decl_list(self, p):
        '''
        func_decl_list : func_decl
                       | func_decl_list func_decl
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[2]]

    def p_func_decl(self, p):
        '''
        func_decl : DEF ID method_param ARROW type COLON NEWLINE block
        '''
        p[0] = ast.MethodDecl(p[2], p[5], p[3], p[8])

    ################################
    ## Formals / Parameters
    ################################

    def p_method_param(self, p):
        '''
        method_param : LPAREN formals_or_empty RPAREN
        '''
        p[0] = ast.ParamList(p[2])

    def p_formals_or_empty(self, p):
        '''
        formals_or_empty : formal_lst
                         | empty
        '''
        if len(p) == 1:
            p[0] = []
        else:
            p[0] = p[1]

    def p_formal_lst(self, p):
        '''
        formal_lst : formal_lst COMMA formal
                   | formal
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    def p_formal(self, p):
        '''
        formal : ID COLON type
        '''
        p[0] = ast.Formal(p[1], p[3])

    ################################
    ## Statements
    ################################

    def p_block(self, p):
        '''
        block : INDENT stmts_or_empty DEDENT
        '''
        p[0] = ast.StmtList(p[2])

    def p_statements_or_empty(self, p):
        '''
        stmts_or_empty : empty
                       | stmts_or_empty statement
        '''
        if len(p) == 2:
            p[0] = []
        else:
            p[0] = p[1] + [p[2]]

    def p_statement(self, p):
        '''
        statement : simple_stmt NEWLINE
                  | compound_stmt
        '''
        p[0] = p[1]

    def p_simple_statement(self, p):
        '''
        simple_stmt : assign_stmt
                    | print_stmt
                    | ret_stmt
        '''
        p[0] = p[1]

    def p_expr_statement(self, p):
        '''
        simple_stmt : expr
        '''
        p[0] = ast.ExprStmt(p[1])

    def p_assignment_statement(self, p):
        '''
        assign_stmt : ID EQ expr
        '''
        p[0] = ast.AssignStmt(p[1], p[3])
        
    def p_array(self, p):
        '''
        expr : LBRACK RBRACK
             | LBRACK array_values RBRACK
        '''
        if len(p) == 3:
            p[0] = ast.Array([])
        else:
            p[0] = ast.Array(p[2])
            
    def p_array_values(self, p):
        '''
        array_values : expr COMMA array_values
                     | expr
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]
        
    def p_print_statement(self, p):
        '''
        print_stmt : PRINT LPAREN args_list RPAREN
        '''
        p[0] = ast.PrintStmt(p[3])
        
    def p_function_call(self, p):
        '''
        fn_call : ID LPAREN args_list RPAREN 
                | ID LPAREN RPAREN
        '''
        if len(p) == 4:
            p[0] = ast.FunctionCall(p[1], [])
        else:
            p[0] = ast.FunctionCall(p[1], p[3])
            
    def p_args_list(self, p):
        '''
        args_list : expr COMMA args_list
                  | expr
        '''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = [p[1]] + p[3]
        
    def p_compound_statement(self, p):
        '''
        compound_stmt : if_else_stmt
                      | if_stmt
                      | while_stmt
        '''
        p[0] = p[1]

    def p_if_else_statement(self, p):
        '''
        if_else_stmt : IF expr COLON NEWLINE block ELSE COLON NEWLINE block
        '''
        p[0] = ast.IfStmt(p[2], p[5], p[9])
        
    def p_if_statement(self, p):
        '''
        if_stmt : IF expr COLON NEWLINE block
        '''
        p[0] = ast.IfStmt(p[2], p[5], None)

    def p_while_statement(self, p):
        '''
        while_stmt : WHILE expr COLON NEWLINE block
        '''
        p[0] = ast.WhileStmt(p[2], p[5])

    def p_return_statement(self, p):
        '''
        ret_stmt : RETURN expr
        '''
        p[0] = ast.RetStmt(p[2])


    ################################
    ## Expressions
    ################################

    def p_expr_binops(self, p):
        '''
        expr : expr PLUS expr
             | expr MINUS expr
             | expr MOD expr
             | expr TIMES expr
             | expr DIVIDE expr
             | expr LESS expr
             | expr LESSEQ expr
             | expr GREATER expr
             | expr GREATEREQ expr
             | expr EQOP expr
             | expr NEQ expr
             | expr AND expr
             | expr OR expr
        '''
        p[0] = ast.BinOp(p[2], p[1], p[3])

    def p_func_call_expr(self, p):
        '''
        expr : fn_call
        '''
        p[0] = p[1]
        
    def p_array_indexing(self, p):
        '''
        expr : ID LBRACK expr RBRACK
        '''
        p[0] = ast.ArrayIndexing(ast.Constant('id', p[1]), p[3])

    def p_expr_group(self, p):
        '''
        expr : LPAREN expr RPAREN
        '''
        p[0] = p[2]

    def p_expr_unary(self, p):
        '''
        expr : MINUS expr %prec UNARY
             | NOT expr %prec UNARY
        '''
        p[0] = ast.UnaryOp(p[1], p[2])

    def p_expr_number(self, p):
        '''
        expr : DECIMAL
        '''
        p[0] = ast.Constant('int', p[1])

    def p_expr_bool(self, p):
        '''
        expr : TRUE
             | FALSE
        '''
        p[0] = ast.Constant('bool', p[1] == 'True')

    def p_expr_id(self, p):
        '''
        expr : ID
        '''
        p[0] = ast.Constant('id', p[1])


    def p_expr_string(self, p):
        '''
        expr : STRINGLIT
        '''
        p[0] = ast.Constant('str', p[1])

    ################################
    ## Types
    ################################

    def p_type(self, p):
        '''
        type : base_type
        '''
        p[0] = ast.Type(p[1])

    def p_base_type(self, p):
        '''
        base_type : INT
                  | BOOLEAN
                  | STRING
        '''
        p[0] = p[1]

    ################################
    ## Misc
    ################################

    # This can be used to handle the empty production, by using 'empty'
    # as a symbol. For example:
    #
    #       optitem : item
    #               | empty
    def p_empty(self, p):
        'empty :'
        pass

    def p_error(self, p):
        raise SyntaxError("Syntax error at token {}".format(p))

    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = SimplePythonLexer()
        self.lexer.build()
        self.parser = yacc.yacc(module=self, **kwargs)

    def test(self, data):
        # self.lexer.test(data)
        result = self.parser.parse(data)
        visitor = ast.NodeVisitor()
        visitor.visit(result)
        return result

    def __init__(self):
        """
        Builds the Lexer and Parser
        """
        self.tokens = tokens
        self.lexer = SimplePythonLexer()
        self.lexer.build()
        self.parser = yacc.yacc(module=self)

    def parse(self, data):
        """
        Returns the root (Program) node of the AST, after parsing the file
        """
        return self.parser.parse(data)

if __name__ == "__main__":

    argparser = argparse.ArgumentParser(description='Take in the source code and parses it')
    argparser.add_argument('FILE', help='Input file with source code')
    args = argparser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    m = SimplePythonParser()
    m.build()
    m.test(data)
