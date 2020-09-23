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

myLock = Lock()

#Форматирует уравнения
#Пример входящих данных: [1, 2, 3]
#Исходящие: 7 + 5, где 5 это x0
def format(equation, x):
	equation = ''.join([config.elements[i] for i in equation])

	x_count = 0
	for x_item in x:
		equation = equation.replace("v|x" + str(x_count), x_item)  
		x_count = x_count + 1
	equation = equation.replace("n|", "")
	equation = equation.replace("o|", "")
	equation = equation.replace("om|", "")
	equation = equation.replace("bl|", "")
	equation = equation.replace("br|", "")
	equation = equation.replace("e|", "")

	return equation

#Выполняет уравнение и српанивает решение с 'y', если решение решено верно, то возвращает True
#Пример входящих данных: "51 * 62 + 73" и "3235"
#Исходящие True
def calc(equation, y):
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore") #Отключаем Warning на сулчай если в equation будет "4(3)"
			y_equation = eval(equation)
		if float(y_equation) == float(y):
			return True
	except:			
		return False

#Выполняет все (например 100шт) уравнения (например из файла data1.txt) и если все уравнения решены верно, то возвращает True
#То, что функция calc() решила уравнение верно, не означает что это искомое уравнение. 
#Если calc() вернула True, то запускаем функцию calc_all(), где проверяем уравнение на большом количестве данных
#Пример входящих данных: массив "51 * 62 + 73" и "3235"
#Исходящие True
def calc_all(equation, new_arr):
	for new_arr_item in new_arr:
		equation_format = format(equation, new_arr_item['x'])
		if not calc(equation_format, new_arr_item['y']):
			return False
	return True
			
		
#Проверяет число по allow соседней, стоящих друг с другом 
def check_allow_concat(equation):
	for key, e in enumerate(equation):
		if key == 0:
			left_element = ''
			left_element_type = get_type(left_element)
		else:
			left_element = equation[key - 1]
			left_element_type = get_type(config.elements[left_element])
		right_element = e
		right_element_type = get_type(config.elements[right_element])

		if not left_element_type in config.types[right_element_type]['allow_left']:
			return {'result': False, 'key': key}
	return {'result': True, 'key': 0}

#Получает тип элемента
#Входящие параметры n|8
#Результат n
#Не используем регулярки, ибо накладно
def get_type(equation):
	if not equation:
		return 's'
	end = equation.rfind('|')
	return equation[0:end]

#Пишет в лог log.txt (например найденные уравнения)
def writeln(str):
	myLock.acquire()		
	with open(config.script_path + "\log.txt", 'a') as the_file:
		the_file.write(str + "\n")
	myLock.release()

#Входящие данные [12, 9, 5]
#Исходящие данные [12, 9, 6]
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
		if current_number < (config.elements_len - 1):
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

#Форматирование уравнения в читабельный вид
#Входящие данные [1, 2, 3]
#исходящие данные v|x0;o|*;v|x1;o|+;v|x2
def format_human(equation):
	equation_human = ""
	for e in equation:
		if equation_human == "":
			equation_human = config.elements[e]
		else:
			equation_human = equation_human + ';' + config.elements[e]
	return equation_human