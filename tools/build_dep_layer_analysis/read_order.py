#!/usr/bin/env python3

from sys import argv

print("WARNING: this is not an efficient lookup, but it is used as a demonstration")

print()
print("This shows a discreet step down, but we could make the steps arbitrarily small.")

if len(argv) <= 2:
    print("usage: read_order.py order.txt [module]+")

with open(argv[1], "r") as order_file:
    order = [i.strip() for i in order_file.readlines()]

# FIXME: Since Java dependencies aren't counted in the current implementation,
# we cut off the bottom half of targets.
order = order[len(order)//2:]

index = {m:i for i,m in enumerate(order)}

# The current ceiling to the allowed flake rate.
MAX_FLAKINESS = .95

# The lower this is, the more aggressive flakes are tackled.
EASE = 12
STEPS_TO_SIMULATE = 12

# If OFFSET is 0.4, then only the least complex 40% flakers will have
# an increased flakiness requirement.
OFFSET = 0.5

# How quickly the offset goes away. The offset will be completely gone
# after STEPS_TO_SIMULATE / OFFSET_DELAY is >= 1
OFFSET_DELAY = 0.5

def time_multiplier(time):
    # this reduces rapidly and then gradually decreases, representing how the
    # closer to a 0 flake rate you get, the more difficult it is
    return 1 - time / (time + EASE)

# important properties - for time_multiplier
assert time_multiplier(0) == 1
assert time_multiplier(10000) < 0.01

def offset_add(time):
    return OFFSET * time_multiplier(time / OFFSET_DELAY)

assert offset_add(0) == OFFSET
assert offset_add(10000) < 0.01

def allowed_flake_rate(time, complexity):
    return min(MAX_FLAKINESS, offset_add(time) + time_multiplier(time) * complexity * MAX_FLAKINESS)

assert allowed_flake_rate(0, 0) < MAX_FLAKINESS
assert allowed_flake_rate(0, OFFSET) == MAX_FLAKINESS
assert allowed_flake_rate(0, 1) == MAX_FLAKINESS
assert allowed_flake_rate(1, 0) < MAX_FLAKINESS
assert allowed_flake_rate(1, 1) == MAX_FLAKINESS # b/c EASE
assert allowed_flake_rate(10000, 0) < 0.01
assert allowed_flake_rate(10000, 1) < 0.01

for module in argv[2:]:
    if module not in index:
        print("Could not find",module)
        continue

    complexity_score = index[module]/len(index)

    print()
    print(f"Consider {module}")
    print(f"    Approximate complexity (in [0,1] interval) {complexity_score:.2f}")
    print(f"    Consider stepping down allowed flake rate like this:")
    for time in range(0, STEPS_TO_SIMULATE):
        afr = allowed_flake_rate(time, complexity_score)
        print(f"    - Phase {time+1:<20} {afr:.2f}")
    print(f"    - ...")
