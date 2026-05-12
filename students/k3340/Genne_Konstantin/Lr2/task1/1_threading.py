import time
import threading
import os

N = 10000000000
WORKERS_NUM = os.cpu_count()
CHUNK_SIZE = N // WORKERS_NUM
EXPECTED_SUM = N * (N + 1) // 2

def calculate_sum(start, end, results, index):
    part_sum = 0
    for i in range(start, end + 1):
        part_sum += i
    results[index] = part_sum

def main():
    ranges = []
    for i in range(WORKERS_NUM):
        start = i * CHUNK_SIZE + 1
        end = (i + 1) * CHUNK_SIZE if i < WORKERS_NUM - 1 else N
        ranges.append((start, end))

    threads = []
    results = [0] * WORKERS_NUM

    start_t = time.perf_counter()

    for i, (start, end) in enumerate(ranges):
        t = threading.Thread(
            target=calculate_sum,
            args=(start, end, results, i)
        )
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    total_sum = sum(results)
    elapsed_t = time.perf_counter() - start_t

    print("Сумма чисел с использованием THREADING\n")
    print(f"Количество workers: {WORKERS_NUM}")
    print(f"Ожидаемая сумма: {EXPECTED_SUM}")
    print(f"Полученная сумма: {total_sum}")
    print(f"Затраченное время: {elapsed_t:.6f} сек")

if __name__ == "__main__":
    main()