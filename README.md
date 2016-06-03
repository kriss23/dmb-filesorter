# Deutsche Mailbox dmb File Sorter

Toot to make sure that data uploaded by the EPG data provider "dmb GmbH Deutsche Mailbox" is only kept
until is getting older than 1 Week.

This prevents the XML upload directory from getting overcrowded with outdated EPG data.

## Setup
```
git co <repo>
```

## Usage
Use `dmb-filesorter <START_DATE>` to copy all files containing broadcasts older that START_DATE
into a subfolder called START_DATE.
