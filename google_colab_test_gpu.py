import time
import itertools
import torch

# ---------------- ПАРАМЕТРЫ ----------------
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Устройство:", device)

y = 4211
start, end = -1000, 1000          # диапазон X; можешь увеличить
dtype = torch.int64

# Пул операндов: 'x' плюс константы (сюда добавляй свои числа)
CONST_POOL = [59, 70, 81]

# ---------------- УТИЛИТЫ ----------------
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
    # a и b — тензоры одной формы (вектор по x)
    valid = (b != 0) & (a.remainder(b) == 0)
    out = torch.empty_like(a)
    if valid.any():
        out[valid] = a[valid] // b[valid]
    if (~valid).any():
        out[~valid] = 0  # значение не важно — всё равно будет отфильтровано mask'ом
    return out, valid

OPS = {'+': op_add, '-': op_sub, '*': op_mul, '/': op_div}

def operand_tensor(token, x_vals):
    """Возвращает тензор-операнд для токена: 'x' или константа."""
    if token == 'x':
        return x_vals
    else:
        # скаляр конвертируем в тензор и broadсast-им до формы x_vals
        return torch.full_like(x_vals, int(token), dtype=x_vals.dtype, device=x_vals.device)

def eval_expr_tokens(tokens, ops, x_vals):
    """
    tokens: список операндов длиной N из {'x'} ∪ {строковые константы}
    ops: список символов операций длиной N-1
    Возвращает:
      - res: тензор результатов для каждого x (если нет 'x' в tokens — скалярный тензор одинакового значения)
      - valid: булев тензор валидности на каждой позиции x (если нет 'x' — единичный булев тензор True/False, растянем)
      - has_x: bool — участвует ли x в выражении
    """
    has_x = any(tok == 'x' for tok in tokens)
    if has_x:
        res = operand_tensor(tokens[0], x_vals)
        valid = torch.ones_like(x_vals, dtype=torch.bool)
    else:
        # нет x: используем фиктивный одномерный тензор, потом растянем
        dummy = torch.tensor([0], device=x_vals.device, dtype=x_vals.dtype)
        res = operand_tensor(tokens[0], dummy)[:1]  # скаляр с shape [1]
        valid = torch.ones(1, dtype=torch.bool, device=x_vals.device)

    for sym, tok in zip(ops, tokens[1:]):
        b = operand_tensor(tok, x_vals if has_x else res)  # если нет x — shape [1]
        fn = OPS[sym]
        res, v_step = fn(res, b)
        valid = valid & v_step
        if has_x and not valid.any():
            break
        if not has_x and not bool(valid.item()):
            break

    if not has_x:
        # растягиваем скаляр до длины x_vals
        res = res.expand_as(x_vals)
        valid = valid.expand_as(x_vals)

    return res, valid, has_x

def build_formula(tokens, x_value=None):
    """Собирает строку формулы. Если x_value задан — подставляет число вместо 'x'."""
    parts = []
    for i, tok in enumerate(tokens):
        val = str(x_value) if (tok == 'x' and x_value is not None) else str(tok)
        parts.append(val)
        if i < len(tokens) - 1:
            # оператор будет добавлен снаружи
            parts.append(None)  # плейсхолдер под оператор
    return parts  # список из чисел/None (операторы на местах None)

def stringify(parts, ops):
    out = []
    op_iter = iter(ops)
    for p in parts:
        if p is None:
            out.append(next(op_iter))
        else:
            out.append(str(p))
    return " ".join(out)

# ---------------- ПОИСК ----------------
torch.cuda.synchronize() if device == 'cuda' else None
t0 = time.perf_counter()

x_vals = torch.arange(start, end + 1, dtype=dtype, device=device)

solution = None
solution_tokens = None
solution_ops = None
solution_x = None

OPERAND_POOL = ['x'] + [str(c) for c in CONST_POOL]

checked_exprs = 0

for length in range(1, 6):  # длина по операндам
    if solution is not None:
        break
    # все последовательности операндов
    for tokens in itertools.product(OPERAND_POOL, repeat=length):
        # все последовательности операций соответствующей длины
        if length == 1:
            ops_list = [()]
        else:
            ops_list = itertools.product('+-*/', repeat=length - 1)

        for ops in ops_list:
            checked_exprs += 1

            res, valid, has_x = eval_expr_tokens(tokens, ops, x_vals)
            hit = valid & (res == y)

            if hit.any():
                idx = torch.nonzero(hit, as_tuple=False)[0, 0]
                x_found = int(x_vals[idx].item()) if has_x else None
                solution = True
                solution_tokens = tokens
                solution_ops = ops
                solution_x = x_found
                break
        if solution is not None:
            break

torch.cuda.synchronize() if device == 'cuda' else None
t1 = time.perf_counter()

# ---------------- ВЫВОД ----------------
elapsed = t1 - t0

if solution:
    parts = build_formula(solution_tokens, x_value=solution_x)
    formula_str = stringify(parts, solution_ops)
    if solution_x is not None:
        print(f"Найдено: x = {solution_x}")
        print(f"Формула: {formula_str} = {y}")
    else:
        print("Найдена формула без x:")
        print(f"{formula_str} = {y}")
else:
    print("Решения не найдено в заданном диапазоне и наборе выражений.")

print(f"Пул констант: {CONST_POOL}")
print(f"Длина выражений: 1..5")
print(f"Диапазон X: [{start}, {end}]")
print(f"Проверено выражений (комбинаций): ~{checked_exprs:,}")
print(f"Время: {fmt_time(elapsed)}")
