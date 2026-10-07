// Referee brute force: exhaustive check of order-independence of banding + back-substitution.
// Written from the abstract setting only (not from scripts/check_order_independence.py).
//
// usage: enum m w rbits kmax mode
//   mode 0: rows have a 1 at start s (0 <= s <= m-w), other w-1 window bits arbitrary
//   mode 1: ANY nonzero row of GF(2)^m (hypothesis "leading 1 at start / window" dropped)
// Enumerates every multiset of k equations (k = 1..kmax) over all (row, b) pairs, and for each
// multiset every one of the k! insertion orders.
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

static int m, w, rbits, kmax, mode;
static int neq;
static uint32_t ROW[4096], RES[4096];
static int perms[720][6], nperm;

static void gen_perms(int k) {
  int a[6], c[6];
  nperm = 0;
  for (int i = 0; i < k; i++) { a[i] = i; c[i] = 0; }
  memcpy(perms[nperm++], a, sizeof a);
  int i = 0;
  while (i < k) {
    if (c[i] < i) {
      int j = (i % 2 == 0) ? 0 : c[i];
      int t = a[j]; a[j] = a[i]; a[i] = t;
      memcpy(perms[nperm++], a, sizeof a);
      c[i]++; i = 0;
    } else { c[i] = 0; i++; }
  }
}

#define NG 3
static inline uint32_t g(int which, int j) {
  uint32_t mask = (1u << rbits) - 1;
  switch (which) {
    case 0: return 0;
    case 1: return (uint32_t)((uint64_t)j * 0x9E3779B185EBCA87ULL) & mask; // kernel-style
    default: return (((0x2Du >> j) & 1) | (((0x53u >> j) & 1) << 1)) & mask; // arbitrary table
  }
}

typedef struct {
  uint32_t occ;        // occupied slot mask
  uint32_t z[NG];      // packed solution, column c in bits [8c, 8c+m)
  int bad;             // some row reduced to zero with nonzero result
  uint32_t dropped;    // bitmask over key indices (positions in the multiset) that were dropped
} Out;

static inline void run(const int *eq, const int *perm, int k, Out *o) {
  uint32_t coef[8] = {0}, res[8] = {0}, occ = 0;
  o->bad = 0; o->dropped = 0;
  for (int t = 0; t < k; t++) {
    int key = perm[t];
    uint32_t r = ROW[eq[key]], b = RES[eq[key]];
    for (;;) {
      if (r == 0) { o->dropped |= 1u << key; if (b) o->bad = 1; break; }
      int i = __builtin_ctz(r);          // leading position = lowest index with a 1
      if (!((occ >> i) & 1)) { coef[i] = r; res[i] = b; occ |= 1u << i; break; }
      r ^= coef[i]; b ^= res[i];
    }
  }
  o->occ = occ;
  for (int gi = 0; gi < NG; gi++) {
    uint32_t zc[2] = {0, 0};
    for (int i = m - 1; i >= 0; i--) {
      uint32_t v;
      if ((occ >> i) & 1) {
        v = res[i];
        uint32_t hi = coef[i] & ~(1u << i);
        for (int c = 0; c < rbits; c++) v ^= (uint32_t)__builtin_parity(hi & zc[c]) << c;
      } else v = g(gi, i);
      for (int c = 0; c < rbits; c++) zc[c] |= ((v >> c) & 1u) << i;
    }
    o->z[gi] = zc[0] | (zc[1] << 8);
  }
}

// independent consistency test: brute force over all 2^m assignments per result column
static int consistent(const int *eq, int k) {
  for (int c = 0; c < rbits; c++) {
    int found = 0;
    for (uint32_t z = 0; z < (1u << m) && !found; z++) {
      int ok = 1;
      for (int t = 0; t < k && ok; t++)
        if ((uint32_t)__builtin_parity(ROW[eq[t]] & z) != ((RES[eq[t]] >> c) & 1u)) ok = 0;
      found = ok;
    }
    if (!found) return 0;
  }
  return 1;
}
static int solves(const int *eq, int k, uint32_t zpacked) {
  for (int c = 0; c < rbits; c++) {
    uint32_t z = (zpacked >> (8 * c)) & 0xff;
    for (int t = 0; t < k; t++)
      if ((uint32_t)__builtin_parity(ROW[eq[t]] & z) != ((RES[eq[t]] >> c) & 1u)) return 0;
  }
  return 1;
}

static unsigned long long n_sys, n_cons, n_incons, n_orders, n_orders_cons;
static unsigned long long viol_Z, viol_occ, viol_bad_cons, viol_b, viol_notsol, viol_free;
static unsigned long long incons_Zdiff[NG], cons_with_drops, cons_dropset_differs, cons_dependent;
static int printed;

static void print_sys(const int *eq, int k) {
  for (int t = 0; t < k; t++) {
    printf("    key %d: row=", t);
    for (int i = 0; i < m; i++) putchar(((ROW[eq[t]] >> i) & 1) ? '1' : '0');
    printf(" b=%u\n", RES[eq[t]]);
  }
}
static void print_order(const int *p, int k) { for (int t = 0; t < k; t++) printf("%d ", p[t]); }

// multiset of dropped equations as a sorted list signature
static uint64_t dropsig(const int *eq, int k, uint32_t dropped) {
  // eq[] is nondecreasing, so listing dropped equation ids in key order is canonical
  uint64_t s = 1469598103934665603ULL;
  for (int t = 0; t < k; t++) if ((dropped >> t) & 1) { s ^= (uint64_t)eq[t] + 1; s *= 1099511628211ULL; }
  return s;
}

static void check(const int *eq, int k) {
  n_sys++;
  int cons = consistent(eq, k);
  if (cons) n_cons++; else n_incons++;
  Out ref, o;
  run(eq, perms[0], k, &ref);
  uint64_t refsig = dropsig(eq, k, ref.dropped);
  int zdiff[NG] = {0}, dropdiff = 0, anybadfree = 0;
  for (int p = 0; p < nperm; p++) {
    run(eq, perms[p], k, &o);
    n_orders++;
    if (cons) n_orders_cons++;
    if (o.occ != ref.occ) { viol_occ++; if (printed < 5) { printed++; printf("OCC SET DIFFERS m=%d\n", m); print_sys(eq, k); } }
    for (int gi = 0; gi < NG; gi++) if (o.z[gi] != ref.z[gi]) zdiff[gi] = 1;
    if (dropsig(eq, k, o.dropped) != refsig) dropdiff = 1;
    if (cons) {
      if (o.bad) viol_bad_cons++;
      for (int gi = 0; gi < NG; gi++) {
        if (!solves(eq, k, o.z[gi])) viol_notsol++;
        for (int j = 0; j < m; j++) if (!((o.occ >> j) & 1))
          for (int c = 0; c < rbits; c++)
            if (((o.z[gi] >> (8 * c + j)) & 1u) != ((g(gi, j) >> c) & 1u)) viol_free++;
      }
      for (int gi = 0; gi < NG; gi++) if (o.z[gi] != ref.z[gi]) {
        viol_Z++;
        if (printed < 5) {
          printed++;
          printf("COUNTEREXAMPLE (claim) m=%d w=%d rbits=%d g#%d\n", m, w, rbits, gi);
          print_sys(eq, k);
          printf("    order A: "); print_order(perms[0], k); printf("-> Z=0x%x\n", ref.z[gi]);
          printf("    order B: "); print_order(perms[p], k); printf("-> Z=0x%x\n", o.z[gi]);
        }
      }
    } else {
      if (!o.bad) {
        viol_b++; anybadfree = 1;
        if (printed < 5) {
          printed++;
          printf("COUNTEREXAMPLE (corollary b) m=%d w=%d rbits=%d\n", m, w, rbits);
          print_sys(eq, k); printf("    order with no zero-row/nonzero-b: "); print_order(perms[p], k); printf("\n");
        }
      }
    }
  }
  (void)anybadfree;
  if (cons) {
    if (ref.dropped) cons_with_drops++;
    if (dropdiff) cons_dropset_differs++;
  } else for (int gi = 0; gi < NG; gi++) if (zdiff[gi]) incons_Zdiff[gi]++;
}

static void rec(int *eq, int depth, int k, int lo) {
  if (depth == k) { check(eq, k); return; }
  for (int e = lo; e < neq; e++) { eq[depth] = e; rec(eq, depth + 1, k, e); }
}

int main(int argc, char **argv) {
  if (argc < 6) return 2;
  m = atoi(argv[1]); w = atoi(argv[2]); rbits = atoi(argv[3]); kmax = atoi(argv[4]); mode = atoi(argv[5]);
  int nrows = 0; uint32_t rows[256];
  if (mode == 0) {
    for (int s = 0; s + w <= m; s++)
      for (uint32_t hi = 0; hi < (1u << (w - 1)); hi++) rows[nrows++] = (1u << s) | (hi << (s + 1));
  } else {
    for (uint32_t r = 1; r < (1u << m); r++) rows[nrows++] = r;
  }
  for (int i = 0; i < nrows; i++)
    for (uint32_t b = 0; b < (1u << rbits); b++) { ROW[neq] = rows[i]; RES[neq] = b; neq++; }
  int eq[6];
  for (int k = 1; k <= kmax; k++) { gen_perms(k); rec(eq, 0, k, 0); }
  printf("m=%d w=%d rbits=%d kmax=%d mode=%d distinct_eqs=%d | systems=%llu consistent=%llu inconsistent=%llu "
         "orders=%llu orders_on_consistent=%llu | VIOL: Z_differs=%llu occ_differs=%llu "
         "consistent_but_zero_row_nonzero_b=%llu inconsistent_order_without_failure=%llu Z_not_solution=%llu "
         "free_slot_not_g=%llu | info: consistent_with_drops=%llu consistent_dropped_eq_multiset_differs=%llu "
         "inconsistent_Z_order_dependent(g0,g1,g2)=%llu,%llu,%llu\n",
         m, w, rbits, kmax, mode, neq, n_sys, n_cons, n_incons, n_orders, n_orders_cons, viol_Z, viol_occ,
         viol_bad_cons, viol_b, viol_notsol, viol_free, cons_with_drops, cons_dropset_differs,
         incons_Zdiff[0], incons_Zdiff[1], incons_Zdiff[2]);
  return 0;
}
