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

#����������� ���������
#������ �������� ������: [1, 2, 3]
#���������: 7 + 5, ��� 5 ��� x0
def format(equation, x):
	equation = ''.join([config.elements[i] for i in equation])

	variable_count = 0
	for x_item in x:
		equation = equation.replace("v|x" + str(variable_count), x_item)
		variable_count = variable_count + 1
	equation = equation.replace("n|", "")
	equation = equation.replace("o|", "")
	equation = equation.replace("om|", "")
	equation = equation.replace("bl|", "")
	equation = equation.replace("br|", "")
	equation = equation.replace("e|", "")

	return equation

#��������� ��������� � ���������� ������� � 'y', ���� ������� ������ �����, �� ���������� True
#������ �������� ������: "51 * 62 + 73" � "3235"
#��������� True
def calc(equation, y):
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore") #��������� Warning �� ������ ���� � equation ����� �� ��������, �������� "4(3)"
			result_of_equation = eval(equation)
		if float(result_of_equation) == float(y):
			return True
	except:
		return False

#��������� ��� (�������� 100��) ��������� (�������� �� ����� data1.txt) � ���� ��� ��������� ������ �����, �� ���������� True
#��, ��� ������� calc() ������ ��������� �����, �� �������� ��� ��� ������� ���������. 
#���� calc() ������� True, �� ��������� ������� calc_all(), ��� ��������� ��������� �� ������� ���������� ������
#������ �������� ������: ������ "51 * 62 + 73" � "3235"
#��������� True
def calc_all(equation, dataset):
	for dataset_item in dataset:
		equation_format = format(equation, dataset_item['x'])
		if not calc(equation_format, dataset_item['y']):
			return False
	return True
			
		
#��������� ����� �� allow ��������, ������� ���� � ������ 
def check_allow_concat(equation):
	for key, e in enumerate(equation):
		if key == 0:
			left_element = ''
			left_element_type = get_type_of_element(left_element)
		else:
			left_element = equation[key - 1]
			left_element_type = get_type_of_element(config.elements[left_element])
		right_element = e
		right_element_type = get_type_of_element(config.elements[right_element])

		if not left_element_type in config.types_of_elements[right_element_type]['allow_left']:
			return {'result': False, 'key': key}
	return {'result': True, 'key': 0}

#�������� ��� ��������
#�������� ��������� n|8
#��������� n
#�� ���������� ���������, ��� ��������
def get_type_of_element(element):
	if not element:
		return 's'
	index_of_type = element.rfind('|')
	return element[0:index_of_type]

#����� � ��� log.txt (�������� ��������� ���������)
def writeln(str):
	myLock.acquire()		
	with open(config.script_path + "\log.txt", 'a') as the_file:
		the_file.write(str + "\n")
	myLock.release()

#�������� ������ [12, 9, 5]
#��������� ������ [12, 9, 6]
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
				print('��������� ��������� ������ ' + str(len(equation)))
				equation = [0] + equation
				return equation

#�������������� ��������� � ����������� ���
#�������� ������ [1, 2, 3]
#��������� ������ v|x0;o|*;v|x1;o|+;v|x2
def format_equation_to_human_view(equation):
	equation_human = ""
	for index_of_element in equation:
		if equation_human == "":
			equation_human = config.elements[index_of_element]
		else:
			equation_human = equation_human + ';' + config.elements[index_of_element]
	return equation_human