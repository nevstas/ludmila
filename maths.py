# -*- coding: windows-1251 -*-

# 1 Линейное y = ax + b
# 2 Теорема пифагора a ^ 2 + b ^ 2 = c ^ 2
# 3 Квадратные ax ^ 2 + bx + c = 0

# 6 значная формула до соседней оптимизации - строк 34 012 224, размер файла 453 Мб

import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

myLock = Lock()

elements = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "+", "-", "*", "/"]

script_path = os.path.dirname(os.path.realpath(__file__))

def task(new_arr):
	global elements
	first = new_arr[0]
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{x" + str(fcount) + "}")
		fcount = fcount + 1
	elements = elements + new_first_x

	with open(script_path + "\\equations.txt", 'w') as f:
		for e in elements:
			f.write("%s\n" % e)

	i = 1
	while (True):
		current_time = time.time()

		with open(script_path + "\\equations.txt") as infile:
			for equation in infile:
				equation = equation.strip()
				if calc(equation, first['y'], first['x']):
					result = True
					for new_arr_item in new_arr:
						if not calc(equation, new_arr_item['y'], new_arr_item['x']):
							result = False
							break
					if result:
						writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение: " + equation)
						print(time.strftime("%d.%m.%Y %H:%M:%S") + " Решение: " + equation)
				
		total_time = time.time() - current_time
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " Проверены уравнения длинной " + str(i) + " символов за " + str(round(total_time, 2)) + " сек")
		build_equation(elements)
		i = i +1

def build_equation(elements):

	with open(script_path + "\\equations.txt") as infile:
		with open(script_path + "\\equations_tmp.txt", "a") as k:
			for equation in infile:
				equation = equation.strip()
				if equation:
					for element in elements:
						k.write(str(equation) + str(element) + "\n")
	
	os.remove(script_path + "\\equations.txt")
	os.rename(script_path + "\\equations_tmp.txt", script_path + "\\equations.txt")

	return True


def calc(equation, y, x):
	try:
		x_count = 0
		for x_item in x:
			equation = equation.replace("{x" + str(x_count) + "}", x_item)  
			x_count = x_count + 1

		y_equation = eval(equation)
		if y_equation == int(y):
			return True
	except:			
		return False

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

new_arr = [] # [1, [1, 2, 3, 4, 5]] Первый элемент значение (решение) уравнения, второй элемент входящие данные
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