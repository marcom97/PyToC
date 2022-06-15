def odd_or_even(x: int) -> str:
    if x % 2 == 0:
        return "Even"
    else:
        return "Odd"
    


def main():
    x = [1,2,3,4]
    i = 0
    y = 0
    
    while i < 3:
        y = x[i]
        print(odd_or_even(y))
        i = i + 1
    
