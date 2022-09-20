import os
import sys

#Путь к папке выполняемого скрипта
script_path = "e:\python\maths"

# 1 Линейное 5 символов
# y = ax + b
# v|x0;o|*;v|x1;o|+;v|x2

# 2 Теорема пифагора 8 символов
# a ** 2 + b ** 2 = c ** 2 
# bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5

# 3 ряд простых чисел


dataset_id = 1

#Имя файла с 'x' и 'y', например если dataset_id = 1, то dataset_filename будет 'data1.txt'
dataset_filename = "data" + str(dataset_id) + ".txt"

#Текущее уравнение с которого начинаем, далее оно будет инкрементится
equation = [0]

#элементы, из которых составляются уравнения путем конкатенции друг с другом
#21-чная система счисления (от 0 до 20)
#"0" => "n|0", "1" => "n|1", "2" => "n|2", "3" => "n|3", "4" => "n|4", "5" => "n|5"
#"6" => "n|6", "7" => "n|7", "8" => "n|8", "9" => "n|9", "10" => "n|10"
#"11" => "o|+", 12" => "o|*", 13" => "o|/", 14" => "om|-"
#"15" => "bl|(", "16" => "br|)"
#"17" => "e|**2", "18" => "e|**3", "19" => "e|**0.5", "20" => "e|**(1/3)"
#"21" => "n|1;n|0"
#"22" => "n|1;n|1"
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

types_of_elements = {
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

