#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import argparse
import time


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


# def get_new_filename(fn):
#     fn = os.path.basename(fn)
#     fn, ext = os.path.splitext(fn)
#     i = 0
#     while True:
#         filename = os.path.join(targetf, fn + ext.lower())
#         if os.path.exists(filename):
#             fn += "{}".format(i + 1)
#         if not os.path.exists(filename):
#             break
#     return filename


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='renames all movie files in a directory with creation date in their name')
    parser.add_argument("targetfolder", type=valid_directory)
    args = parser.parse_args()
    os.chdir(args.targetfolder)

    for fn in os.listdir(os.curdir):
        monthfolder = time.strftime("%Y-%m", time.localtime(os.stat(fn).st_mtime))
        if not os.path.exists(monthfolder):
            os.makedirs(monthfolder)
        newfn = os.path.join(monthfolder, fn)
        shutil.move(fn, newfn)
        print "{:<30} -> {:<}".format(fn, newfn)
