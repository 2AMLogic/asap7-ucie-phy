#!/usr/bin/env python3
"""Self-test for slice_routed.r13.netdiff.py's instance-pairing invariants.

Exercises anchor_pair() on synthetic fixtures that the committed r13 inputs
cannot reach (their realised pairing is injective, so the collision branch is
dead on them): a within-round collision -- two reference instances whose
unique full-vote match is the same extract index -- must defer every claimant
instead of committing one arbitrarily or both, a deferred claimant must still
pair on a later round once more nets are mapped, and the post-fixpoint
injectivity guard must reject a map that points two reference names at one
extract instance. Run: python3 -I slice_routed.r13.netdiff.selftest.py
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_spec = importlib.util.spec_from_file_location(
    "netdiff_under_test",
    os.path.join(HERE, "slice_routed.r13.netdiff.py"))
netdiff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(netdiff)

T = "slice"  # SPICE nodes are namespaced per .SUBCKT; fixtures use one


def inst(name, base, **conn):
    return {"name": name, "base": base, "conn": conn}


def ext(idx, base, **conn):
    return {"idx": idx, "base": base, "conn": conn}


def run(name, ok, detail=""):
    print("  %-34s %s%s" % (name, "ok" if ok else "FAIL",
                            ("  " + detail) if detail and not ok else ""))
    return ok


def case_collision_defers_both():
    # Two identical reference instances each uniquely full-vote-match the
    # single extract instance in round 1. Neither may win: both are deferred,
    # nothing commits, and the map stays empty rather than double-pairing
    # (the pre-guard behaviour committed both names against idx 0).
    refs = [inst("r1", "BUF", X="a", Y="y"), inst("r2", "BUF", X="a", Y="y")]
    exts = [ext(0, "BUF", X=(T, "n_a"), Y=(T, "n_y"))]
    paired, netmap, rev, rounds = netdiff.anchor_pair(
        refs, {}, exts, {}, {"a": (T, "n_a")})
    ok = paired == {} and rounds == 1
    ok &= len(rev) == 1 and rev[(T, "n_a")] == "a"
    return run("collision_defers_both", ok,
               "paired=%r rounds=%r" % (paired, rounds))


def case_collision_resolves_next_round():
    # r1 and r2 collide on extract idx 0 in round 1 (only CK is mapped) and
    # are both deferred; r0 pairs idx 1 unmoved. In round 2 r2's D maps to
    # idx 1's node, so r2 no longer full-vote-matches idx 0, and r1 pairs it.
    # The map ends injective; r2 -- whose connectivity straddles both extract
    # instances -- stays unpaired instead of being double-committed. Without
    # the guard this fixture exits with an inconsistent-net-map failure,
    # because the first-claimant commit would map d1 twice.
    refs = [inst("r0", "DFF", D="d1", CK="w", Q="q1"),
            inst("r1", "DFF", D="d0", CK="a", Q="q0"),
            inst("r2", "DFF", D="d1", CK="a", Q="q0")]
    exts = [ext(0, "DFF", D=(T, "n_d0"), CK=(T, "n_a"), Q=(T, "n_q0")),
            ext(1, "DFF", D=(T, "n_d1"), CK=(T, "n_w"), Q=(T, "n_q1"))]
    paired, netmap, rev, rounds = netdiff.anchor_pair(
        refs, {}, exts, {}, {"a": (T, "n_a"), "w": (T, "n_w")})
    ok = paired == {"r0": 1, "r1": 0} and "r2" not in paired
    ok &= rounds == 3 and len(set(paired.values())) == len(paired)
    ok &= netmap.get("d1") == (T, "n_d1") and netmap.get("d0") == (T, "n_d0")
    return run("collision_resolves_next_round", ok,
               "paired=%r rounds=%r" % (paired, rounds))


def case_unresolvable_ends_unpaired():
    # Identical references against one extract instance never resolve: every
    # round re-contests the same index, nothing commits, and both stay
    # unpaired (diagnose() files them as ambiguous) instead of coverage
    # reading 100% against one extract instance.
    refs = [inst("r1", "DFF", D="d0", CK="a", Q="q0"),
            inst("r2", "DFF", D="d0", CK="a", Q="q0")]
    exts = [ext(0, "DFF", D=(T, "n_d0"), CK=(T, "n_a"), Q=(T, "n_q0"))]
    paired, netmap, rev, rounds = netdiff.anchor_pair(
        refs, {}, exts, {}, {"a": (T, "n_a")})
    ok = paired == {} and rounds == 1
    return run("unresolvable_ends_unpaired", ok,
               "paired=%r rounds=%r" % (paired, rounds))


def case_uncontested_round_untouched():
    # Positive control: distinct full-vote matches in one round still commit
    # in that round; the guard must not disturb unambiguous pairing. rounds
    # reads 2 because the loop needs one round past completion to observe the
    # empty newly (the committed r13 run's propagation_rounds: 9 likewise).
    refs = [inst("r1", "BUF", X="a", Y="y0"), inst("r2", "BUF", X="b", Y="y1")]
    exts = [ext(0, "BUF", X=(T, "n_a"), Y=(T, "n_y0")),
            ext(1, "BUF", X=(T, "n_b"), Y=(T, "n_y1"))]
    seeds = {"a": (T, "n_a"), "b": (T, "n_b"),
             "y0": (T, "n_y0"), "y1": (T, "n_y1")}
    paired, netmap, rev, rounds = netdiff.anchor_pair(refs, {}, exts, {}, seeds)
    ok = paired == {"r1": 0, "r2": 1} and rounds == 2
    ok &= len(set(paired.values())) == len(paired)
    return run("uncontested_round_untouched", ok,
               "paired=%r rounds=%r" % (paired, rounds))


def case_injective_guard():
    # The post-fixpoint guard accepts an injective map ...
    ok1 = False
    try:
        netdiff.require_injective({"r1": 0, "r2": 1, "r3": 2})
        ok1 = True
    except SystemExit as e:
        print("    injective map rejected: %s" % e)
    ok = run("injective_map_accepted", ok1)
    # ... and hard-fails (a bare sys.exit, deliberately not a checks entry)
    # naming every colliding extract index and its claimants.
    caught = None
    try:
        netdiff.require_injective({"r1": 5, "r2": 5, "r3": 7, "r4": 7})
    except SystemExit as e:
        caught = str(e)
    ok &= caught is not None \
        and "idx 5 claimed by ['r1', 'r2']" in caught \
        and "idx 7 claimed by ['r3', 'r4']" in caught
    return run("non_injective_rejected", ok, repr(caught))


def main():
    print("slice_routed.r13.netdiff pairing invariants:")
    allok = case_collision_defers_both()
    allok &= case_collision_resolves_next_round()
    allok &= case_unresolvable_ends_unpaired()
    allok &= case_uncontested_round_untouched()
    allok &= case_injective_guard()
    print("selftest: %s" % ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
