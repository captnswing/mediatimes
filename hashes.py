#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import re
import argparse
import shutil
import hashlib
import shelve


def getmd5hash(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), ''):
            md5.update(chunk)
    return md5.hexdigest()


def getallhashes():
    allhashes = []
    for directory, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if re.match('^clip-.*\.mov$', filename):
                fn = os.path.join(directory, filename)
                print fn
                md5h = getmd5hash(fn)
                allhashes.append((md5h, fn))
    return allhashes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='rename movie files according to their hash')
    parser.add_argument("targetdir")
    args = parser.parse_args()
    print args.targetdir

    if os.path.isdir(args.targetdir):
        os.chdir(args.targetdir)
        items = os.listdir(os.curdir)
    else:
        items = [args.targetdir]

    root = os.path.abspath(args.targetdir)
    for directory, dirnames, filenames in os.walk(args.targetdir):
        for f in filenames:
            fn = os.path.join(directory, f)
            if f.startswith("."):
                if os.path.exists(fn):
                    os.remove(fn)
                continue
            ext = os.path.splitext(f)[-1].lower()
            newfn = getmd5hash(fn)
            newfn += ext
            newfn = os.path.join(root, newfn)
            if not os.path.exists(newfn):
                os.rename(fn, newfn)
            else:
                print newfn
            print "{:<30} -> {:<}".format(fn, newfn)

    # for item in items:
    #     if item == ".DS_Store" or os.path.isdir(item):
    #         continue
    #     ext = os.path.splitext(item)[-1].lower()
    #     newfn = getmd5hash(item)
    #     newfn += ext
    #     os.rename(item, os.path.join('..', newfn))
