# Ludmila – Solving Unsolved Mathematical Problems by Brute Force

[README.md](README.md) – English version of README.md  

[README-RU.md](README-RU.md) – Russian version of README.md  

## Description
The Ludmila script is designed to solve unsolved mathematical problems using a brute-force method.  
It has a list of equation elements:

- Numbers (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
- Operations (+, *, /, -)
- Brackets (left, right)
- Powers (square, cubic, square root, cube root)
- Variables `x` (there can be several in the dataset – x0, x1, x2, ...)

It uses input datasets:
- `data1.txt` (linear equation)
- `data2.txt` (Pythagoras theorem)
- `data3.txt` (prime number series)

Example of `data1.txt` (linear equation):

```
3235    51    62    73
3350    52    63    74
3467    53    64    75
...
```
(100 elements total)

The first number is the value of `y`, the following numbers are the values of `x` (in this case x0, x1, x2).

To find the correct equation, combinations of equations are iterated over. It looks like this:

```
y = 1
y = 2
...
```

All equations of length 1 are tried, then of length 2. Equations of length 3 might look like:

```
y = 1 + x0
y = 1 + x1
...
```
and so on until reaching:

```
y = x0 * x1 + x2
```

As a result, the dataset `(3235  51  62  73)` will produce a match, then this formula is tested on all datasets in `data1.txt` (100 total). If all 100 datasets pass, the equation is considered solved.

## Optimization
Since it makes no sense to have, for example, two `+` operators next to each other, concatenation rules define what can be next to what.  
This increased the script’s speed by 15 times.  
The concatenation rules are found in variable `types_of_elements`.

## Performance
Performance on CPU:

- Linear equation is solved in 7 seconds (5 characters): `v|x0;o|*;v|x1;o|+;v|x2`
- Pythagoras theorem is solved in 8100 seconds (8 characters): `bl|(;v|x0;e|**2;o|+;v|x1;e|**2;br|);e|**0.5`

## Purpose
The main goal of this script is to solve unsolved mathematical problems:  
- [Open Mathematical Problems](https://en.wikipedia.org/wiki/List_of_unsolved_problems_in_mathematics)
- [Millennium Prize Problems](https://en.wikipedia.org/wiki/Millennium_Prize_Problems)

But not all of them can be represented as datasets.

## To Do
- Rewrite to use GPU instead of CPU
- Add more mathematical operations – sin, cos, tg, ctg, π, e, log (performance will drop, but the probability of finding a formula will increase).
- Add datasets for other unsolved mathematical problems.

## How to Run
- Set the variable `dataset_id` to the dataset ID (1 – linear, 2 – Pythagoras theorem, 3 – prime number series).  
  To add a dataset for a new equation, place the file in the `datasets` folder (tab separator; first element is `y`, the rest are `x`).
- Run the file `ludmila.py` with the command:
```
c:\Python37\python e:\python\maths\ludmila.py
```
- The result will be in the console and also in the log file `log.txt`.

## Files
- [ludmila.py](ludmila.py) – CPU
- [ludmila_processpoll.py](ludmila_processpoll.py) – CPU multiprocessing
- [google_colab.py](google_colab.py) – CPU Google Colab
- [google_colab_processpoll.py](google_colab_processpoll.py) – CPU Google Colab multiprocessing  

## Discussions on Mathematician & Programmer Forums
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

## Useful Links
- [BOINC](https://en.wikipedia.org/wiki/BOINC)
- [Volunteer Computing](https://en.wikipedia.org/wiki/Volunteer_computing)
