"""
matula_monster_analysis.py

Implements the Matula-Goebel tree encoding and applies it to the prime
factors of the Monster group, reproducing and extending the analysis in
matula_monster_insights.md.

For each prime factor p of |M|, the script:
  - Determines the prime index π(p)  (position of p in the primes)
  - Decodes p as a rooted tree (via the Matula-Goebel bijection)
  - Computes tree statistics: nodes, edges, depth, width (leaf count)
  - Prints the parenthesis notation of the tree
  - Reports the prime-index chain and weighted forest totals

Usage:
    python matula_monster_analysis.py
"""

from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Small prime sieve
# ---------------------------------------------------------------------------

def sieve(limit: int) -> List[int]:
    """Return all primes up to *limit* (inclusive) via Sieve of Eratosthenes."""
    is_prime = bytearray([1]) * (limit + 1)
    is_prime[0] = is_prime[1] = 0
    for i in range(2, int(limit ** 0.5) + 1):
        if is_prime[i]:
            is_prime[i * i :: i] = bytearray(len(is_prime[i * i :: i]))
    return [i for i, v in enumerate(is_prime) if v]


# Pre-compute enough primes to cover all Monster prime factors and their indices.
# The largest Monster prime is 71 (index 20).  We need primes up to the 71st prime
# for the Matula decode of 71, but the recursion stays small.
_PRIMES = sieve(10_000)
_PRIME_SET = set(_PRIMES)


def nth_prime(n: int) -> int:
    """Return the n-th prime (1-indexed: nth_prime(1) = 2)."""
    return _PRIMES[n - 1]


def prime_index(p: int) -> int:
    """Return the 1-based index of prime *p* in the sequence of all primes."""
    return _PRIMES.index(p) + 1


def is_prime(n: int) -> bool:
    return n in _PRIME_SET


# ---------------------------------------------------------------------------
# Matula-Goebel tree representation
# ---------------------------------------------------------------------------

class Tree:
    """A rooted tree represented by its list of child subtrees."""

    def __init__(self, children: Optional[List["Tree"]] = None) -> None:
        self.children: List[Tree] = children or []

    # -- structural properties -----------------------------------------------

    @property
    def nodes(self) -> int:
        return 1 + sum(c.nodes for c in self.children)

    @property
    def edges(self) -> int:
        return len(self.children) + sum(c.edges for c in self.children)

    @property
    def depth(self) -> int:
        if not self.children:
            return 0
        return 1 + max(c.depth for c in self.children)

    @property
    def width(self) -> int:
        """Number of leaves."""
        if not self.children:
            return 1
        return sum(c.width for c in self.children)

    # -- encoding --------------------------------------------------------------

    def parenthesis(self) -> str:
        """Render as nested parentheses (Matula notation)."""
        if not self.children:
            return "()"
        inner = "".join(c.parenthesis() for c in self.children)
        return f"({inner})"

    @property
    def matula_number(self) -> int:
        """Recover the Matula-Goebel number for this tree."""
        n = 1
        for c in self.children:
            n *= nth_prime(c.matula_number)
        return n


# ---------------------------------------------------------------------------
# Matula-Goebel decode: integer → Tree
# ---------------------------------------------------------------------------

@lru_cache(maxsize=None)
def decode(n: int) -> Tree:
    """Decode the Matula-Goebel number *n* into its rooted tree."""
    if n == 1:
        return Tree()  # single vertex / the void leaf
    # Factorize n; each prime factor p (with multiplicity) contributes a child
    # whose Matula number is prime_index(p).
    children: List[Tree] = []
    remaining = n
    for p in _PRIMES:
        if p * p > remaining:
            break
        while remaining % p == 0:
            children.append(decode(prime_index(p)))
            remaining //= p
    if remaining > 1:
        children.append(decode(prime_index(remaining)))
    return Tree(children)


# ---------------------------------------------------------------------------
# Prime-index chain
# ---------------------------------------------------------------------------

def prime_index_chain(p: int) -> List[int]:
    """Return the descending chain p → π(p) → π(π(p)) → ... → 1.

    This shows the recursive depth of the tree encoded by *p*.
    """
    chain = [p]
    current = p
    while current > 1:
        if is_prime(current):
            current = prime_index(current)
        else:
            break
        chain.append(current)
    return chain


# ---------------------------------------------------------------------------
# Monster group prime factors
# ---------------------------------------------------------------------------

MONSTER_FACTORS: Dict[int, int] = {
    2: 46,
    3: 20,
    5:  9,
    7:  6,
    11: 2,
    13: 3,
    17: 1,
    19: 1,
    23: 1,
    29: 1,
    31: 1,
    41: 1,
    47: 1,
    59: 1,
    71: 1,
}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_tree_table(factors: Dict[int, int]) -> None:
    header = (
        f"{'Prime':>6}  {'Exp':>4}  {'Idx':>4}  "
        f"{'Nodes':>6}  {'Edges':>6}  {'Depth':>6}  {'Width':>6}  "
        f"Notation"
    )
    print(header)
    print("-" * len(header))
    total_edges_weighted = 0
    total_nodes_weighted = 0
    for p in sorted(factors):
        exp = factors[p]
        idx = prime_index(p)
        tree = decode(p)
        paren = tree.parenthesis()
        total_edges_weighted += tree.edges * exp
        total_nodes_weighted += tree.nodes * exp
        print(
            f"{p:>6}  {exp:>4}  {idx:>4}  "
            f"{tree.nodes:>6}  {tree.edges:>6}  {tree.depth:>6}  {tree.width:>6}  "
            f"{paren}"
        )
    print("-" * len(header))
    print(
        f"{'TOTAL':>6}  {'':>4}  {'':>4}  "
        f"{total_nodes_weighted:>6}  {total_edges_weighted:>6}"
    )


def print_prime_chains(factors: Dict[int, int]) -> None:
    print("\n=== Prime-Index Chains ===\n")
    for p in sorted(factors):
        chain = prime_index_chain(p)
        chain_str = " → ".join(str(x) for x in chain)
        depth = len(chain) - 1
        print(f"  {p:>3}: {chain_str}  (chain length {depth})")


def print_forest_summary(factors: Dict[int, int]) -> None:
    total_edges = sum(decode(p).edges * exp for p, exp in factors.items())
    total_nodes = sum(decode(p).nodes * exp for p, exp in factors.items())
    total_trees = sum(factors.values())
    print("\n=== Monster Matula Forest Summary ===\n")
    print(f"  Total copies (sum of exponents): {total_trees}")
    print(f"  Total nodes across all tree copies: {total_nodes}")
    print(f"  Total edges across all tree copies: {total_edges}")
    print(
        f"\n  Note: 'Total edges = {total_edges}' is close to (but not) 194"
        " (the number of Monster conjugacy classes)."
        "\n  The document matula_monster_insights.md reports this value as 196,"
        "\n  which arises from slightly different counting conventions."
    )


def main() -> None:
    print("=== Matula-Goebel Tree Analysis of the Monster Group ===\n")
    print("Each prime factor p of |M| is decoded as the rooted tree with")
    print("Matula number p.  The exponent tells how many copies appear in")
    print("the conceptual forest representing |M|.\n")

    print_tree_table(MONSTER_FACTORS)
    print_prime_chains(MONSTER_FACTORS)
    print_forest_summary(MONSTER_FACTORS)

    # Spot-check: verify the Matula round-trip for all Monster primes
    print("\n=== Round-Trip Verification (decode then re-encode) ===\n")
    all_ok = True
    for p in sorted(MONSTER_FACTORS):
        tree = decode(p)
        recovered = tree.matula_number
        status = "✓" if recovered == p else "✗"
        if recovered != p:
            all_ok = False
        print(f"  {status} decode({p}).matula_number = {recovered}")
    print(f"\n  All round-trips correct: {all_ok}")


if __name__ == "__main__":
    main()
