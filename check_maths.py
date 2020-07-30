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

#Путь к располажению выполняемого скрипта
script_path = os.path.dirname(os.path.realpath(__file__))

# 1 Линейное 5 символов: y = ax + b
# 2 Теорема пифагора 8 символов: a ** 2 + b ** 2 = c ** 2
# 3 Квадратные ax ^ 2 + bx + c = 0
data_id = 2

#Имя файла с 'x' и 'y', например если data_id = 1, то data_filename будет 'data1.txt'
data_filename = "data" + str(data_id) + ".txt"

equation = "{b|(}{v|x0}{e|**2}{o|+}{v|x1}{e|**2}{b|)}{e|**0.5}"

with open(script_path + "\\" + data_filename) as f:
	arr = f.readlines() #считываем набор данных (например из файла data1.txt). Пример данных "3235	51	62	73"

new_arr = [] #В конце цикла массив new_arr должен содержать элементы вида [3235, [51, 62, 73]] Первый элемент значение (решение) уравнения y, второй элемент массив входящих данных x
for arr_item in arr:
	arr_item = arr_item.strip()
	arr_item = arr_item.split("\t")
	y = arr_item[0]
	arr_item.pop(0) # Удаляем первый элемент массива (y), он нам не нужен
	x = arr_item
	new_arr.append({"y": y, "x": x})

#если уравнение equation, выполнило проверку на большом наборе данных new_arr, то возвращается True
if core_maths.calc_all(equation, new_arr):
	print(True)
else:
	print(False)


#Команда для запуска:
#c:\Python38\python e:\python\maths\check_maths.py