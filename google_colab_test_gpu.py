import torch
import time

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print("Устройство:", device)

y = 4211
start, end = -100000000, 99
base = 59 * 70

torch.cuda.synchronize() if device == 'cuda' else None
t0 = time.perf_counter()

x_vals = torch.arange(start, end + 1, dtype=torch.int32, device=device)
mask = (base + x_vals) == y
idx = torch.nonzero(mask, as_tuple=False)

torch.cuda.synchronize() if device == 'cuda' else None
t1 = time.perf_counter()

if idx.numel() > 0:
    solution = int(x_vals[idx[0, 0]].item())
    elapsed = t1 - t0
    ms = int((elapsed % 1) * 1000)
    sec = int(elapsed) % 60
    mins = int(elapsed // 60)
    print(f"Решение: x = {solution}")
    print(f"Время: {mins} мин {sec} сек {ms} мс")
else:
    print("Решения в заданном диапазоне нет.")
