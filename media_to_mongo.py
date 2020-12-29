#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os

from pymongo import MongoClient


def load_media_data(coll, dir):
    os.chdir(dir)
    print(f"cd {dir}; exiftool -m -j -r . >exifdata.json")
    with open(os.path.join(dir, "exifdata.json")) as s:
        data = json.load(s)
        print(len(data))
        m_id = coll.insert_many(data)
        print(m_id)


if __name__ == "__main__":
    target_dir = "/Volumes/Photos/frank/"
    client = MongoClient("mongodb://mongodb:27017/")
    # client.drop_database("iphoto")
    db = client.iphoto
    media_collection = db.media
    media_collection.create_index([("SourceFile", "text")])
    # load_media_data(media_collection, target_dir)

    remove = media_collection.find(
        {
            "$or": [
                {"FileName": "shared_album_comments.json"},
                {"FileName": "print-subscriptions.json"},
                {"FileName": "metadata.json"},
                {"FileName": "archive_browser.html"},
                {"MIMEType": {"$eq": "text/html"}},
            ]
        }
    )
    for r in remove:
        try:
            os.remove(r["SourceFile"])
        except FileNotFoundError:
            # assume the remove happened already in an earlier run
            pass
        db.media.delete_one(r)

    media_collection.delete_many(
        {"MIMEType": {"$eq": "application/zip"}}
    )
    media_collection.update_many(
        {
            "$or": [
                {"CreateDate": {"$eq": "0000:00:00 00:00:00"}},
                {"CreateDate": {"$eq": "    :  :     :  :  "}},
            ]
        },
        {"$set": {"CreateDate": None}},
    )
    media_collection.update_many(
        {
            "$or": [
                {"DateTimeOriginal": {"$eq": "0000:00:00 00:00:00"}},
                {"DateTimeOriginal": {"$eq": "    :  :     :  :  "}},
            ]
        },
        {"$set": {"DateTimeOriginal": None}},
    )

    db.flatjson.drop()
    db.command(
        {
            "create": "flatjson",
            "viewOn": "media",
            "pipeline": [
                {
                    "$project": {
                        "SourceFile": "$SourceFile",
                        "FileName": "$FileName",
                        "Directory": "$Directory",
                        "FileSize": "$FileSize",
                        "FileTypeExtension": "$FileTypeExtension",
                        "MIMEType": "$MIMEType",
                        "DateTimeOriginal": "$DateTimeOriginal",
                        "CreateDate": "$CreateDate",
                        "ContentCreateDate": "$ContentCreateDate",
                        "CreationDate": "$CreationDate",
                        "PhotoTakenTimeFormatted": "$PhotoTakenTimeFormatted",
                    }
                },
                {
                    "$addFields": {
                        "DateTimeOriginal": {"$toDate": "$DateTimeOriginal"},
                        "CreateDate": {"$toDate": "$CreateDate"},
                        "ContentCreateDate": {"$toDate": "$ContentCreateDate"},
                        "CreationDate": {"$toDate": "$CreationDate"},
                        "PhotoTakenTimeFormatted": {
                            "$toDate": "$PhotoTakenTimeFormatted"
                        },
                    }
                },
            ],
        }
    )
