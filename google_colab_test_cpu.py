import time

y = 4211
start, end = -100000000, 99
base = 59 * 70

t0 = time.perf_counter()

solution = None
for x in range(start, end + 1):
    if y == base + x:
        solution = x
        break

t1 = time.perf_counter()

if solution is not None:
    elapsed = t1 - t0
    ms = int((elapsed % 1) * 1000)
    sec = int(elapsed) % 60
    mins = int(elapsed // 60)
    print(f"Решение: x = {solution}")
    print(f"Время: {mins} мин {sec} сек {ms} мс")
else:
    print("Решения в заданном диапазоне нет.")
