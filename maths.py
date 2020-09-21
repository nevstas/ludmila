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
	first = new_arr[0] #����� �� �������� ������ ������ (�������� 100) ������ �������
	new_first_x = []
	fcount = 0
	for f in first['x']:
		new_first_x.append("v|x" + str(fcount))
		fcount = fcount + 1
	config.elements = config.elements + new_first_x #��������� � ��������� ��� 'x', �� ����� ���� ������ ����������
	
	config.elements_len = len(config.elements)

	equation = config.equation

	i = 1
	time_total_start = time.time()
	while (True):

		equation_format = core_maths.format(equation, first['x']) #����������� ���������

		#print(core_maths.format_human(equation))
		#core_maths.writeln(core_maths.format_human(equation))

		if core_maths.calc(equation_format, first['y']): #���� ��������� ��������� �� ����� ������ ������ x � y
			
			if core_maths.calc_all(equation, new_arr): #����� ��������� �������� ��������� �� ������� ������ ������ (�������� 100)
				time_total = time.time() - time_total_start
				core_maths.writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(config.data_id) + ": " + core_maths.format_human(equation) + " �� " + str(round(time_total, 2)) + " ���")
				print(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(config.data_id) + ": " + core_maths.format_human(equation) + " �� " + str(round(time_total, 2)) + " ���")
				
		equation = core_maths.equation_number_increment(equation)

		i = i +1

if os.path.isfile(config.script_path + "\equations.txt"):
	os.remove(config.script_path + "\equations.txt") #������� equations.txt
	
if os.path.isfile(config.script_path + "\equations_tmp.txt"):
	os.remove(config.script_path + "\equations_tmp.txt") #������� equations_tmp.txt

with open(config.script_path + "\\" + config.data_filename) as f:
	arr = f.readlines() #��������� ����� ������ (�������� �� ����� data1.txt). ������ ������ "3235	51	62	73"

new_arr = [] #� ����� ����� ������ new_arr ������ ��������� �������� ���� [3235, [51, 62, 73]] ������ ������� �������� (�������) ��������� y, ������ ������� ������ �������� ������ x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # ������� ������ ������� ������� (y), �� ��� �� �����
	x = arr_item
	new_arr.append({"y": y, "x": x})

task(new_arr) #�������� ��������� �������

#������� ��� �������:
#c:\Python38\python e:\python\maths\maths.py