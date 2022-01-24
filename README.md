# file_auditor

This is a script for auditing the files in a directory.

In particular, it creates a spreadsheet that records the path, size, SHA256 checksum and last modified date of every file in the directory.
Additionally, if the file is a [zip archive], it records these attributes both for the zip as a whole *and* the individual entries in the zip.

The output is a CSV with rows something like:

<table>
  <tr>
    <th>path</th>
    <th>size</th>
    <th>last_modified_time</th>
    <th>sha256</th>
  </tr>
  <tr>
    <td>files/greeting.rtf</td>
    <td>380</td>
    <td>2021-11-23T12:10:23</td>
    <td>083257fa6f484b36b809ddd3e74e5b90eb7ce948220268f7fb15bc5f3fb25632</td>
  </tr>
  <tr>
    <td>files/test.dmg</td>
    <td>1114112</td>
    <td>2021-11-23T12:16:10</td>
    <td>5e59137961d5e14a903af3f1597fcf24bb6bd1880b6324bbe1821ecf50d7eb94</td>
  </tr>
  <tr>
    <td>files/medicine/Paracetamol.pdf</td>
    <td>48200</td>
    <td>2020-05-07T15:42:05</td>
    <td>cea68134752b8a3f78cf5c6d89fa113af74fe6031927d5070d59d1933fb44885</td>
  </tr>
</table>

[zip archive]: https://en.wikipedia.org/wiki/ZIP_(file_format)



## Motivation

We have an on-premise file share, from which some of the files have been uploaded to S3 and our [cloud storage service] -- but not all of them.
This script will allow us to match files in the share to files in the storage service, and determine what can be safely deleted from the on-premise share.

[cloud storage service]: https://github.com/wellcomecollection/storage-service



## Usage

Download the script `run.py` from this repo, then run the script, passing the path to the directory you want to audit, e.g.:

```console
$ python2 run.py /Volumes/wdl_born_digital
```

This will create two spreadsheets in the local directory:

-   `audit.csv` lists individual files
-   `audit_with_zipfile_entries.csv` lists the individual entries in zip files, if found



## Features

*   The script is designed to run for long periods unattended.
    If there's an issue auditing a single file, the exception is logged to a file for later inspection -- rather than interrupting the whole script.

*   The script runs incrementally.
    If it's interrupted and resumed later, it picks up where it left off -- skipping files it's already checked.

*   The script is designed to run with the builtin Python 2.7 in macOS.
    This means it can run on any Mac, even if we don't have root access/the ability to install extra software.



## Remote monitoring

I'm running this script on a headless Mac mini connected to the wired network, which is in Wellcome's office.
So I can get the results while working from home, I have another terminal window open, uploading the results to S3:

```bash
while true; do echo $(date); aws s3 cp audit.csv s3://my-s3-bucket/audit.csv; sleep 300; done
```
