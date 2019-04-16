import os
import re
import shutil
import hashlib
import shelve


def makeenglish():
    for dirname in os.listdir('.'):
        if u'Ny ha\u0308ndelse ' in dirname.decode('utf8'):
            newname = re.sub(u'Ny ha\xcc\x88ndelse ', 'New Event ', dirname)
            print newname
            shutil.move(dirname, newname)

    for dirname in os.listdir('.'):
        if ' Dag' in dirname:
            newname = re.sub(' Dag', ' Day', dirname)
            print newname
            #                if os.path.exists(newname):
            #                    newname =
            shutil.move(dirname, newname)


def getmd5hash(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), ''):
            md5.update(chunk)
    return md5.hexdigest()


def getallhashes():
    allhashes = []
    for directory, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if re.match('^clip-.*\.mov$', filename):
                fn = os.path.join(directory, filename)
                print fn
                md5h = getmd5hash(fn)
                allhashes.append((md5h, fn))
    return allhashes


d = shelve.open('hashes.shelve')
d['allhashes'] = allhashes
d.close()
