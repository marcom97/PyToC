# PyToC
A simple compiler that parses a limited subset of the Python language and outputs an optimized C program. The compiler supports python integers, booleans, strings, and lists (with the semantics of C arrays), as well as control flow statements such as if, else, and while. 

The parsed AST is checked for type constraints and variable types are inferred from the type of the first value used. The AST is then traversed to generate a custom IR based on three-address code. The IR then goes through the optimzer which performs constant folding and constant propagation as well as some dead-code elimination before the final C code is generated.
