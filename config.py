# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings

#Путь к располажению выполняемого скрипта
script_path = os.path.dirname(os.path.realpath(__file__))

# 1 Линейное 5 символов 
# y = ax + b
# v|x0;o|*;v|x1;o|+;v|x2

# 2 Теорема пифагора 8 символов
# a ** 2 + b ** 2 = c ** 2 
# bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5

# 3 ряд простых чисел

# 4 Квадратные a * x ^ 2 + b * x + c = 0

data_id = 2

#Имя файла с 'x' и 'y', например если data_id = 1, то data_filename будет 'data1.txt'
data_filename = "data" + str(data_id) + ".txt"

equation = [0]

#элементы, из которых составляются уравнения путем конкатенции друг с другом
elements = [
	#числа: 0-10
	"n|0",
	"n|1",
	"n|2",
	"n|3",
	"n|4",
	"n|5",
	"n|6",
	"n|7",
	"n|8",
	"n|9",
	"n|10",

	#операции: +, -, *, /
	"o|+", 
	"o|*", 
	"o|/",
	"om|-", 

	#скобки ( и )
	"bl|(",
	"br|)",

	#степень: 2 степень, 3 степень, корень квадратный, корень кубический
	"e|**2",
	"e|**3",
	"e|**0.5",
	"e|**(1/3)",
]

elements_len = len(elements)

#Ключи - типы элементов
#allow_left - правила при конкатенции, содержит типы элементов, которые могут находится слева
#При конкатенции элемента типа number смотрится на то кто стоит слева, разрешены o(operator), om(operator minus), s(start) и bl(bracket left)
#Если слева символ иного типа, то конкатенция не происходит
#Это сделано для уменьшения кол-ва вариантов при комбинаторике, уменьшения кол-ва ненужных итераций

types = {
	#start начало строки
	's': {
		'allow_left': [],
	},
	#number
	'n': {
		'allow_left': ['s', 'o', 'om', 'bl'],
	},
	#operator
	'o': {
		'allow_left': ['n', 'br', 'v', 'e'],
	},
	#operator minus
	'om': {
		'allow_left': ['s', 'n', 'bl', 'br', 'v', 'e'],
	},
	#bracket left
	'bl': {
		'allow_left': ['s', 'o', 'om', 'e'],
	},
	#bracket right
	'br': {
		'allow_left': ['n', 'v', 'e'],
	},
	#variable
	'v': {
		'allow_left': ['s', 'o', 'om', 'bl'],
	},
	#exponentiation
	'e': {
		'allow_left': ['n', 'br', 'v'],
	},
}

