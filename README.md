# EPG Data File Management: Archive Outdated XML Files from dmb GmbH Deutsche Mailbox

Tool to make sure that data uploaded by the EPG data provider "dmb GmbH Deutsche Mailbox" is only kept
until is getting older than e.g. one week.

This prevents the XML upload directory from getting overcrowded with outdated EPG data.

## Usage
```
git clone <repo>
cp dmb-filesorter/dmb-filesorter.py ./
python dmb-filesorter.py --do-not-simulate
```

## Options
Use `dmb-filesorter --do-not-simulate --start_date <START_DATE>` to copy all files containing broadcasts older that
START_DATE into a subfolder with the name START_DATE (e.g. 2016-04-16).
If --start_date is left out the script defaults to today-14 days.

Use `dmb-filesorter --do-not-simulate --move` to move all outdated files into the subfolder.


## Ideas for Future Features
- Option for compression
- Option to Restore from a list of (compressed) subfolders
