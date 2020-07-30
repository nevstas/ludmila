# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings

import config
import core_maths

#if not sys.warnoptions:
#	warnings.simplefilter("ignore")

myLock = Lock()


def task(new_arr):
	global config
	first = new_arr[0]
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{v|x" + str(fcount) + "}")
		fcount = fcount + 1
	config.elements = config.elements + new_first_x

	with open(config.script_path + "\equations.txt", 'w') as f:
		for e in config.elements:
			f.write("%s\n" % e)

	i = 1
	time_total_start = time.time()
	while (True):

		with open(config.script_path + "\equations.txt") as infile:
			with open(config.script_path + "\equations_tmp.txt", "a") as k:
				for equation in infile:
					equation = equation.strip()
					if equation:
						for element in config.elements:
							if core_maths.is_allow_concat(equation, element):
								k.write(str(equation) + str(element) + "\n")
					equation_format = core_maths.format(equation, first['x'])
					if core_maths.calc(equation_format, first['y']):
						if core_maths.calc_all(equation, new_arr):
							time_total = time.time() - time_total_start
							core_maths.writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + equation + " на " + str(round(time_total, 2)) + " сек")
							print(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + equation + " на " + str(round(time_total, 2)) + " сек")
		
		os.remove(config.script_path + "\equations.txt")
		os.rename(config.script_path + "\equations_tmp.txt", config.script_path + "\equations.txt")
				
		time_total = time.time() - time_total_start
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " Проверены уравнения длинной " + str(i) + " символов на " + str(round(time_total, 2)) + " сек")
		i = i +1

if os.path.isfile(config.script_path + "\equations.txt"):
	os.remove(config.script_path + "\equations.txt")
	
if os.path.isfile(config.script_path + "\equations_tmp.txt"):
	os.remove(config.script_path + "\equations_tmp.txt")

with open(config.script_path + "\\" + config.data_filename) as f:
	arr = f.readlines()

new_arr = [] # [1, [1, 2, 3, 4, 5]] Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = arr_item
	new_arr.append({"y": y, "x": x})

task(new_arr)

#Команда для запуска:
#c:\Python38\python e:\python\maths\maths.py