#!/bin/python
# -*- coding: utf-8 -*-

import urllib
import json
import time
import argparse
import httplib
import httplib2
import re

import sys
reload(sys)
sys.setdefaultencoding('utf8')

EPG_REQUEST_URL = 'http://freenettv.mixd.tv/epg/%s/15Days/?api_key=55d347a9-bb71-feae-04ba-ec5cb675d07a'
BROADCASTER_LISTING_URL = 'http://freenettv.mixd.tv/broadcasters/?api_key=55d347a9-bb71-feae-04ba-ec5cb675d07a'

images_missing = 0
images_found = 0
images_ignored = 0

isOmitExistingImages = False

def convert_to_spaceless_ascii_string(in_string):
    out = in_string.lower()
    out = out.decode("utf8")
    out = out.replace(u" ", "_")
    out = out.replace(u":", "_")
    out = out.replace(u".", "_")
    out = out.replace(u",", "_")
    out = out.replace(u";", "_")
    out = out.replace(u"/", "_")
    out = out.replace(u"ö", "oe")
    out = out.replace(u"ü", "ue")
    out = out.replace(u"ä", "ae")
    out = out.replace(u"ß", "ss")
    out = re.sub(r'\W+', '', out)  # strip averythin that's not alphanum or '_'
    return out

def get_epg_listing(broadcaster_ID):
    global images_found
    global images_missing
    global images_ignored

    if broadcaster_ID == None:
        print "Requesting Listing from", BROADCASTER_LISTING_URL
        broadcaster_listing_json = urllib.urlopen(BROADCASTER_LISTING_URL).read()
        broadcaster_listing_json = json.loads(broadcaster_listing_json)

        for broadcaster in broadcaster_listing_json['msg']:
            # print '--> Checking for missing Images of ' + broadcaster['title'].encode("ascii", "ignore") + ' (' + broadcaster['epgId'] + ')'
            print ('\n' + broadcaster['name'].encode("ascii", "ignore"))
            sys.stdout.flush()
            get_epg_listing(broadcaster['epgId'])
            # time.sleep(60 * 5)
    else:
        images_listing_json = urllib.urlopen(EPG_REQUEST_URL % broadcaster_ID).read()
        # print "Got broadcasts from", EPG_REQUEST_URL % broadcaster_ID
        images_listing_json = json.loads(images_listing_json)


    for broadcast in images_listing_json['msg']:
        if broadcast['epgBroadcastTime'] >= time.time() and broadcast.has_key('teaserImageUrl') and not isOmitExistingImages:
            # print "found " + broadcast['title'] + ' -> ' + broadcast['teaserImageUrl']
            sys.stdout.flush()

            import httplib2
            h = httplib2.Http()
            resp = h.request(broadcast['teaserImageUrl'], 'HEAD')
            if int(resp[0]['status']) != 200:
                print(broadcast['teaserImageUrl'].split('_16x9.jpg')[0].split('/')[-1])
                sys.stdout.flush()
                images_missing = images_missing + 1
            else:
                images_found = images_found + 1
                # print ("found: (%s) %s" % (int(resp[0]['status']), broadcast['teaserImageUrl']))

            server_name = broadcast['teaserImageUrl'].replace('http://', '').split('/')[0]
            # print "Server", server_name
            c = httplib.HTTPConnection(server_name)
            URI = '/' + '/'.join(broadcast['teaserImageUrl'].replace('http://', '').split('/')[1:])
            # print "URI:", URI
            c.request("HEAD", URI)
            status_code = c.getresponse().status
            if status_code == 200:
                # print('Found!')
                sys.stdout.write('.')
                sys.stdout.flush()
                pass
            else:
                print('\nMissing! ' + broadcast['teaserImageUrl'] + ' HTTP Status Code: ' + status_code)

        elif not broadcast.has_key('teaserImageUrl'):
            print "HERE-13"
            images_ignored = images_ignored + 1
        elif broadcast.has_key('teaserImageUrl'):  # and broadcast.has_key('teaserImageIsGenrePlaceholder')
            # print "==="
            # print broadcast['title']
            # print broadcast['programTypeDE']
            # print broadcast['genreDE']
            continue

            print "HERE-14"
            urllib.urlopen('http://images.mixd.tv:9756/image-genre-image/%s/%s/%s' % (broadcast['broadcastId'],
                convert_to_spaceless_ascii_string(broadcast['programTypeDE']),
                convert_to_spaceless_ascii_string(broadcast['genreDE'])))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--broadcaster_id', help='define broadcaster by ID')
    parser.add_argument('--isOmitExistingImages', help='only check for genre images (opt. can be 0 or 1)')
    args = parser.parse_args()
    isOmitExistingImages = (args.isOmitExistingImages == "1")
    print (args.isOmitExistingImages == "1")
    get_epg_listing(args.broadcaster_id)
    print "images_missing", images_missing
    print "images_found", images_found
    print "images_ignored", images_ignored
