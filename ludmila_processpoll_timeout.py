import time
from threading import Lock
import threading
import core
import config
import multiprocessing
import json
import atexit
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Process
import signal
from contextlib import contextmanager
import random

# logger = multiprocessing.log_to_stderr()
# logger.setLevel(multiprocessing.SUBDEBUG)

class TimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

@atexit.register
def cleanup():
	core.the_file.close()

def get_tasks(fnc_num_tasks, fnc_equation_decimal_start, fnc_task_position, fnc_chunk):
    # print('get tasks ' + str(random.randint(1, 100)))
    # Создаем несколько задач для одновременной обработки
    tasks = []
    for _ in range(fnc_num_tasks):
        position_decimal_start = fnc_equation_decimal_start + fnc_task_position * fnc_chunk
        position_decimal_end = position_decimal_start + fnc_chunk

        position_start = core.decimal_to_custom(position_decimal_start)
        position_end = core.decimal_to_custom(position_decimal_end)

        fnc_task_position += 1
        tasks.append([position_start.copy(), position_end.copy(), position_decimal_start, position_decimal_end])
    return [fnc_task_position, tasks]

def task(fnc_variable_elements, fnc_time_total_start, fnc_dataset, fnc_first_element_of_dataset, fnc_position_start, fnc_position_end, fnc_position_decimal_start, fnc_position_decimal_end):
    # Выполнение задачи (например, печать начала позиции)
    if not fnc_variable_elements[0] in config.elements:
        config.elements = config.elements + fnc_variable_elements
        config.elements_len = len(config.elements)

    # print('task was started')
    equation = fnc_position_start.copy()
    while True:
        equation_format = core.format(equation, fnc_first_element_of_dataset['x'])

        try:
            with time_limit(1):
                calc_result = core.calc(equation_format, fnc_first_element_of_dataset['y'])
        except TimeoutException as e:
            calc_result = False
            print("Timed out!")
        except Exception as e:
            calc_result = False
            print(str(e))

        if calc_result:
            try:
                with time_limit(1):
                    calc_all_result = core.calc_all(equation, fnc_dataset)
            except TimeoutException as e:
                calc_all_result = False
                print("Timed out!")
            except Exception as e:
                calc_all_result = False
                print(str(e))
            if calc_all_result:
                time_total = time.time() - fnc_time_total_start
                message = time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(
                    config.dataset_id) + ": " + core.format_equation_to_human_view(equation) + " на " + str(
                    round(time_total, 2)) + " сек"
                core.writeln(message)
                print(message)

        equation = core.equation_number_increment(equation)
        equation_decimal = core.custom_to_decimal(equation)

        if equation_decimal >= fnc_position_decimal_end:
            # print("task was finished")
            return

if __name__ == '__main__':
    time_total_start = time.time()
    task_position = 0

    with open(config.script_path + "/datasets/" + config.dataset_filename) as f:
        dataset_plain = f.readlines()

    dataset = []
    for dataset_plain_item in dataset_plain:
        dataset_plain_item = dataset_plain_item.strip()
        dataset_plain_item = dataset_plain_item.split("\t")
        y = dataset_plain_item[0]
        dataset_plain_item.pop(0)
        x = dataset_plain_item
        dataset.append({"y": y, "x": x})

    first_element_of_dataset = dataset[0]
    variable_elements = []
    for variable_count, f in enumerate(first_element_of_dataset['x']):
        variable_elements.append("v|x" + str(variable_count))
    config.elements = config.elements + variable_elements
    config.elements_len = len(config.elements)

    equation_start = config.equation
    equation_decimal_start = core.custom_to_decimal(equation_start)

    # equation_decimal_start = 2000000 #remove this

    chunk = 10000000

    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = []
        try:
            while True:
                # Получаем список задач
                tasks_fnc = get_tasks(20 * multiprocessing.cpu_count(), equation_decimal_start, task_position, chunk)  # Создаем больше задач, чтобы загрузить все ядра
                task_position = tasks_fnc[0]
                task_list = tasks_fnc[1]

                # Добавляем все задачи в пул
                for task_data in task_list:
                    future = executor.submit(task, variable_elements, time_total_start, dataset, first_element_of_dataset, task_data[0], task_data[1], task_data[2], task_data[3])
                    futures.append(future)

                # Ожидание завершения некоторых задач, чтобы избежать переполнения памяти
                # Проверяем завершенные задачи и убираем их из списка
                for f in as_completed(futures):
                    futures.remove(f)
        except:
            print('Exeption')
        finally:
            # Ожидание завершения всех оставшихся задач перед выходом
            for future in futures:
                future.cancel()


#c:\Python311\python d:\python\maths\ludmila_processpoll_timeout.py
#python3 /home/nevep/web/nevep.ru/public_html/tmp/ludmila/ludmila_processpoll_timeout.py