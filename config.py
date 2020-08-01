# -*- coding: windows-1251 -*-
import os
import subprocess, time
from threading import Lock

from threading import Lock
import re
import hashlib

import sys
import warnings

#���� � ������������ ������������ �������
script_path = os.path.dirname(os.path.realpath(__file__))

# 1 �������� 5 ��������: y = ax + b
# 2 ������� �������� 8 ��������: a ** 2 + b ** 2 = c ** 2
# 4
# ���������� a * x ^ 2 + b * x + c = 0
data_id = 1

#��� ����� � 'x' � 'y', �������� ���� data_id = 1, �� data_filename ����� 'data1.txt'
data_filename = "data" + str(data_id) + ".txt"

#��������, �� ������� ������������ ��������� ����� ����������� ���� � ������
elements = [
	#�����: 0-10
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

	#��������: +, -, *, /
	"o|+", 
	"o|*", 
	"o|/",
	"om|-", 

	#������ ( � )
	"bl|(",
	"br|)",

	#�������: 2 �������, 3 �������, ������ ����������, ������ ����������
	"e|**2",
	"e|**3",
	"e|**0.5",
	"e|**(1/3)",
]

#����� - ���� ���������
#allow_left - ������� ��� �����������, �������� ���� ���������, ������� ����� ��������� �����
#��� ����������� �������� ���� number ��������� �� �� ��� ����� �����, ��������� o(operator) � b(#brackets)
#���� ����� ������ ����� ����, �� ����������� �� ����������
#��� ������� ��� ���������� ���-�� ��������� ��� �������������, ���������� ���-�� �������� �������� � ���������� ������� ����� � �����������
types = {
	#start ������ ������
	's': {
		'allow_left': [],
	},
	#number
	'n': {
		'allow_left': ['s', 'o', 'om', 'bl'],
	},
	#operator
	'o': {
		'allow_left': ['n', 'bl', 'br', 'v', 'e'],
	},
	#operator minus
	'om': {
		'allow_left': ['s', 'n', 'bl', 'br', 'v', 'e'],
	},
	#bracket left
	'bl': {
		'allow_left': ['s', 'o', 'om', 'v', 'e'],
	},
	#bracket right
	'br': {
		'allow_left': ['n', 'v', 'e'],
	},
	#variable
	'v': {
		'allow_left': ['s', 'o', 'om', 'br'],
	},
	#exponentiation
	'e': {
		'allow_left': ['n', 'br', 'v'],
	},
}

