#!/usr/bin/env python3

import argparse
from ply import lex

# List of token names. This is always required
tokens = [
    'DECIMAL',
    'STRINGLIT',
    'ID',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'MOD',
    'LESS',
    'LESSEQ',
    'GREATER',
    'GREATEREQ',
    'EQOP',
    'NEQ',
    'COMMA',
    'COLON',
    'ARROW',
    'EQ',
    'LPAREN',
    'RPAREN',
    'LBRACK',
    'RBRACK',
    'INDENT',
    'DEDENT',
    'NEWLINE'
]

# Reserved words which should not match any IDs
reserved = {
    'int' : 'INT',
    'bool' : 'BOOLEAN',
    'def' : 'DEF',
    'main' : 'MAIN',
    'True' : 'TRUE',
    'False' : 'FALSE',
    'and' : 'AND',
    'or' : 'OR',
    'not' : 'NOT',
    'str' : 'STRING',
    'if' : 'IF',
    'else' : 'ELSE',
    'while' : 'WHILE',
    'print' : 'PRINT',
    'return' : 'RETURN'
}

# Add reserved names to list of tokens
tokens += list(reserved.values())


class SimplePythonLexer():
    def __init__(self):
        # Keeps track of the current indentation level
        self.current_indentation = 0
        self.remaining_indentation = 0 # Needed to force PLY to emit multiple tokens
        self.indentation_type = 'INDENT'

    # A string containing ignored characters (spaces and tabs)
    t_ignore = ' \t'

    # Regular expression rule with some action code
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MOD = r'%'
    t_LESSEQ = r'\<='
    t_LESS = r'\<'
    t_GREATEREQ = r'\>='
    t_GREATER = r'\>'
    t_EQOP = r'\=='
    t_NEQ = r'\!='
    t_COMMA = r','
    t_COLON = r':'
    t_ARROW = r'->'
    t_EQ = r'\='
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACK = r'\['
    t_RBRACK = r'\]'

    # A regular expression rule with some action code
    def t_DECIMAL(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_STRINGLIT(self, t):
        r'\'(\\\'|[^\'])*\' | "(\\"|[^"])*"'
        # Clean up outer quotes and remove backslashes before quotes
        t.value = t.value[1:-1].replace("\\'", "'").replace('\\"', '"')
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'ID') # Check for reserved words
        return t

    def t_INDENTATION(self, t):
        r'\s*\n(\ {4})*'
        length = len(t.value)

        # Check if this is the first run
        if self.remaining_indentation == 0:
            lines = t.value.split('\n')
            spaces = len(lines[-1])
            t.lexer.lineno += len(lines) - 1
            indentation = spaces//4
            if indentation > self.current_indentation:
                self.indentation_type = 'INDENT'
                self.remaining_indentation = indentation - self.current_indentation
            else:
                self.indentation_type = 'DEDENT'
                self.remaining_indentation = self.current_indentation - indentation
            self.current_indentation = indentation
            t.type = 'NEWLINE'
            t.value = '\n'
        else:
            t.type = self.indentation_type
            t.value = self.current_indentation
            self.remaining_indentation -= 1

        # Repeat if we have more indentation tokens remaining
        if self.remaining_indentation > 0:
            t.lexer.lexpos -= length

        return t

    # Define a rule so we can track line numbers. DO NOT MODIFY
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # Error handling rule. DO NOT MODIFY
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Build the lexer. DO NOT MODIFY
    def build(self, **kwargs):
        self.tokens = tokens
        self.lexer = lex.lex(module=self, **kwargs)

    # Test the output. DO NOT MODIFY
    def test(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            print(tok)


# Main function. DO NOT MODIFY
if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Take in the simplePython source code and perform lexical analysis.')
    parser.add_argument('FILE', help="Input file with simplePython source code")
    args = parser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    m = SimplePythonLexer()
    m.build()
    m.test(data)
