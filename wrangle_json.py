#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import numpy as np
import pandas as pd
from pymongo import MongoClient


def find_rikard():
    mediadf = pd.DataFrame.from_records(
        db.json.find({"people.name": {"$regex": ".*ickard.*"}})
    )
    for fn in sorted(mediadf["filename"]):
        print(fn)


def canonical_name(fn):
    bn = os.path.basename(os.path.splitext(fn)[0])
    bn = bn.replace("-edited", "")
    bn = re.sub(r"#\d+", "", bn)
    bn = re.sub(r"\(\d+\)", "", bn)
    bn = re.sub(r"[-_]\d$", "", bn)
    return bn.strip()


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

    # jsondf = pd.DataFrame.from_records(
    #     db.flatjson.find({})
    # )
    # del jsondf['_id']
    # print(jsondf.head(10))
    # print(jsondf.shape)
    mediadf = pd.DataFrame.from_records(db.flatfiles.find({}))
    del mediadf["_id"]

    mediadf["canonical_name"] = mediadf["name"].apply(canonical_name)
    mediadf["createdate"] = pd.to_datetime(
        mediadf["createdate"], format="%Y:%m:%d %H:%M:%S"
    )
    mediadf["datetimeoriginal"] = pd.to_datetime(
        mediadf["datetimeoriginal"], format="%Y:%m:%d %H:%M:%S"
    )
    mediadf["subfolder"] = mediadf["folder"].apply(
        lambda x: re.sub(".*/Takeout/Google Photos/", "", x)
    )
    # mediadf.sort_values(by=['canonical_name'], inplace=True)
    # print(mediadf.head(100))
    # print(mediadf.info())
    # print(mediadf.shape)

    for n in mediadf["canonical_name"]:
        rows = mediadf[mediadf["name"].str.contains(n)]
        rows.sort_values(by=["createdate"], inplace=True)
        print(rows)
        break
        # for r in rows.iterrows():
        #     print(r)
        #     if  pd.isna(r.datetimeoriginal):
        #         print("b")
        # break
