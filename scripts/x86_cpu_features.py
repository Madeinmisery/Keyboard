import subprocess

CLANG = 'prebuilts/clang/host/linux-x86/clang-r498229b/bin/clang'
INPUT = b'int main() { return 0; }'

CPU_NAMES = [
    ('Core/Core 2', 'core2'),
    ('Nehalem', 'nehalem'),
    ('Westmere', 'westmere'),
    ('Sandy Bridge', 'sandybridge'),
    ('Bay Trail', 'baytrail'),
    ('Ivy Bridge', 'ivybridge'),
    ('Haswell', 'haswell'),
    ('Broadwell', 'broadwell'),
    ('Ivy Bridge', 'ivybridge'),
    ('Skylake', 'skylake'),
    ('Broadwell', 'broadwell'),
    ('Skylake/Cascade Lake', 'cascadelake'),
    ('Apollo Lake', 'apollolake'),
    ('Cannon Lake', 'cannonlake'),
    ('Ice Lake client', 'icelake-client'),
    ('Ice Lake server', 'icelake-server'),
    ('Gemini Lake', 'geminilake'),
    ('Lakefield', 'lakefield'),
    ('Tiger Lake', 'tigerlake'),
    ('Kaby Lake/Coffee Lake/Comet Lake', 'kabylake'),
    ('Sapphire Rapids', 'sapphirerapids'),
    ('Elkhart Lake', 'elkhartlake'),
    ('Alder Lake', 'alderlake'),
    ('Jasper Lake', 'jasperlake'),
    ('Kaby Lake/Coffee Lake/Comet Lake', 'coffeelake'),
    ('Comet Lake', 'cometlake'),
    ('Rocket Lake', 'rocketlake'),
    ('Raptor Lake', 'raptorlake'),
    ('Alder Lake', 'alderlake'),
    ('Raptor Lake', 'raptorlake'),
    ('K8', 'k8'),
    ('K8', 'k8'),
    ('K10', 'k10'),
    ('Bobcat version 1', 'btver1'),
    ('Bobcat version 2', 'btver2'),
    ('Bulldozer version 1', 'bdver1'),
    ('Bulldozer version 2', 'bdver2'),
    ('Bulldozer version 3', 'bdver3'),
    ('Bulldozer version 4', 'bdver4'),
    ('Jaguar', 'jaguar'),
    ('Zen', 'znver1'),
    ('Zen+', 'znver1'),
    ('Zen2', 'znver2'),
    ('Zen3', 'znver3'),
    ('Zen3+', 'znver3'),
    ('Zen4', 'znver4'),
]


def find_cpu_features(target):
    try:
        output = subprocess.check_output([CLANG, '-emit-llvm', '-S',
                                          '-o', '-',
                                          '-x', 'c', '-',
                                          '-target', 'x86_64-linux-gnu', f'-march={target}'
                                          ],
                                         input=INPUT,
                                         stderr=subprocess.PIPE
                                         )
    except subprocess.CalledProcessError as e:
        if b'unknown target' in e.stderr:
            return set(['UNKNOWN'])
        raise e
    output = output.decode('utf-8').split('"')
    feats = output[output.index('target-features') + 2]
    feats = feats[1:].split(',+')
    return set(feats)


def main():
    baselines = ['x86-64', 'x86-64-v2', 'x86-64-v3', 'x86-64-v4']
    baseline_feats = list(map(find_cpu_features, baselines))

    """
    for baseline, feats in zip(baselines, baseline_feats):
        print(baseline, feats)
    """

    def find_match(target, cpu_feats):
        match = None
        if 'UNKNOWN' in cpu_feats:
            return f'UNKNOWN-MARCH-{target}'
        for baseline, feats in zip(baselines, baseline_feats):
            if feats.issubset(cpu_feats):
                match = baseline
        return match

    for cpu, target in CPU_NAMES:
        cpu_feats = find_cpu_features(target)
        match = find_match(target, cpu_feats)
        print(f'"{cpu}", "{match}"')

main()
