#!/bin/python
# -*- coding: utf-8 -*-

import urllib
import json
import argparse
import subprocess
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

EPG_REQUEST_URL = 'http://freenettv.mixd.tv/epg/%s/15Days/?api_key=d57cb0b3-19a5-5383-bb58-a6c9d3e8ab92&format=json'
BROADCASTER_LISTING_URL = 'http://freenettv.mixd.tv/broadcasters/?api_key=55d347a9-bb71-feae-04ba-ec5cb675d07a'
SMARTCROP_BIN = 'smartcrop'
# smartcrop --quality 93 --width 852 --height 480 input.jpg output.jpg
# --faceDetection --quality 93
done_list = []


def smart_crop_image(image_dir, input_filename, image_hash_filename, use_16x9=False):
    print "will crop", input_filename, 'and store it to', image_hash_filename
    global done_list
    
    if use_16x9:
        input_filename_path = os.path.join(image_dir, input_filename) + '_16x9.jpg'
    else:
        input_filename_path = os.path.join(image_dir, input_filename)
    output_filename_path = os.path.join(image_dir, image_hash_filename)

    if os.path.isfile(input_filename_path) and output_filename_path not in done_list and not os.path.isfile(output_filename_path):
        done_list.append(output_filename_path)
        smart_crop_call = [SMARTCROP_BIN,
                         "--faceDetection",
                         "--quality", "93",
                         "--width", "852",
                         "--height", "480",
                         "--minScale", "1.0",
                         input_filename_path,
                         output_filename_path]
        print 'Running:',
        print ' '.join(smart_crop_call)

        # render output image
        subprocess.call(smart_crop_call)

    if os.path.isfile(output_filename_path):
        print "Success"
    elif not use_16x9:
        print "File Missing:", output_filename_path,
        print "retrying with 16/9 version"
        smart_crop_image(image_dir, input_filename, image_hash_filename, use_16x9=True)

    print 'CALLING:',

def rename_to_hash(image_url):
    print "convert from url:", image_url
    if len(image_url.split('_')) >= 4:
        filename = image_url.split('_')[3] + '.jpg'
    else:
        filename = image_url
    # print "converted to filename:", filename
    return filename

def get_filename_from_URL(image_url):
    # print "getting from url:", image_url
    if len(image_url.split('/')) >= 1 and image_url.split('/')[-1].endswith('_16x9.jpg'):
        filename = image_url.split('/')[-1].split('_16x9.jpg')[0]
    else:
        return None
    # print "got filename:", filename
    return filename


def get_epg_listing(broadcaster_ID, image_dir):
    if broadcaster_ID == None:
        print "Requesting Listing from", BROADCASTER_LISTING_URL
        broadcaster_listing_json = urllib.urlopen(BROADCASTER_LISTING_URL).read()
        broadcaster_listing_json = json.loads(broadcaster_listing_json)
        omnit = False

        broadcaster_list = broadcaster_listing_json['msg']
        broadcaster_list.append({
            'epgId': 'ZDH',
            'name': 'ZDF HD'
        })
        for broadcaster in broadcaster_list:
            if broadcaster['epgId'] == 'ARD':
                omnit = False

            #if broadcaster['epgId'] == 'ARD':
            #    continue

            if omnit:
                continue
            # print '--> Checking for missing Images of ' + broadcaster['title'].encode("ascii", "ignore") + ' (' + broadcaster['epgId'] + ')'
            print ('\n' + broadcaster['name'].encode("ascii", "ignore"))
            sys.stdout.flush()
            get_epg_listing(broadcaster['epgId'], image_dir)
            # time.sleep(60 * 5)
        images_listing_json = {}  # init as emty dict
    else:
        try:
            # print "op: " + EPG_REQUEST_URL % broadcaster_ID
            images_listing_json = urllib.urlopen(EPG_REQUEST_URL % broadcaster_ID).read()
            # print "done: ", len(images_listing_json)
        except IOError:
            print "ERROR opening ", EPG_REQUEST_URL % broadcaster_ID
            return
        # print "Got broadcasts from", EPG_REQUEST_URL % broadcaster_ID
        try:
            images_listing_json = json.loads(images_listing_json)
        except ValueError:
            images_listing_json = {
                'msg': []
            }

    if not images_listing_json or not images_listing_json.has_key('msg'):
        print 'Ignoring missing data from:', broadcaster_ID
        return
        
    for broadcast in images_listing_json['msg']:
        if broadcast.has_key('teaserImageUrlOld'):
            image_url = broadcast['teaserImageUrlOld']
        else:
            image_url = broadcast['teaserImageUrl']
        image_filename = get_filename_from_URL(image_url)
        image_hash_filename = rename_to_hash(image_url)
        print 'broadcaster id', broadcaster_ID
        if not image_filename:
            print 'Ignoring:', image_url
        else:
            smart_crop_image(image_dir + broadcaster_ID, image_filename, image_hash_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broadcaster_id', help='define broadcaster by ID')
    parser.add_argument('--image_dir', default='.', help='directory that hold input and output files')
    args = parser.parse_args()

    get_epg_listing(args.broadcaster_id, args.image_dir)
