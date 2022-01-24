#!/usr/bin/env python2

from __future__ import print_function

import csv
import datetime
import errno
import hashlib
import os
import traceback
import zipfile


V_DRIVE_ROOT = "/Volumes/Shares/LIB_WDL_Digital/WDL_Born_digital"

AUDIT_CSV_PATH = "v_drive_audit.csv"
AUDIT_ZIPFILES_CSV_PATH = "v_drive_audit_zipfiles.csv"

AUDIT_CSV_FIELDNAMES = ["path", "size", "last_modified_time", "sha256"]
AUDIT_ZIPFILES_CSV_FIELDNAMES = ["path", "entry_filename", "size", "sha256"]


def get_size_and_sha256(infile):
    """
    Returns the size and SHA256 checksum (as hex) of the given file.
    """
    h = hashlib.sha256()
    size = 0

    while True:
        chunk = infile.read(8192)
        if not chunk:
            break
        h.update(chunk)
        size += len(chunk)

    return (size, h.hexdigest())


def get_file_paths_under(root):
    """Generates the paths to every file under ``root``."""
    if not os.path.isdir(root):
        raise ValueError("Cannot find files under non-existent directory: %r" % root)

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if os.path.isfile(os.path.join(dirpath, f)):
                yield os.path.join(dirpath, f)


def get_existing_audit_entries():
    """
    Returns a list of all the entries already saved in ``AUDIT_CSV_PATH``.
    """
    try:
        with open(AUDIT_CSV_PATH) as infile:
            return list(csv.DictReader(infile))
    except IOError as err:
        if err.errno == errno.ENOENT:
            with open(AUDIT_CSV_PATH, "w") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=AUDIT_CSV_FIELDNAMES)
                writer.writeheader()
                return []
        else:
            raise


def get_existing_audit_zip_entries(path):
    """
    Returns a list of all the entries already saved in ``AUDIT_ZIPFILES_CSV_PATH``
    that match ``path``.
    """
    try:
        with open(AUDIT_ZIPFILES_CSV_PATH) as infile:
            return [entry for entry in csv.DictReader(infile) if entry["path"] == path]
    except IOError as err:
        if err.errno == errno.ENOENT:
            with open(AUDIT_ZIPFILES_CSV_PATH, "w") as outfile:
                writer = csv.DictWriter(
                    outfile, fieldnames=AUDIT_ZIPFILES_CSV_FIELDNAMES
                )
                writer.writeheader()
                return []
        else:
            raise


def get_paths_to_audit(root):
    """
    Generates a list of paths that should be audited.
    """
    existing_audit_paths = {e["path"] for e in get_existing_audit_entries()}

    for path in get_file_paths_under(root):

        # These files are of no consequence.  We can ignore them.
        if os.path.basename(path) in {".DS_Store", "Thumbs.db"}:
            continue

        if path in existing_audit_paths:
            continue

        yield path


def record_audit_for_zipfile_entries(path):
    """
    Record audit information for all the entries in a zipfile.
    """
    assert path.endswith(".zip")

    existing_zip_entry_names = {e["name"] for e in get_existing_audit_zip_entries(path)}

    with open(AUDIT_ZIPFILES_CSV_PATH, "a") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=AUDIT_ZIPFILES_CSV_FIELDNAMES)

        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                if info.filename in existing_zip_entry_names:
                    continue

                with zf.open(info) as entry:
                    size, sha256 = get_size_and_sha256(entry)

                writer.writerow(
                    {
                        "path": path,
                        "entry_filename": info.filename,
                        "size": size,
                        "sha256": sha256,
                    }
                )


def record_audit_for_path(path):
    """
    Record audit information for a single file.
    """
    with open(AUDIT_CSV_PATH, "a") as outfile:
        assert 0
        writer = csv.DictWriter(outfile, fieldnames=AUDIT_CSV_FIELDNAMES)

        stat = os.stat(path)

        with open(path, "rb") as infile:
            size, sha256 = get_size_and_sha256(infile)

        mtime = os.stat(path).st_mtime
        last_modified_time = datetime.datetime.fromtimestamp().isoformat()

        writer.writerow(
            {
                "path": path,
                "size": size,
                "last_modified_time": last_modified_time,
                "sha256": sha256,
            }
        )


if __name__ == "__main__":
    for path in get_paths_to_audit(root=V_DRIVE_ROOT):
        try:
            if path.endswith(".zip"):
                record_audit_for_zipfile_entries(path)

            record_audit_for_path(path)
        except Exception as exc:
            with open("exceptions.log", "a") as outfile:
                outfile.write("Exception while trying to audit %r:\n\n" % path)
                traceback.print_exc(file=outfile)
                outfile.write("\n---\n\n")
