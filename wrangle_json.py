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


def process_clean_cases(df):
    dates_agree = df[df["createdate"] == df["datetimeoriginal"]]
    dates_agree = dates_agree[
        ~dates_agree.duplicated(subset=["canonical_name", "size"])
    ]
    dates_agree = dates_agree.sort_values(by=["canonical_name"])
    print(dates_agree.sample(20))
    print(dates_agree.shape)
    with open("/tmp/frank_doit.sh", "w+") as f:
        for row in dates_agree.itertuples():
            msg = f"mkdir -p '/Volumes/Photos/frank_import/{os.path.dirname(row.subfolder)}'\n"
            print(msg, end="")
            f.write(msg)
            msg = f"cp '{row.fn_x}' '/Volumes/Photos/frank_import/{row.subfolder}'\n"
            print(msg, end="")
            f.write(msg)


def process_file(f, d):
    bn, ext = os.path.splitext(f.fn_x)
    if ext.lower() in video_formats:
        print(f.fn_x, d, ext)

    elif ext.lower() in image_formats:
        pass
    else:
        print("DONTKNOWHOWTOHANDLE")


def process_corner_cases(df):
    rest = df[df["createdate"] != df["datetimeoriginal"]]
    rest = rest.sort_values(by=["canonical_name"])
    a = rest.groupby("canonical_name").first()
    a.fillna(value=np.nan, inplace=True)
    a = a[a.createdate.isnull() | a.datetimeoriginal.isnull()]
    a["extension"] = a["fn_x"].apply(lambda x: os.path.splitext(x)[1].lower())
    print(set(a["extension"].to_list()))
    images = a[a["extension"].isin(image_formats)]
    videos = a[a["extension"].isin(video_formats)]
    print(rest.info())
    print(a.info())
    print(images.info())
    print(videos.info())

    with open("/tmp/frank_doit.sh", "w+") as f:
        msg = f"mkdir -p '/Users/frahof/frank_import/BAD'\n"
        f.write(msg)
        for row in videos.itertuples():
            msg = f"mkdir -p '/Users/frahof/frank_import/{os.path.dirname(row.subfolder)}'\n"
            f.write(msg)
            msg = f"cp -p '{row.fn_x}' '/Users/frahof/frank_import/{row.subfolder}'\n"
            f.write(msg)
            new_fn = f"/Users/frahof/frank_import/{row.subfolder}"
            # print(new_fn)
            if not pd.isnull(row.createdate):
                msg = f"exiftool -m -overwrite_original -DateTimeOriginal='{row.createdate}' '{new_fn}'\n"
                f.write(msg)
            elif not pd.isnull(row.datetimeoriginal):
                msg = f"exiftool -m -overwrite_original -CreateDate='{row.datetimeoriginal}' '{new_fn}'\n"
                f.write(msg)
            elif not pd.isnull(row.photoTakenTime):
                msg = f"exiftool -m -overwrite_original -DateTimeOriginal='{row.photoTakenTime}' -CreateDate='{row.photoTakenTime}' '{new_fn}'\n"
                f.write(msg)
            else:
                print(f"no timestamp for '{new_fn}'")
                msg = f"mv '{new_fn}' /Users/frahof/frank_import/BAD\n"
                f.write(msg)


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
