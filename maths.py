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
		new_first_x.append("{v|x" + str(fcount) + "}")
		fcount = fcount + 1
	config.elements = config.elements + new_first_x #��������� � ��������� ��� 'x', �� ����� ���� ������ ����������

	with open(config.script_path + "\equations.txt", 'w') as f:
		for e in config.elements:
			f.write("%s\n" % e) #����� � ���� ��� ��������. � ������ �������� ����� ����������� ��������� ���� y = 1, y = 2. ������ ��������� ����� �����������

	i = 1
	time_total_start = time.time()
	while (True):

		with open(config.script_path + "\equations.txt") as infile:
			with open(config.script_path + "\equations_tmp.txt", "a") as k:
				for equation in infile: #��������� ������ ���� equations.txt ��� �������� ��� � ����������� ������
					equation = equation.strip()
					if equation:
						for element in config.elements: #���������� �� ��������� ���������
							if core_maths.is_allow_concat(equation, element): #��������� �� �������� ����� �� ������ ����������� �������
								k.write(str(equation) + str(element) + "\n") #� ����� � ���� equations_tmp.txt ����������, ������ ������� �� ����� equations.txt ������������� � ���������� ����������
					equation_format = core_maths.format(equation, first['x']) #����������� ���������
					if core_maths.calc(equation_format, first['y']): #���� ��������� ��������� �� ����� ������ ������ x � y
						if core_maths.calc_all(equation, new_arr): #����� ��������� �������� ��������� �� ������� ������ ������ (�������� 100)
							time_total = time.time() - time_total_start
							core_maths.writeln(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(config.data_id) + ": " + equation + " �� " + str(round(time_total, 2)) + " ���")
							print(time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(config.data_id) + ": " + equation + " �� " + str(round(time_total, 2)) + " ���")
		
		os.remove(config.script_path + "\equations.txt") #������� ���� equations.txt
		os.rename(config.script_path + "\equations_tmp.txt", config.script_path + "\equations.txt") #� �� ��� ����� ����� ����� ���� equations_tmp.txt, � ������� ���������� ��������� ������������� � ���������� ����������
				
		time_total = time.time() - time_total_start
		print(time.strftime("%d.%m.%Y %H:%M:%S") + " ��������� ��������� ������� " + str(i) + " �������� �� " + str(round(time_total, 2)) + " ���")
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