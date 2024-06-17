import time
import core
import config
from threading import Thread
from threading import Lock
import time
import requests
import os
import threading
import queue
from queue import Queue
import multiprocessing as mp
from multiprocessing import JoinableQueue
from multiprocessing import Pool
import json

queue = mp.Queue()
# queue = JoinableQueue


myLock = threading.Lock()
myLock2 = Lock()
time_total_start = time.time()

def get_data():
	global equation
	while (True):
		equation = core.equation_number_increment(equation)
		yield equation

a=get_data()

def task(equation):
	equation_format = core.format(equation, first_element_of_dataset['x'])  # форматируем уравнение

	if core.calc(equation_format,
				 first_element_of_dataset['y']):  # если уравнение выполнено на одном наборе данных x и y
		if core.calc_all(equation,
						 dataset):  # тогда выполняем проверку уравнения на большом наборе данных (например 100)
			time_total = time.time() - time_total_start
			message = time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(
				config.dataset_id) + ": " + core.format_equation_to_human_view(equation) + " на " + str(
				round(time_total, 2)) + " сек"
			core.writeln(message)
			print(message)
	# core.writeln('xzcxzccxzzxcc')
	return

with open(config.script_path + "/datasets/" + config.dataset_filename) as f:
	dataset_plain = f.readlines() #считываем набор данных (например из файла data1.txt). Пример данных "3235	51	62	73"

dataset = [] #dataset содержит элементы вида {'y': 3235, 'x': [51, 62, 73]} Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for dataset_plain_item in dataset_plain:
	dataset_plain_item = dataset_plain_item.strip()
	dataset_plain_item = dataset_plain_item.split("\t")
	y = dataset_plain_item[0]
	dataset_plain_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = dataset_plain_item
	dataset.append({"y": y, "x": x})
first_element_of_dataset = dataset[0] #Берем из большого набора данных (например 100) первый элемент
variable_elements = []
for variable_count, f in enumerate(first_element_of_dataset['x']):
	variable_elements.append("v|x" + str(variable_count))
config.elements = config.elements + variable_elements #добавляем к элементам все 'x', их может быть разное количество
config.elements_len = len(config.elements)

equation = config.equation

num_threads = 1
if __name__ == '__main__':
	p = Pool()
	results = p.imap(task, a, chunksize=10000)
	p.close()
	p.join()
#c:\Python311\python d:\python\maths\ludmila_multiprocessing_pool.py