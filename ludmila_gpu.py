import time
import itertools
import torch
import threading
from threading import Lock
import os

myLock = threading.Lock()

script_path = os.path.dirname(os.path.realpath(__file__))

dataset_id = 2
dataset_filename = "data" + str(dataset_id) + ".txt"

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Device:", device)

# X range
start, end = -10, 10
dtype = torch.int64

def fmt_time(t):
    ms = int((t % 1) * 1000)
    sec = int(t) % 60
    mins = int(t // 60)
    return f"{mins} min {sec} sec {ms} ms"

def op_add(a, b):
    return a + b, torch.ones_like(a, dtype=torch.bool)

def op_sub(a, b):
    return a - b, torch.ones_like(a, dtype=torch.bool)

def op_mul(a, b):
    return a * b, torch.ones_like(a, dtype=torch.bool)

def op_div(a, b):
    # strict integer divisibility and ban on division by 0
    valid = (b != 0) & (a.remainder(b) == 0)
    out = torch.empty_like(a)
    if valid.any():
        out[valid] = a[valid] // b[valid]
    if (~valid).any():
        out[~valid] = 0
    return out, valid

def op_pow2(a, _b_ignored):
    # (a)^2, always valid
    return a * a, torch.ones_like(a, dtype=torch.bool)

def op_sqrt(a, _b_ignored):
    # sqrt(a) only for a >= 0 and only if a is a perfect square
    valid = (a >= 0)

    # get integer root
    r = torch.sqrt(a.float()).to(torch.int64)

    # check accuracy: r*r == a
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

    # --- First pass: *, /, ^2 ---
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
            # postpone sqrt until the very end (after + and -)
            trailing_sqrt = True
            # IMPORTANT: do not add b, it is "dummy" for unary operation
        else:
            # + or - (and any other operator if you want to extend)
            ops2.append(sym)
            vals2.append(b)

    # Early exit
    if has_x and not valid.any():
        return torch.zeros_like(x_vals), torch.zeros_like(x_vals, dtype=torch.bool), has_x
    if not has_x and not bool(valid.item()):
        out = torch.zeros_like(x_vals)
        msk = torch.zeros_like(x_vals, dtype=torch.bool)
        return out, msk, has_x

    # --- Second pass: + and - ---
    res = vals2[0]
    for i, sym in enumerate(ops2):
        fn = OPS[sym]
        b = vals2[i + 1]
        res, v_step = fn(res, b)
        valid = valid & v_step
        if has_x and not valid.any(): break
        if not has_x and not bool(valid.item()): break

    # --- Deferred sqrt at the very end ---
    if trailing_sqrt:
        res, v_step = OPS['^0.5'](res, res)   # b is ignored
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
            parts.append(None)  # placeholder for operator
    return parts

def stringify(parts, ops):
    out = []
    op_iter = iter(ops)
    for p in parts:
        if p is None:
            try:
                out.append(next(op_iter))
            except StopIteration:
                # Just in case, but normally won't get here
                pass
        else:
            out.append(str(p))
    # If there are leftover operators (e.g., final unary ^0.5) — append them at the end
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
    Expects lines of the format:
    y [c1 c2 c3 ...]
    Returns a list: [(y, [c1, c2, c3, ...]), ...]
    The number of constants after y can be arbitrary (including 0).
    Empty lines are ignored.
    """
    ds = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # at minimum — one number (y)
            try:
                yv = int(parts[0])
            except ValueError:
                # line is invalid — skip it
                continue
            consts = []
            for p in parts[1:]:
                try:
                    consts.append(int(p))
                except ValueError:
                    # invalid token — skip only this one
                    continue
            ds.append((yv, consts))
    return ds


# --- Mapping constants by indices (key to universal check) ---
def make_const_index_map(const_pool):
    """
    Returns dict: {"51": 0, "62": 1, "73": 2} for the current pool.
    """
    return {str(v): i for i, v in enumerate(const_pool)}

def remap_tokens_to_target_consts(tokens, base_const_pool, target_consts):
    """
    Transfers the structure of tokens, replacing constants from the base pool
    with the corresponding constants of target_consts by INDEX.
    Example: tokens = ['x','*','51','+','73'] with target=[52,63,74]
    -> ['x','*','52','+','74']
    """
    idx_map = make_const_index_map(base_const_pool)
    out = []
    for tok in tokens:
        if tok == 'x':
            out.append('x')
        else:
            # this is a constant from the base pool
            k = idx_map.get(tok, None)
            if k is None:
                # Protection: if tokens unexpectedly contain a number not from the pool
                out.append(tok)
            else:
                out.append(str(target_consts[k]))
    return out

def validate_formula_on_all_sets(tokens_base, ops):
    """
    Checks the formula (structure tokens_base + ops), selected on the first set,
    on all sets of the dataset. For each set substitutes its constants
    by indices and checks if there exists at least one x in the range
    such that res == y of the set with valid operations.
    Returns (ok, xs_per_set) — ok: bool; xs_per_set: list of found x or None.
    """
    xs_demo = []  # for info: which x were found on the sets
    for (y_target, consts_target) in dataset:
        # Transfer tokens to constants of this set
        tokens_target = remap_tokens_to_target_consts(tokens_base, CONST_POOL_BASE, consts_target)
        # Compute
        res, valid, has_x = eval_expr_tokens(tokens_target, ops, x_vals)
        hits = torch.nonzero(valid & (res == y_target), as_tuple=False).flatten()
        if hits.numel() == 0:
            return False, None
        # Save one demo x
        xs_demo.append(int(x_vals[hits[0]].item()) if has_x else None)
    return True, xs_demo

if device == 'cuda':
    torch.cuda.synchronize()
t0 = time.perf_counter()

# Load the whole dataset
dataset_path = script_path + "/datasets/" + dataset_filename
dataset = load_dataset(dataset_path)
if not dataset:
    raise RuntimeError(f"Dataset is empty or not read: {dataset_path}")

# The first set is the base for initial search
# CHANGED: no checks or comparisons — just take the first line from the file
y_base, CONST_POOL_BASE = dataset[0]  # CHANGED

x_vals = torch.arange(start, end + 1, dtype=dtype, device=device)

OPERAND_POOL_BASE = ['x'] + [str(c) for c in CONST_POOL_BASE]

# stats:
checked_exprs = 0
solutions_found_global = 0  # how many "universal" formulas found and logged
attempted_eqs_total_base = 0                  # (2a) scalar checks f(x)=y on the base set
attempted_eqs_by_len_base = {L: 0 for L in range(1, 6)}

time_total_start = time.time()

for length in range(1, 6):  # operand length
    # all operand sequences
    for tokens in itertools.product(OPERAND_POOL_BASE, repeat=length):
        # all operator sequences of corresponding length
        OPS_ALPHABET = ['+', '-', '*', '/', '^2', '^0.5']

        if length == 1:
            ops_list = [()]
        else:
            ops_list = itertools.product(OPS_ALPHABET, repeat=length - 1)

        for ops in ops_list:
            # Compute on the BASE set (as before)
            res, valid, has_x = eval_expr_tokens(tokens, ops, x_vals)
            hits = torch.nonzero(valid & (res == y_base), as_tuple=False).flatten()

            n_valid_base = int(valid.sum().item())

            # stats:
            checked_exprs += 1
            attempted_eqs_total_base += n_valid_base
            attempted_eqs_by_len_base[length] += n_valid_base

            if hits.numel() == 0:
                continue

            # Previously we logged right away. Now — first validate on ALL sets.
            ok, xs_demo = validate_formula_on_all_sets(list(tokens), ops)
            if not ok:
                # Formula is not universal — skip without logs
                continue

            # Universal formula found — log ONCE
            # Show the formula with x substituted from the first hit on the base set
            x_found_base = int(x_vals[hits[0]].item()) if has_x else None
            parts = build_formula(tokens, x_value=x_found_base)
            formula_str = stringify(parts, ops)
            time_total = time.time() - time_total_start
            message = time.strftime("%d.%m.%Y %H:%M:%S") + " Solution data" + str(dataset_id) + ": " + formula_str + " at " + str(round(time_total, 2)) + " seconds"

            print(message)
            writeln(message)
            solutions_found_global += 1
            # We may NOT stop search — let it find alternative universal formulas
            # If you want to stop at the first one — uncomment the next line:
            # raise SystemExit

if device == 'cuda':
    torch.cuda.synchronize()
t1 = time.perf_counter()

# ---------------- OUTPUT ----------------
elapsed = t1 - t0

if solutions_found_global == 0:
    print("No universal solutions found in the given range and set of expressions.")
else:
    print(f"Total universal formulas: {solutions_found_global}")

print(f"Base constant pool: {CONST_POOL_BASE}")
print(f"X range: [{start}, {end}]")
print(f"Checked expressions (combinations) on the base set: ~{checked_exprs:,}")
print(f"Time: {fmt_time(elapsed)}")
#c:\Python311\python d:\python\maths\ludmila_gpu.py