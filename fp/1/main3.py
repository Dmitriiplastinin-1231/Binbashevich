from functools import reduce
import operator

orders = [
    {"order_id": 1, "customer_id": 201, "amount": 250.0},
    {"order_id": 2, "customer_id": 202, "amount": 350.0},
    {"order_id": 3, "customer_id": 201, "amount": 125.0},
    {"order_id": 4, "customer_id": 203, "amount": 180.0},
    {"order_id": 5, "customer_id": 201, "amount": 90.0},
    {"order_id": 6, "customer_id": 204, "amount": 420.0},
    {"order_id": 7, "customer_id": 202, "amount": 210.0},
    {"order_id": 8, "customer_id": 205, "amount": 550.0},
    {"order_id": 9, "customer_id": 201, "amount": 160.0},
    {"order_id": 10, "customer_id": 206, "amount": 310.0},
    {"order_id": 11, "customer_id": 203, "amount": 110.0},
    {"order_id": 12, "customer_id": 207, "amount": 680.0},
    {"order_id": 13, "customer_id": 202, "amount": 190.0},
    {"order_id": 14, "customer_id": 208, "amount": 380.0},  \
    {"order_id": 15, "customer_id": 201, "amount": 145.0},
    {"order_id": 16, "customer_id": 209, "amount": 520.0},
    {"order_id": 17, "customer_id": 205, "amount": 240.0},
    {"order_id": 18, "customer_id": 204, "amount": 480.0},
    {"order_id": 19, "customer_id": 210, "amount": 270.0},
    {"order_id": 20, "customer_id": 201, "amount": 320.0},
]

def f1(arg):
    if arg["customer_id"] == 201:  
        return arg

def f2(arg):
    return arg["amount"]

e1 = list(filter(f1, orders))
print(e1)
print('\n')
e2 = list(map(f2, e1))
print(reduce(operator.add, e2))
print('\n')
print(reduce(operator.add, e2) / len(e2))
