# -*- coding: utf-8 -*-

'''
(C) 2016 mixd.tv by MWG Media Wedding GmbH
All Rights Reserved.

Kristian Müller <kristian.mueller@mixd.tv>
'''
from __future__ import print_function  # make upward compatbile to python 3

import argparse
import datetime
import os  # to access files in the current directory
import sys


def is_file_containing_only_content_older_than(xml_file, start_datetime):
    found_timestamp = False
    is_older = False
    newest_broadcast_stop_time = datetime.date.today() - datetime.timedelta(days=99)
    newest_broadcast_stop_time = datetime.datetime(newest_broadcast_stop_time.year,
                                                   newest_broadcast_stop_time.month,
                                                   newest_broadcast_stop_time.day)

    # print ("    Accessing file: %s" % xml_file)
    with open(xml_file) as file_handle:
        lines_string = file_handle.readlines()
        for line_string in lines_string:
            if "<stop>" in line_string and "</stop>" in line_string:
                broadcast_stop_time_string = line_string.split('<stop>')[1].split('</stop>')[0]
                broadcast_stop_time = datetime.datetime.strptime(broadcast_stop_time_string, '%Y-%m-%dT%H:%M:%S')
                if broadcast_stop_time > newest_broadcast_stop_time:
                    newest_broadcast_stop_time = broadcast_stop_time
                    found_timestamp = True
                # print ("        broadcast_stop_time: %s" % broadcast_stop_time)

    if found_timestamp:
        # print ("        found newest broadcast to end at: %s" % newest_broadcast_stop_time)
        return newest_broadcast_stop_time < start_datetime
    else:
        return false  # if not found at all we can ignore the file


def copy_old_files(start_datetime):
    outdated_files = []

    print ("Will copy anything older than %s" % start_datetime)

    # get all files in current directory (excluding sub directories)
    files_in_current_directory = [f for f in os.listdir('.') if os.path.isfile(f)]
    # filter only .XML files
    files_in_current_directory = [f for f in files_in_current_directory if f.lower().endswith(".xml")]

    # check content for lastest broadcast stop time
    for xml_file in files_in_current_directory:
        print ("file %s is older? %s" % (xml_file, is_file_containing_only_content_older_than(xml_file, start_datetime)))
        if is_file_containing_only_content_older_than(xml_file, start_datetime):
            outdated_files.append(xml_file)

    print ("got %i outdated files: %s" % (len(outdated_files), outdated_files))

if __name__ == "__main__":
    # determine default date (2 weeks before today)
    default_start_date = datetime.date.today() - datetime.timedelta(days=14)
    default_start_date = default_start_date.strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser()
    parser.add_argument('--start_date',
                        help='Specify date for the newest alowed broadcast time in any EPG file (Format: 2016-04-16)',
                        default=default_start_date,
                        required=False)
    args = parser.parse_args()
    start_datetime = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')

    copy_old_files(start_datetime)
