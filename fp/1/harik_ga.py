"""
Программная проверка формулы Жоржа Харика (1999) и верификация ГА
на функции Хёльдера.

Формула Харика:
    N = [ -2^(k-1) * ln(alpha) * sqrt(pi * m) ] / d

    N     — минимальный размер популяции
    k     — порядок схемы (order of schema): кол-во жёстко зафиксированных битов
    alpha — допустимая вероятность ошибки (вероятность потерять строительный блок)
    m     — длина хромосомы (число битов)
    d     — сигнал: разница между средним фитнесом строительного блока
            и средним фитнесом популяции, нормированная на дисперсию.
            Показывает, насколько «заметно» хорошее решение среди всех особей.

Что именно показывает формула?
    Формула отвечает на вопрос: «Какой минимальный размер популяции N нужен,
    чтобы с вероятностью (1 - alpha) не проиграть «казино»?»
    Каждый шаг генетического алгоритма подобен ставке в казино: лучшая схема
    (строительный блок) должна «победить» в конкуренции со всеми остальными.
    Харик доказал, что вероятность проигрыша (потери строительного блока)
    убывает экспоненциально с ростом N, а необходимый N растёт с k
    тоже экспоненциально — поэтому сложные задачи с большим k требуют
    огромных популяций без дополнительных механизмов (элитизм, турнирная селекция).
"""

import math
import random
import copy


# ---------------------------------------------------------------------------
# 1. ФОРМУЛА ХАРИКА
# ---------------------------------------------------------------------------

def harik_population_size(k: int, alpha: float, m: int, d: float) -> float:
    """
    Возвращает минимальный размер популяции N по формуле Харика (1999).

    Параметры
    ----------
    k     : порядок схемы — количество жёстко фиксированных битов
    alpha : допустимая вероятность потери строительного блока
    m     : длина хромосомы (бит)
    d     : нормированный «сигнал» — разница фитнесов / стандартное отклонение

    Возвращает
    ----------
    N : вещественное число; на практике берут math.ceil(N).
    """
    power_of_two = 2 ** (k - 1)         # 2^(k-1)
    ln_alpha     = math.log(alpha)       # ln(alpha) < 0
    sqrt_pi_m    = math.sqrt(math.pi * m)
    # Числитель: -2^(k-1) * ln(alpha) * sqrt(pi*m)
    # Поскольку ln(alpha) < 0, два минуса дают плюс
    numerator = -power_of_two * ln_alpha * sqrt_pi_m
    return numerator / d


def print_harik_calculation(k: int, alpha: float, m: int, d: float) -> None:
    """Выводит пошаговый расчёт формулы Харика."""
    print(f"\n{'='*60}")
    print(f"  Параметры: k={k}, alpha={alpha}, m={m}, d={d}")
    print(f"{'='*60}")
    step1 = 2 ** (k - 1)
    step2 = math.log(alpha)
    step3_inner = math.pi * m
    step3 = math.sqrt(step3_inner)
    numerator = -step1 * step2 * step3
    N = numerator / d
    print(f"  Шаг 1  — 2^(k-1)        = 2^{k-1} = {step1}")
    print(f"  Шаг 2  — ln(alpha)       = ln({alpha}) ≈ {step2:.4f}")
    print(f"  Шаг 3  — pi * m          = {math.pi:.5f} * {m} ≈ {step3_inner:.3f}")
    print(f"           sqrt(pi * m)    ≈ {step3:.4f}")
    print(f"  Числитель (-2^(k-1)*ln(alpha)*sqrt(pi*m)):")
    print(f"           = -({step1}) * ({step2:.4f}) * {step3:.4f}")
    print(f"           ≈ {numerator:.4f}")
    print(f"  Знаменатель d            = {d}")
    print(f"  N = {numerator:.4f} / {d} ≈ {N:.2f}")
    print(f"  >>> Минимальный размер популяции N ≈ {math.ceil(N)} особей")


# ---------------------------------------------------------------------------
# 2. ТЕОРЕМА СХЕМ (SCHEMA THEOREM, Holland / Goldberg)
# ---------------------------------------------------------------------------
# E[m(s, t+1)] ≥ m(s,t) * [f(s)/f̄] * (1 - p_c * δ(s)/(L-1)) * (1 - p_m)^o(s)

def schema_theorem(
    m_s_t: float,    # m(s, t)  — кол-во копий схемы s в поколении t
    f_s: float,      # f(s)     — средний фитнес схемы s
    f_avg: float,    # f̄        — средний фитнес популяции
    p_c: float,      # p_c      — вероятность кроссовера
    delta_s: int,    # δ(s)     — определяющая длина схемы (расстояние между крайними
                     #            зафиксированными позициями)
    L: int,          # L        — длина хромосомы
    p_m: float,      # p_m      — вероятность мутации на бит
    o_s: int,        # o(s)     — порядок схемы (= k)
) -> float:
    """Вычисляет нижнюю оценку E[m(s, t+1)] по теореме схем."""
    fitness_ratio  = f_s / f_avg
    crossover_term = 1.0 - p_c * delta_s / (L - 1)
    mutation_term  = (1.0 - p_m) ** o_s
    return m_s_t * fitness_ratio * crossover_term * mutation_term


def print_schema_theorem_calculation(
    m_s_t, f_s, f_avg, p_c, delta_s, L, p_m, o_s
) -> None:
    """Выводит пошаговый расчёт теоремы схем с пояснениями для нашей задачи."""
    print(f"\n{'='*60}")
    print("  ТЕОРЕМА СХЕМ — расчёт для нашей задачи")
    print(f"{'='*60}")
    print(f"  Параметры:")
    print(f"    m(s, t) = {m_s_t}   — начальное число копий строительного блока")
    print(f"    f(s)    = {f_s}   — средний фитнес схемы s (хорошие биты X и Y)")
    print(f"    f̄       = {f_avg}   — средний фитнес по всей популяции")
    print(f"    p_c     = {p_c}   — вероятность кроссовера")
    print(f"    δ(s)    = {delta_s}   — определяющая длина схемы (расстояние между")
    print(f"                       крайними важными битами внутри 58-битной строки;")
    print(f"                       биты X и Y разделены ~29 позициями)")
    print(f"    L       = {L}   — длина хромосомы (бит)")
    print(f"    p_m     = {p_m}  — вероятность мутации на один бит")
    print(f"    o(s)    = {o_s}   — порядок схемы (= k; число жёстко фикс. битов)")
    print()

    fitness_ratio  = f_s / f_avg
    crossover_term = 1.0 - p_c * delta_s / (L - 1)
    mutation_term  = (1.0 - p_m) ** o_s
    result         = m_s_t * fitness_ratio * crossover_term * mutation_term

    print(f"  Шаг 1 — Соотношение фитнесов:")
    print(f"    f(s)/f̄ = {f_s}/{f_avg} = {fitness_ratio:.4f}")
    print(f"    Поясн.: схема в 1.43 раза лучше среднего → естественный отбор")
    print(f"            помогает ей размножаться.")
    print()
    print(f"  Шаг 2 — Потери от кроссовера:")
    print(f"    1 - p_c * δ(s)/(L-1) = 1 - {p_c}*{delta_s}/{L-1}")
    print(f"                          = 1 - {p_c * delta_s / (L-1):.4f}")
    print(f"                          = {crossover_term:.4f}")
    print(f"    Поясн.: кроссовер с вероятностью {p_c*delta_s/(L-1):.1%} разрывает")
    print(f"            строительный блок. Именно поэтому нужно высокое p_c:")
    print(f"            чем больше скрещиваний, тем быстрее блок собирается заново.")
    print()
    print(f"  Шаг 3 — Потери от мутации:")
    print(f"    (1 - p_m)^o(s) = (1 - {p_m})^{o_s} = {mutation_term:.4f}")
    print(f"    Поясн.: мутация с вероятностью {1-mutation_term:.1%} испортит хотя бы")
    print(f"            один из {o_s} важных битов схемы.")
    print()
    print(f"  Результат (нижняя оценка копий схемы в следующем поколении):")
    print(f"    E[m(s, t+1)] ≥ {m_s_t} * {fitness_ratio:.4f} * {crossover_term:.4f} * {mutation_term:.4f}")
    print(f"                 ≥ {result:.2f}")
    print(f"  >>> Ожидается не менее {result:.1f} копий строительного блока")
    print(f"      в следующем поколении (рост с {m_s_t} до {result:.1f}).")


# ---------------------------------------------------------------------------
# 3. ГЕНЕТИЧЕСКИЙ АЛГОРИТМ ДЛЯ ФУНКЦИИ ХЁЛЬДЕРА
# ---------------------------------------------------------------------------
# Функция Хёльдера (Holder Table):
#   f(x, y) = -|sin(x)*cos(y)*exp(|1 - sqrt(x²+y²)/pi|)|
# Область поиска: x, y ∈ [-10, 10]
# Глобальные минимумы ≈ -19.2085 в 4 точках: (±8.05502, ±9.66459)
#
# Кодирование: 29 бит на каждую переменную (1 знак + 4 целая часть + 24 дробная)
# Итого L = 58 бит.
# Диапазон [-10, 10] покрывается через: x = -10 + val / (2^29 - 1) * 20

BITS_PER_VAR = 29    # бит на одну переменную
L_TOTAL      = 58    # длина хромосомы
X_MIN, X_MAX = -10.0, 10.0

RANGE        = X_MAX - X_MIN   # 20.0
MAX_INT      = (1 << BITS_PER_VAR) - 1   # 2^29 - 1


def holder_table(x: float, y: float) -> float:
    """Функция Хёльдера (Holder Table function), глобальный min ≈ -19.2085."""
    inner = abs(1.0 - math.sqrt(x * x + y * y) / math.pi)
    return -abs(math.sin(x) * math.cos(y) * math.exp(inner))


def decode_chromosome(chromosome: list) -> tuple:
    """
    Декодирует хромосому (список из 58 бит) в пару (x, y).
    Первые 29 бит → x, последние 29 бит → y.
    Отображение: val / MAX_INT * RANGE + X_MIN
    """
    def bits_to_float(bits):
        val = 0
        for b in bits:
            val = (val << 1) | b
        return X_MIN + val / MAX_INT * RANGE

    x = bits_to_float(chromosome[:BITS_PER_VAR])
    y = bits_to_float(chromosome[BITS_PER_VAR:])
    return x, y


def random_chromosome() -> list:
    return [random.randint(0, 1) for _ in range(L_TOTAL)]


def fitness(chromosome: list) -> float:
    """
    Приспособленность: так как минимизируем f(x,y), приспособленность = -f(x,y).
    Чем меньше f, тем выше приспособленность.
    """
    x, y = decode_chromosome(chromosome)
    return -holder_table(x, y)   # holder_table возвращает отрицательные значения,
                                  # поэтому -holder_table ≥ 0


def single_point_crossover(parent1: list, parent2: list) -> tuple:
    """Одноточечный кроссовер."""
    point = random.randint(1, L_TOTAL - 1)
    child1 = parent1[:point] + parent2[point:]
    child2 = parent2[:point] + parent1[point:]
    return child1, child2


def mutate(chromosome: list, p_m: float) -> list:
    """Побитовая мутация с вероятностью p_m на каждый бит."""
    return [bit ^ 1 if random.random() < p_m else bit for bit in chromosome]


def tournament_selection(population: list, fitnesses: list, k: int = 3) -> list:
    """Турнирная селекция: выбирает лучшую особь из k случайных."""
    contestants = random.sample(range(len(population)), k)
    winner = max(contestants, key=lambda i: fitnesses[i])
    return copy.copy(population[winner])


def run_genetic_algorithm(
    pop_size:   int   = 500,
    generations: int  = 300,
    p_crossover: float = 0.85,
    p_mutation:  float = 1.0 / L_TOTAL,
    elitism:     int   = 2,
    seed:        int   = 42,
    verbose:     bool  = True,
) -> dict:
    """
    Запускает ГА для поиска глобального минимума функции Хёльдера.

    Параметры
    ----------
    pop_size    : размер популяции
    generations : число поколений
    p_crossover : вероятность кроссовера
    p_mutation  : вероятность мутации на бит (по умолчанию 1/L)
    elitism     : число лучших особей, переносимых без изменений
    seed        : фиксированный seed для воспроизводимости
    verbose     : печатать ли прогресс

    Возвращает
    ----------
    dict с ключами: best_x, best_y, best_f, best_chromosome, history
    """
    random.seed(seed)

    # Инициализация
    population = [random_chromosome() for _ in range(pop_size)]
    history = []

    for gen in range(generations):
        fitnesses = [fitness(chrom) for chrom in population]

        best_idx  = max(range(pop_size), key=lambda i: fitnesses[i])
        best_fit  = fitnesses[best_idx]
        best_x, best_y = decode_chromosome(population[best_idx])
        history.append((gen, best_x, best_y, holder_table(best_x, best_y)))

        if verbose and (gen % 50 == 0 or gen == generations - 1):
            print(f"  Поколение {gen:4d}: f({best_x:7.4f}, {best_y:7.4f})"
                  f" = {holder_table(best_x, best_y):.6f}")

        # Элитизм: сохраняем лучших
        sorted_idx   = sorted(range(pop_size), key=lambda i: fitnesses[i], reverse=True)
        new_population = [copy.copy(population[sorted_idx[i]]) for i in range(elitism)]

        # Формируем новое поколение
        while len(new_population) < pop_size:
            parent1 = tournament_selection(population, fitnesses)
            parent2 = tournament_selection(population, fitnesses)

            if random.random() < p_crossover:
                child1, child2 = single_point_crossover(parent1, parent2)
            else:
                child1, child2 = copy.copy(parent1), copy.copy(parent2)

            new_population.append(mutate(child1, p_mutation))
            if len(new_population) < pop_size:
                new_population.append(mutate(child2, p_mutation))

        population = new_population

    # Финальная оценка
    fitnesses = [fitness(chrom) for chrom in population]
    best_idx  = max(range(pop_size), key=lambda i: fitnesses[i])
    best_chrom = population[best_idx]
    best_x, best_y = decode_chromosome(best_chrom)
    best_f = holder_table(best_x, best_y)

    return {
        "best_x":          best_x,
        "best_y":          best_y,
        "best_f":          best_f,
        "best_chromosome": best_chrom,
        "history":         history,
    }


# ---------------------------------------------------------------------------
# 4. ОСНОВНАЯ ПРОГРАММА — ПОЛНАЯ ПРОВЕРКА
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  ЧТО ПОКАЗЫВАЕТ ФОРМУЛА ХАРИКА (1999)?")
    print("=" * 60)
    print("""
  Формула: N = [ -2^(k-1) * ln(alpha) * sqrt(pi * m) ] / d

  Формула Харика отвечает на вопрос:
  «Какой минимальный размер стартовой популяции N нужен,
   чтобы генетический алгоритм с вероятностью не менее
   (1 - alpha) сохранил ключевой строительный блок
   из k жёстко связанных битов и нашёл глобальный оптимум?»

  Параметры:
    k     — кол-во жёстко фиксированных битов (порядок схемы)
    alpha — макс. допустимая вероятность ошибки
    m     — длина хромосомы (бит)
    d     — нормированный «сигнал» (разница фитнесов лучшего
            строительного блока и среднего по популяции)

  Физический смысл:
    • N растёт ЭКСПОНЕНЦИАЛЬНО с k: удвоение каждые +1 к k.
    • N растёт логарифмически при уменьшении alpha (надёжнее → больше).
    • N растёт с ростом m (длиннее хромосома → сложнее поиск).
    • N падает при росте d (ярче «сигнал» → меньше нужно особей).
    """)

    # ------------------------------------------------------------------
    # 4.1 Расчёт Харика для всех обсуждавшихся параметров
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("  РАСЧЁТ ФОРМУЛЫ ХАРИКА (все варианты параметров)")
    print("=" * 60)

    cases = [
        dict(k=6, alpha=0.05, m=58, d=0.17),
        dict(k=4, alpha=0.05, m=58, d=0.17),
        dict(k=4, alpha=0.04, m=58, d=0.17),
        dict(k=4, alpha=0.02, m=58, d=0.17),
    ]
    for case in cases:
        print_harik_calculation(**case)

    # ------------------------------------------------------------------
    # 4.2 Теорема схем — расчёт для нашей задачи
    # ------------------------------------------------------------------
    # Параметры для Хёльдера / нашего ГА:
    #   L       = 58 (длина хромосомы)
    #   o(s)    = k = 4 (порядок схемы)
    #   δ(s)    = 29 (биты X стоят в позициях 0-28, биты Y — 29-57;
    #               крайние важные биты — знак X (позиция 0) и знак Y (позиция 29),
    #               расстояние = 29)
    #   p_c     = 0.85
    #   p_m     = 1/58 ≈ 0.01724
    #   m(s,t)  = 50  (начальное число копий; при pop_size=500 ≈ 10%)
    #   f(s)    = 14.3 (средний фитнес «хорошей» схемы, примерно -(-14.3)=14.3)
    #   f̄       = 10.0 (средний фитнес по популяции)
    print_schema_theorem_calculation(
        m_s_t   = 50,
        f_s     = 14.3,
        f_avg   = 10.0,
        p_c     = 0.85,
        delta_s = 29,
        L       = 58,
        p_m     = round(1 / 58, 6),
        o_s     = 4,
    )

    # ------------------------------------------------------------------
    # 4.3 Запуск ГА и проверка результата
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("  ЗАПУСК ГЕНЕТИЧЕСКОГО АЛГОРИТМА НА ФУНКЦИИ ХЁЛЬДЕРА")
    print(f"{'='*60}")

    # Теоретически необходимый размер популяции (k=4, alpha=0.05)
    n_theoretical = harik_population_size(k=4, alpha=0.05, m=58, d=0.17)
    n_with_elitism = 500   # реальный, с элитизмом

    print(f"\n  Теоретический N (формула Харика, k=4): {math.ceil(n_theoretical)} особей")
    print(f"  Используемый N (с элитизмом):          {n_with_elitism} особей")
    print(f"\n  Известные глобальные минимумы функции Хёльдера:")
    print(f"    f(±8.05502, ±9.66459) ≈ -19.2085")
    print(f"\n  Запуск ГА (500 особей, 300 поколений, p_c=0.85)...")

    result = run_genetic_algorithm(
        pop_size    = 500,
        generations = 300,
        p_crossover = 0.85,
        p_mutation  = 1.0 / L_TOTAL,
        elitism     = 2,
        seed        = 42,
        verbose     = True,
    )

    print(f"\n{'='*60}")
    print("  РЕЗУЛЬТАТ ВЕРИФИКАЦИИ")
    print(f"{'='*60}")
    print(f"  Найденная точка:  x = {result['best_x']:.5f}, y = {result['best_y']:.5f}")
    print(f"  Значение функции: f(x, y) = {result['best_f']:.6f}")
    print(f"  Эталонный минимум:          -19.208500")
    error = abs(result['best_f'] - (-19.2085))
    print(f"  Отклонение от эталона:      {error:.6f}")
    if error < 0.01:
        print("  >>> ВЕРИФИКАЦИЯ ПРОЙДЕНА: ГА нашёл глобальный минимум!")
    else:
        print("  >>> Решение не оптимально; попробуйте увеличить pop_size или generations.")

    # ------------------------------------------------------------------
    # 4.4 Чувствительность N к параметрам (таблица)
    # ------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("  СВОДНАЯ ТАБЛИЦА: N в зависимости от k и alpha")
    print(f"  (m=58, d=0.17)")
    print(f"{'='*60}")
    print(f"  {'k':>3}  {'alpha':>6}  {'N (формула)':>12}  {'N (ceil)':>10}")
    print(f"  {'-'*3}  {'-'*6}  {'-'*12}  {'-'*10}")
    for k_val in [4, 5, 6]:
        for alpha_val in [0.05, 0.04, 0.02]:
            n = harik_population_size(k=k_val, alpha=alpha_val, m=58, d=0.17)
            print(f"  {k_val:>3}  {alpha_val:>6.2f}  {n:>12.2f}  {math.ceil(n):>10}")


if __name__ == "__main__":
    main()
