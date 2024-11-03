from threading import Lock
import warnings
import config

myLock = Lock()

#Форматирует уравнения
#Пример входящих данных: [1, 2, 3]
#Исходящие: 7 + 5, где 5 это x0
def format(equation, x):
	equation = ''.join([config.elements[i] for i in equation])
	for variable_count, x_item in enumerate(x):
		equation = equation.replace("v|x" + str(variable_count), x_item)
	equation = equation.replace("n|", "")
	equation = equation.replace("o|", "")
	equation = equation.replace("om|", "")
	equation = equation.replace("bl|", "")
	equation = equation.replace("br|", "")
	equation = equation.replace("e|", "")

	return equation

#Выполняет уравнение и српанивает решение с 'y', если решение решено верно, то возвращает True
#Пример входящих данных: "51 * 62 + 73" и "3235"
#Исходящие True
def calc(equation, y):
	try:
		with warnings.catch_warnings():
			warnings.simplefilter("ignore") #Отключаем Warning на сулчай если в equation будет не вылидным, например "4(3)"
			result_of_equation = eval(equation)
		if float(result_of_equation) == float(y):
			return True
		else:
			return False
	except:
		return False

#Выполняет все (например 100шт) уравнения (например из файла data1.txt) и если все уравнения решены верно, то возвращает True
#То, что функция calc() решила уравнение верно, не означает что это искомое уравнение.
#Если calc() вернула True, то запускаем функцию calc_all(), где проверяем уравнение на большом количестве данных
#Пример входящих данных: массив "51 * 62 + 73" и "3235"
#Исходящие True
def calc_all(equation, dataset):
	for dataset_item in dataset:
		equation_format = format(equation, dataset_item['x'])
		if not calc(equation_format, dataset_item['y']):
			return False
	return True
			
		
#Проверяет число по allow соседней, стоящих друг с другом
def check_allow_concat(equation):
	for key, e in enumerate(equation):
		if key == 0:
			left_element = ''
			left_element_type = get_type_of_element(left_element)
		else:
			left_element = equation[key - 1]
			left_element_type = get_type_of_element(config.elements[left_element])
		right_element = e
		right_element_type = get_type_of_element(config.elements[right_element])

		if not left_element_type in config.types_of_elements[right_element_type]['allow_left']:
			return {'result': False, 'key': key}
	return {'result': True, 'key': 0}

#Получает тип элемента
#Входящие параметры n|8
#Результат n
#Не используем регулярки, ибо накладно
def get_type_of_element(element):
	if not element:
		return 's'
	index_of_type = element.rfind('|')
	return element[0:index_of_type]

#Пишет в лог log.txt (например найденные уравнения)
the_file = open(config.script_path + "/log.txt", 'a')
def writeln(str):
    with myLock:
        with open(config.script_path + "/log.txt", 'a') as the_file:
            the_file.write(str + "\n")
            the_file.flush()

#Входящие данные [12, 9, 5]
#Исходящие данные [12, 9, 6]
def equation_number_increment(equation):
	current_index = len(equation) - 1
	while (True):
		equation = equation_number_increment_by_index(equation, current_index)
		check_equation = check_allow_concat(equation)

		if check_equation['result']:
			return equation
		else:
			for key, e in enumerate(equation):
				if key > check_equation['key']:
					equation[key] = 0
			current_index = check_equation['key']

def equation_number_increment_by_index(equation, current_index):
	while (True):
		current_number = equation[current_index]
		if current_number < (config.elements_len - 1):
			equation[current_index] = current_number + 1
			return equation
		else:
			if current_index > 0:
				equation[current_index] = 0
				current_index = current_index - 1
			else:
				for key, number in enumerate(equation):
					equation[key] = 0
				print('Проверены уравнения длиной ' + str(len(equation)))
				equation = [0] + equation
				return equation

#Форматирование уравнения в читабельный вид
#Входящие данные [1, 2, 3]
#исходящие данные v|x0;o|*;v|x1;o|+;v|x2
def format_equation_to_human_view(equation):
	equation_human = ""
	for index_of_element in equation:
		if equation_human == "":
			equation_human = config.elements[index_of_element]
		else:
			equation_human = equation_human + ';' + config.elements[index_of_element]
	return equation_human

#Ковертирует число десятичной системы счисления в число elements_len системы счисления (например 21)
#Входящие данные 24
#исходящие данные [1, 3]
def decimal_to_custom(number):
	x = (number % config.elements_len)
	ch = [x]
	if (number - x != 0):
		return decimal_to_custom(number // config.elements_len) + ch
	else:
		return ch

def custom_to_decimal(arr):
    decimal = 0
    for index, number in enumerate(reversed(arr)):
        decimal += number * (config.elements_len ** index)
    return decimal