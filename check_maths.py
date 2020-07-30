# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings

import core_maths

#���� � ������������ ������������ �������
script_path = os.path.dirname(os.path.realpath(__file__))

# 1 �������� 5 ��������: y = ax + b
# 2 ������� �������� 8 ��������: a ** 2 + b ** 2 = c ** 2
# 3 ���������� ax ^ 2 + bx + c = 0
data_id = 2

#��� ����� � 'x' � 'y', �������� ���� data_id = 1, �� data_filename ����� 'data1.txt'
data_filename = "data" + str(data_id) + ".txt"

equation = "{b|(}{v|x0}{e|**2}{o|+}{v|x1}{e|**2}{b|)}{e|**0.5}"

with open(script_path + "\\" + data_filename) as f:
	arr = f.readlines() #��������� ����� ������ (�������� �� ����� data1.txt). ������ ������ "3235	51	62	73"

new_arr = [] #� ����� ����� ������ new_arr ������ ��������� �������� ���� [3235, [51, 62, 73]] ������ ������� �������� (�������) ��������� y, ������ ������� ������ �������� ������ x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # ������� ������ ������� ������� (y), �� ��� �� �����
	x = arr_item
	new_arr.append({"y": y, "x": x})

#���� ��������� equation, ��������� �������� �� ������� ������ ������ new_arr, �� ������������ True
if core_maths.calc_all(equation, new_arr):
	print(True)
else:
	print(False)


#������� ��� �������:
#c:\Python38\python e:\python\maths\check_maths.py