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
#Пример входящих данных: {n|7}{o|+}{v|x0}
#Исходящие: 7 + 5, где 5 это x0
def format(equation, x):
	x_count = 0
	for x_item in x:
		equation = equation.replace("v|x" + str(x_count), x_item)  
		x_count = x_count + 1
	equation = equation.replace("n|", "")
	equation = equation.replace("o|", "")
	equation = equation.replace("b|", "")
	equation = equation.replace("e|", "")
	equation = equation.replace(";", "")

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
			
		
#Проверяет правилом можно ли делать конкатенцию двух соседей
#Берет последний элемент уравнения, определяет его тип (например v) и сравнивает с правилом (['o', 'b']) добавляемого элемента (например n)
#Входящие данные первый параметр: {n|7}{o|+}{v|x0}
#Входящие данные второй параметр: {n|8}
#Результат должен быть False
def is_allow_concat(equation, element):
	equation1 = get_last_element(equation)
	equation1_type = get_type(equation1)
	equation2_type = get_type(element)

	if equation1_type in config.types[equation2_type]['allow_left']:
		return True
	else:
		return False

#Получает последний элемент уравнения
#Входящие данные {n|7}{o|+}{v|x0}
#Результат {v|x0}
#Не используем регулярки, ибо накладно
def get_last_element(equation):
	if ';' not in equation:
		return equation
	start = equation.rfind(';') + 1
	end = len(equation)

	return equation[start:end]

#Получает тип элемента
#Входящие параметры {n|8}
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