import time
import asyncio
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

async def main():
    tasks = [asyncio.to_thread(calculate_sum,
                               i * CHUNK_SIZE + 1,
                               (i + 1) * CHUNK_SIZE if i < WORKERS_NUM - 1 else N
                               )
                               for i in range(WORKERS_NUM)]

    start_t = time.perf_counter()
    sums = await asyncio.gather(*tasks)
    total_sum = sum(sums)
    elapsed_t = time.perf_counter() - start_t

    print("Сумма чисел с использованием ASYNC\n")
    print(f"Количество workers: {WORKERS_NUM}")
    print(f"Ожидаемая сумма: {EXPECTED_SUM}")
    print(f"Полученная сумма: {total_sum}")
    print(f"Затраченное время: {elapsed_t}")

if __name__ == "__main__":
    asyncio.run(main())