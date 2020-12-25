#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import datetime
import json
import os
import subprocess

import arrow


def valid_directory(d):
    if os.path.isdir(d):
        return d
    else:
        raise argparse.ArgumentTypeError("Not a valid directory: '{0}'.".format(d))


def get_earliest_date(mediafile):
    exif_dates = subprocess.check_output(
        ["/usr/local/bin/exiftool", "-G1", "-Alldates", "-j", mediafile]
    )
    exif_dates = json.loads(exif_dates)[0]
    del exif_dates["SourceFile"]
    dto_key = [key for key in exif_dates if "datetimeoriginal" in key.lower()][0]
    dto_key = dto_key.replace("Composite:", "")
    dateformats = ["YYYY:MM:DD HH:mm:ssZZ", "YYYY:MM:DD HH:mm:ss", "YYYY:MM:DD"]
    parsed_dates = [arrow.now()]
    for dk in exif_dates:
        if exif_dates[dk] == "Off":
            continue
        try:
            d = arrow.get(exif_dates[dk], dateformats)
            if d.time() != datetime.time(0, 0):
                parsed_dates.append(d)
        except ValueError:
            continue
    return dto_key, min(parsed_dates)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="sets DateTimeOriginal for images to earliest date found in EXIF data"
    )
    parser.add_argument("targetfolder", type=valid_directory)
    args = parser.parse_args()
    for root, dirs, files in os.walk(args.targetfolder, topdown=True):
        for name in files:
            if ".DS_Store" in name:
                continue
            if os.path.splitext(name)[1] == ".mov":
                continue

            mediafile = os.path.join(root, name)
            print(mediafile)
            dto_key, mindate = get_earliest_date(mediafile)
            mindate = mindate.format("YYYY-MM-DD HH:mm:ss")
            # print(f"-{dto_key}='{mindate}'", mediafile)
            subprocess.run(
                [
                    "/usr/local/bin/exiftool",
                    "-q",
                    "-m",
                    "-overwrite_original",
                    f"-{dto_key}='{mindate}'",
                    mediafile,
                ]
            )
