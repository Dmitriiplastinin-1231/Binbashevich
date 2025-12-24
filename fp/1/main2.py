from functools import reduce
import operator

users = [
    {"name": "Alice", "expenses": [1200, 850, 950, 1100]},
    {"name": "Bob", "expenses": [750, 820, 680, 900]},
    {"name": "Charlie", "expenses": [1500, 1300, 950, 1250]},
    {"name": "David", "expenses": [1100, 1250, 1400, 1600]},
    {"name": "Eve", "expenses": [920, 780, 1150, 1320]},
    {"name": "Frank", "expenses": [650, 720, 580, 810]},
    {"name": "Grace", "expenses": [1850, 1550, 1200, 950]},
    {"name": "Heidi", "expenses": [890, 1010, 1130, 1250]},
    {"name": "Ivan", "expenses": [2100, 1950, 1800, 1650]},
    {"name": "Judy", "expenses": [570, 685, 795, 905]},
    {"name": "Kevin", "expenses": [1280, 1420, 1560, 1700]},
    {"name": "Linda", "expenses": [750, 900, 1050, 1200]},
    {"name": "Mike", "expenses": [1600, 1750, 1900, 2050]},
    {"name": "Nancy", "expenses": [680, 770, 860, 950]},
    {"name": "Oscar", "expenses": [1140, 1260, 1380, 1500]},
    {"name": "Peggy", "expenses": [2350, 2500, 2650, 2800]},
    {"name": "Quincy", "expenses": [425, 550, 675, 800]},
    {"name": "Rita", "expenses": [1270, 1390, 1510, 1630]},
    {"name": "Sam", "expenses": [895, 1005, 1115, 1225]},
    {"name": "Tina", "expenses": [2400, 2300, 2200, 2100]},
]

def filter_low_first_expense(user):
    if user["expenses"][0] <= 1000:
        return user

def calculate_total_expenses(user):
    return (user["name"], reduce(operator.add, user["expenses"]))

def sum_expenses(user):
    return reduce(operator.add, user["expenses"])

filtered_users = list(filter(filter_low_first_expense, users))
print(filtered_users)
print('\n')
print(list(map(calculate_total_expenses, users)))
print('\n')
print(reduce(operator.add, list(map(sum_expenses, filtered_users))))
