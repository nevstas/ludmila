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
import core

myLock = Lock()

def task(dataset):
	global config
	first_element_of_dataset = dataset[0] #����� �� �������� ������ ������ (�������� 100) ������ �������
	variable_elements = []
	variable_count = 0
	for f in first_element_of_dataset['x']:
		variable_elements.append("v|x" + str(variable_count))
		variable_count = variable_count + 1
	config.elements = config.elements + variable_elements #��������� � ��������� ��� 'x', �� ����� ���� ������ ����������
	
	config.elements_len = len(config.elements)

	equation = config.equation

	time_total_start = time.time()
	while (True):

		equation_format = core.format(equation, first_element_of_dataset['x']) #����������� ���������

		#print(core.format_equation_to_human_view(equation))
		# core.writeln(core.format_equation_to_human_view(equation))

		if core.calc(equation_format, first_element_of_dataset['y']): #���� ��������� ��������� �� ����� ������ ������ x � y
			
			if core.calc_all(equation, dataset): #����� ��������� �������� ��������� �� ������� ������ ������ (�������� 100)
				time_total = time.time() - time_total_start
				message = time.strftime("%d.%m.%Y %H:%M:%S") + " ������� data" + str(config.dataset_id) + ": " + core.format_equation_to_human_view(equation) + " �� " + str(round(time_total, 2)) + " ���"
				core.writeln(message)
				print(message)
				
		equation = core.equation_number_increment(equation)

with open(config.script_path + "\\datasets\\" + config.dataset_filename) as f:
	dataset_plain = f.readlines() #��������� ����� ������ (�������� �� ����� data1.txt). ������ ������ "3235	51	62	73"

dataset = [] #dataset �������� �������� ���� {'y': 3235, 'x': [51, 62, 73]} ������ ������� �������� (�������) ��������� y, ������ ������� ������ �������� ������ x
for dataset_plain_item in dataset_plain:
	dataset_plain_item = dataset_plain_item.strip()
	dataset_plain_item = dataset_plain_item.split("\t")
	y = dataset_plain_item[0]
	dataset_plain_item.pop(0) # ������� ������ ������� ������� (y), �� ��� �� �����
	x = dataset_plain_item
	dataset.append({"y": y, "x": x})

task(dataset) #�������� ��������� �������
