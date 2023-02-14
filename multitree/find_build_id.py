#!/usr/bin/python3

import xml.etree.ElementTree as ET
import json
import subprocess
import concurrent.futures
import requests
import os
import tempfile
import pprint
import sys

branch = subprocess.getoutput(
    "cat .repo/manifests/default.xml | grep super | sed 's/.*revision=\\\"\(.*\)\\\".*/\\1/'").strip()
text = subprocess.getoutput(
    "repo forall -c 'echo \\\"$REPO_PROJECT\\\": \\\"$(git log m/" + branch + " --format=format:%H -1)\\\",'")
json_text = "{" + text[:-1] + "}"
current = json.loads(json_text)
threshold = 1000
result = dict()


def rating(bid, target):
    filename = "manifest_" + bid + ".xml"
    result = subprocess.run(["/google/data/ro/projects/android/fetch_artifact", "--bid", bid,
                            "--target", target, filename], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    if result.returncode != 0:
        raise Exception('no artificats yet')

    tree = ET.parse(filename)
    root = tree.getroot()

    remote = dict()
    for child in root:
        if child.tag == "project" and "revision" in child.attrib:
            remote[child.attrib["name"]] = child.attrib["revision"]

    common_key = current.keys() & remote.keys()

    return sum([1 for key in common_key if current[key] != remote[key]])


def batch(nextPageToken="", branch="aosp-master", target="aosp_cf_x86_64_phone-userdebug", batch_size=100, total_try=0):
    url = "https://androidbuildinternal.googleapis.com/android/internal/build/v3/buildIds/%s?buildIdSortingOrder=descending&buildType=submitted&maxResults=%d" % (
        branch, batch_size)
    if nextPageToken != "":
        url += "&pageToken=%s" % nextPageToken
    res = requests.get(url)
    bids = res.json()
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(
            rating, bid_obj["buildId"], target): bid_obj["buildId"] for bid_obj in bids["buildIds"]}
        for future in concurrent.futures.as_completed(futures):
            try:
                bid = futures[future]
                different_prj_cnt = future.result()
            except Exception as exc:
                # Ignore..
                pass
            else:
                result[bid] = different_prj_cnt
                if different_prj_cnt == 0:
                    print("%s is the bid to use %s in %s for your repository" %
                          (bid, target, branch))
                    return True
    total_try += batch_size
    if total_try >= threshold:
        pprint.pprint(sorted(result.items(), key=lambda x: -int(x[1])))
        print("""
Cannot find the perfect matched bid during %d builds: There are 3 options
  1. Choose a bid from the list above(bid, count of different projects)
  2. Increase threshold
  3. repo sync
""" % total_try)

        return False
    return batch(nextPageToken=bids["nextPageToken"], branch=branch, target=target, batch_size=batch_size, total_try=total_try)


def main():
    if len(sys.argv) == 1:
        batch()
    elif len(sys.argv) == 3:
        batch(branch=sys.argv[1], target=sys.argv[2])
    else:
        print("run without arguments or two arguments(branch and target)")


with tempfile.TemporaryDirectory() as tmpdirname:
    os.chdir(tmpdirname)
    main()
