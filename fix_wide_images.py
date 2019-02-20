#!/bin/python
# -*- coding: utf-8 -*-

import urllib
import json
import argparse
import subprocess
import shutil
import os
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from PIL import Image

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
        filename = image_url.split('/')[-1] # .split('_16x9.jpg')[0]
        # return None
    # print "got filename:", filename
    return filename

def increase_image_height(input_filename_path, output_filename_path, width, height):
    if os.path.isfile(input_filename_path): # and not os.path.isfile(output_filename_path):
        convert_call = [CONVERT_BIN,
                         input_filename_path,
                         "-resize", str(width) + 'x' + str(height),
                         "-background", "white",
                         "-gravity", "center",
                         "-extent", str(width) + 'x' + str(height),
                         output_filename_path]

        print 'Running:',
        print ' '.join(convert_call)

        # render output image
        subprocess.call(convert_call)



def get_epg_listing(broadcaster_ID, image_dir):
    if broadcaster_ID == None:
        print "Requesting Listing from", BROADCASTER_LISTING_URL
        broadcaster_listing_json = urllib.urlopen(BROADCASTER_LISTING_URL).read()
        broadcaster_listing_json = json.loads(broadcaster_listing_json)
        omnit = False

        for broadcaster in broadcaster_listing_json['msg']:
            if broadcaster['epgId'] == 'LOK':
                omnit = False

            if broadcaster['epgId'] == 'LOK':
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

    for broadcast in images_listing_json['msg']:
        #
        # # MOCK
        # if True:
        #     broadcast = {
        #         'teaserImageUrl': 'http://images2.mixd.tv/images/852/ARD/846f152f.jpg',
        #     }
        #     broadcaster_ID = 'ARD'
        #     # END MOCK

        image_url = broadcast['teaserImageUrl']
        print 'image_url', image_url
        image_filename = get_filename_from_URL(image_url)
        print 'image_filename', image_filename
        image_path = './orig/' + broadcaster_ID + '/' + image_filename
        target_image_path = './852/' + broadcaster_ID + '/' + image_filename
        target_image_path_tmp = './852/' + broadcaster_ID + '/' + image_filename + '_temp'

        if not os.path.isfile(image_path):
            continue

        image_handle = Image.open(image_path)
        width, height = image_handle.size

        print 'width: %d, height: %s' % (width, height)

        aspect_ratio = float(width) / float(height)

        print 'aspect_ratio', aspect_ratio

        if aspect_ratio > 1.8:
            print 'increasing image height to 16/9 aspect ratio for:', image_filename
            new_height = int(float(width) / (16. / 9))
            print 'new_height', new_height

            if os.path.isfile(image_path):
                shutil.copy(image_path, image_path + '_pre.jpg')

            increase_image_height(image_path, image_path, width, new_height)
            if os.path.isfile(target_image_path):
                shutil.move(target_image_path, target_image_path_tmp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broadcaster_id', help='define broadcaster by ID')
    parser.add_argument('--image_dir', default='.', help='directory that hold input and output files')
    args = parser.parse_args()

    get_epg_listing(args.broadcaster_id, args.image_dir)
