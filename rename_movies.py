#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import argparse
import time


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


def get_new_filename(fn):
    mtime = os.path.getmtime(fn)
    ds = int(time.strftime("%Y%m%d%H%M%S", time.localtime(mtime)))
    ext = os.path.splitext(fn)[-1].lower()
    while True:
        filename = "MVI_{}{}".format(ds, ext)
        if os.path.exists(filename):
            ds += 1
        if not os.path.exists(filename):
            break
    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="renames all movie files in a directory with creation date in their name"
    )
    parser.add_argument("moviefolder", type=valid_directory)
    args = parser.parse_args()
    os.chdir(args.moviefolder)

    for fn in os.listdir(os.curdir):
        # filetype = subprocess.check_output(["file", fn])
        # filetype = "".join(filetype.split(":")[1:]).strip()
        # if not filetype.startswith("ISO Media, "):
        #     print "********************** " + fn
        #     continue
        # base, ext = os.path.splitext(fn)
        # if ext.lower() == ".avi":
        #     os.rename(fn, base+".mov")
        newfn = get_new_filename(fn)
        os.rename(fn, newfn)
        print("{:<30} -> {:<}".format(fn, newfn))
