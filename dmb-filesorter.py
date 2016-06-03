# -*- coding: utf-8 -*-

'''
(C) 2016 mixd.tv by MWG Media Wedding GmbH
All Rights Reserved.

Kristian Müller <kristian.mueller@mixd.tv>
'''
from __future__ import print_function  # make upward compatbile to python 3

import argparse
import datetime
import os  # to access files in the current directory, create directory
import shutil  # moving / copying files
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
        return False  # if not found at all we can ignore the file - thus when it's not older it wont be archived


def copy_or_move_files(file_list, start_datetime, is_simulation_run, is_moving_files):
    if is_simulation_run:
        return 0

    source_directory_name = os.path.realpath('.')
    target_directory_name = os.path.realpath(os.path.relpath(start_datetime.strftime('%Y-%m-%d')))

    # create target_directory if not already existing
    if not os.path.exists(target_directory_name):
        os.makedirs(target_directory_name)

    # move or copy files
    for file in file_list:
        if is_moving_files:
            shutil.move(os.path.join(source_directory_name, file),
                        os.path.join(target_directory_name, file))
        else:
            shutil.copyfile(os.path.join(source_directory_name, file),
                            os.path.join(target_directory_name, file))


def handle_outdated_files(start_datetime, is_simulation_run, is_moving_files):
    outdated_files = []

    print ("Will copy anything older than %s" % start_datetime)

    # get all files in current directory (excluding sub directories)
    files_in_current_directory = [f for f in os.listdir('.') if os.path.isfile(f)]
    # filter only .XML files
    files_in_current_directory = [f for f in files_in_current_directory if f.lower().endswith(".xml")]

    # check content for lastest broadcast stop time
    for xml_file in files_in_current_directory:
        # print ("file %s is older? %s" % (xml_file, is_file_containing_only_content_older_than(xml_file, start_datetime)))
        if is_file_containing_only_content_older_than(xml_file, start_datetime):
            outdated_files.append(xml_file)

    # archive older files
    print ("got %i outdated files: %s" % (len(outdated_files), outdated_files))

    copy_or_move_files(outdated_files, start_datetime, is_simulation_run, is_moving_files)


if __name__ == "__main__":
    # determine default date (2 weeks before today)
    default_start_date = datetime.date.today() - datetime.timedelta(days=14)
    default_start_date = default_start_date.strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser()
    parser.add_argument('--start-date',
                        help='Specify date for the newest alowed broadcast time in any EPG file (Format: 2016-04-16)',
                        default=default_start_date,
                        dest="start_date",
                        required=False)
    parser.add_argument('--do-not-simulate',
                        help='actually change any file - this needs to be set for anything to happen',
                        default=True,
                        required=False,
                        dest="is_simulation_run",
                        action='store_false')
    parser.add_argument('--move',
                        help='Remove outdated files from the current directory',
                        default=False,
                        required=False,
                        action='store_true')

    args = parser.parse_args()
    start_datetime = datetime.datetime.strptime(args.start_date, '%Y-%m-%d')
    is_simulation_run = args.is_simulation_run
    is_moving_files = args.move

    handle_outdated_files(start_datetime, is_simulation_run, is_moving_files)
