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
#������ �������� ������: {n|7}{o|+}{v|x0}
#���������: 7 + 5, ��� 5 ��� x0
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

#��������� ��������� � ���������� ������� � 'y', ���� ������� ������ �����, �� ���������� True
#������ �������� ������: "51 * 62 + 73" � "3235"
#��������� True
def calc(equation, y):
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore") #��������� Warning �� ������ ���� � equation ����� "4(3)"
			y_equation = eval(equation)
		if float(y_equation) == float(y):
			return True
	except:			
		return False

#��������� ��� (�������� 100��) ��������� (�������� �� ����� data1.txt) � ���� ��� ��������� ������ �����, �� ���������� True
#��, ��� ������� calc() ������ ��������� �����, �� �������� ��� ��� ������� ���������. 
#���� calc() ������� True, �� ��������� ������� calc_all(), ��� ��������� ��������� �� ������� ���������� ������
#������ �������� ������: ������ "51 * 62 + 73" � "3235"
#��������� True
def calc_all(equation, new_arr):
	for new_arr_item in new_arr:
		equation_format = format(equation, new_arr_item['x'])
		if not calc(equation_format, new_arr_item['y']):
			return False
	return True
			
		
#��������� �������� ����� �� ������ ����������� ���� �������
#����� ��������� ������� ���������, ���������� ��� ��� (�������� v) � ���������� � �������� (['o', 'b']) ������������ �������� (�������� n)
#�������� ������ ������ ��������: {n|7}{o|+}{v|x0}
#�������� ������ ������ ��������: {n|8}
#��������� ������ ���� False
def is_allow_concat(equation, element):
	equation1 = get_last_element(equation)
	equation1_type = get_type(equation1)
	equation2_type = get_type(element)

	if equation1_type in config.types[equation2_type]['allow_left']:
		return True
	else:
		return False

#�������� ��������� ������� ���������
#�������� ������ {n|7}{o|+}{v|x0}
#��������� {v|x0}
#�� ���������� ���������, ��� ��������
def get_last_element(equation):
	if ';' not in equation:
		return equation
	start = equation.rfind(';') + 1
	end = len(equation)

	return equation[start:end]

#�������� ��� ��������
#�������� ��������� {n|8}
#��������� n
#�� ���������� ���������, ��� ��������
def get_type(equation):
	if not equation:
		return 's'
	end = equation.rfind('|')
	return equation[0:end]

#����� � ��� log.txt (�������� ��������� ���������)
def writeln(str):
	myLock.acquire()		
	with open(config.script_path + "\log.txt", 'a') as the_file:
		the_file.write(str + "\n")
	myLock.release()