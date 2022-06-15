def f(x: int) -> int:
    return 2 * x
    

def g(x: int) -> str:
    if (x % 2 == 0):
        return "even"
    else:
        return "odd"
    

def h(x: bool, y: bool) -> bool:
    y = (x and y) or ((not x) and (not y))


def main():
    x = 1
    y = 4
    
    if (x < 2):
        print(x)
    else:
        print(y)
    
    if (y > 3):
        print(y+(3*4))
    
    z = 0
    
    while (z < 20):
        z = z + 2
        z = z - 1
    
    print(x+y)
