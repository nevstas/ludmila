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

# 1 Линейное 5 символов: y = ax + b
# 2 Теорема пифагора 8 символов: a ** 2 + b ** 2 = c ** 2
# 3 Квадратные a * x ^ 2 + b * x + c = 0
data_id = 1

#Имя файла с 'x' и 'y', например если data_id = 1, то data_filename будет 'data1.txt'
data_filename = "data" + str(data_id) + ".txt"

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
	"o|-", 
	"o|*", 
	"o|/",

	#скобки ( и )
	"b|(",
	"b|)",

	#степень: 2 степень, 3 степень, корень квадратный, корень кубический
	"e|**2",
	"e|**3",
	"e|**0.5",
	"e|**(1/3)",
]

#для первого формирования списка уравнений удаляем некоторые элементы (например "/", так как деление не может идти в начале уравнения)
elements_start = list(elements)
elements_start.remove('o|+')
elements_start.remove('o|*')
elements_start.remove('o|/')
elements_start.remove('b|)')
elements_start.remove('e|**2')
elements_start.remove('e|**3')
elements_start.remove('e|**0.5')
elements_start.remove('e|**(1/3)')

#Ключи - типы элементов
#allow_left - правила при конкатенции. 
#При конкатенции элемента типа number смотрится на то кто стоит слева, разрешены o(operator) и b(#brackets)
#Если слева символ иного типа, то конкатенция не происходит
#Это сделано для уменьшения кол-ва вариантов при комбинаторике, уменьшения кол-ва ненужных итераций и уменьшения размера файла с уравнениями
types = {
	#number
	'n': {
		'allow_left': ['o', 'b'],
	},
	#operator
	'o': {
		'allow_left': ['n', 'b', 'v', 'e'],
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
		'allow_left': ['n', 'o', 'b', 'v'],
	},
}

