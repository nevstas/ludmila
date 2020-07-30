# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings

# 1 Линейное 5 символов: y = ax + b
# 2 Теорема пифагора 8 символов: a ** 2 + b ** 2 = c ** 2
# 3 Квадратные ax ^ 2 + bx + c = 0
data_id = 2

data_filename = "data" + str(data_id) + ".txt"


elements = [
	"{n|0}",
	"{n|1}",
	"{n|2}",
	"{n|3}",
	"{n|4}",
	"{n|5}",
	"{n|6}",
	"{n|7}",
	"{n|8}",
	"{n|9}",
	"{n|10}",
	"{o|+}", 
	"{o|-}", 
	"{o|*}", 
	"{o|/}",
	"{b|(}",
	"{b|)}",
	"{e|**2}",
	"{e|**3}",
	"{e|**0.5}",
	"{e|**(1/3)}",
]

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

script_path = os.path.dirname(os.path.realpath(__file__))