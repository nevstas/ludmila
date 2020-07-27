# -*- coding: windows-1251 -*-

# 1 Линейное y = ax + b
# 2 Теорема пифагора a ^ 2 + b ^ 2 = c ^ 2
# 3 Квадратные ax ^ 2 + bx + c = 0

import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

myLock = Lock()

elements = [
	"{number|0}",
	"{number|1}",
	"{number|2}",
	"{number|3}",
	"{number|4}",
	"{number|5}",
	"{number|6}",
	"{number|7}",
	"{number|8}",
	"{number|9}",
	"{number|10}",
	"{operator|+}", 
	"{operator|-}", 
	"{operator|*}", 
	"{operator|/}"
]

script_path = os.path.dirname(os.path.realpath(__file__))

types = {
	'number': {
		'allow_left': ['operator'],
		'allow_right': ['operator'],
	},
	'variable': {
		'allow_left': ['operator'],
		'allow_right': ['operator'],
	},
	'operator': {
		'allow_left': ['number', 'variable'],
		'allow_right': ['number', 'variable'],
	},
}

def task(new_arr):
	global elements
	first = new_arr[0]
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{variable|x" + str(fcount) + "}")
		fcount = fcount + 1
	elements = elements + new_first_x

	with open(script_path + "\\equations.txt", 'w') as f:
		for e in elements:
			f.write("%s\n" % e)

	i = 1
	time_total_start = time.time()
	while (True):

		with open(script_path + "\\equations.txt") as infile:
			for equation in infile:
				equation = equation.strip()
				equation_format = format(equation, first['x'])
				if calc(equation_format, first['y']):
					result = True
					for new_arr_item in new_arr:
						equation_format = format(equation, new_arr_item['x'])
						if not calc(equation_format, new_arr_item['y']):
							result = False
							break
					if result:
						time_total = time.time() - time_total_start
						writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение: " + equation + " на " + str(round(time_total, 2)) + " сек")
						print(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение: " + equation + " на " + str(round(time_total, 2)) + " сек")
				
		time_total = time.time() - time_total_start
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " Проверены уравнения длинной " + str(i) + " символов на " + str(round(time_total, 2)) + " сек")
		build_equation(elements)
		i = i +1

#Перемножаем (комбинаторик) существующие данные equations.txt с массивом elements, и помещаем результат обратно в equations.txt
def build_equation(elements):

	with open(script_path + "\\equations.txt") as infile:
		with open(script_path + "\\equations_tmp.txt", "a") as k:
			for equation in infile:
				equation = equation.strip()
				if equation:
					for element in elements:
						if is_allow_concat(equation, element):
							k.write(str(equation) + str(element) + "\n")
	
	os.remove(script_path + "\\equations.txt")
	os.rename(script_path + "\\equations_tmp.txt", script_path + "\\equations.txt")

	return True

#Пример входящих данных: {number|7}{operator|+}{variable|x0}
#Исходящие: 7 + 5, где 5 это x0
def format(equation, x):
	x_count = 0
	for x_item in x:
		equation = equation.replace("{variable|x" + str(x_count) + "}", x_item)  
		x_count = x_count + 1
	equation = equation.replace("{number|", "")
	equation = equation.replace("{operator|", "")
	equation = equation.replace("}", "")

	return equation

def calc(equation, y):
	try:
		y_equation = eval(equation)
		if y_equation == int(y):
			return True
	except:			
		return False

#Входящие данные первый параметр: {number|7}{operator|+}{variable|x0}
#Входящие данные второй параметр: {number|8}
#Результат должен быть False
def is_allow_concat(equation, element):
	equation1 = get_last_element(equation)
	equation1_type = get_type(equation1)
	equation2_type = get_type(element)
	
	if equation1_type in types[equation2_type]['allow_left']:
		return True
	else:
		return False

#Входящие данные {number|7}{operator|+}{variable|x0}
#Результат {variable|x0}
def get_last_element(equation):
	start = equation.rfind('{')
	end = len(equation)
	return equation[start:end]

#Входящие параметры {number|8}
#Результат number
#Не используем регулярки, ибо накладно
def get_type(equation):
	end = equation.rfind('|')
	return equation[1:end]

def writeln(str):
	myLock.acquire()		
	with open(script_path + '\\sucess.txt', 'a') as the_file:
		the_file.write(str + "\n")
	myLock.release()

if os.path.isfile(script_path + "\\equations.txt"):
	os.remove(script_path + "\\equations.txt")
	
if os.path.isfile(script_path + "\\equations_tmp.txt"):
	os.remove(script_path + "\\equations_tmp.txt")

with open(script_path + '\\data.txt') as f:
	arr = f.readlines()

new_arr = [] # [1, [1, 2, 3, 4, 5]] Первый элемент значение (решение) уравнения, второй элемент массив входящих данных
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = arr_item
	new_arr.append({"y": y, "x": x})

task(new_arr)

#Команда для запуска:
#c:\\Python38\\python z:\\python\\maths\\maths.py