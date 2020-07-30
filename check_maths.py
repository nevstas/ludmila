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

script_path = os.path.dirname(os.path.realpath(__file__))
data_id = 2
data_filename = "data" + str(data_id) + ".txt"

equation = "{b|(}{v|x0}{e|**2}{o|+}{v|x1}{e|**2}{b|)}{e|**0.5}"

with open(script_path + "\\" + data_filename) as f:
	arr = f.readlines()

new_arr = [] # [1, [1, 2, 3, 4, 5]] Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = arr_item
	new_arr.append({"y": y, "x": x})

if core_maths.calc_all(equation, new_arr):
	print(True)
else:
	print(False)


#Команда для запуска:
#c:\Python38\python e:\python\maths\check_maths.py