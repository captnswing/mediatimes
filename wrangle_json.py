#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import shutil

from bson import ObjectId
from pymongo import MongoClient

from google_takeout_util import (
    image_formats,
    video_formats,
)


def canonical_name(fn):
    bn = os.path.basename(os.path.splitext(fn)[0])
    bn = bn.replace("-edited", "")
    bn = re.sub(r"#\d+", "", bn)
    bn = re.sub(r"\(\d+\)", "", bn)
    bn = re.sub(r"[-_]\d$", "", bn)
    return bn.strip()


def _find_original_record(edited_record):
    # './Google Photos/2015-04-22-23/IMG_2079-edited.jpg' --> './Google Photos/2015-04-22-23/IMG_2079.JPG'
    original_base = (
        edited_record["SourceFile"].replace("-edited", "").replace("-redigerad", "")
    )
    myregexp = f".*{os.path.splitext(original_base)[0]}\..*"
    # print(myregexp)
    original_record = db.flatjson.find_one(
        {
            "$and": [
                {"SourceFile": {"$regex": myregexp}},
                {"MIMEType": {"$eq": edited_record["MIMEType"]}},
            ]
        }
    )
    return original_record


def move_edited_to_original(target_dir):
    os.chdir(target_dir)
    edited = media_collection.find(
        {
            "$or": [
                {"SourceFile": {"$regex": ".*-redigerad.*"}},
                {"SourceFile": {"$regex": ".*-edited.*"}},
            ]
        }
    )
    for e in edited:
        o = _find_original_record(e)
        if o:
            print(f"{e['SourceFile']} --> {os.path.basename(o['SourceFile'])}")
            try:
                shutil.move(e["SourceFile"], o["SourceFile"])
            except FileNotFoundError:
                # assume the move happened already in an earlier run
                pass
        db.media.delete_one({"_id": ObjectId(e["_id"])})


def fix_wrong_heic(target_dir):
    os.chdir(target_dir)
    wrong = media_collection.find(
        {
            "$and": [
                {"FileName": {"$regex": ".*\HEIC$"}},
                {"MIMEType": {"$ne": "image/heic"}},
            ]
        }
    )
    for w in wrong:
        fn, ext = os.path.splitext(w["SourceFile"])
        new_ext = ""
        if w["MIMEType"] == "image/jpeg":
            new_ext = ".jpg"
        elif w["MIMEType"] == "video/mp4":
            new_ext = ".mp4"
        elif w["MIMEType"] == "video/quicktime":
            new_ext = ".mov"
        if not new_ext:
            print("-" * 50)
            print(w)
            print("-" * 50)
            continue

        print(f"move {w['SourceFile']} {fn}{new_ext}")
        try:
            shutil.move(w["SourceFile"], f"{fn}{new_ext}")
        except FileNotFoundError:
            # assume the move happened already in an earlier run
            pass
        db.media.update_one(
            {"_id": w["_id"]},
            {
                "$set": {
                    "SourceFile": w["SourceFile"].replace(ext, new_ext),
                    "FileName": w["FileName"].replace(ext, new_ext),
                }
            },
            upsert=False,
        )


if __name__ == "__main__":
    target_dir = "/Volumes/Photos/frank/"
    client = MongoClient("mongodb://mongodb:27017/")
    db = client.iphoto
    media_collection = db.media

    move_edited_to_original(target_dir)
    # fix_wrong_heic(target_dir)
    # duplicate images/videos
    # fix missing date images
    # fix missing date videos
    # fix video format
