# Ludmila - решение нерешенных математических задач методом подбора

[README.md](README.md) - английская версия README.md 

[README-RU.md](README-RU.md) - русская версия README.md

## Описание
Скрипт Ludmila предназначен для решения нерешенных математических задач методом подбора.
Есть список элементов уравнений:

- числа (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- операции (+, *, /, -)
- скобки (левая, правая)
- степень (квадратная, кубическая, корень квадратный, корень кубический)
- x (может быть несколько в наборе - x0, x1, x2, ...)

Есть входящие наборы данных:
- `data1.txt` (линейное уравнение)
- `data2.txt` (теорема пифагора)
- `data3.txt` (ряд простых чисел)

Например набор `data1.txt` (линейное уравнение) выглядит вот так:

```
3235	51	62	73
3350	52	63	74
3467	53	64	75
...
```
(всего 100 элеметов в наборе)

Первая цифра значение `y`, последующие цифры значения `x` (в данном случае x0, x1, x2) 

Для нахождения верного уравнения перебираются комбинации уравнений. Выглядит это примерно так:

```
y = 1
y = 2
...
```

перебираются все уравнения длинной 1, затем длинной 2. Уравнения длинной 3 могут выглядеть например так:

```
y = 1 + x0
y = 1 + x1
...
```
и так далее, пока не дойдет до:

```
y = x0 * x1 + x2
```

В итоге набор данных `(3235	51	62	73)` выдаст совпадение, далее эта форумла перебирает все наборы данных `data1.txt` их всего 100 штук. И если все 100 наборы данных прошли проверку, то уравнение считается решенным.

## Производительность
Производительность на CPU:

- Линейное уравнение решается за 7 секунд (5 символов) `v|x0;o|*;v|x1;o|+;v|x2`
- Теорема пифагора решается за 8100 секунд (8 символов) `bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5`

Производительность на GPU:
- Линейное уравнение решается за 0.27 секунд (5 символов) `v|x0;o|*;v|x1;o|+;v|x2`
- Теорема пифагора решается за 168 секунд (8 символов) `bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5`

## Задачи
Главной задачей данного скрипта является решение нерешенных математических задач 
- [Открытые математические проблемы](https://ru.wikipedia.org/wiki/%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8B%D0%B5_%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D0%B5_%D0%BF%D1%80%D0%BE%D0%B1%D0%BB%D0%B5%D0%BC%D1%8B)
- [Задачи тысячелетия](https://ru.wikipedia.org/wiki/%D0%97%D0%B0%D0%B4%D0%B0%D1%87%D0%B8_%D1%82%D1%8B%D1%81%D1%8F%D1%87%D0%B5%D0%BB%D0%B5%D1%82%D0%B8%D1%8F)

Но не все они могут быть представлены в виде наборов данных.

## To Do
- Добавить больше математических операций - sin, cos, tg, ctg, π, e, log (упадет производительность, но увеличится вероятность нахождения формулы).
- Добавить наборы данных для других нерешенных математических задач.

## Запуск
- В переменной `dataset_id` указать id набора данных (1 - линейное, 2 - теорема пифагора, 3 - ряд простых чисел). Чтобы добавить dataset нового уравнения - поместите файл в папку `datasets` (разделитель tab; первый элемент y, остальные элементы это x)
- Запустить файл `ludmila_cpu.py` командой:
```
c:\Python311\python d:\python\maths\ludmila_cpu.py
```
- Результат будет в консоле, а так же в лог файле `log.txt`
- Для запуска GPU версии используйте [ludmila_gpu.py](ludmila_gpu.py)
- Для запуска [google_colab_gpu.py](google_colab_gpu.py) используйте блокнот google colab [google_colab_gpu.ipynb](google_colab_gpu.ipynb)

## Файлы
- [ludmila_cpu.py](ludmila_cpu.py) - CPU
- [ludmila_cpu_processpoll.py](ludmila_cpu_processpoll.py) - CPU multiprocessing
- [ludmila_gpu.py](ludmila_gpu.py) - GPU (рекомендуется)
- [google_colab_cpu.py](google_colab_cpu.py) - Google Colab CPU
- [google_colab_cpu_processpoll.py](google_colab_cpu_processpoll.py) - Google Colab CPU multiprocessing
- [google_colab_gpu.py](google_colab_gpu.py) - Google Colab GPU (рекомендуется), также смотрите [google_colab_gpu.ipynb](google_colab_gpu.ipynb)

## Обсуждение на форумах математиков и программистов
- [linux.org.ru](https://www.linux.org.ru/forum/general/16478781)
- [dxdy.ru](https://dxdy.ru/topic146962.html)
- [ru.stackoverflow.com](https://ru.stackoverflow.com/questions/1318101/gpu-%d0%b2%d1%8b%d1%87%d0%b8%d1%81%d0%bb%d0%b5%d0%bd%d0%b8%d1%8f-%d0%b2%d0%bc%d0%b5%d1%81%d1%82%d0%be-cpu-%d0%b2%d1%8b%d1%87%d0%b8%d1%81%d0%bb%d0%b5%d0%bd%d0%b8%d0%b9)
- [python.su](https://python.su/forum/topic/40596/)
- [mathhelpplanet.com](http://mathhelpplanet.com/viewtopic.php?f=51&t=74861)
- [cyberforum.ru](https://www.cyberforum.ru/python-science/thread2865629.html)
- [mathforum.ru](http://www.mathforum.ru/forum/read/1/103766/)
- [alexlarin.com](https://alexlarin.com/viewtopic.php?f=4&t=17347)
- [math10.com](https://www.math10.com/ru/forum/viewtopic.php?f=42&t=3185)
- [math.hashcode.ru](http://math.hashcode.ru/questions/226775/python-ludmila-%D1%80%D0%B5%D1%88%D0%B5%D0%BD%D0%B8%D0%B5-%D0%BD%D0%B5%D1%80%D0%B5%D1%88%D0%B5%D0%BD%D0%BD%D1%8B%D1%85-%D0%BC%D0%B0%D1%82%D0%B5%D0%BC%D0%B0%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B8%D1%85-%D0%B7%D0%B0%D0%B4%D0%B0%D1%87-%D0%BC%D0%B5%D1%82%D0%BE%D0%B4%D0%BE%D0%BC-%D0%BF%D0%BE%D0%B4%D0%B1%D0%BE%D1%80%D0%B0)
- [boinc.berkeley.edu](https://boinc.berkeley.edu/forum_thread.php?id=15575)

## Полезные ссылки
- [BOINC](https://ru.wikipedia.org/wiki/BOINC)
- [Добровольные вычисления](https://ru.wikipedia.org/wiki/%D0%94%D0%BE%D0%B1%D1%80%D0%BE%D0%B2%D0%BE%D0%BB%D1%8C%D0%BD%D1%8B%D0%B5_%D0%B2%D1%8B%D1%87%D0%B8%D1%81%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F)
- [Google Colab](https://colab.research.google.com/signup)
- [RunPod](https://www.runpod.io/pricing)