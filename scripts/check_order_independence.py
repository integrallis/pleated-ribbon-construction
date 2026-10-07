"""Independent check of the order-independence claims for ribbon banding over GF(2).

Model (as in the paper and docs/order-independence-proof.md): each key has a start s, a w-bit
coefficient row whose first bit is 1, and an r-bit result b. Banding reduces the row against
stored rows at its leading position until it lands in an empty slot or reduces to zero (then it
is dropped). Back-substitution assigns every free slot j the value g(j) and solves the rest.

Checked, over many random instances and insertion orders (and ALL orders for tiny instances):
  A. homogeneous (all b = 0), instances that DO contain dependent rows: is Z identical in
     every order?   <- the unreviewed strengthening
  B. non-homogeneous, rows independent: Z identical in every order?  <- Proposition 1
  C. non-homogeneous with dependent rows, arbitrary results: can Z differ between orders?
     (expected: yes; such systems are almost always inconsistent, and a real standard-ribbon
     build would fail and retry instead of dropping the row)
  D. non-homogeneous, dependent rows present, but CONSISTENT (results generated from a hidden
     solution): Z identical in every order?   <- the general statement: consistency suffices
"""
import itertools, random

def band(m, w, eqs):
    coeff = [0] * m          # coeff[i]: w-bit row stored at slot i, bit 0 = column i
    res = [0] * m
    dropped = 0
    for s, c, b in eqs:
        i = s
        while True:
            if c == 0:
                dropped += 1 if True else 0
                consistent = (b == 0)
                break
            # shift so the lowest set bit is at bit 0; advance i accordingly
            tz = (c & -c).bit_length() - 1
            c >>= tz; i += tz
            if coeff[i] == 0:
                coeff[i], res[i] = c, b
                consistent = True
                break
            c ^= coeff[i]; b ^= res[i]
        if c == 0 and not consistent:
            pass  # inconsistent dropped equation (only possible when non-homogeneous)
    return coeff, res, dropped

def backsubst(m, w, r, coeff, res, g):
    Z = [0] * m
    for i in range(m - 1, -1, -1):
        if coeff[i] == 0:
            Z[i] = g(i) & ((1 << r) - 1)
        else:
            acc = res[i]
            c = coeff[i] >> 1
            j = i + 1
            while c:
                if c & 1:
                    acc ^= Z[j]
                c >>= 1; j += 1
            Z[i] = acc
    return Z

def instance(rng, m, w, n, r, homogeneous, consistent=False):
    eqs = []
    hidden = [rng.getrandbits(r) for _ in range(m)]
    for _ in range(n):
        s = rng.randrange(m - w + 1)
        c = rng.getrandbits(w) | 1
        if homogeneous:
            b = 0
        elif consistent:  # b = row . hidden, so the whole system has a solution
            b = 0
            for k in range(w):
                if (c >> k) & 1:
                    b ^= hidden[s + k]
        else:
            b = rng.getrandbits(r)
        eqs.append((s, c, b))
    return eqs

g = lambda i: (i * 0x9E3779B185EBCA87) & 0xFFFFFFFFFFFFFFFF   # the kernel's rule

def run(label, homogeneous, want_dependent, trials, exhaustive, consistent=False):
    rng = random.Random(12345 + homogeneous * 7 + want_dependent)
    tested = identical = with_dep = 0
    while tested < trials:
        if exhaustive:
            m, w, n, r = 10, 4, rng.randrange(5, 8), 3
        else:
            m, w, r = rng.choice([(40, 8, 7), (96, 16, 7), (200, 32, 8)])
            n = rng.randrange(int(m * 0.7), int(m * 1.2))
        eqs = instance(rng, m, w, n, r, homogeneous, consistent)
        _, _, d0 = band(m, w, eqs)
        if (d0 > 0) != want_dependent:
            continue
        tested += 1; with_dep += d0 > 0
        orders = (itertools.permutations(eqs) if exhaustive
                  else (rng.sample(eqs, len(eqs)) for _ in range(40)))
        ref = None; same = True
        for o in orders:
            c, rs, _ = band(m, w, list(o))
            Z = backsubst(m, w, r, c, rs, g)
            if ref is None: ref = Z
            elif Z != ref: same = False; break
        identical += same
    print(f"{label:<58} instances={tested:4d} with dropped rows={with_dep:4d} "
          f"identical in every order={identical:4d}")

for ex in (True, False):
    tag = "ALL orders, tiny" if ex else "40 random orders"
    t = 200 if ex else 400
    run(f"A homogeneous, dependent rows present ({tag})", True, True, t, ex)
    run(f"B non-homogeneous, rows independent ({tag})", False, False, t, ex)
    run(f"C non-homogeneous, dependent rows present ({tag})", False, True, t, ex)
    run(f"D non-homogeneous, dependent but consistent ({tag})", False, True, t, ex, consistent=True)
