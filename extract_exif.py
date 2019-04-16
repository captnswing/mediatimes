#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import subprocess
import re
import argparse
import datetime
from dateutil.parser import parse

testdata = [
    "2015:06:05 19:35:48+02:00",
    "2016:06:25 17:13:54+02:00",
    "2016:04:03 10:32:41+02:00",
    "2015:06:05 17:37:40",
    "2015:05:14 14:35:06+02:00",
    "2016:06:25 17:06:52+02:00",
    "2016:04:03 10:41:09+02:00",
    "0000:00:00 00:00:00",
    "2010:03:21 18:46:10+01:00"
]


def parsedate(ds):
    day, hour = ds.split(" ")
    if day == "0000:00:00":
        day = "1970:01:01"
    day = day.replace(":", "-")
    pd = parse(day + " " + hour)
    # print(ds, type(ds))
    # print(pd, type(pd))
    return pd


def get_earliest_date(exifdata, verbose=False):
    parsed_dates = []
    date_lines = []
    for line in exifdata.splitlines():
        pattern = re.compile(r".* : (\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})(.\d{2}.\d{2})?")
        if pattern.match(line):
            datestring = pattern.match(line).group(1)
            parsed_dates.append(parsedate(datestring))
            date_lines.append((line.split(" : ")[0], parsedate(datestring).strftime("%Y-%m-%d %H:%M:%S")))
    if verbose:
        date_lines.sort(key=lambda t: t[1], reverse=False)
        for l in date_lines:
            print(l)
    return min(parsed_dates)


# touch -a -tCCYYMMDDHH.SS <file>
# touch -m -tCCYYMMDDHH.SS <file>
# SetFile -d "MM/DD/CCYY HH:MM:SS" <file>

def correct_dates(movie, d=None):
    print(movie)
    if not d:
        exif_data = subprocess.check_output(["/usr/local/bin/exiftool", "-G", movie])
        exif_data = exif_data.decode('utf-8')
        d = get_earliest_date(exif_data)
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
    templ = "-{{}}={date}".format(date=d)
    for k in keys:
        cmd.append(templ.format(k))
    cmd.append("{}".format(movie))
    print(cmd)
    subprocess.check_output(cmd)
    ts = int(d.strftime("%s"))
    os.utime(movie, (ts, ts))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='set datetime on individual movie or all movies in a folder')
    parser.add_argument("target")
    parser.add_argument("targetdate", nargs='?', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d %H:%M'))
    args = parser.parse_args()

    print(args.target)
    print(args.targetdate)

    if os.path.isdir(args.target):
        items = os.listdir(args.target)
    else:
        items = [args.target]

    for item in items:
        if item == ".DS_Store" or os.path.isdir(item):
            continue
        correct_dates(item, args.targetdate)
