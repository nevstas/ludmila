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

myLock = threading.Lock()

# Путь к располажению выполняемого скрипта
script_path = "/content/drive/My Drive/ludmila/ludmila"

# 1 Линейное 5 символов
# y = ax + b
# v|x0;o|*;v|x1;o|+;v|x2

# 2 Теорема пифагора 8 символов
# a ** 2 + b ** 2 = c ** 2
# bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5

# 3 ряд простых чисел


dataset_id = 1

# Имя файла с 'x' и 'y', например если dataset_id = 1, то dataset_filename будет 'data1.txt'
dataset_filename = "data" + str(dataset_id) + ".txt"

# Текущее уравнение с которого начинаем, далее оно будет инкрементится
equation = [0]

# элементы, из которых составляются уравнения путем конкатенции друг с другом
elements = [
    # числа: 0-10
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

    # операции: +, -, *, /
    "o|+",
    "o|*",
    "o|/",
    "om|-",

    # скобки ( и )
    "bl|(",
    "br|)",

    # степень: 2 степень, 3 степень, корень квадратный, корень кубический
    # "e|**2",
    # "e|**3",
    # "e|**0.5",
    # "e|**(1/3)",
]

elements_len = len(elements)

# Ключи - типы элементов
# allow_left - правила при конкатенции, содержит типы элементов, которые могут находится слева
# При конкатенции элемента типа number смотрится на то кто стоит слева, разрешены o(operator), om(operator minus), s(start) и bl(bracket left)
# Если слева символ иного типа, то конкатенция не происходит
# Это сделано для уменьшения кол-ва вариантов при комбинаторике, уменьшения кол-ва ненужных итераций

types_of_elements = {
    # start начало строки
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
    dataset_plain = f.readlines()  # считываем набор данных (например из файла data1.txt). Пример данных "3235 51 62 73"

dataset = []  # dataset содержит элементы вида {'y': 3235, 'x': [51, 62, 73]} Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for dataset_plain_item in dataset_plain:
    dataset_plain_item = dataset_plain_item.strip()
    dataset_plain_item = dataset_plain_item.split("\t")
    y = dataset_plain_item[0]
    dataset_plain_item.pop(0)  # Удаляем первый элемент массива (y), он нам не нужен
    x = dataset_plain_item
    dataset.append({"y": y, "x": x})

first_element_of_dataset = dataset[0]  # Берем из большого набора данных (например 100) первый элемент
variable_elements = []
for variable_count, f in enumerate(first_element_of_dataset['x']):
    variable_elements.append("v|x" + str(variable_count))
elements = elements + variable_elements  # добавляем к элементам все 'x', их может быть разное количество
elements_len = len(elements)

# Форматирует уравнения
# Пример входящих данных: [1, 2, 3]
# Исходящие: 7 + 5, где 5 это x0
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


# Выполняет уравнение и српанивает решение с 'y', если решение решено верно, то возвращает True
# Пример входящих данных: "51 * 62 + 73" и "3235"
# Исходящие True
def calc(equation, y):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter(
                "ignore")  # Отключаем Warning на сулчай если в equation будет не вылидным, например "4(3)"
            result_of_equation = eval(equation)
        if float(result_of_equation) == float(y):
            return True
        else:
            return False
    except:
        return False


# Выполняет все (например 100шт) уравнения (например из файла data1.txt) и если все уравнения решены верно, то возвращает True
# То, что функция calc() решила уравнение верно, не означает что это искомое уравнение.
# Если calc() вернула True, то запускаем функцию calc_all(), где проверяем уравнение на большом количестве данных
# Пример входящих данных: массив "51 * 62 + 73" и "3235"
# Исходящие True
def calc_all(equation, dataset):
    for dataset_item in dataset:
        equation_format = format(equation, dataset_item['x'])
        if not calc(equation_format, dataset_item['y']):
            return False
    return True


# Проверяет число по allow соседней, стоящих друг с другом
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


# Получает тип элемента
# Входящие параметры n|8
# Результат n
# Не используем регулярки, ибо накладно
def get_type_of_element(element):
    if not element:
        return 's'
    index_of_type = element.rfind('|')
    return element[0:index_of_type]


# Пишет в лог log.txt (например найденные уравнения)
def writeln(str):
    myLock.acquire()
    with open(script_path + "/log.txt", 'a', encoding='utf-8') as the_file:
        the_file.write(str + "\n")
    myLock.release()


# Входящие данные [12, 9, 5]
# Исходящие данные [12, 9, 6]
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
                print('Проверены уравнения длиной ' + str(len(equation)))
                equation = [0] + equation
                return equation


# Форматирование уравнения в читабельный вид
# Входящие данные [1, 2, 3]
# исходящие данные v|x0;o|*;v|x1;o|+;v|x2
def format_equation_to_human_view(equation):
    equation_human = ""
    for index_of_element in equation:
        if equation_human == "":
            equation_human = elements[index_of_element]
        else:
            equation_human = equation_human + ';' + elements[index_of_element]
    return equation_human


# Ковертирует число десятичной системы счисления в число elements_len системы счисления (например 21)
# Входящие данные 24
# исходящие данные [1, 3]
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
    # Создаем несколько задач для одновременной обработки
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
    # Выполнение задачи (например, печать начала позиции)

    # print('task was started')
    equation = fnc_position_start.copy()
    while True:
        equation_format = format(equation, fnc_first_element_of_dataset['x'])

        if calc(equation_format, fnc_first_element_of_dataset['y']):
            if calc_all(equation, fnc_dataset):
                time_total = time.time() - fnc_time_total_start
                message = time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(
                    dataset_id) + ": " + format_equation_to_human_view(equation) + " на " + str(
                    round(time_total, 2)) + " сек"
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
                # Получаем список задач
                tasks_fnc = get_tasks(20 * multiprocessing.cpu_count(), equation_decimal_start, task_position, chunk)  # Создаем больше задач, чтобы загрузить все ядра
                task_position = tasks_fnc[0]
                task_list = tasks_fnc[1]

                # Добавляем все задачи в пул
                for task_data in task_list:
                    future = executor.submit(task, elements, variable_elements, time_total_start, dataset, first_element_of_dataset, task_data[0], task_data[1], task_data[2], task_data[3])
                    futures.append(future)

                # Ожидание завершения некоторых задач, чтобы избежать переполнения памяти
                # Проверяем завершенные задачи и убираем их из списка
                for f in as_completed(futures):
                    completed_tasks += 1
                    equation_count = completed_tasks * chunk
                    speed = equation_count / (time.time() - time_stat)
                    print(f"Speed: {int(speed)} eq/s")
                    futures.remove(f)
        except:
            print('Exeption')
        finally:
            # Ожидание завершения всех оставшихся задач перед выходом
            for future in futures:
                future.cancel()

task(dataset)  # вызываем основноую функцию