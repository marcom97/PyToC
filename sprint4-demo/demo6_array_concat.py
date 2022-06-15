def main():
    x = [2,4,6]
    y = [1,3,5]
    
    z1 = x + y
    z2 = [-3,-2,-1] + [1,2,3]
    z3 = [0] + x
    z4 = y + [0]
    
    i = 0
    while i < 6:
        print(z1[i])
        i = i + 1
    
    i = 0
    while i < 6:
        print(z2[i])
        i = i + 1
    
    i = 0
    while i < 4:
        print(z3[i])
        i = i + 1
    
    i = 0
    while i < 4:
        print(z4[i])
        i = i + 1
    
