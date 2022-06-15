#!/usr/bin/env python3

import argparse
import sys

from SimplePythonLexer import SimplePythonLexer
from SimplePythonParser import SimplePythonParser
from SimplePythonSymbolTable import GlobalSymbolTable
from SimplePythonTypeChecker import TypeChecker
from SimplePythonIRGen import IRGen
from SimplePythonIRtoC import SPtoC
from SimplePythonOptimizer import ConstOptimizer
import SimplePythonAST as ast

if __name__ == "__main__":

    # Python module "argparse" allows you to easily add commandline flags
    # to your program, which can help with adding debugging options, such
    # as '--verbose' and '--print-ast' as described below.
    #
    # Of course, this is entirely optional and not necessary, as long as
    # the compiler functions correctly.
    argparser = argparse.ArgumentParser(description='Take in the python source code and compile it')
    argparser.add_argument('FILE', help="Input file")
    argparser.add_argument('-o', '--output', action='store', default='a.c', help="Specify the name for the output file")
    argparser.add_argument('-a', '--print-ast', action='store_true', help="Print AST Nodes")
    argparser.add_argument('-p', '--parse-only', action='store_true', help="Stop after scanning and parsing the input")
    argparser.add_argument('-t', '--typecheck-only', action='store_true', help="Stop after typechecking")
    argparser.add_argument('-i', '--ir', action='store_true', help='Display IR')
    argparser.add_argument('-v', '--verbose', action='store_true', help="Provides additional output")
    argparser.add_argument('-O', '--optimize', action='store_true', help="Use optimizations (constant folding and peephole optimization)")
    args = argparser.parse_args()

    # Prints additional output if the flag is set
    if args.verbose:
        print("* Reading file " + args.FILE + "...\n")

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    if args.verbose:
        print("* Scanning and Parsing...\n")

    # Build and runs the parser to get AST
    parser = SimplePythonParser()
    root = parser.parse(data)

    # Use the default visitor (from W5) to go through the AST and print them
    # if the user provdes '--print-ast' flag
    if args.print_ast:
        visitor = ast.NodeVisitor()
        visitor.visit(root)

    # If user asks to quit after parsing, do so.
    if args.parse_only:
        quit()

    if args.verbose:
        print("* Typechecking...\n")

    typechecker = TypeChecker()
    typechecker.typecheck(root)

    if args.typecheck_only:
        quit()

    if args.verbose:
        print("* Generating IR...")
    
    irgen = IRGen()
    irgen.generate(root)
    
    if args.ir:
        if args.verbose:
            print()
            print('==================================')
            print('==================================')
            print('======== Generated IR ============')
            print('==================================')
            print('==================================')
            print()

        irgen.print_ir()

    if args.optimize:
        const_opt = ConstOptimizer(irgen.IR_lst)
        const_opt.optimize()

    try:
        out = open(args.output, 'w')
    except:
        out = sys.stdout

    sptoc = SPtoC(irgen)
    sptoc.emitCcode(out)
    