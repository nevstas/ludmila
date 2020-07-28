# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

myLock = Lock()

#6 ��������, ������ ����� 355��
#6 ��������, ����������� "variable -> v" ������ ����� 161��


# 1 �������� 5 ��������: y = ax + b
# 2 ������� �������� 8 ��������: a ** 2 + b ** 2 = c ** 2
# 3 ���������� ax ^ 2 + bx + c = 0
data_id = 2

data_filename = "data" + str(data_id) + ".txt"


elements = [
	"{n|0}",
	"{n|1}",
	"{n|2}",
	"{n|3}",
	"{n|4}",
	"{n|5}",
	"{n|6}",
	"{n|7}",
	"{n|8}",
	"{n|9}",
	"{n|10}",
	"{o|+}", 
	"{o|-}", 
	"{o|*}", 
	"{o|/}",
	"{b|(}",
	"{b|)}",
	"{e|**2}",
	"{e|**3}",
	"{e|**0.5}",
	"{e|**(1/3)}",
]

script_path = os.path.dirname(os.path.realpath(__file__))

types = {
	#number
	'n': {
		'allow_left': ['o', 'b'],
	},
	#operator
	'o': {
		'allow_left': ['n', 'v', 'b'],
	},
	#brackets
	'b': {
		'allow_left': ['n', 'o', 'v', 'e'],
	},
	#variable
	'v': {
		'allow_left': ['o', 'b'],
	},
	#exponentiation
	'e': {
		'allow_left': ['n', 'o', 'b'],
	},
}

def task(new_arr):
	global elements
	global data_id
	first = new_arr[0]
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("{v|x" + str(fcount) + "}")
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
						writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(data_id) + ": " + equation + " �� " + str(round(time_total, 2)) + " ���")
						print(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(data_id) + ": " + equation + " �� " + str(round(time_total, 2)) + " ���")
				
		time_total = time.time() - time_total_start
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " ��������� ��������� ������� " + str(i) + " �������� �� " + str(round(time_total, 2)) + " ���")
		build_equation(elements)
		i = i +1

#����������� (������������) ������������ ������ equations.txt � �������� elements, � �������� ��������� ������� � equations.txt
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

#������ �������� ������: {n|7}{o|+}{v|x0}
#���������: 7 + 5, ��� 5 ��� x0
def format(equation, x):
	x_count = 0
	for x_item in x:
		equation = equation.replace("{v|x" + str(x_count) + "}", x_item)  
		x_count = x_count + 1
	equation = equation.replace("{n|", "")
	equation = equation.replace("{o|", "")
	equation = equation.replace("{b|", "")
	equation = equation.replace("{e|", "")
	equation = equation.replace("}", "")

	return equation

def calc(equation, y):
	try:
		y_equation = eval(equation)
		if float(y_equation) == float(y):
			return True
	except:			
		return False

#�������� ������ ������ ��������: {n|7}{o|+}{v|x0}
#�������� ������ ������ ��������: {n|8}
#��������� ������ ���� False
def is_allow_concat(equation, element):
	equation1 = get_last_element(equation)
	equation1_type = get_type(equation1)
	equation2_type = get_type(element)
	
	if equation1_type in types[equation2_type]['allow_left']:
		return True
	else:
		return False

#�������� ������ {n|7}{o|+}{v|x0}
#��������� {v|x0}
#�� ���������� ���������, ��� ��������
def get_last_element(equation):
	start = equation.rfind('{')
	end = len(equation)
	return equation[start:end]

#�������� ��������� {n|8}
#��������� number
#�� ���������� ���������, ��� ��������
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

with open(script_path + '\\' + data_filename) as f:
	arr = f.readlines()

new_arr = [] # [1, [1, 2, 3, 4, 5]] ������ ������� �������� (�������) ��������� y, ������ ������� ������ �������� ������ x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # ������� ������ ������� ������� (y), �� ��� �� �����
	x = arr_item
	new_arr.append({"y": y, "x": x})

task(new_arr)

#������� ��� �������:
#c:\\Python38\\python z:\\python\\maths\\maths.py