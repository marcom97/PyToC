def f(x: int) -> int:
    fact = 1
    n = 2
    
    while n < x:
        fact = fact * n
        n = n + 1
    
    return fact


def main():
    x = 20
    
    f(x)
