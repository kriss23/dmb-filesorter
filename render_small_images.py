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
CONVERT_BIN = 'convert'
# smartcrop --quality 93 --width 852 --height 480 input.jpg output.jpg


def smart_crop_image(image_dir, input_filename, image_hash_filename, use_16x9=False):
    print "will crop", input_filename, 'and store it to', image_hash_filename

    if use_16x9:
        input_filename_path = os.path.join(image_dir, input_filename) + '_16x9.jpg'
    else:
        input_filename_path = os.path.join(image_dir, input_filename)
    output_filename_path = os.path.join(image_dir, image_hash_filename)

    if os.path.isfile(input_filename_path) and not os.path.isfile(output_filename_path):
        smart_crop_call = [SMARTCROP_BIN,
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

def render_small_image(image_directory, image_filename, image_hash_filename):
    # print 'image_filename: ', image_filename
    # print 'image_hash_filename: ', image_hash_filename
    # print 'image_directory: ', image_directory

    image_hash = image_hash_filename.split('.')[0]
    source_file = '/var/www/html/images/852/' + image_directory + '/' + image_hash_filename
    target_file = '/var/www/html/images/852/' + image_directory + '/' + image_hash + '_small.jpg'

    # print 'source_file: ', source_file
    # print 'target_file: ', target_file

    if '/336/' in source_file or '/broadcaster_defaults/' in source_file:
        return  # don't convert genre imgs
    
    if os.path.isfile(target_file):
        # print "already done."
        return


    # convert example.png -resize 200 example.png
    resize_call = [CONVERT_BIN,
                     source_file,
                     "-resize", "212",
                     target_file]
    print 'Running:',
    print ' '.join(resize_call),
    subprocess.call(resize_call)

    if os.path.isfile(target_file):
        print "Success"
    else:
        print "File Missing:", target_file,


def rename_to_hash(image_url):
    # print "convert from url:", image_url
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

        for broadcaster in broadcaster_listing_json['msg']:
            if broadcaster['epgId'] == 'CPY':
                omnit = False

            # CPY, LOK, 
            if broadcaster['epgId'] in ['CPY', 'LOK', 'I00', 'a00', 'MSP', 'SDI', None]:
                continue

            if omnit:
                continue
            # print '--> Checking for missing Images of ' + broadcaster['title'].encode("ascii", "ignore") + ' (' + broadcaster['epgId'] + ')'
            print ('\n' + broadcaster['name'].encode("ascii", "ignore"))
            sys.stdout.flush()
            get_epg_listing(broadcaster['epgId'], image_dir)
            # time.sleep(60 * 5)

    else:
        try:
            # print "op: " + EPG_REQUEST_URL % broadcaster_ID
            images_listing_json = urllib.urlopen(EPG_REQUEST_URL % broadcaster_ID).read()
            # print "done: ", len(images_listing_json)
        except IOError:
            print "ERROR opening ", EPG_REQUEST_URL % broadcaster_ID
            return
        # print "Got broadcasts from", EPG_REQUEST_URL % broadcaster_ID
        images_listing_json = json.loads(images_listing_json)

    print 'broadcaster id', broadcaster_ID

    if not broadcaster_ID:
        return
    
    for broadcast in images_listing_json['msg']:
        if broadcast.has_key('teaserImageUrlOld'):
            image_url = broadcast['teaserImageUrlOld']
        else:
            image_url = broadcast['teaserImageUrl']
        image_filename = get_filename_from_URL(image_url)
        image_directory = image_url.split('/')[-2]
        image_hash_filename = rename_to_hash(image_url)

        render_small_image(image_directory, image_filename, image_hash_filename)

        # return

        # if not image_filename:
        #     print 'Ignoring:', image_url
        # else:
        #     smart_crop_image(image_dir + broadcaster_ID, image_filename, image_hash_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broadcaster_id', help='define broadcaster by ID')
    parser.add_argument('--image_dir', default='.', help='directory that hold input and output files')
    args = parser.parse_args()

    get_epg_listing(args.broadcaster_id, args.image_dir)
