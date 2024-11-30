import time
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

def get_tasks(num_tasks=10):
    print(7777)
    # Создаем несколько задач для одновременной обработки
    tasks = []
    for _ in range(num_tasks):
        tasks.append([1, 2, 3, 4])
    return tasks

def task(position_start, position_end, position_decimal_start, position_decimal_end):
    # Выполнение задачи (например, печать начала позиции)
    print(f"Processing task with start: {position_start}")
    total = 0
    for i in range(10 ** 7):
        total += i % 10
    return total

def main():
    # Используем ProcessPoolExecutor для управления процессами
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        futures = []

        try:
            while True:
                # Получаем список задач
                task_list = get_tasks(num_tasks=200)  # Создаем больше задач, чтобы загрузить все ядра

                # Добавляем все задачи в пул
                for task_data in task_list:
                    future = executor.submit(task, task_data[0], task_data[1], task_data[2], task_data[3])
                    futures.append(future)

                # Ожидание завершения некоторых задач, чтобы избежать переполнения памяти
                # Проверяем завершенные задачи и убираем их из списка
                for f in as_completed(futures):
                    futures.remove(f)
        finally:
            # Ожидание завершения всех оставшихся задач перед выходом
            for future in futures:
                future.cancel()

if __name__ == '__main__':
    main()



#c:\Python311\python d:\python\maths\ludmila_processpoll_simple.py