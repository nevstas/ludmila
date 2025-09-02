# -*- coding: utf-8 -*-
import time
import itertools
import torch

# ---------------- ПАРАМЕТРЫ ----------------
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Устройство:", device)

y = 4211
rng_start, rng_end = -1000, 1000   # диапазон значений для КАЖДОГО операнда (меняй при необходимости)
dtype = torch.int64

# Предохранитель от экспоненты: сколько скалярных итераций позволяем максимум
max_scalar_loops = 5_000_000

# ---------------- УТИЛИТЫ ----------------
def fmt_time(t):
    ms = int((t % 1) * 1000)
    sec = int(t) % 60
    mins = int(t // 60)
    return f"{mins} мин {sec} сек {ms} мс"

def apply_op_scalar(a, b, op):
    """Скалярная операция. Для '/' — строгое целочисленное деление без остатка."""
    if op == '+':
        return a + b, True
    if op == '-':
        return a - b, True
    if op == '*':
        return a * b, True
    if op == '/':
        if b == 0:
            return 0, False
        if a % b != 0:
            return 0, False
        return a // b, True
    return 0, False

def inverse_last_needed(r, op_last, y_const):
    """
    Для известного промежуточного r и последней операции op_last находим необходимый
    последний операнд v, чтобы (r op_last v) == y_const.
    r и y_const — тензоры одинаковой формы.
    Возвращает (v, valid_mask).
    """
    if op_last == '+':
        return (y_const - r), torch.ones_like(r, dtype=torch.bool)

    if op_last == '-':
        # r - v = y  =>  v = r - y
        return (r - y_const), torch.ones_like(r, dtype=torch.bool)

    if op_last == '*':
        # r * v = y  =>  r != 0, y % r == 0, v = y // r
        valid = (r != 0) & (y_const % r == 0)
        v = torch.empty_like(r)
        if valid.any():
            v[valid] = y_const[valid] // r[valid]
        if (~valid).any():
            v[~valid] = 0
        return v, valid

    if op_last == '/':
        # r / v = y  =>  y != 0, r % y == 0, v = r // y, и v != 0
        # (случай y==0 даёт бесконечно много решений; не рассматриваем)
        y0 = y_const
        if (y0 == 0).all():
            return torch.zeros_like(r), torch.zeros_like(r, dtype=torch.bool)
        valid = (y0 != 0) & (r % y0 == 0)
        v = torch.empty_like(r)
        if valid.any():
            v[valid] = r[valid] // y0[valid]
        if (~valid).any():
            v[~valid] = 0
        valid = valid & (v != 0)
        return v, valid

    raise ValueError("Unknown op")

def in_range_int(v, lo, hi):
    return (v >= lo) & (v <= hi)

def print_formula(operands, ops):
    parts = []
    for i, val in enumerate(operands):
        parts.append(str(int(val)))
        if i < len(ops):
            parts.append(ops[i])
    return " ".join(parts)

# ---------------- ПОДГОТОВКА ----------------
vec_vals = torch.arange(rng_start, rng_end + 1, dtype=dtype, device=device)
range_vals = list(range(rng_start, rng_end + 1))
ops_set = ['+', '-', '*', '/']

# ---------------- ПОИСК ----------------
torch.cuda.synchronize() if device == 'cuda' else None
t0 = time.perf_counter()

found = False
found_operands = None
found_ops = None
scalar_loops = 0

# длина выражения (число операндов) 1..5
for length in range(1, 6):
    if found:
        break

    # length == 1: просто a == y
    if length == 1:
        if rng_start <= y <= rng_end:
            found = True
            found_operands = [y]
            found_ops = []
        continue

    # генерируем все последовательности операций длиной length-1
    for ops in itertools.product(ops_set, repeat=length - 1):
        if found:
            break

        if length == 2:
            # выражение: a op b
            # перебираем a скаляром, b находим аналитически (тензором), фильтруем попадания
            for a in range_vals:
                scalar_loops += 1
                if scalar_loops > max_scalar_loops:
                    break

                r = torch.full_like(vec_vals, a, device=device)
                y_vec = torch.full_like(vec_vals, y, device=device)
                v_needed, valid = inverse_last_needed(r, ops[-1], y_vec)
                hit = valid & in_range_int(v_needed, rng_start, rng_end)
                if hit.any():
                    b = int(v_needed[hit][0].item())
                    found = True
                    found_operands = [a, b]
                    found_ops = [ops[-1]]
                    break

        elif length == 3:
            # выражение: (a op0 b) op1 c
            # перебираем a скаляром, b — вектором, c находим аналитически
            for a in range_vals:
                scalar_loops += 1
                if scalar_loops > max_scalar_loops:
                    break

                b_vec = vec_vals
                a_vec = torch.full_like(b_vec, a, device=device)

                if ops[0] == '/':
                    valid_r = (b_vec != 0) & (a_vec.remainder(b_vec) == 0)
                    r_vec = torch.empty_like(b_vec)
                    if valid_r.any():
                        r_vec[valid_r] = a_vec[valid_r] // b_vec[valid_r]
                    if (~valid_r).any():
                        r_vec[~valid_r] = 0
                elif ops[0] == '+':
                    r_vec = a_vec + b_vec
                    valid_r = torch.ones_like(r_vec, dtype=torch.bool)
                elif ops[0] == '-':
                    r_vec = a_vec - b_vec
                    valid_r = torch.ones_like(r_vec, dtype=torch.bool)
                elif ops[0] == '*':
                    r_vec = a_vec * b_vec
                    valid_r = torch.ones_like(r_vec, dtype=torch.bool)
                else:
                    raise RuntimeError

                y_vec = torch.full_like(r_vec, y, device=device)
                v_needed, valid2 = inverse_last_needed(r_vec, ops[1], y_vec)
                hit = valid_r & valid2 & in_range_int(v_needed, rng_start, rng_end)
                if hit.any():
                    b = int(b_vec[hit][0].item())
                    c = int(v_needed[hit][0].item())
                    found = True
                    found_operands = [a, b, c]
                    found_ops = [ops[0], ops[1]]
                    break

        elif length == 4:
            # выражение: ((a op0 b) op1 c) op2 d
            # перебираем a,b скалярами, c — вектором, d находим аналитически
            for a in range_vals:
                if found:
                    break
                for b in range_vals:
                    scalar_loops += 1
                    if scalar_loops > max_scalar_loops:
                        break

                    r1, ok1 = apply_op_scalar(a, b, ops[0])
                    if not ok1:
                        continue

                    c_vec = vec_vals
                    r1_vec = torch.full_like(c_vec, r1, device=device)

                    if ops[1] == '/':
                        valid_r2 = (c_vec != 0) & (r1_vec.remainder(c_vec) == 0)
                        r2 = torch.empty_like(c_vec)
                        if valid_r2.any():
                            r2[valid_r2] = r1_vec[valid_r2] // c_vec[valid_r2]
                        if (~valid_r2).any():
                            r2[~valid_r2] = 0
                    elif ops[1] == '+':
                        r2 = r1_vec + c_vec
                        valid_r2 = torch.ones_like(r2, dtype=torch.bool)
                    elif ops[1] == '-':
                        r2 = r1_vec - c_vec
                        valid_r2 = torch.ones_like(r2, dtype=torch.bool)
                    elif ops[1] == '*':
                        r2 = r1_vec * c_vec
                        valid_r2 = torch.ones_like(r2, dtype=torch.bool)
                    else:
                        raise RuntimeError

                    y_vec = torch.full_like(r2, y, device=device)
                    v_needed, valid3 = inverse_last_needed(r2, ops[2], y_vec)
                    hit = valid_r2 & valid3 & in_range_int(v_needed, rng_start, rng_end)
                    if hit.any():
                        c = int(c_vec[hit][0].item())
                        d = int(v_needed[hit][0].item())
                        found = True
                        found_operands = [a, b, c, d]
                        found_ops = [ops[0], ops[1], ops[2]]
                        break

        elif length == 5:
            # выражение: (((a op0 b) op1 c) op2 d) op3 e
            # перебираем a,b,c скалярами, d — вектором, e находим аналитически
            for a in range_vals:
                if found:
                    break
                for b in range_vals:
                    if found:
                        break
                    for c in range_vals:
                        scalar_loops += 1
                        if scalar_loops > max_scalar_loops:
                            break

                        r1, ok1 = apply_op_scalar(a, b, ops[0])
                        if not ok1:
                            continue
                        r2, ok2 = apply_op_scalar(r1, c, ops[1])
                        if not ok2:
                            continue

                        d_vec = vec_vals
                        r2_vec = torch.full_like(d_vec, r2, device=device)

                        if ops[2] == '/':
                            valid_r3 = (d_vec != 0) & (r2_vec.remainder(d_vec) == 0)
                            r3 = torch.empty_like(d_vec)
                            if valid_r3.any():
                                r3[valid_r3] = r2_vec[valid_r3] // d_vec[valid_r3]
                            if (~valid_r3).any():
                                r3[~valid_r3] = 0
                        elif ops[2] == '+':
                            r3 = r2_vec + d_vec
                            valid_r3 = torch.ones_like(r3, dtype=torch.bool)
                        elif ops[2] == '-':
                            r3 = r2_vec - d_vec
                            valid_r3 = torch.ones_like(r3, dtype=torch.bool)
                        elif ops[2] == '*':
                            r3 = r2_vec * d_vec
                            valid_r3 = torch.ones_like(r3, dtype=torch.bool)
                        else:
                            raise RuntimeError

                        y_vec = torch.full_like(r3, y, device=device)
                        v_needed, valid4 = inverse_last_needed(r3, ops[3], y_vec)
                        hit = valid_r3 & valid4 & in_range_int(v_needed, rng_start, rng_end)
                        if hit.any():
                            d = int(d_vec[hit][0].item())
                            e = int(v_needed[hit][0].item())
                            found = True
                            found_operands = [a, b, c, d, e]
                            found_ops = [ops[0], ops[1], ops[2], ops[3]]
                            break

        else:
            raise RuntimeError("unexpected length")

# ---------------- ВЫВОД ----------------
torch.cuda.synchronize() if device == 'cuda' else None
t1 = time.perf_counter()
elapsed = t1 - t0

if found:
    formula = print_formula(found_operands, found_ops)
    print("Найдена формула:")
    print(f"{formula} = {y}")
else:
    print("Решение не найдено в установленных ограничениях (см. max_scalar_loops).")

print(f"Диапазон операндов: [{rng_start}, {rng_end}]")
print(f"Макс. скалярных итераций: {max_scalar_loops:,}")
print(f"Время: {fmt_time(elapsed)}")
