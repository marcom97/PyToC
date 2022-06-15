#!/usr/bin/env python3

class ParseError(Exception): pass

class SymbolTable(object):
    """
    Base symbol table class
    """

    def __init__(self):
        self.scope_stack = [dict()]

    def push_scope(self):
        self.scope_stack.append(dict())

    def pop_scope(self):
        assert len(self.scope_stack) > 1
        self.scope_stack.pop()

    def declare_variable(self, name, type, line_number):
        """
        Add a new variable.
        Need to do duplicate variable declaration error checking.
        """
        if name in self.scope_stack[-1]:
            raise ParseError("Redeclaring variable named \"" + name + "\"", line_number)
        self.scope_stack[-1][name] = type

    def lookup_variable(self, name, line_number):
        """
        Return the type of the variable named 'name', or throw
        a ParseError if the variable is not declared in the scope.
        """
        # You should traverse through the entire scope stack
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

class FunctionSymbolTable(SymbolTable):
    """
    The class for the symbol table for a function, which stores the interfaces of
    its methods and class variables
    """

    def __init__(self, func_name):
        super().__init__()
        self.func_name = func_name

class GlobalSymbolTable(SymbolTable):
    """
    The class for the symbol table for the global scope, which
    stores information about classes.
    """

    def __init__(self):
        # Dictionary from class names to symbol tables for each of the
        # top-level funcs in the program
        super().__init__()
        self.funcs = dict()

    def declare_func(self, func_name, types, line_number):
        """
        Declare a new function in the global scope.
        Need to do duplicate-function-declaration error checking.
        """
        if func_name in self.funcs:
            raise ParseError("Redeclaring function named \"" + func_name + "\"", line_number)
        self.funcs[func_name] = types

    def lookup_func(self, func_name, line_number):
        """
        Return the symbol table for the class named 'class_name', or
        throw a ParseError if the class isn't declared
        """
        if func_name in self.funcs:
            return self.funcs[func_name]

        raise ParseError("Referencing undefined function \"" + func_name + "\"", line_number)