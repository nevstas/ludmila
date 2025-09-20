import time
import itertools
import torch
import threading
from threading import Lock
from collections import defaultdict

myLock = threading.Lock()

service = "runpod" #"google_colab" or "runpod"

if service == "runpod":
    script_path = "/root/ludmila/ludmila"
elif service == "google_colab":
    script_path = "/content/drive/My Drive/ludmila/ludmila"
else:
    print("Unknown service")
    exit(1)


dataset_id = 2
dataset_filename = "data" + str(dataset_id) + ".txt"

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Device:", device)

REPEAT = 256   #1024–8192
start, end = -10, 10
dtype = torch.int32

BATCH_CACHE = None

def _rebuild_batch_cache():
    global BATCH_CACHE
    x_stack, y_stack, const_table = build_batched_inputs(REPEAT)
    BATCH_CACHE = {
        "repeat": REPEAT,
        "x": x_stack,
        "y": y_stack,
        "const": const_table,
        "ncols": x_stack.shape[1],
    }

def get_batched_inputs():
    global BATCH_CACHE
    need = (
        BATCH_CACHE is None
        or BATCH_CACHE["repeat"] != REPEAT
        or BATCH_CACHE["ncols"] != x_vals.numel() * REPEAT
    )
    if need:
        _rebuild_batch_cache()
    return BATCH_CACHE["x"], BATCH_CACHE["y"], BATCH_CACHE["const"]


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
    valid = (b != 0) & (a.remainder(b) == 0)
    out = torch.empty_like(a)
    out[valid] = torch.div(a[valid], b[valid], rounding_mode='trunc')
    out[~valid] = 0
    return out, valid

def op_pow2(a, _b_ignored):
    # (a)^2, always valid
    return a * a, torch.ones_like(a, dtype=torch.bool)

def op_sqrt(a, _b_ignored):
    valid = (a >= 0)
    r = torch.sqrt(a.float()).to(a.dtype)
    valid = valid & ((r * r) == a)

    out = torch.empty_like(a)
    out[valid] = r[valid]
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

CONST_CACHE = {}

def operand_tensor(token, x_vals):
    if token == 'x':
        return x_vals
    t = CONST_CACHE.get(token)
    if t is None or t.shape != x_vals.shape or t.device != x_vals.device or t.dtype != x_vals.dtype:
        t = torch.full_like(x_vals, int(token))
        CONST_CACHE[token] = t
    return t


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
        elif sym == '^0.5' and is_last:
            # postpone sqrt until the very end (after + and -)
            trailing_sqrt = True
            # IMPORTANT: do not add b, it is "dummy" for unary operation
        else:
            # + or - (and any other operator if you want to extend)
            ops2.append(sym)
            vals2.append(b)

    # --- Second pass: + and - ---
    res = vals2[0]
    for i, sym in enumerate(ops2):
        fn = OPS[sym]
        b = vals2[i + 1]
        res, v_step = fn(res, b)
        valid = valid & v_step

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

def build_batched_inputs(REPEAT=1):
    S = len(dataset)
    N = x_vals.numel()

    # [S, N]
    x_stack = x_vals.unsqueeze(0).expand(S, N)
    if REPEAT > 1:
        x_stack = x_stack.repeat(1, REPEAT)  # [S, N*REPEAT]

    y_vec = torch.tensor([y for (y, _) in dataset], device=device, dtype=dtype)
    y_stack = y_vec.unsqueeze(1).expand(S, x_stack.shape[1])

    const_table = {}
    for idx, base_val in enumerate(CONST_POOL_BASE):
        per_set = torch.tensor([consts[idx] for (_, consts) in dataset],
                               device=device, dtype=dtype)                 # [S]
        const_table[str(base_val)] = per_set.unsqueeze(1).expand_as(x_stack) # [S, N*REPEAT]
    return x_stack, y_stack, const_table


def eval_expr_tokens_batched(tokens, ops, x_stack, const_table):
    has_x = any(t == 'x' for t in tokens)
    valid = torch.ones_like(x_stack, dtype=torch.bool)

    vals = [(x_stack if t == 'x' else const_table[t]) for t in tokens]

    # --- pass 1: *, /, ^2 ---
    vals2 = [vals[0]]
    ops2 = []
    trailing_sqrt = False
    n_ops = len(ops)

    for i, sym in enumerate(ops):
        b = vals[i + 1]
        is_last = (i == n_ops - 1)
        if sym in OPS_FIRST_PASS:
            cur, v_step = OPS[sym](vals2[-1], b)
            vals2[-1] = cur
            valid = valid & v_step
        elif sym == '^0.5' and is_last:
            trailing_sqrt = True
        else:
            ops2.append(sym)
            vals2.append(b)

    # --- pass 2: + и - ---
    res = vals2[0]
    for i, sym in enumerate(ops2):
        res, v_step = OPS[sym](res, vals2[i + 1])
        valid = valid & v_step

    if trailing_sqrt:
        res, v_step = OPS['^0.5'](res, res)
        valid = valid & v_step

    return res, valid, has_x

def validate_formula_on_all_sets(tokens_base, ops):
    x_stack, y_stack, const_table = get_batched_inputs()

    with torch.no_grad():
        res, valid, has_x = eval_expr_tokens_batched(tokens_base, ops, x_stack, const_table)
        hit = valid & (res == y_stack)                # [S, N*REPEAT]

        ok_per_x_expanded = hit.all(dim=0)            # [N*REPEAT]

        if REPEAT > 1:
            ok_mask = ok_per_x_expanded.view(REPEAT, -1).any(dim=0)  # [N]
        else:
            ok_mask = ok_per_x_expanded                              # [N]

        ok = bool(ok_mask.any().item())

        xs_demo = None
        if ok:
            j = int(torch.nonzero(ok_mask, as_tuple=False).flatten()[0].item())
            xs_demo = [int(x_stack[s, j].item()) for s in range(x_stack.shape[0])]

    return ok, xs_demo, ok_mask



def stringify_pretty(tokens, ops, x_value=None, sqrt_style="pow"):
    def tok(t):
        return str(x_value) if (t == 'x' and x_value is not None) else str(t)

    if not tokens:
        return ""

    out = tok(tokens[0])
    i_tok = 1

    for i, op in enumerate(ops):
        is_last = (i == len(ops) - 1)

        if op in ('+','-','*','/'):
            if i_tok >= len(tokens): break
            out = f"{out} {op} {tok(tokens[i_tok])}"
            i_tok += 1

        elif op == '^2':
            out = f"{out} ^2"
            if i_tok < len(tokens):
                i_tok += 1

        elif op == '^0.5':
            if sqrt_style == "func":
                out = f"sqrt({out})"
            else:
                out = f"({out}) ^0.5"
            if i_tok < len(tokens):
                i_tok += 1

    return out


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
solutions_found_global = 0
attempted_eqs_total_base = 0
attempted_eqs_by_len_base = defaultdict(int)

time_total_start = time.time()

OPS_ALPHABET = ['+', '-', '*', '/', '^2', '^0.5']

try:
    # INFINITE LOOP OF LENGTHS: 1,2,3,4,5, ...
    for length in itertools.count(1):  # CHANGED: instead of range(1, 6)
        # all operand sequences of length `length`
        for tokens in itertools.product(OPERAND_POOL_BASE, repeat=length):

            # all operator sequences of the corresponding length
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
                attempted_eqs_by_len_base[length] += n_valid_base  # lengths grow without limits

                if hits.numel() == 0:
                    continue

                ok, xs_demo, ok_mask = validate_formula_on_all_sets(list(tokens), ops)
                if not ok:
                    continue

                # Universal formula found — log ONCE
                common_hits = torch.nonzero(ok_mask, as_tuple=False).flatten()
                x_found_base = int(x_vals[common_hits[0]].item()) if common_hits.numel() > 0 else None
                formula_str = stringify_pretty(list(tokens), list(ops), x_value=x_found_base, sqrt_style="pow")
                time_total = time.time() - time_total_start
                message = time.strftime("%d.%m.%Y %H:%M:%S") + " Solution data" + str(dataset_id) + ": " + formula_str + " at " + str(round(time_total, 2)) + " seconds"

                print(message)
                writeln(message)
                solutions_found_global += 1

except KeyboardInterrupt:
    # Graceful termination by Ctrl+C with statistics output
    if device == 'cuda':
        torch.cuda.synchronize()
    elapsed = time.perf_counter() - t0
    print("\nStopped by user (Ctrl+C). Current results:")
    if solutions_found_global == 0:
        print("No universal formulas found yet.")
    else:
        print(f"Universal formulas found: {solutions_found_global}")
    print(f"Base constant set: {CONST_POOL_BASE}")
    print(f"Range X: [{start}, {end}]")
    print(f"Checked combinations on base set: ~{checked_exprs:,}")
    print(f"Time: {fmt_time(elapsed)}")
