#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import argparse
import time
from bashplotlib.histogram import plot_hist
from sparklines import sparklines


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="renames all movie files in a directory with creation date in their name"
    )
    parser.add_argument("targetfolder", type=valid_directory)
    args = parser.parse_args()

    a = []
    for directory, dirnames, filenames in os.walk(args.targetfolder):
        print(os.path.abspath(os.curdir))
        for f in filenames:
            if f.endswith(".txt") or f == ".DS_Store":
                continue
            ds = time.strftime(
                "%d", time.localtime(os.stat(os.path.join(directory, f)).st_mtime)
            )
            a.append(ds)

    plot_hist(a)
    for line in sparklines(a):
        print(line)
