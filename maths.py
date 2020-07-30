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

myLock = Lock()


def task(new_arr):
	global config
	first = new_arr[0] #Берем из большого набора данных (например 100) первый элемент
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{v|x" + str(fcount) + "}")
		fcount = fcount + 1
	config.elements = config.elements + new_first_x #добавляем к элементам все 'x', их может быть разное количество

	with open(config.script_path + "\equations.txt", 'w') as f:
		for e in config.elements:
			f.write("%s\n" % e) #пишем в файл все элементы. В первой итерации будут проверяться уравнения типа y = 1, y = 2. Дальше уравнения будут усложняться

	i = 1
	time_total_start = time.time()
	while (True):

		with open(config.script_path + "\equations.txt") as infile:
			with open(config.script_path + "\equations_tmp.txt", "a") as k:
				for equation in infile: #построчно читаем файл equations.txt без загрузки его в оперативную память
					equation = equation.strip()
					if equation:
						for element in config.elements: #проходимся по эталонным элементам
							if core_maths.is_allow_concat(equation, element): #проверяем по правилам можно ли делать конкатенцию соседей
								k.write(str(equation) + str(element) + "\n") #и пишем в файл equations_tmp.txt комбинации, каждый элемент из файла equations.txt перемножается с эталонными элементами
					equation_format = core_maths.format(equation, first['x']) #форматируем уравнение
					if core_maths.calc(equation_format, first['y']): #если уравнение выполнено на одном наборе данных x и y
						if core_maths.calc_all(equation, new_arr): #тогда выполняем проверку уравнения на большом наборе данных (например 100)
							time_total = time.time() - time_total_start
							core_maths.writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + equation + " на " + str(round(time_total, 2)) + " сек")
							print(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + equation + " на " + str(round(time_total, 2)) + " сек")
		
		os.remove(config.script_path + "\equations.txt") #удаляем файл equations.txt
		os.rename(config.script_path + "\equations_tmp.txt", config.script_path + "\equations.txt") #и на его место ложим новый файл equations_tmp.txt, в котором предыдущие уравнения перемножаются с эталонными элементами
				
		time_total = time.time() - time_total_start
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " Проверены уравнения длинной " + str(i) + " символов на " + str(round(time_total, 2)) + " сек")
		i = i +1

if os.path.isfile(config.script_path + "\equations.txt"):
	os.remove(config.script_path + "\equations.txt") #удаляем equations.txt
	
if os.path.isfile(config.script_path + "\equations_tmp.txt"):
	os.remove(config.script_path + "\equations_tmp.txt") #удаляем equations_tmp.txt

with open(config.script_path + "\\" + config.data_filename) as f:
	arr = f.readlines() #считываем набор данных (например из файла data1.txt). Пример данных "3235	51	62	73"

new_arr = [] #В конце цикла массив new_arr должен содержать элементы вида [3235, [51, 62, 73]] Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = arr_item
	new_arr.append({"y": y, "x": x})

task(new_arr) #вызываем основноую функцию

#Команда для запуска:
#c:\Python38\python e:\python\maths\maths.py