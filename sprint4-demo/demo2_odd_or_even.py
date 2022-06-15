def f(x: int) -> str:
    if (x % 2 == 0):
        return "even"
    else:
        return "odd"
    


def main():
    x = 159
    
    f(x)
    f(((3*x)+15)%10)
