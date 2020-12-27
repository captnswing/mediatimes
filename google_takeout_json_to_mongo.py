#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re

import arrow
import pandas as pd
from pymongo import MongoClient
from tzwhere.tzwhere import tzwhere


def walk_json(dir):
    os.chdir(dir)
    for root, dirs, files in os.walk("."):
        for name in files:
            fn = os.path.join(root, name)
            extension = os.path.splitext(name)[1]
            if extension.lower() == ".json":
                yield (os.path.join(dir, fn))


def load_json_data(coll, dir):
    w = tzwhere()
    for j in walk_json(dir):
        if "print-subscriptions.json" in j:
            continue
        if "shared_album_comments.json" in j:
            continue
        if "metadata" in j:
            continue
        data = json.load(open(j))
        if "trashed" in data:
            continue
        del data["description"]
        del data["imageViews"]
        if "googlePhotosOrigin" in data:
            del data["googlePhotosOrigin"]
        del data["geoDataExif"]
        del data["modificationTime"]
        data["filename"] = j
        data["tzname"] = "UTC"
        if data["geoData"]["longitude"]:
            data["tzname"] = w.tzNameAt(
                data["geoData"]["latitude"], data["geoData"]["longitude"]
            )
        j_id = coll.insert_one(data).inserted_id


if __name__ == "__main__":
    pd.set_option("display.width", None)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", None)

    # load_json_data()
    target_dir = "/Volumes/Photos/frank/"
    client = MongoClient("mongodb://mongodb:27017/")
    # client.drop_database("iphoto")
    db = client.iphoto
    json_collection = db.json
    json_collection.create_index([("filename", "text")])
    # load_json_data(json_collection, target_dir)

    db.flatjson.drop()
    db.command(
        {
            "create": "flatjson",
            "viewOn": "json",
            "pipeline": [
                {
                    "$project": {
                        "name": "$title",
                        "fn": "$filename",
                        "photoTakenTime": "$photoTakenTime.formatted",
                        "tz": "$tzname",
                        "geoData": "$geoData",
                    }
                },
                {
                    "$addFields": {
                        "photoTakenTime": {"$toDate": "$photoTakenTime"},
                    }
                },
            ],
        }
    )

    jsondf = pd.DataFrame.from_records(db.flatjson.find({}))
    del jsondf["_id"]
    print(jsondf.head(10))
    print(jsondf.shape)
    print(jsondf.info())
