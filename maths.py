# -*- coding: windows-1251 -*-

# 1 Линейное y = ax + b
# 2 Теорема пифагора
# 3 Квадратные

import os
import subprocess, time

elements = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "+", "-", "*", "/"]

script_path = os.path.dirname(os.path.realpath(__file__))

def task(new_arr):
	global elements
	first = new_arr[0]
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{{x" + str(fcount) + "}}")
		fcount = fcount + 1
	elements = elements + new_first_x
	equations = elements
	i = 1
	while (True):
		current_time = time.time()
		for equation in equations:
			#if (equation == "{{x0}}*{{x1}}+{{x2}}"):
			#	print(22222)
			
			if calc(equation, first['y'], first['x']):
				result = True
				for new_arr_item in new_arr:
					if not calc(equation, new_arr_item['y'], new_arr_item['x']):
						result = False
						break
				if result:
					print("Решение: " + equation)
				
		total_time = time.time() - current_time
		print("Проверены уравнения длинной " + str(i) + " символов за " + str(round(total_time, 2)) + " сек")
		equations = build_equation(equations, elements)
		i = i +1

def build_equation(equations, elements):
	new_equations = []
	for equation in equations:
		for element in elements:
			new_equations.append(equation + element)
	return new_equations


def calc(equation, y, x):
	try:
		x_count = 0
		for x_item in x:
			equation = equation.replace("{{x" + str(x_count) + "}}", x_item)  
			x_count = x_count + 1

		y_equation = eval(equation)
		if y_equation == int(y):
			return True
	except:			
		return False

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


	#for element in elements:

task(new_arr)

#c:\\Python38\\python z:\\python\\maths\\maths.py