import random
import time


class BasicRNG:
    def __init__(self, seed=42):
        self.m = 2**31 - 1  # модуль, число Мерсена
        self.a = 1103515245  # множитель, теорема Халла - Добелла
        self.c = 12345  # приращение, если 0 = мультипликативный
        self.x = seed

    def next(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m

    def generate(self, n):
        return [self.next() for _ in range(n)]


THEORETICAL_MEAN = 0.5
THEORETICAL_VAR = 1 / 12
N = 100_000


def sample_mean(values):
    return sum(values) / len(values)


def sample_variance(values):
    m = sample_mean(values)
    return sum((x - m) ** 2 for x in values) / (len(values) - 1)


my_rng = BasicRNG(seed=42)
my_sample = my_rng.generate(N)
my_mean = sample_mean(my_sample)
my_var = sample_variance(my_sample)

random.seed(42)
builtin_sample = [random.random() for _ in range(N)]
builtin_mean = sample_mean(builtin_sample)
builtin_var = sample_variance(builtin_sample)


print("=" * 55)
print("1. РАВНОМЕРНОЕ РАСПРЕДЕЛЕНИЕ")
print("=" * 55)
print(
    f"{'Характеристика':<20} {'Теория':>10} {'Мой датчик':>12} {'random.random()':>12}"
)
print("-" * 55)
print(
    f"{'Среднее':<20} {THEORETICAL_MEAN:>10.5f} {my_mean:>12.5f} {builtin_mean:>12.5f}"
)
print(
    f"{'Дисперсия':<20} {THEORETICAL_VAR:>10.5f} {my_var:>12.5f} {builtin_var:>12.5f}"
)
print("=" * 55)


def autocorrelation(values):
    pairs_x = values[:-1]
    pairs_y = values[1:]
    mean_x = sample_mean(pairs_x)
    mean_y = sample_mean(pairs_y)
    cov = sum(
        (a - mean_x) * (b - mean_y) for a, b in zip(pairs_x, pairs_y)
    ) / len(pairs_x)
    std_x = sample_variance(pairs_x) ** 0.5
    std_y = sample_variance(pairs_y) ** 0.5
    return cov / (std_x * std_y)


my_corr = autocorrelation(my_sample)
builtin_corr = autocorrelation(builtin_sample)

print("\n2. ОТСУТСТВИЕ КОРРЕЛЯЦИИ")
print("=" * 55)
print(f"{'':20} {'Мой датчик':>17} {'random.random()':>15}")
print("-" * 55)
print(f"{'Автокорреляция':<20} {my_corr:>17.6f} {builtin_corr:>15.6f}")
print(
    f"{'Вывод':<20} {'норма' if abs(my_corr) < 0.01 else 'есть корреляция':>17}"
    f" {'норма' if abs(builtin_corr) < 0.01 else 'есть корреляция':>15}"
)
print("=" * 55)


print("\n3. АПЕРИОДИЧНОСТЬ")
print("=" * 55)
period = BasicRNG(seed=42).m
print(f"Максимальный период генератора : {period:,}")
print(f"Размер нашей выборки           : {N:,}")
print(f"Использовано периода           : {N / period * 100:.4f}%")
print("=" * 55)


print("\n4. ВОСПРОИЗВОДИМОСТЬ")
print("=" * 55)
rng1 = BasicRNG(seed=42)
rng2 = BasicRNG(seed=42)
sample1 = rng1.generate(5)
sample2 = rng2.generate(5)
print(f"Запуск 1 (seed=42): {[round(x, 5) for x in sample1]}")
print(f"Запуск 2 (seed=42): {[round(x, 5) for x in sample2]}")
print(f"Совпадают: {sample1 == sample2}")
print("=" * 55)


print("\n5. БЫСТРОТА")
print("=" * 55)

start = time.time()
BasicRNG(seed=42).generate(N)
my_time = time.time() - start

start = time.time()
random.seed(42)
[random.random() for _ in range(N)]
builtin_time = time.time() - start

print(f"{'':20} {'Мой датчик':>17} {'random.random()':>15}")
print("-" * 55)
print(f"{'Время (сек)':<20} {my_time:>17.4f} {builtin_time:>15.4f}")
print("=" * 55)
