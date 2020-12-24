#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import pandas as pd
import arrow
from pymongo import MongoClient

if __name__ == "__main__":
    pd.set_option("display.width", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    # pd.set_option('display.max_colwidth', -1)

    # load_json_data()
    target_dir = "/Volumes/Photos/frank/"
    client = MongoClient("mongodb://mongodb:27017/")
    # client.drop_database("iphoto")
    db = client.iphoto
    json_collection = db.json
    media_collection = db.media

    db.flatfiles.drop()
    db.command(
        {
            "create": "flatfiles",
            "viewOn": "media",
            "pipeline": [
                {
                    "$project": {
                        "name": "$File.FileName",
                        "folder": "$File.Directory",
                        "size": "$File.FileSize",
                        "createdate": "$EXIF.CreateDate",
                        "datetimeoriginal": "$EXIF.DateTimeOriginal",
                        "gpsdate": "$Composite.GPSDateTime",
                    }
                }
            ],
        }
    )
    db.flatjson.drop()
    db.command(
        {
            "create": "flatjson",
            "viewOn": "json",
            "pipeline": [
                {
                    "$project": {
                        "datetimeoriginal": "$photoTakenTime.formatted",
                        "folder": "$filename",
                        "name": "$title",
                        "tz": "$tzname",
                        "geoData": "$geoData",
                    }
                }
            ],
        }
    )

    # jsondf = pd.DataFrame.from_records(
    #     db.flatjson.find({})
    # )
    # del jsondf['_id']
    # print(jsondf.head(10))
    # print(jsondf.shape)
    mediadf = pd.DataFrame.from_records(db.flatfiles.find({}))
    del mediadf["_id"]

    def canonical_name(fn):
        bn = os.path.basename(os.path.splitext(fn)[0])
        bn = bn.replace("-edited", "")
        bn = re.sub(r"#\d+", "", bn)
        bn = re.sub(r"\(\d+\)", "", bn)
        bn = re.sub(r"[-_]\d$", "", bn)
        return bn.strip()

    def canonical_time(row):
        # print(row.createdate, row.datetimeoriginal, row.gpsdate)
        if pd.isna(row.createdate):
            row.createdate = None
        else:
            row.createdate = arrow.get(row.createdate, "YYYY:MM:DD HH:mm:ss")
        if pd.isna(row.datetimeoriginal):
            row.datetimeoriginal = None
        else:
            row.createdate = arrow.get(row.datetimeoriginal, "YYYY:MM:DD HH:mm:ss")
        if pd.isna(row.gpsdate):
            row.gpsdate = None
        else:
            row.gpsdate = arrow.get(
                row.gpsdate, ["YYYY:MM:DD HH:mm:ss.SS[Z]", "YYYY:MM:DD HH:mm:ss[Z]"]
            )

        return row.createdate

    def myDateConv(tt):
        sep = tt[2]
        if sep == "-":
            return pd.to_datetime(tt, format="%d-%m-%Y")
        elif sep == "/":
            return pd.to_datetime(tt, format="%m/%d/%Y")
        else:
            return tt

    # mediadf.replace("    :  :     :  :  ", np.nan, inplace=True)
    # mediadf.replace("0000:00:00 00:00:00", np.nan, inplace=True)
    #
    # mediadf["canonical_name"] = mediadf["name"].apply(canonical_name)
    # mediadf["createdate"] = pd.to_datetime(
    #     mediadf["createdate"], format="%Y:%m:%d %H:%M:%S"
    # )
    # mediadf["datetimeoriginal"] = pd.to_datetime(
    #     mediadf["datetimeoriginal"], format="%Y:%m:%d %H:%M:%S"
    # )
    # mediadf["gpsdate"] = pd.to_datetime(
    #     mediadf["gpsdate"], format="%Y:%m:%d %H:%M:%S[.:]%f[Z]"
    # )
    # mediadf["canonical_time"] = mediadf.apply(canonical_time, axis=1)
    # mediadf.sort_values(by=['canonical_time'])
    # print(mediadf.head(100))
    # print(mediadf.info())
    # print(mediadf.shape)
    mediadf = pd.DataFrame.from_records(
        db.json.find({"people.name": {"$regex": ".*ickard.*"}})
    )
    for fn in sorted(mediadf["filename"]):
        print(fn)
