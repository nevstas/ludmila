import warnings
import os
import sys
from threading import Lock
import threading
import time

import multiprocessing
import json
import atexit
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Process
import signal
from contextlib import contextmanager
import random

import numpy as np
from timeit import default_timer as timer
from numba import vectorize

# config
dataset_id = 2
# config

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
    "e|**2",
    # "e|**3",
    "e|**0.5",
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

with open(script_path + "/datasets/" + dataset_filename) as f:
    dataset_plain = f.readlines()  # read the dataset (e.g., from file data1.txt). Example: "3235 51 62 73"

dataset = []  # dataset contains elements like {'y': 3235, 'x': [51, 62, 73]} — first element is the solution y, second element is the input array x
for dataset_plain_item in dataset_plain:
    dataset_plain_item = dataset_plain_item.strip()
    dataset_plain_item = dataset_plain_item.split("\t")
    y = dataset_plain_item[0]
    dataset_plain_item.pop(0)  # Delete the first element of the array (y), we don’t need it
    x = dataset_plain_item
    dataset.append({"y": y, "x": x})

first_element_of_dataset = dataset[0]  # Takes from the large dataset (e.g., 100) the first element
variable_elements = []
for variable_count, f in enumerate(first_element_of_dataset['x']):
    variable_elements.append("v|x" + str(variable_count))
elements = elements + variable_elements  # add all 'x' to elements, their number can vary
elements_len = len(elements)


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


# Converts a decimal number to a number in elements_len numeral system (e.g., 21)
# Input data 24
# Output data [1, 3]
def decimal_to_custom(number):
    x = (number % elements_len)
    ch = [x]
    if (number - x != 0):
        return decimal_to_custom(number // elements_len) + ch
    else:
        return ch


def custom_to_decimal(arr):
    decimal = 0
    for index, number in enumerate(reversed(arr)):
        decimal += number * (elements_len ** index)
    return decimal

@atexit.register
def cleanup():
    the_file.close()

def get_tasks(fnc_num_tasks, fnc_equation_decimal_start, fnc_task_position, fnc_chunk):
    print('get tasks ' + str(random.randint(1, 100)))
    # Create multiple tasks for simultaneous processing
    tasks = []
    for _ in range(fnc_num_tasks):
        position_decimal_start = fnc_equation_decimal_start + fnc_task_position * fnc_chunk
        position_decimal_end = position_decimal_start + fnc_chunk

        position_start = decimal_to_custom(position_decimal_start)
        position_end = decimal_to_custom(position_decimal_end)

        fnc_task_position += 1
        tasks.append([position_start.copy(), position_end.copy(), position_decimal_start, position_decimal_end])
    return [fnc_task_position, tasks]

def task(fnc_elements, fnc_variable_elements, fnc_time_total_start, fnc_dataset, fnc_first_element_of_dataset, fnc_position_start, fnc_position_end, fnc_position_decimal_start, fnc_position_decimal_end):
    # print('task was started')
    equation = fnc_position_start.copy()
    while True:
        equation_format = format(equation, fnc_first_element_of_dataset['x'])

        if calc(equation_format, fnc_first_element_of_dataset['y']):
            if calc_all(equation, fnc_dataset):
                time_total = time.time() - fnc_time_total_start
                message = time.strftime("%d.%m.%Y %H:%M:%S") + " Solution data" + str(
                    dataset_id) + ": " + format_equation_to_human_view(equation) + " at " + str(
                    round(time_total, 2)) + " seconds"
                writeln(message)
                print(message)

        equation = equation_number_increment(equation)
        equation_decimal = custom_to_decimal(equation)

        if equation_decimal >= fnc_position_decimal_end:
            # print("task was finished")
            return

if __name__ == '__main__':
    time_total_start = time.time()
    task_position = 0

    equation_start = equation
    equation_decimal_start = custom_to_decimal(equation_start)

    # equation_decimal_start = 2000000 #remove this

    chunk = 10000000
    completed_tasks = 0
    threads = multiprocessing.cpu_count()
    time_stat = time.time()

    with ProcessPoolExecutor(max_workers=threads) as executor:
        futures = []
        try:
            while True:
                # Receive a list of tasks
                tasks_fnc = get_tasks(20 * multiprocessing.cpu_count(), equation_decimal_start, task_position, chunk)  # Create more tasks to load all cores
                task_position = tasks_fnc[0]
                task_list = tasks_fnc[1]

                # Add all tasks to the pool
                for task_data in task_list:
                    future = executor.submit(task, elements, variable_elements, time_total_start, dataset, first_element_of_dataset, task_data[0], task_data[1], task_data[2], task_data[3])
                    futures.append(future)

                # Waiting for some tasks to complete to avoid memory overflow
                # Checking completed tasks and removing them from the list
                for f in as_completed(futures):
                    completed_tasks += 1
                    equation_count = completed_tasks * chunk
                    speed = equation_count / (time.time() - time_stat)
                    print(f"Speed: {int(speed)} eq/s")
                    futures.remove(f)
        except:
            print('Exeption')
        finally:
            # Wait for all remaining tasks to complete before exiting
            for future in futures:
                future.cancel()

task(dataset)  # call the main function