"""PIGOU-J reference mathematical checks (NOT a vLLM implementation).
Run: python PIGOUJ_math_checks.py -v
Tests establish limited algebraic and toy-model properties only.
"""
import itertools
import math
import random
import unittest
from math import factorial


def shapley(i, coalition, value):
    others = [x for x in coalition if x != i]
    n = len(others)
    total = 0.0
    for k in range(n + 1):
        weight = factorial(k) * factorial(n - k) / factorial(n + 1)
        for subset in itertools.combinations(others, k):
            S = frozenset(subset)
            total += weight * (value(S | {i}) - value(S))
    return total


def worker_energy(incumbents, newcomer=None, *, wake=120.0, self_energy=None):
    self_energy = self_energy or {}
    xs = list(incumbents) + ([newcomer] if newcomer else [])
    return (wake if xs else 0.0) + sum(self_energy[x] for x in xs)


class AtomicReservation:
    """Abstract reservation ledger; assumes exact upper block demand from engine."""
    def __init__(self, cap):
        self.cap = int(cap)
        self.held = {}

    def reserve(self, key, blocks):
        if key in self.held or blocks < 0 or sum(self.held.values()) + blocks > self.cap:
            return False
        self.held[key] = blocks
        return True

    def release(self, key):
        self.held.pop(key, None)


class TestMath(unittest.TestCase):
    def test_signed_bilinear_energy_identity(self):
        rng = random.Random(20261111)
        for _ in range(20000):
            p0 = rng.uniform(0, 700)
            p1 = rng.uniform(0, 700)
            t0 = rng.uniform(0, 0.8)
            t1 = rng.uniform(0, 0.8)
            lhs = p1 * t1 - p0 * t0
            rhs = (p1 - p0) * t0 + p1 * (t1 - t0)
            self.assertAlmostEqual(lhs, rhs, delta=1e-10)

    def test_shapley_equal_marginal_for_additive_coalition(self):
        ids = ['a', 'b', 'c', 'd']
        val = {'a': 5, 'b': 9, 'c': 3, 'd': 6}
        fn = lambda S: sum(val[x] for x in S)
        for n in range(1, len(ids) + 1):
            for subset in itertools.combinations(ids, n):
                T = frozenset(subset)
                for i in subset:
                    self.assertAlmostEqual(shapley(i, T, fn), fn(T) - fn(T - {i}))

    def test_shapley_wakeup_rank_reversal(self):
        e1 = {'inc1':10., 'new':9.}
        e2 = {'inc1':10., 'inc2':10., 'inc3':10., 'inc4':10., 'new':15.}
        V1 = lambda S: (120. if S else 0.) + sum(e1[x] for x in S)
        V2 = lambda S: (120. if S else 0.) + sum(e2[x] for x in S)
        T1 = frozenset({'inc1','new'})
        T2 = frozenset({'inc1','inc2','inc3','inc4','new'})
        d1 = V1(T1) - V1(T1 - {'new'})
        d2 = V2(T2) - V2(T2 - {'new'})
        self.assertEqual((d1,d2), (9.,15.))
        self.assertEqual((shapley('new',T1,V1),shapley('new',T2,V2)), (69.,39.))

    def test_uniform_error_two_epsilon_regret_bound(self):
        rng = random.Random(123)
        for _ in range(20000):
            costs = [rng.uniform(-30,180) for _ in range(rng.randrange(2,10))]
            eps = rng.uniform(0,.5)
            est = [c + rng.uniform(-eps,eps) for c in costs]
            selected = min(range(len(costs)), key=lambda i: est[i])
            self.assertLessEqual(costs[selected]-min(costs), 2*eps+1e-10)

    def test_unbiased_bernoulli_audit_exact_enumeration(self):
        p = 0.25
        z = [1.,0.,1.,1.,0.]
        expected = 0.
        for bits in itertools.product([0,1], repeat=len(z)):
            prob = math.prod(p if b else (1-p) for b in bits)
            estimated = sum(b*zi/p for b,zi in zip(bits,z)) / len(z)
            expected += prob * estimated
        self.assertAlmostEqual(expected, sum(z)/len(z), places=12)

    def test_atomic_reserved_block_invariant(self):
        rng = random.Random(99)
        ledger = AtomicReservation(512)
        for i in range(2000):
            if rng.random() < 0.65:
                ledger.reserve(i, rng.randint(0,30))
            else:
                ledger.release(rng.randint(0,i))
            self.assertLessEqual(sum(ledger.held.values()), 512)

    def test_equal_common_horizon_energy_idle_cancels(self):
        idle = 85.
        H = 5.
        base_intervals = [(1.2,90.),(0.8,150.)]  # (duration, excess watts)
        plus_intervals = [(1.4,100.),(1.0,175.)]
        def total(xs):
            return idle*H + sum(d*active for d,active in xs)
        delta = total(plus_intervals)-total(base_intervals)
        self.assertAlmostEqual(delta, (140+175)-(108+120))

    def test_marginal_energy_can_be_negative(self):
        # One state with workload interference/consolidation: illustrates
        # why clipping (estimated) marginal energy to nonnegative is unjustified.
        E_base = 50.
        E_augmented = 44.
        self.assertEqual(E_augmented-E_base,-6.)


if __name__ == '__main__':
    unittest.main(verbosity=2)
