#!/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2  # for basic auth
import json
import argparse
import base64

import sys
reload(sys)
sys.setdefaultencoding('utf8')

EPG_REQUEST_URL = 'http://freenettv.mixd.tv/epg/%s/15Days/?api_key=d57cb0b3-19a5-5383-bb58-a6c9d3e8ab92&format=json'

# DMB image server
IMAGE_XML_URL = "http://portal.deutschemailbox.de/dmb/medianet/image.php?resolution=2&sidnr=%i&xml=1"
IMAGE_DOWNLOAD_URL = "http://portal.deutschemailbox.de/dmb/medianet/image.php?resolution=2&id=%i"
USERNAME = "mixd3bild"
PASSWORD = "7cp9UKrj"


def get_images_for_broadcast(broadcast_id):
    print('getting images for broadcast: %s via %s' % (broadcast_id, IMAGE_XML_URL % int(broadcast_id)))

    url = IMAGE_XML_URL % int(broadcast_id)
    # print 'URL:', url

    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header( "Authorization", "Basic %s" % base64string)
    try:
        broadcast_image_xml = urllib2.urlopen(request).read()
    except urllib2.HTTPError:
        print 'error 1'
        return None

    print('====')
    print(broadcast_image_xml)
    print('====')

    image_id = broadcast_image_xml.split('<BILDID>')[1].split('</BILDID>')[0]
    image_filename = broadcast_image_xml.split('<NAME>')[1].split('</NAME>')[0]
    print('ID is %s' % image_id)
    print('Filename is %s' % image_filename)

    # IMAGE_DOWNLOAD_URL
    image_url = IMAGE_DOWNLOAD_URL % int(image_id)
    request = urllib2.Request(image_url)
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header( "Authorization", "Basic %s" % base64string)
    try:
        broadcast_image = urllib2.urlopen(request).read()
    except urllib2.HTTPError:
        print 'error 1'
        return None

    print('Writing %d Bytes to file <%s>' % (len(broadcast_image), image_filename))
    with open(image_filename, 'wb') as tmp_file:
        tmp_file.write(broadcast_image)


def check_for_missing_images(broadcaster_id):
    print('check_for_missing_images on url: %s' % EPG_REQUEST_URL % broadcaster_id)

    try:
        images_listing_json = urllib.urlopen(EPG_REQUEST_URL % broadcaster_id).read()
        print "done: ", len(images_listing_json)
    except IOError:
        print "ERROR opening ", EPG_REQUEST_URL % broadcaster_id
        return

    print "Got broadcasts from", EPG_REQUEST_URL % broadcaster_id
    images_listing_json = json.loads(images_listing_json)

    already_checked = []
    for broadcast in images_listing_json['msg']:
        if broadcast.has_key('imageList'):
            for image_url in broadcast['imageList']:
                if image_url in already_checked:
                    continue
                already_checked.append(image_url)
                # print('checking for %s' % image_url)
                image_handle = urllib.urlopen(image_url)
                if image_handle.getcode() != 200:
                    print('missing image %s (HTTP Error: %d) - EPG_ID: %s' % (image_url, image_handle.getcode(), broadcast['broadcastId']))
                    get_images_for_broadcast(broadcast['broadcastId'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broadcaster_id', help='define broadcaster by ID')
    args = parser.parse_args()

    check_for_missing_images(args.broadcaster_id)
    #get_images_for_broadcast('1034811771')
