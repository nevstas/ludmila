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
import core

myLock = Lock()


def task(new_arr):
	global config
	first = new_arr[0] #Берем из большого набора данных (например 100) первый элемент
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("v|x" + str(fcount))
		fcount = fcount + 1
	config.elements = config.elements + new_first_x #добавляем к элементам все 'x', их может быть разное количество
	
	config.elements_len = len(config.elements)

	equation = config.equation

	time_total_start = time.time()
	while (True):

		equation_format = core.format(equation, first['x']) #форматируем уравнение

		#print(core.format_human(equation))
		# core.writeln(core.format_human(equation))

		if core.calc(equation_format, first['y']): #если уравнение выполнено на одном наборе данных x и y
			
			if core.calc_all(equation, new_arr): #тогда выполняем проверку уравнения на большом наборе данных (например 100)
				time_total = time.time() - time_total_start
				core.writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + core.format_human(equation) + " на " + str(round(time_total, 2)) + " сек")
				print(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение data" + str(config.data_id) + ": " + core.format_human(equation) + " на " + str(round(time_total, 2)) + " сек")
				
		equation = core.equation_number_increment(equation)

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
#c:\Python37\python e:\python\maths\ludmila.py