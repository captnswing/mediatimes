#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import mimetypes
import os
import re
import shutil
import subprocess

from bson import ObjectId
from pymongo import MongoClient

from google_takeout_util import (
    image_formats,
    video_formats,
    move_subfolders_into_batches,
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


def move_edited_to_original():
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
                shutil.move(
                    os.path.abspath(e["SourceFile"]), os.path.abspath(o["SourceFile"])
                )
            except FileNotFoundError:
                # assume the move happened already in an earlier run
                # print("J")
                pass
            db.media.delete_one({"_id": ObjectId(e["_id"])})


def fix_wrong_heic():
    wrong = media_collection.find(
        {
            "$and": [
                {"FileName": {"$regex": ".*\HEIC$"}},
                {"MIMEType": {"$ne": "image/heic"}},
            ]
        }
    )
    for w in wrong:
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
        change_extension(w, new_ext)


def change_extension(doc, new_ext):
    base, ext = os.path.splitext(doc["SourceFile"])
    mt = mimetypes.MimeTypes().guess_type(doc["SourceFile"])[0]
    print(mt)
    print(f"move {doc['SourceFile']} {base}.{new_ext}")
    try:
        shutil.move(doc["SourceFile"], f"{base}{new_ext}")
        print("ok")
    except FileNotFoundError:
        # assume the move happened already in an earlier run
        pass
    db.media.update_one(
        {"_id": doc["_id"]},
        {
            "$set": {
                "SourceFile": doc["SourceFile"].replace(ext, new_ext),
                "FileName": doc["FileName"].replace(ext, new_ext),
                "MIMEType": mt,
            }
        },
        upsert=False,
    )


def update_exif_date(doc, dt):
    command = [
        "/usr/local/bin/exiftool",
        "-m",
        "-overwrite_original",
        f"-DateTimeOriginal='{dt}'",
        f"-CreateDate='{dt}'",
        doc["SourceFile"],
    ]
    try:
        s = subprocess.check_output(command, encoding="utf-8", stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if "Not a valid PNG (looks more like a JPEG)":
            change_extension(doc, ".jpg")
        print(e.output)


def find_matching_json(doc):
    cn = canonical_name(doc["FileName"])
    cd = doc["Directory"].split("/")[-1]
    jsonmatch = f".*{cd}/{cn}.*json"
    return db.flatjson.find_one(
        {
            "$and": [
                {"SourceFile": {"$regex": jsonmatch}},
            ]
        }
    )


def fix_missing_date_videos():
    BAD_DIR = "/Users/frahof/frank_import/tttt"
    extensions = [e.strip(".") for e in video_formats]
    missing_date = db.flatjson.find(
        {
            "$and": [
                # {"SourceFile": {"$regex": ".*takeout-20201108T103354Z-001.*"}},
                {"FileTypeExtension": {"$in": extensions}},
                {
                    "$or": [
                        # {"DateTimeOriginal": None},
                        {"CreateDate": None},
                        {"CompressorName": "Apple Intermediate Codec"},
                    ]
                },
            ]
        }
    )
    for m in missing_date:
        j = find_matching_json(m)
        if not j:
            print(f"moving bad file {m['SourceFile']}")
            shutil.move(m["SourceFile"], os.path.join(BAD_DIR, m["FileName"]))
            db.media.delete_one({"_id": ObjectId(m["_id"])})
            continue
        base, ext = os.path.splitext(m["SourceFile"])
        new_ext = ".mp4"
        print(
            f"ffmpeg -hide_banner -loglevel panic -i '{m['SourceFile']}' -c:v libx264 -c:a aac -pix_fmt yuv420p -y '{base}{new_ext}'"
        )
        print(
            f"exiftool -m -overwrite_original -CreationDate='{j['PhotoTakenTimeFormatted']}' -CreateDate='{j['PhotoTakenTimeFormatted']}' '{base}{new_ext}'"
        )
        print(f"rm '{m['SourceFile']}'")
        db.media.update_one(
            {"_id": m["_id"]},
            {
                "$set": {
                    "CreationDate": j["PhotoTakenTimeFormatted"],
                    "CreateDate": j["PhotoTakenTimeFormatted"],
                    "SourceFile": m["SourceFile"].replace(ext, new_ext),
                    "FileName": m["FileName"].replace(ext, new_ext),
                    "MIMEType": "video/mp4",
                }
            },
            upsert=False,
        )


def fix_missing_date_images():
    BAD_DIR = "/Users/frahof/frank_import/tttt"
    extensions = [e.strip(".") for e in image_formats]
    missing_date = db.flatjson.find(
        {
            "$and": [
                # {"SourceFile": {"$regex": ".*takeout-20201108T103354Z-002.*"}},
                {"FileTypeExtension": {"$in": extensions}},
                {"DateTimeOriginal": None},
                {"CreateDate": None},
            ]
        }
    )
    for m in missing_date:
        j = find_matching_json(m)
        if not j:
            print(f"moving bad file {m['SourceFile']}")
            shutil.move(m["SourceFile"], os.path.join(BAD_DIR, m["FileName"]))
            db.media.delete_one({"_id": ObjectId(m["_id"])})
            continue
        print(
            f"updating DateTimeOriginal of {m['FileName']} to {j['PhotoTakenTimeFormatted']}"
        )
        update_exif_date(m, j["PhotoTakenTimeFormatted"])
        db.media.update_one(
            {"_id": m["_id"]},
            {
                "$set": {
                    "DateTimeOriginal": j["PhotoTakenTimeFormatted"],
                    "CreateDate": j["PhotoTakenTimeFormatted"],
                }
            },
            upsert=False,
        )


if __name__ == "__main__":
    target_dir = "/Volumes/Photos/frank/"
    os.chdir(target_dir)
    client = MongoClient("mongodb://mongodb:27017/")
    db = client.iphoto
    media_collection = db.media

    # move_edited_to_original()
    # fix_wrong_heic()
    # fix_missing_date_images()
    fix_missing_date_videos()

    # for m in media_collection.find(
    #         {"MIMEType": {"$eq": None}}
    # ):
    #     mt = mimetypes.MimeTypes().guess_type(m["SourceFile"])[0]
    #     print(mt)
    #     db.media.update_one(
    #         {"_id": m["_id"]},
    #         {
    #             "$set": {
    #                 "MIMEType": mt
    #             }
    #         },
    #         upsert=False,
    #     )

    # move_subfolders_into_batches("/Volumes/Photos/frank/files")
    # doc = media_collection.find_one(
    #     {"SourceFile": "./takeout-20201108T103354Z-001/Takeout/Google Photos/2020-07-24 #2/IMG_0058.PNG"}
    # )
    # update_exif_date(doc, '2020-11-07 09:03:18')
    # remove duplicate images/videos
