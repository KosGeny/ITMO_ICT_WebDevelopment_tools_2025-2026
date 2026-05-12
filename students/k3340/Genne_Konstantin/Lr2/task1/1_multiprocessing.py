import time
import multiprocessing
import os

N = 10000000000
WORKERS_NUM = os.cpu_count()
CHUNK_SIZE = N // WORKERS_NUM
EXPECTED_SUM = N * (N + 1) // 2

def calculate_sum(start, end):
    part_sum = 0
    for i in range(start, end+1):
        part_sum += i
    return part_sum

def main():
    ranges = []
    for i in range(WORKERS_NUM):
        start = i * CHUNK_SIZE + 1
        end = (i + 1) * CHUNK_SIZE if i < WORKERS_NUM - 1 else N
        ranges.append((start, end))

    start_t = time.perf_counter()

    with multiprocessing.Pool(processes=WORKERS_NUM) as pool:
        sums = pool.starmap(calculate_sum, ranges)
    
    total_sum = sum(sums)

    elapsed_t = time.perf_counter() - start_t

    print("Сумма чисел с использованием MULTIPROCESSING\n")
    print(f"Количество workers: {WORKERS_NUM}")
    print(f"Ожидаемая сумма: {EXPECTED_SUM}")
    print(f"Полученная сумма: {total_sum}")
    print(f"Затраченное время: {elapsed_t} сек")

if __name__ == "__main__":
    main()