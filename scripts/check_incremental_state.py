"""Exact canonical-update obstruction using documented slot-index free values.

See docs/order-independence-proof.md for the free-value convention.
Rows are masks, the leftmost pivot is the least significant set bit.
The 7- and 8-bit examples use A={1}, B={31}, incoming row=2.
Both old systems solve to the same vector and pivot set because
g(1) XOR g(2) XOR g(3) XOR g(4) = 0. Adding row 2 forces slot 1
to zero, causing the canonical slot 0 to differ by g(1).

Therefore even the solved vector plus pivot bitmap and rank cannot
determine the exact same-seed canonical union in this banded model.
Keeping an echelon basis is sufficient, since its span is unchanged
by elimination. This does not rule out approximate membership
merging, alternative encodings, or special restricted hash families.
No production hash/kernel behavior or literature priority is claimed.

Run: python scripts/check_incremental_state.py
"""
from itertools import permutations


def solve(rows, bits=7, slots=5):
    pivots = {}
    for row in rows:
        while row:
            i = (row & -row).bit_length() - 1
            if i not in pivots:
                pivots[i] = row
                break
            row ^= pivots[i]
    mask = (1 << bits) - 1
    x = [i * 0x9E3779B185EBCA87 & mask for i in range(slots)]
    for i, row in sorted(pivots.items(), reverse=True):
        x[i] = 0
        for j in range(i + 1, slots):
            if row >> j & 1:
                x[i] ^= x[j]
    for row in rows:
        value = 0
        for j in range(slots):
            if row >> j & 1:
                value ^= x[j]
        assert value == 0
    return tuple(x), tuple(sorted(pivots))


if __name__ == '__main__':
    a, b, c = (1,), (31,), 2
    for bits in (7, 8):
        old = solve(a, bits)
        assert old == solve(b, bits)
        left, right = solve((*a, c), bits), solve((*b, c), bits)
        assert left[1] == right[1] == (0, 1)
        assert left[0] != right[0]
        for rows in (a, b, (*a, c), (*b, c)):
            assert all(solve(p, bits) == solve(rows, bits) for p in permutations(rows))
        print(bits, old, left, right)
