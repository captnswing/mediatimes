#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import datetime
import json
import os
import subprocess
# https://opensource.com/article/18/4/python-datetime-libraries
import arrow


def get_earliest_date(exifdata, dry_run=False):
    exifdata = {**exifdata['File'], **exifdata['QuickTime']}
    datekeys = [k for k in exifdata.keys() if "date" in k.lower()]
    parsed_dates = [arrow.get(exifdata[dk], ['YYYY:MM:DD HH:mm:ssZZ', 'YYYY:MM:DD HH:mm:ss']).datetime for dk in datekeys]
    # if dry_run:
    #     print("-"*50)
    #     print(exifdata)
    #     print(datekeys)
    #     print(parsed_dates)
    return min(parsed_dates)


# touch -a -tCCYYMMDDHH.SS <file>
# touch -m -tCCYYMMDDHH.SS <file>
# SetFile -d "MM/DD/CCYY HH:MM:SS" <file>

def correct_dates(mediafile, d=None, dry_run=False):
    if not d:
        exif_data = subprocess.check_output(["/usr/local/bin/exiftool", "-g", "-j", mediafile])
        exif_data = json.loads(exif_data)[0]
        d = get_earliest_date(exif_data, dry_run)
#    assert (type(d) is arrow.Arrow)
    assert (type(d) is datetime.datetime)
    # https://productforums.google.com/d/msg/photos/oj96JZK14Fs/upbMBWvmAQAJ
    keys = ["AllDates",
            "FileModifyDate",
            # "FileCreateDate", # Windows only
            "TrackModifyDate",
            "TrackCreateDate",
            "MediaModifyDate",
            "MediaCreateDate"]

    cmd = ["/usr/local/bin/exiftool", "-overwrite_original"]
    templ = f"-{{}}={d}"
    for k in keys:
        cmd.append(templ.format(k))
    cmd.append("{}".format(mediafile))
    if dry_run:
        print(d, os.path.basename(mediafile))
        # print(cmd)
    else:
        subprocess.check_output(cmd)
        ts = int(d.strftime("%s"))
        os.utime(mediafile, (ts, ts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='set datetime on individual movie or all movies in a folder')
    parser.add_argument("target")
    parser.add_argument("targetdate", nargs='?', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d %H:%M'))
    parser.add_argument("--dry-run", action="store_true", default=False, help="show some output.")
    args = parser.parse_args()

    if os.path.isdir(args.target):
        items = os.listdir(args.target)
        items = [os.path.join(args.target, i) for i in items]
    else:
        items = [args.target]

    for item in items:
        if item == ".DS_Store" or os.path.isdir(item):
            continue
        correct_dates(item, args.targetdate, args.dry_run)
