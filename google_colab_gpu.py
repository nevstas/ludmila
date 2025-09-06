import time
import itertools
import torch
import threading
from threading import Lock

myLock = threading.Lock()

script_path = "/content/drive/My Drive/ludmila/ludmila"

dataset_id = 2
dataset_filename = "data" + str(dataset_id) + ".txt"

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Device:", device)

# Диапазон X
start, end = -10, 10
dtype = torch.int64

def fmt_time(t):
    ms = int((t % 1) * 1000)
    sec = int(t) % 60
    mins = int(t // 60)
    return f"{mins} мин {sec} сек {ms} мс"

def op_add(a, b):
    return a + b, torch.ones_like(a, dtype=torch.bool)

def op_sub(a, b):
    return a - b, torch.ones_like(a, dtype=torch.bool)

def op_mul(a, b):
    return a * b, torch.ones_like(a, dtype=torch.bool)

def op_div(a, b):
    # строгая целочисленная делимость и запрет деления на 0
    valid = (b != 0) & (a.remainder(b) == 0)
    out = torch.empty_like(a)
    if valid.any():
        out[valid] = a[valid] // b[valid]
    if (~valid).any():
        out[~valid] = 0
    return out, valid

def op_pow2(a, _b_ignored):
    # (a)^2, всегда валидно
    return a * a, torch.ones_like(a, dtype=torch.bool)

def op_sqrt(a, _b_ignored):
    # sqrt(a) только для a >= 0 и только если a — идеальный квадрат
    valid = (a >= 0)

    # получаем целочисленный корень
    r = torch.sqrt(a.float()).to(torch.int64)

    # проверяем точность: r*r == a
    valid = valid & ((r * r) == a)

    out = torch.empty_like(a)
    if valid.any():
        out[valid] = r[valid]
    if (~valid).any():
        out[~valid] = 0
    return out, valid


OPS = {
    '+': op_add,
    '-': op_sub,
    '*': op_mul,
    '/': op_div,
    '^2': op_pow2,
    '^0.5': op_sqrt,
}

OPS_FIRST_PASS = {'*', '/', '^2'}

def operand_tensor(token, x_vals):
    if token == 'x':
        return x_vals
    else:
        return torch.full_like(x_vals, int(token), dtype=x_vals.dtype, device=x_vals.device)

def eval_expr_tokens(tokens, ops, x_vals):
    has_x = any(tok == 'x' for tok in tokens)
    if has_x:
        base = x_vals
        valid = torch.ones_like(x_vals, dtype=torch.bool)
    else:
        base = torch.tensor([0], device=x_vals.device, dtype=x_vals.dtype)
        valid = torch.ones(1, dtype=torch.bool, device=x_vals.device)

    vals = [operand_tensor(tok, base) for tok in tokens]

    # --- Первый проход: *, /, ^2 ---
    vals2 = [vals[0]]
    ops2 = []
    trailing_sqrt = False
    n_ops = len(ops)

    for i, sym in enumerate(ops):
        b = vals[i + 1]
        is_last = (i == n_ops - 1)
        if sym in OPS_FIRST_PASS:
            fn = OPS[sym]
            cur, v_step = fn(vals2[-1], b)
            vals2[-1] = cur
            valid = valid & v_step
            if has_x and not valid.any(): break
            if not has_x and not bool(valid.item()): break
        elif sym == '^0.5' and is_last:
            # отложим sqrt на самый конец (после + и -)
            trailing_sqrt = True
            # IMPORTANT: не добавляем b, он "фиктивный" для унарной операции
        else:
            # + или - (и любой другой оператор, если решите расширять)
            ops2.append(sym)
            vals2.append(b)

    # Ранний выход
    if has_x and not valid.any():
        return torch.zeros_like(x_vals), torch.zeros_like(x_vals, dtype=torch.bool), has_x
    if not has_x and not bool(valid.item()):
        out = torch.zeros_like(x_vals)
        msk = torch.zeros_like(x_vals, dtype=torch.bool)
        return out, msk, has_x

    # --- Второй проход: + и - ---
    res = vals2[0]
    for i, sym in enumerate(ops2):
        fn = OPS[sym]
        b = vals2[i + 1]
        res, v_step = fn(res, b)
        valid = valid & v_step
        if has_x and not valid.any(): break
        if not has_x and not bool(valid.item()): break

    # --- Отложенный sqrt в самом конце ---
    if trailing_sqrt:
        res, v_step = OPS['^0.5'](res, res)   # b игнорируется
        valid = valid & v_step

    if not has_x:
        res = res.expand_as(x_vals)
        valid = valid.expand_as(x_vals)

    return res, valid, has_x

def build_formula(tokens, x_value=None):
    parts = []
    for i, tok in enumerate(tokens):
        val = str(x_value) if (tok == 'x' and x_value is not None) else str(tok)
        parts.append(val)
        if i < len(tokens) - 1:
            parts.append(None)  # плейсхолдер под оператор
    return parts

def stringify(parts, ops):
    out = []
    op_iter = iter(ops)
    for p in parts:
        if p is None:
            try:
                out.append(next(op_iter))
            except StopIteration:
                # На всякий случай, но обычно не попадём сюда
                pass
        else:
            out.append(str(p))
    # Если остались операторы (например, финальный унарный ^0.5) — добавим их в конец
    for sym in op_iter:
        out.append(sym)
    return " ".join(out)


def writeln(str):
    myLock.acquire()
    with open(script_path + "/log.txt", 'a', encoding='utf-8') as the_file:
        the_file.write(str + "\n")
    myLock.release()

def load_dataset(path):
    """
    Ожидает строки формата:
    y [c1 c2 c3 ...]
    Возвращает список: [(y, [c1, c2, c3, ...]), ...]
    Количество констант после y может быть любым (в том числе 0).
    Пустые строки игнорируются.
    """
    ds = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # минимум — одно число (y)
            try:
                yv = int(parts[0])
            except ValueError:
                # строка некорректна — пропустим
                continue
            consts = []
            for p in parts[1:]:
                try:
                    consts.append(int(p))
                except ValueError:
                    # некорректный токен — пропустим только его
                    continue
            ds.append((yv, consts))
    return ds


# --- Маппинг констант по индексам (ключ к универсальной проверке) ---
def make_const_index_map(const_pool):
    """
    Возвращает dict: {"51": 0, "62": 1, "73": 2} для текущего пула.
    """
    return {str(v): i for i, v in enumerate(const_pool)}

def remap_tokens_to_target_consts(tokens, base_const_pool, target_consts):
    """
    Переносит структуру tokens, заменяя константы из базового пула
    на соответствующие константы target_consts по ИНДЕКСУ.
    Пример: tokens = ['x','*','51','+','73'] при target=[52,63,74]
    -> ['x','*','52','+','74']
    """
    idx_map = make_const_index_map(base_const_pool)
    out = []
    for tok in tokens:
        if tok == 'x':
            out.append('x')
        else:
            # это константа из базового пула
            k = idx_map.get(tok, None)
            if k is None:
                # Защита: если в tokens неожиданно есть число не из пула
                out.append(tok)
            else:
                out.append(str(target_consts[k]))
    return out

def validate_formula_on_all_sets(tokens_base, ops):
    """
    Проверяет формулу (структура tokens_base + ops), подобранную на первом наборе,
    на всех наборах датасета. Для каждого набора подставляет его константы
    по индексам и проверяет существование хотя бы одного x в диапазоне,
    чтобы res == y набора при валидных операциях.
    Возвращает (ok, xs_per_set) — ok: bool; xs_per_set: список найденных x или None.
    """
    xs_demo = []  # для информации: какие x нашлись на наборах
    for (y_target, consts_target) in dataset:
        # Переносим токены на константы этого набора
        tokens_target = remap_tokens_to_target_consts(tokens_base, CONST_POOL_BASE, consts_target)
        # Считаем
        res, valid, has_x = eval_expr_tokens(tokens_target, ops, x_vals)
        hits = torch.nonzero(valid & (res == y_target), as_tuple=False).flatten()
        if hits.numel() == 0:
            return False, None
        # Сохраним один демонстрационный x
        xs_demo.append(int(x_vals[hits[0]].item()) if has_x else None)
    return True, xs_demo

if device == 'cuda':
    torch.cuda.synchronize()
t0 = time.perf_counter()

# Загружаем весь датасет
dataset_path = script_path + "/datasets/" + dataset_filename
dataset = load_dataset(dataset_path)
if not dataset:
    raise RuntimeError(f"Датасет пуст или не прочитан: {dataset_path}")

# Первый набор — базовый для первичного поиска
# CHANGED: без проверок и сравнений — просто берем первую строку из файла
y_base, CONST_POOL_BASE = dataset[0]  # CHANGED

x_vals = torch.arange(start, end + 1, dtype=dtype, device=device)

OPERAND_POOL_BASE = ['x'] + [str(c) for c in CONST_POOL_BASE]

# stats:
checked_exprs = 0
solutions_found_global = 0  # сколько "универсальных" формул нашли и залогировали
attempted_eqs_total_base = 0                  # (2a) скалярных проверок f(x)=y на базовом наборе
attempted_eqs_by_len_base = {L: 0 for L in range(1, 6)}

time_total_start = time.time()

for length in range(1, 6):  # длина по операндам
    # все последовательности операндов
    for tokens in itertools.product(OPERAND_POOL_BASE, repeat=length):
        # все последовательности операций соответствующей длины
        OPS_ALPHABET = ['+', '-', '*', '/', '^2', '^0.5']

        if length == 1:
            ops_list = [()]
        else:
            ops_list = itertools.product(OPS_ALPHABET, repeat=length - 1)

        for ops in ops_list:
            # Считаем на БАЗОВОМ наборе (как раньше)
            res, valid, has_x = eval_expr_tokens(tokens, ops, x_vals)
            hits = torch.nonzero(valid & (res == y_base), as_tuple=False).flatten()

            n_valid_base = int(valid.sum().item())

            # stats:
            checked_exprs += 1
            attempted_eqs_total_base += n_valid_base
            attempted_eqs_by_len_base[length] += n_valid_base

            if hits.numel() == 0:
                continue

            # Раньше мы сразу писали в лог. Теперь — сперва валидируем на ВСЕХ наборах.
            ok, xs_demo = validate_formula_on_all_sets(list(tokens), ops)
            if not ok:
                # Формула не универсальна — пропускаем без логов
                continue

            # Универсальная формула найдена — логируем ОДИН раз
            # Покажем формулу, подставив x из первого попадания на базовом наборе
            x_found_base = int(x_vals[hits[0]].item()) if has_x else None
            parts = build_formula(tokens, x_value=x_found_base)
            formula_str = stringify(parts, ops)
            time_total = time.time() - time_total_start
            message = time.strftime("%d.%m.%Y %H:%M:%S") + " Solution data" + str(dataset_id) + ": " + formula_str + " at " + str(round(time_total, 2)) + " seconds"

            print(message)
            writeln(message)
            solutions_found_global += 1
            # Можно НЕ прерывать поиск — пусть находит альтернативные универсальные формулы
            # Если хотите остановить на первой — раскомментируйте следующую строку:
            # raise SystemExit

if device == 'cuda':
    torch.cuda.synchronize()
t1 = time.perf_counter()

# ---------------- ВЫВОД ----------------
elapsed = t1 - t0

if solutions_found_global == 0:
    print("Универсальных решений не найдено в заданном диапазоне и наборе выражений.")
else:
    print(f"Всего универсальных формул: {solutions_found_global}")

print(f"Базовый пул констант: {CONST_POOL_BASE}")
print(f"Диапазон X: [{start}, {end}]")
print(f"Проверено выражений (комбинаций) на базовом наборе: ~{checked_exprs:,}")
print(f"Время: {fmt_time(elapsed)}")
