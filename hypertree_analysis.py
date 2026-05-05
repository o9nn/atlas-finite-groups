"""
hypertree_analysis.py

Classifies all 26 sporadic finite simple groups using the Rooted Hyper-Tree
encoding described in hypertree_formalization.md.

For each group the script computes:
  - The distinct prime factors of its order (hyper-tree order k)
  - The sorted tuple of prime exponents (hyper-tree signature)
  - Comparison of the top exponents against OEIS A000081

Usage:
    python hypertree_analysis.py
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Data: orders of the 26 sporadic simple groups
# Source: ATLAS of Finite Groups / Wikipedia
# ---------------------------------------------------------------------------

SPORADIC_GROUPS: Dict[str, int] = {
    "M11":   7920,
    "M12":   95040,
    "J1":    175560,
    "M22":   443520,
    "J2":    604800,
    "M23":   10200960,
    "HS":    44352000,
    "J3":    50232960,
    "M24":   244823040,
    "McL":   898128000,
    "He":    4030387200,
    "Ru":    145926144000,
    "Suz":   448345497600,
    "ON":    460815505920,
    "Co3":   495766656000,
    "Co2":   42305421312000,
    "Fi22":  64561751654400,
    "HN":    273030912000000,
    "Ly":    51765179004000000,
    "Th":    90745943887872000,
    "Fi23":  31671033903198208000,
    "Co1":   4157776806543360000,
    "J4":    86775571046077562880,
    "Fi24":  1255205709190661721292800,
    "B":     4154781481226426191177580544000000,
    "M":     808017424794512875886459904961710757005754368000000000,
}

# First 15 terms of OEIS A000081 (index 0..14):
#   a(0)=0, a(1)=1, a(2)=1, a(3)=2, a(4)=4, a(5)=9, a(6)=20,
#   a(7)=48, a(8)=115, a(9)=286, a(10)=719, a(11)=1842, a(12)=4766,
#   a(13)=12486, a(14)=32973
A000081 = [0, 1, 1, 2, 4, 9, 20, 48, 115, 286, 719, 1842, 4766, 12486, 32973]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def prime_factorization(n: int) -> Dict[int, int]:
    """Return the prime factorization of *n* as {prime: exponent}."""
    factors: Dict[int, int] = {}
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    return factors


def hypertree_order(factors: Dict[int, int]) -> int:
    """Number of distinct prime factors (= hyper-tree order k)."""
    return len(factors)


def hypertree_signature(factors: Dict[int, int]) -> Tuple[int, ...]:
    """Sorted-descending tuple of prime exponents (= hyper-tree signature)."""
    return tuple(sorted(factors.values(), reverse=True))


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyse_all() -> List[dict]:
    results = []
    for name, order in SPORADIC_GROUPS.items():
        factors = prime_factorization(order)
        k = hypertree_order(factors)
        sig = hypertree_signature(factors)
        results.append({
            "name": name,
            "order": order,
            "factors": factors,
            "k": k,
            "signature": sig,
        })
    results.sort(key=lambda r: (r["k"], r["order"]))
    return results


def compare_monster_with_a000081(factors: Dict[int, int]) -> None:
    """Print the alignment table between Monster exponents and A000081.

    The alignment follows monster_self_reference.md: the k largest exponents
    are compared against A000081(k) for k = 1..7, i.e. the sorted-descending
    exponents are matched top-to-bottom against a(7), a(6), ..., a(1).
    """
    primes = sorted(factors.keys())
    # Pair each prime with its exponent, largest exponent first
    pairs = [(p, factors[p]) for p in primes]
    pairs.sort(key=lambda x: -x[1])

    # The document aligns the 7 largest exponents against A000081(7..1)
    alignment_depth = 7  # primes 2, 3, 5, 7, 11, 13, and the block of 1-exponents
    print("\n=== Monster Exponents vs. OEIS A000081 (aligned as in monster_self_reference.md) ===\n")
    header = (
        f"{'A-idx':>6}  {'Prime':>6}  {'Exponent':>10}  {'A000081':>10}  {'Diff':>6}  Notes"
    )
    print(header)
    print("-" * len(header))
    for rank, (p, exp) in enumerate(pairs[:alignment_depth]):
        a_idx = alignment_depth - rank  # 7, 6, 5, 4, 3, 2, 1
        a_val = A000081[a_idx] if a_idx < len(A000081) else None
        diff = (exp - a_val) if a_val is not None else None
        notes = ""
        if diff is not None:
            if diff == 0:
                notes = "✓ Exact match"
            elif abs(diff) == 2:
                notes = f"Near miss ({diff:+d})"
        a_str = str(a_val) if a_val is not None else "—"
        diff_str = f"{diff:+d}" if diff is not None else "—"
        print(f"{a_idx:>6}  {p:>6}  {exp:>10}  {a_str:>10}  {diff_str:>6}  {notes}")


def print_hypertree_table(results: List[dict]) -> None:
    """Print the classification table grouped by hyper-tree order."""
    print("\n=== All 26 Sporadic Groups: Hyper-Tree Classification ===\n")
    header = f"{'k':>4}  {'Group':>6}  {'Signature (top 6)':<30}  {'Sum of exponents':>18}"
    print(header)
    print("-" * len(header))
    current_k = None
    for r in results:
        if r["k"] != current_k:
            current_k = r["k"]
            print()
        sig_str = str(r["signature"][:6]) + ("..." if len(r["signature"]) > 6 else "")
        exp_sum = sum(r["signature"])
        print(f"{r['k']:>4}  {r['name']:>6}  {sig_str:<30}  {exp_sum:>18}")


def print_summary_by_k(results: List[dict]) -> None:
    """Print the compact summary table from hypertree_formalization.md."""
    from collections import defaultdict
    groups_by_k: Dict[int, List[str]] = defaultdict(list)
    for r in results:
        groups_by_k[r["k"]].append(r["name"])

    print("\n=== Sporadic Groups by Hyper-Tree Order ===\n")
    print(f"{'k':>4}  {'Count':>6}  Groups")
    print("-" * 60)
    for k in sorted(groups_by_k):
        names = groups_by_k[k]
        print(f"{k:>4}  {len(names):>6}  {', '.join(names)}")


def print_signature_diversity(results: List[dict]) -> None:
    """Show how many unique signatures exist at each hyper-tree order."""
    from collections import defaultdict
    sigs_by_k: Dict[int, set] = defaultdict(set)
    for r in results:
        sigs_by_k[r["k"]].add(r["signature"])

    print("\n=== Signature Diversity per Hyper-Tree Order ===\n")
    print(f"{'k':>4}  {'Groups':>6}  {'Unique signatures':>18}")
    print("-" * 36)
    for k in sorted(sigs_by_k):
        count = sum(1 for r in results if r["k"] == k)
        print(f"{k:>4}  {count:>6}  {len(sigs_by_k[k]):>18}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    results = analyse_all()

    print_summary_by_k(results)
    print_signature_diversity(results)
    print_hypertree_table(results)

    monster = SPORADIC_GROUPS["M"]
    monster_factors = prime_factorization(monster)
    compare_monster_with_a000081(monster_factors)

    print("\n=== Monster Group: Full Prime Factorization ===\n")
    for p in sorted(monster_factors):
        print(f"  {p}^{monster_factors[p]}")

    sig = hypertree_signature(monster_factors)
    print(f"\nMonster hyper-tree order: {len(monster_factors)}")
    print(f"Monster hyper-tree signature: {sig}")
    print(f"Sum of exponents: {sum(sig)}")
    print("(For weighted Matula-forest edge totals, run matula_monster_analysis.py)")


if __name__ == "__main__":
    main()
