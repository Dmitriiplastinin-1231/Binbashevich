from functools import reduce
import operator

max_average = -1

students = [
    {"name": "Sophia", "age": 19, "grades": [92, 88, 95, 90]},
    {"name": "Liam", "age": 21, "grades": [85, 79, 82, 88]},
    {"name": "Emma", "age": 20, "grades": [96, 94, 91, 93]},
    {"name": "Noah", "age": 22, "grades": [78, 85, 80, 83]},
    {"name": "Olivia", "age": 19, "grades": [89, 92, 87, 90]},
    {"name": "William", "age": 21, "grades": [75, 82, 79, 81]},
    {"name": "Ava", "age": 20, "grades": [93, 90, 94, 91]},
    {"name": "James", "age": 23, "grades": [88, 85, 90, 87]},
    {"name": "Isabella", "age": 19, "grades": [84, 87, 82, 85]},
    {"name": "Benjamin", "age": 21, "grades": [91, 89, 93, 90]},
    {"name": "Mia", "age": 20, "grades": [95, 97, 94, 96]},
    {"name": "Lucas", "age": 22, "grades": [83, 86, 80, 84]},
    {"name": "Charlotte", "age": 19, "grades": [90, 88, 92, 89]},
    {"name": "Henry", "age": 21, "grades": [77, 80, 75, 78]},
    {"name": "Amelia", "age": 20, "grades": [94, 91, 96, 93]},
    {"name": "Alexander", "age": 23, "grades": [86, 89, 84, 87]},
    {"name": "Harper", "age": 19, "grades": [81, 84, 79, 82]},
    {"name": "Michael", "age": 21, "grades": [92, 90, 94, 91]},
    {"name": "Evelyn", "age": 20, "grades": [87, 90, 85, 88]},
    {"name": "Daniel", "age": 22, "grades": [89, 86, 91, 88]}
]

def filter_young_students(student):
    if student["age"] <= 22:
        return student

def calculate_average_grades(student):
    return (student["name"], reduce(operator.add, student["grades"]) / 4)

def sum_grades(student):
    return reduce(operator.add, student["grades"])

def filter_top_students(student_data):
    if student_data[1] == max_average:
        return student_data

print(list(filter(filter_young_students, students)))
print('\n')
students_with_averages = list(map(calculate_average_grades, students))
for student in students_with_averages:
    if max_average < student[1]:
        max_average = student[1]
print(students_with_averages)
print('\n')
print(reduce(operator.add, list(map(sum_grades, students))) / 4 / 20)
print('\n')
print(list(filter(filter_top_students, students_with_averages)))
