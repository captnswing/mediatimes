#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import os
import shutil
import argparse
import subprocess
import arrow


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


# "FileModifyDate": "2020:03:14 11:02:27+01:00",
# "FileAccessDate": "2020:03:14 11:40:24+01:00",
# "FileInodeChangeDate": "2020:03:14 13:48:13+01:00",
# "ModifyDate": "2007:07:14 15:46:02",
# "DateTimeOriginal": "2007:07:14 15:46:02",
# "CreateDate": "2007:07:14 15:46:02",
# "CreateDate": "2007:07:14 15:46:02",
# "ModifyDate": "2007:07:14 15:46:02",
# "DateCreated": "2007:00:07 15:46:02+02:00",
# "DateCreated": "2007:07:14"
# "DateTimeCreated": "2007:07:14 15:46:02+02:00",

def get_earliest_date(mediafile):
    exif_data = subprocess.check_output(["/usr/local/bin/exiftool", "-g", "-j", mediafile])
    exif_data = json.loads(exif_data)[0]
    flattened_dict = dict()
    for k in exif_data:
        if not isinstance(exif_data[k], dict):
            continue
        flattened_dict.update(exif_data[k])
    datekeys = [k for k in flattened_dict.keys() if "date" in k.lower()]
    dateformats = ['YYYY:MM:DD HH:mm:ssZZ', 'YYYY:MM:DD HH:mm:ss', 'YYYY:MM:DD']
    # print([merged_dict[dk] for dk in datekeys])
    parsed_dates = []
    for dk in datekeys:
        if flattened_dict[dk] == "Off":
            continue
        try:
            d = arrow.get(flattened_dict[dk], dateformats)
            if d.time() != datetime.time(0, 0):
                parsed_dates.append(d)
        except ValueError:
            continue
    return min(parsed_dates)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='renames all movie files in a directory with creation date in their name')
    parser.add_argument("targetfolder", type=valid_directory)
    args = parser.parse_args()
    os.chdir(args.targetfolder)

    for fn in os.listdir(os.curdir):
        if not os.path.isfile(fn):
            continue
        d = get_earliest_date(fn)
        monthfolder = d.format('YYYY-MM')
        if not os.path.exists(monthfolder):
            os.makedirs(monthfolder)
        newfn = os.path.join(monthfolder, fn)
        shutil.move(fn, newfn)
        print(f"{fn:<30} -> {newfn:<}")
