#!/usr/bin/env python3

import json
from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from sys import argv

# things we take to mean some sort of dependency
DEPENDENCY_KEYS = {
    'host_dependencies',
    'shared_libs',
    'target_dependencies',
    'runtime_dependencies',
    'static_dependencies',
    'dependencies',
}

# code may use these, but we want to detect new keys, in case they matter
OTHER_KEYS = {
    'auto_test_config',
    'class',
    'classes_jar',
    'compatibility_suites',
    'data',
    'data_dependencies',
    'installed',
    'is_unit_test',
    'module_name',
    'path',
    'srcjars',
    'srcs',
    'supported_variants',
    'system_shared_libs', # sounds like dep, but defaults to 'none'.
    'tags',
    'test_config',
    'test_mainline_modules',
    'test_options_tags',
}

KNOWN_KEYS = DEPENDENCY_KEYS | OTHER_KEYS

EXCLUDE_DEPS = {
    "none" # there is a bug, this exists under m["dependencies"]
}

def read_modules(file):
    """ read module-info.json - separate function for memory implications """
    module_info = json.load(open(file))

    unknown_keys = set()

    name_deps = defaultdict(set)

    for m in module_info.values():
        unknown_keys |= set(k for k in m.keys() if k not in KNOWN_KEYS)

        name = m["module_name"]

        # trying without test-based logic for now
        # if ("NATIVE_TESTS" in m["class"]) or ("tests" in m.get("tags", [])):
        #     tests.add(name)

        name_deps[name] # make sure it gets reflected

        # if "APPS" in m["class"]:
        #     name_deps[name].add("frameworks.jar")

        for key in DEPENDENCY_KEYS:
            for dep in m.get(key, []):
                if dep in EXCLUDE_DEPS: continue
                name_deps[name].add(dep)

    # TODO: some deps are created by adding things like "_32" or "_vendor"
    # this will cause invalid results for these types of modules. However,
    # since most tests are core variant, it's easier to ignore these. We
    # may discover later that it's important for some groups.
    not_in = set()
    for name, deps in name_deps.items():
        for dep in deps:
            not_in.add(dep)
    for dep in not_in:
        name_deps[dep] # make sure it is reflected

    if unknown_keys: print(f"WARNING: unknown keys {unknown_keys}")
    return dict(name_deps) # disable defaultdict

def find_cycles(graph):
    """ in a dict node -> [node], finds a list of edges which cause the
        graph to be cycles. Quick, poor man's ad hoc algorithm """
    def find_cycles_impl(cache, m, cycle_from):
        if m in cache:
            if cache[m]:
                return { (cycle_from, m) }
            else:
                return set()
        cache[m] = True
        res = set()
        for dep in graph[m]:
            res |= find_cycles_impl(cache, dep, m)
        cache[m] = False
        return res

    cache = {}
    cycles = set()
    for module in graph.keys():
        cycles |= find_cycles_impl(cache, module, module)

    return cycles

##################

if len(argv) != 3:
    print("usage: layers.py $ANDROID_PRODUCT_OUT/module-info.json order.txt")
    exit(1)

name_deps = read_modules(argv[1])
output_file = argv[2]

for mod, dep in find_cycles(name_deps):
    print("WARNING: Cycle detected due to:",mod,"->",dep,"simply removing them to compute easier")
    name_deps[mod].remove(dep)

assert len(find_cycles(name_deps)) == 0 # expensive, but hey

@lru_cache(maxsize=None)
def get_max_depth(m): # implicitly uses name_deps to simplify caching
    return 1 + max((get_max_depth(dep) for dep in name_deps[m]), default=0)

with open(output_file, "w") as output_file:
    for module in sorted(name_deps.keys(), key = lambda m: get_max_depth(m)):
        output_file.write(module + "\n")

