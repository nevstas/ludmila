import warnings
import os
import sys
from threading import Lock
import threading
import time

import numpy as np
from timeit import default_timer as timer
from numba import vectorize

myLock = threading.Lock()

# Path to the folder of the executing script
script_path = "/content/drive/My Drive/ludmila/ludmila"

# 1 Linear (5 characters)
# y = ax + b
# v|x0;o|*;v|x1;o|+;v|x2

# 2 Pythagoras theorem (8 characters)
# a ** 2 + b ** 2 = c ** 2
# bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5

# 3 series of prime numbers


dataset_id = 2

# File name with 'x' and 'y', for example if dataset_id = 1, dataset_filename will be 'data1.txt'
dataset_filename = "data" + str(dataset_id) + ".txt"

# The current equation to start from, then it will be incremented
equation = [0]

# Elements from which equations are formed by concatenating with each other
# Base-21 numeral system (from 0 to 20)
#"0" => "n|0", "1" => "n|1", "2" => "n|2", "3" => "n|3", "4" => "n|4", "5" => "n|5"
#"6" => "n|6", "7" => "n|7", "8" => "n|8", "9" => "n|9", "10" => "n|10"
#"11" => "o|+", 12" => "o|*", 13" => "o|/", 14" => "om|-"
#"15" => "bl|(", "16" => "br|)"
#"17" => "e|**2", "18" => "e|**3", "19" => "e|**0.5", "20" => "e|**(1/3)"
#"21" => "n|1;n|0"
#"22" => "n|1;n|1"
elements = [
    # numbers: 0-10
    "n|0",
    "n|1",
    "n|2",
    "n|3",
    "n|4",
    "n|5",
    "n|6",
    "n|7",
    "n|8",
    "n|9",
    "n|10",

    # operations: +, -, *, /
    "o|+",
    "o|*",
    "o|/",
    "om|-",

    # brackets ( and )
    "bl|(",
    "br|)",

    # exponentiation: power of 2, power of 3, square root, cube root
    # "e|**2",
    # "e|**3",
    # "e|**0.5",
    # "e|**(1/3)",
]

elements_len = len(elements)

# Keys - element types
# allow_left - rules for concatenation, contains element types that can be on the left
# When concatenating a number type element, it checks what is on the left, allowed: o(operator), om(operator minus), s(start), and bl(bracket left)
# If the left symbol is of another type, concatenation does not occur
# This is done to reduce the number of options in combinatorics, and to reduce the number of unnecessary iterations

types_of_elements = {
    # start of the string
    's': {
        'allow_left': [],
    },
    # number
    'n': {
        'allow_left': ['s', 'o', 'om', 'bl'],
    },
    # operator
    'o': {
        'allow_left': ['n', 'br', 'v', 'e'],
    },
    # operator minus
    'om': {
        'allow_left': ['s', 'n', 'bl', 'br', 'v', 'e'],
    },
    # bracket left
    'bl': {
        'allow_left': ['s', 'o', 'om', 'e'],
    },
    # bracket right
    'br': {
        'allow_left': ['n', 'v', 'e'],
    },
    # variable
    'v': {
        'allow_left': ['s', 'o', 'om', 'bl'],
    },
    # exponentiation
    'e': {
        'allow_left': ['n', 'br', 'v'],
    },
}


# Formats equations
# Example input: [1, 2, 3]
# Output: 7 + 5, where 5 is x0
def format(equation, x):
    equation = ''.join([elements[i] for i in equation])
    for variable_count, x_item in enumerate(x):
        equation = equation.replace("v|x" + str(variable_count), x_item)
    equation = equation.replace("n|", "")
    equation = equation.replace("o|", "")
    equation = equation.replace("om|", "")
    equation = equation.replace("bl|", "")
    equation = equation.replace("br|", "")
    equation = equation.replace("e|", "")

    return equation


# Executes the equation and compares the solution with 'y'; if the solution is correct, returns True
# Example input: "51 * 62 + 73" and "3235"
# Output: True
def calc(equation, y):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore")  # Disable Warning on the off chance that the equation is not correct, for example "4(3)"
            result_of_equation = eval(equation)
        if float(result_of_equation) == float(y):
            return True
        else:
            return False
    except:
        return False


# Executes all (e.g., 100) equations (e.g., from file data1.txt) and if all equations are solved correctly, returns True
# The fact that calc() solved one equation correctly does not mean it's the desired equation.
# If calc() returned True, then run calc_all() to check the equation on a large dataset
# Example input: array "51 * 62 + 73" and "3235"
# Output: True
def calc_all(equation, dataset):
    for dataset_item in dataset:
        equation_format = format(equation, dataset_item['x'])
        if not calc(equation_format, dataset_item['y']):
            return False
    return True


# Checks a number against allowed neighbors standing next to each other
def check_allow_concat(equation):
    for key, e in enumerate(equation):
        if key == 0:
            left_element = ''
            left_element_type = get_type_of_element(left_element)
        else:
            left_element = equation[key - 1]
            left_element_type = get_type_of_element(elements[left_element])
        right_element = e
        right_element_type = get_type_of_element(elements[right_element])

        if not left_element_type in types_of_elements[right_element_type]['allow_left']:
            return {'result': False, 'key': key}
    return {'result': True, 'key': 0}


# Gets the type of element
# Input parameters n|8
# Result: n
# We do not use regex because it is too heavy
def get_type_of_element(element):
    if not element:
        return 's'
    index_of_type = element.rfind('|')
    return element[0:index_of_type]


# Writes to log.txt (e.g., found equations)
def writeln(str):
    myLock.acquire()
    with open(script_path + "/log.txt", 'a', encoding='utf-8') as the_file:
        the_file.write(str + "\n")
    myLock.release()


# Input data [12, 9, 5]
# Output data [12, 9, 6]
def equation_number_increment(equation):
    current_index = len(equation) - 1
    while (True):
        equation = equation_number_increment_by_index(equation, current_index)
        check_equation = check_allow_concat(equation)

        if check_equation['result']:
            return equation
        else:
            for key, e in enumerate(equation):
                if key > check_equation['key']:
                    equation[key] = 0
            current_index = check_equation['key']


def equation_number_increment_by_index(equation, current_index):
    while (True):
        current_number = equation[current_index]
        if current_number < (elements_len - 1):
            equation[current_index] = current_number + 1
            return equation
        else:
            if current_index > 0:
                equation[current_index] = 0
                current_index = current_index - 1
            else:
                for key, number in enumerate(equation):
                    equation[key] = 0
                print('Checked equation length ' + str(len(equation)))
                equation = [0] + equation
                return equation


# Formatting equation into human-readable form
# Input data [1, 2, 3]
# Output data v|x0;o|*;v|x1;o|+;v|x2
def format_equation_to_human_view(equation):
    equation_human = ""
    for index_of_element in equation:
        if equation_human == "":
            equation_human = elements[index_of_element]
        else:
            equation_human = equation_human + ';' + elements[index_of_element]
    return equation_human


def task(dataset):
    global elements
    global elements_len
    global equation
    first_element_of_dataset = dataset[0] # Takes from the large dataset (e.g., 100) the first element
    variable_elements = []
    for variable_count, f in enumerate(first_element_of_dataset['x']):
        variable_elements.append("v|x" + str(variable_count))
    elements = elements + variable_elements # add all 'x' to elements, their number can vary
    elements_len = len(elements)

    time_total_start = time.time()
    time_stat = time.time()
    equation_count = 0
    while (True):

        equation_format = format(equation, first_element_of_dataset['x']) # format the equation

        #print(format_equation_to_human_view(equation))
        # writeln(format_equation_to_human_view(equation))

        if calc(equation_format, first_element_of_dataset['y']): # if the equation is valid on one set of x and y

            if calc_all(equation, dataset): # then check the equation on the large dataset (e.g., 100)
                time_total = time.time() - time_total_start
                message = time.strftime("%d.%m.%Y %H:%M:%S") + " Solution data" + str(dataset_id) + ": " + format_equation_to_human_view(equation) + " at " + str(round(time_total, 2)) + " seconds"
                writeln(message)
                print(message)

        equation = equation_number_increment(equation)

        equation_count += 1
        if equation_count % 100000 == 0:
            speed = equation_count / (time.time() - time_stat)
            print(f"Speed: {int(speed)} eq/s")

with open(script_path + "/datasets/" + dataset_filename) as f:
    dataset_plain = f.readlines() # read the dataset (e.g., from file data1.txt). Example: "3235 51 62 73"

dataset = [] # dataset contains elements like {'y': 3235, 'x': [51, 62, 73]} — first element is the solution y, second element is the input array x
for dataset_plain_item in dataset_plain:
    dataset_plain_item = dataset_plain_item.strip()
    dataset_plain_item = dataset_plain_item.split("\t")
    y = dataset_plain_item[0]
    dataset_plain_item.pop(0) # Delete the first element of the array (y), we don’t need it
    x = dataset_plain_item
    dataset.append({"y": y, "x": x})

task(dataset) # call the main function