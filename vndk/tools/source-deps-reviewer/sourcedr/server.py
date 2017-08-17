#!/usr/bin/env python3

from sourcedr.data_utils import *
from sourcedr.preprocess import CodeSearch

from flask import Flask, jsonify, render_template, request
import argparse
import bisect
import hashlib
import json
import os
import subprocess
import sys
import webbrowser

# for Python compatability
if sys.version_info < (3,):
    input = raw_input

app = Flask(__name__)

# whether the code segment is exactly in file
def same(fl, code):
    with open(fl, 'r') as f:
        fc = f.read()
        return code in fc

# check if the file needes to be reiewed again
def check(codes):
    for item in codes:
        fl = item.split(':')[0]
        code = item[len(fl) + 1:]
        if not same(fl, code):
            return False
    return True

@app.route('/get_started')
def _get_started():
    lst, done= [], []
    for key, item in sorted(data.items()):
        lst.append(key)
        if item[0]:
            done.append(check(item[1]))
        else:
            done.append(False)

    pattern_lst = load_pattern()[0]

    return jsonify(lst=json.dumps(lst),
                   done=json.dumps(done),
                   pattern_lst=json.dumps(pattern_lst))

@app.route('/load_file')
def _load_file():
    path = request.args.get('path')

    if path not in data.keys():
        print('No such entry', path)
        return jsonify(result='')
    deps, codes = data[path]

    return jsonify(deps=json.dumps(deps), codes=json.dumps(codes))

@app.route('/get_file')
def _get_file():
    path = request.args.get('path')
    if not os.path.exists(path):
        return jsonify(result='No such file')
    with open(path, 'r') as f:
        code = f.read()

    return jsonify(result=code)

@app.route('/save_all')
def _save_all():
    label = request.args.get('label')
    deps = json.loads(request.args.get('deps'))
    codes = json.loads(request.args.get('codes'))
    data[label] = (deps, codes)
    # save update to file
    save_data(data)
    return jsonify(result='done')

# This function add pattern to grep
@app.route('/add_pattern')
def _add_pattern():
    patt = request.args.get('pattern')
    is_regex = request.args.get('is_regex')
    engine.add_pattern(patt, is_regex)
    # update the data
    global data
    data = load_data()
    save_new_pattern(patt, is_regex)
    return jsonify(result='done')

@app.route('/')
def render():
    return render_template('index.html')

@app.before_first_request
def _run_on_start():
    # load data first for better efficiency
    global data
    data = load_data()

def input_yes_no(question, default=True):
    valid = {'yes': True, 'y': True, 'no': False, 'n': False, '': default}
    prompt = ' [Y/n] ' if default else ' [y/N] '
    while True:
        sys.stdout.write(question + prompt)
        sys.stdout.flush()
        choice = input().lower().strip()
        try:
            return valid[choice]
        except KeyError:
            continue

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--android-root', default='sourcedr/test')
    parser.add_argument('--index-path', default='csearchindex')
    parser.add_argument('--skip-literals', action='store_true')
    parser.add_argument('--skip-comments', action='store_true')

    global args, engine
    args = parser.parse_args()
    # a CodeSearch engine must be initialized with the
    # root of the directory and the path of the csearch index file
    engine = CodeSearch.create_default(args.android_root, args.index_path)

    print('Be careful that previous data files will merge with new data files.')
    print('Delete previous data files(data.json, patterns) if you want ' +
          'to start all over.')

    # If build index again
    if os.path.exists(args.index_path):
        if input_yes_no('Overwrite previous index file.'):
            os.remove(args.index_path)
            engine.build_index()
        else:
            print('Using previous index file.')
    else:
        engine.build_index()

    print('Reading patterns from the database')
    if patterns_exist():
        patterns, is_regexs = load_pattern()
    else:
        print('Finding default patterns: dlopen')
        init_pattern('dlopen', is_regex=False)
        patterns, is_regexs = load_pattern()

    engine.find(patterns, is_regexs)

    assert data_exist() and patterns_exist()
    app.run()

if __name__=='__main__':
    main()
