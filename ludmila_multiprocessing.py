import time
from threading import Lock
import threading
import core
import config
import multiprocessing
import json
import atexit

myLock = threading.Lock()
time_total_start = time.time()

task_position = 0

@atexit.register
def cleanup():
	core.the_file.close()

def get_task():
	global equation_decimal_start
	global chunk
	global task_position
	position_decimal_start = equation_decimal_start + task_position * chunk
	position_decimal_end = position_decimal_start + chunk

	position_start = core.decimal_to_custom(position_decimal_start)
	position_end = core.decimal_to_custom(position_decimal_end)

	task_position += 1
	return [position_start, position_end, position_decimal_start, position_decimal_end]

def task(position_start, position_end, position_decimal_start, position_decimal_end):
	# core.writeln(json.dumps(position_start) + ' ' + json.dumps(position_end))
	equation = position_start.copy()
	while True:
		equation_format = core.format(equation, first_element_of_dataset['x'])

		if core.calc(equation_format, first_element_of_dataset['y']):
			if core.calc_all(equation, dataset):
				time_total = time.time() - time_total_start
				message = time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.dataset_id) + ": " + core.format_equation_to_human_view(equation) + " на " + str(round(time_total, 2)) + " сек"
				core.writeln(message)
				print(message)

		equation = core.equation_number_increment(equation)
		equation_decimal = core.custom_to_decimal(equation)

		if equation_decimal >= position_decimal_end:
			# core.writeln('End: ' + json.dumps(position_start) + ' ' + json.dumps(position_end))
			break

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

chunk = 10000
equation_start = config.equation
equation_decimal_start = core.custom_to_decimal(equation_start)

if __name__ == '__main__':
	def run_tasks(pool):
		while True:
			task_data = get_task()
			pool.apply_async(task, args=(task_data[0], task_data[1], task_data[2], task_data[3]))

	# Создаем пул и запускаем задачи
	with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
		run_tasks(pool)
#c:\Python311\python d:\python\maths\ludmila_multiprocessing.py
