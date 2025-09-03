import time
import itertools
import torch
import threading
from threading import Lock

myLock = threading.Lock()

script_path = "/content/drive/My Drive/ludmila/ludmila"

# ---------------- ПАРАМЕТРЫ ----------------
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Устройство:", device)

y = 4211
start, end = -10, 10          # диапазон X; можешь увеличить
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
    valid = (b != 0) & (a.remainder(b) == 0)
    out = torch.empty_like(a)
    if valid.any():
        out[valid] = a[valid] // b[valid]
    if (~valid).any():
        out[~valid] = 0
    return out, valid

OPS = {'+': op_add, '-': op_sub, '*': op_mul, '/': op_div}

def operand_tensor(token, x_vals):
    if token == 'x':
        return x_vals
    else:
        return torch.full_like(x_vals, int(token), dtype=x_vals.dtype, device=x_vals.device)

def eval_expr_tokens(tokens, ops, x_vals):
    has_x = any(tok == 'x' for tok in tokens)
    if has_x:
        res = operand_tensor(tokens[0], x_vals)
        valid = torch.ones_like(x_vals, dtype=torch.bool)
    else:
        dummy = torch.tensor([0], device=x_vals.device, dtype=x_vals.dtype)
        res = operand_tensor(tokens[0], dummy)[:1]
        valid = torch.ones(1, dtype=torch.bool, device=x_vals.device)

    for sym, tok in zip(ops, tokens[1:]):
        b = operand_tensor(tok, x_vals if has_x else res)
        fn = OPS[sym]
        res, v_step = fn(res, b)
        valid = valid & v_step
        if has_x and not valid.any():
            break
        if not has_x and not bool(valid.item()):
            break

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
            out.append(next(op_iter))
        else:
            out.append(str(p))
    return " ".join(out)

def writeln(str):
    myLock.acquire()
    with open(script_path + "/log.txt", 'a', encoding='utf-8') as the_file:
        the_file.write(str + "\n")
    myLock.release()

# ---------------- ПОИСК ----------------
if device == 'cuda':
    torch.cuda.synchronize()
t0 = time.perf_counter()

x_vals = torch.arange(start, end + 1, dtype=dtype, device=device)

OPERAND_POOL = ['x'] + [str(c) for c in CONST_POOL]

checked_exprs = 0
solutions_found = 0

for length in range(1, 6):  # длина по операндам
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
            hits = torch.nonzero(valid & (res == y), as_tuple=False).flatten()

            if hits.numel() == 0:
                continue

            # Печатаем решения сразу по мере нахождения
            if has_x:
                for idx in hits.tolist():
                    x_found = int(x_vals[idx].item())
                    parts = build_formula(tokens, x_value=x_found)
                    formula_str = stringify(parts, ops)
                    message = time.strftime("%d.%m.%Y %H:%M:%S") + f" Найдено: x = {x_found} | {formula_str} = {y}"
                    print(message)
                    writeln(message)
                    solutions_found += 1
            else:
                # формула без x — либо совпала, либо нет (hits тогда будет полный диапазон)
                parts = build_formula(tokens, x_value=None)
                formula_str = stringify(parts, ops)
                message = time.strftime("%d.%m.%Y %H:%M:%S") + f" Найдена формула без x:{formula_str} = {y}"
                print(message)
                writeln(message)
                solutions_found += 1
                # без x дальнейшие x не влияют — достаточно один раз сообщить

if device == 'cuda':
    torch.cuda.synchronize()
t1 = time.perf_counter()

# ---------------- ВЫВОД ----------------
elapsed = t1 - t0

if solutions_found == 0:
    print("Решения не найдено в заданном диапазоне и наборе выражений.")
else:
    print(f"Всего решений: {solutions_found}")

print(f"Пул констант: {CONST_POOL}")
print(f"Длина выражений: 1..5")
print(f"Диапазон X: [{start}, {end}]")
print(f"Проверено выражений (комбинаций): ~{checked_exprs:,}")
print(f"Время: {fmt_time(elapsed)}")
