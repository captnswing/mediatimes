#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import argparse


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


def get_new_filename(fn):
    fn = os.path.basename(fn)
    fn, ext = os.path.splitext(fn)
    i = 0
    while True:
        filename = os.path.join(targetf, fn + ext.lower())
        if os.path.exists(filename):
            fn += "{}".format(i + 1)
        if not os.path.exists(filename):
            break
    return filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="renames all movie files in a directory with creation date in their name"
    )
    parser.add_argument("targetfolder", type=valid_directory)
    args = parser.parse_args()
    os.chdir(args.targetfolder)

    # 2.4M Aug  3  2009 IMG_4295-2.JPG
    # 2.4M Aug 23  2009 IMG_4295.JPG
    # 849K Jul  9  2015 IMG_42951.jpg*
    files = ["IMG_4295-2.JPG", "IMG_4295.JPG", "IMG_42951.jpg"]
    for f in files:
        phash = subprocess.check_output(["/Users/hoffsummer/Downloads/phashconvert", f])
        print(phash)
