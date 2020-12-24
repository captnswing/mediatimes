#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import argparse
import hashlib
import sys


def getmd5hash(filename):
    file_hash = hashlib.md5()
    BLOCK_SIZE = 128000000
    with open(filename, "rb") as f:
        fb = f.read(BLOCK_SIZE)
        while len(fb) > 0:  # While there is still data being read from the file
            file_hash.update(fb)  # Update the hash
            fb = f.read(BLOCK_SIZE)  # Read the next block from the file
    return file_hash.hexdigest()


def getallhashes():
    allhashes = []
    for directory, dirnames, filenames in os.walk("."):
        for filename in filenames:
            if re.match("^clip-.*\.mov$", filename):
                fn = os.path.join(directory, filename)
                print(fn)
                md5h = getmd5hash(fn)
                allhashes.append((md5h, fn))
    return allhashes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="rename movie files according to their hash"
    )
    parser.add_argument("targetdir")
    args = parser.parse_args()
    print(args.targetdir)

    if not os.path.isdir(args.targetdir):
        sys.exit(1)

    root = os.path.abspath(args.targetdir)
    os.chdir(root)

    for directory, dirnames, filenames in os.walk(os.curdir):
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
                print(newfn)
            print(f"{fn:<30} -> {newfn:<}")
