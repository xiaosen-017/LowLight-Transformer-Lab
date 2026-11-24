"""M4: geometry and overlap fusion for one float32 RGB image (CHW)."""
from itertools import product

import torch


def starts(length, tile, stride):
    regular = list(range(0, length - tile + 1, stride))
    if regular[-1] != length - tile:
        regular.append(length - tile)
    return regular


def reflected_axis(size, target, device):
    # Repeated right/bottom reflect padding also supports padding >= size.
    index = torch.arange(target, device=device)
    if size == 1:
        return torch.zeros_like(index)
    period = 2 * (size - 1)
    return (size - 1) - ((index % period) - (size - 1)).abs()


@torch.inference_mode()
def tiled_predict(image, predict, tile, stride, fusion="mean"):
    if image.ndim != 3 or image.shape[0] != 3 or image.dtype != torch.float32:
        raise ValueError("expected float32 CHW RGB")
    h, w = image.shape[-2:]
    if min(h, w) < 1 or any(t <= 0 or t % 16 or not 0 < s <= t
                             for t, s in zip(tile, stride, strict=True)):
        raise ValueError("tiles must be multiples of 16; stride must be in [1,tile]")
    ph, pw = tile
    H, W = (max(t, ((d + 15) // 16) * 16) for d, t in zip((h, w), tile))
    padded = image.index_select(1, reflected_axis(h, H, image.device))
    padded = padded.index_select(2, reflected_axis(w, W, image.device))
    corners = list(product(starts(H, ph, stride[0]), starts(W, pw, stride[1])))
    # Match upstream materialization and one-tile-per-forward execution.
    patches = torch.stack([padded[:, y:y+ph, x:x+pw] for y, x in corners])
    predictions = [predict(batch) for batch in patches.split(1)]
    window = image.new_ones(tile)
    if fusion == "hann":
        axes = [torch.hann_window(t, periodic=False, device=image.device,
                                  dtype=image.dtype) for t in tile]
        window = torch.outer(*axes).clamp_min(1e-3)
    elif fusion != "mean":
        raise ValueError("fusion must be mean or hann")
    total = torch.zeros_like(padded)
    weights = image.new_zeros(H, W)
    counts = torch.zeros((H, W), device=image.device, dtype=torch.int32)
    for (y, x), batch in zip(corners, predictions):
        if batch.shape != (1, 3, ph, pw):
            raise ValueError("predict must preserve tile shape")
        region = (..., slice(y, y+ph), slice(x, x+pw))
        total[region] += batch[0] * window
        weights[region] += window
        counts[region] += 1
    if not (weights > 0).all():
        raise RuntimeError("uncovered pixels before normalization")
    output = (total / weights)[:, :h, :w]
    if not output.isfinite().all():
        raise RuntimeError("nonfinite reconstruction")
    return output, counts, weights, corners
