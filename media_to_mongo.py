#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import subprocess
from google_takeout_util import video_formats, image_formats
from pymongo import MongoClient


def walk_media(dir, formats):
    os.chdir(dir)
    for root, dirs, files in os.walk("."):
        for name in files:
            fn = os.path.join(root, name)
            extension = os.path.splitext(name)[1]
            if not extension.lower() in formats:
                continue
            yield os.path.join(dir, fn)


def load_media_data(coll, dir):
    for m in walk_media(dir, video_formats + image_formats):
        s = subprocess.check_output(["exiftool", "-m", "-j", "-g", m])
        data = json.loads(s.decode("utf-8"))[0]
        print(data)
        m_id = coll.insert_one(data).inserted_id


if __name__ == "__main__":
    target_dir = "/Volumes/Photos/frank/"
    client = MongoClient("mongodb://mongodb:27017/")
    # client.drop_database("iphoto")
    db = client.iphoto
    media_collection = db.media
    media_collection.create_index([("SourceFile", "text")])
    load_media_data(media_collection, target_dir)
