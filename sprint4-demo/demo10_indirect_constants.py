def f(x: int) -> int:
    return 2 * x
    

def g(x: int) -> str:
    if (x % 2 == 0):
        return "even"
    else:
        return "odd"


def main():
    num = f(3)
    string = g(num)
    
    nums = [1, 2, 3] + [4]
    num1 = nums[3] + 1
    num2 = num1 + 2
    
    print('The' + ' number', num, 'is "' + string + '" and', num2, 'is', g(num2) + '!')
