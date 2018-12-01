#!/bin/python
# -*- coding: utf-8 -*-

'''
(C) 2018 mixd.tv by MWG Media Wedding GmbH
All Rights Reserved.

Kristian Müller <kristian.mueller@mixd.tv>

IMPORTANT - THIS WILL LABEL SPACES AS + AND CONVERT UMLAUTS
=> run image_labler/label_gente_images.py afterwards to fix labels


'''
# from __future__ import print_function  # make upward compatbile to python 3

import sys
reload(sys)
sys.setdefaultencoding('utf8')

import urllib
import urllib2
import base64
import json
import time
import httplib
import pickle
import os
import re

from pymongo import MongoClient

client = MongoClient('localhost', 27001)

media_db = client['media_prod']
epg_raw_collections = media_db['epg_raw']

IMAGE_LIST_XML_URL = "http://portal.deutschemailbox.de/dmb/medianet/bildliste.php?sidnr=%i"
IMAGE_XML_URL = "http://portal.deutschemailbox.de/dmb/medianet/image.php?resolution=2&id=%i&xml=1"
USERNAME = "mixd3bild"
PASSWORD = "7cp9UKrj"

USED_GENRE_IDS = {}

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

def convert_to_ascii_string(in_string):
    out = in_string.lower()
    out = out.decode("utf8")
    out = out.replace(u"ö", "oe")
    out = out.replace(u"ü", "ue")
    out = out.replace(u"ä", "ae")
    out = out.replace(u"ß", "ss")
    return out

def get_main_genres():
    # main_genres = epg_raw_collections.distinct('epgProviderGenre.dmb_haupt_genre')
    return [
        u'Musik',
        u'Report',
        u'Serie',
        u'Natur+Reisen',
        u'Nachrichten',
        u'Unterhaltung',
        u'Bildung',
        u'Kinder',
        u'Kultur',
        u'Spielfilm',
        u'Talk',
        u'Sport',
        u'TV-Film',
        u'Reihe',
        u'Gesundheit',
        u'Theater',
        u'unbestimmt',
    ]

def get_sub_genres(main_genre):
    if os.path.isfile('./' + main_genre + '.pickle'):
         sub_genre_file = open('./' + main_genre + '.pickle', "rb")
         return pickle.load(sub_genre_file)
    else:
        sub_genres = epg_raw_collections.distinct('epgProviderGenre.dmb_neben_genre', {
            'epgProviderGenre.dmb_haupt_genre': main_genre
        })
        sub_genre_file = open(main_genre + '.pickle', "wb")
        pickle.dump(sub_genres, sub_genre_file)
        return sub_genres

def get_genre_image_id(broadcast_id):
    url = IMAGE_LIST_XML_URL % int(broadcast_id)
    # print 'URL:', url

    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)
    try:
        broadcast_image_xml = urllib2.urlopen(request).read()
    except urllib2.HTTPError:
        return None

    for line in broadcast_image_xml.split('\n'):
        if '<idpic art="genre">' in line:
            genre_id = line.split('<idpic art="genre">')[1].split('</idpic>')[0]
            # print broadcast_image_xml
            return genre_id

    return None

def check_image_id(genre_image_id, item_id):
    check_url = IMAGE_XML_URL % genre_image_id

    if genre_image_id in USED_GENRE_IDS.keys():
        print '.',
        return USED_GENRE_IDS[genre_image_id]

    request = urllib2.Request(check_url)
    base64string = base64.b64encode('%s:%s' % (USERNAME, PASSWORD))
    request.add_header("Authorization", "Basic %s" % base64string)
    try:
        broadcast_image_xml = urllib2.urlopen(request).read()
    except urllib2.HTTPError:
        return None

    if len(broadcast_image_xml) <= 0:
        USED_GENRE_IDS[genre_image_id] = False
        print 'ignoreing unusable img ID', genre_image_id, 'for source', item_id,
        return False
    else:
        USED_GENRE_IDS[genre_image_id] = True
        return True

    return None

def update_genre_image(main_genre, sub_genre):
    print '======'
    print main_genre, ' + ', sub_genre + ':',
    image_id = None
    items = epg_raw_collections.find({
        'epgProviderGenre.dmb_haupt_genre': main_genre,
        'epgProviderGenre.dmb_neben_genre': sub_genre,
        'epgBroadcastTime': {'$gt': (int(time.time()-100000))}  # must be a current epg entry for the dmb api to return results
    })
    for item in items:
        if not item:
            print 'no current Broadcast found.'
            return

        image_id = get_genre_image_id(item['epgSourceId'])
        if image_id != None and check_image_id(int(image_id), item['epgSourceId']) == False:
            image_id = None
        if image_id != None:
            if item.has_key('title'):
                print item['title']
            else:
                print 'missing titel for', item['epgSourceId']
            break

    if image_id == None:
        return

    ###### download genre image ##############
    download_genre_img_url = 'http://images.mixd.tv:9756/image-genre-image/%s/%s/%s' % (image_id,
        convert_to_spaceless_ascii_string(main_genre),
        convert_to_spaceless_ascii_string(sub_genre))

    print "===> requesting Genre Image via:", download_genre_img_url
    urllib.urlopen(download_genre_img_url).read()

    GENRE_IMAGE_URL = 'http://images.mixd.tv/images/852/'
    IMAGE_LABLER_URL = 'http://images.mixd.tv:9756/image-import/%s/%s/%s/v_2'

    subGenreString_lower = convert_to_spaceless_ascii_string(sub_genre)
    mainGenreString_lower = convert_to_spaceless_ascii_string(main_genre)
    filename =  main_genre + '_' + sub_genre
    filename = convert_to_spaceless_ascii_string(filename)
    image_url = GENRE_IMAGE_URL + filename + '.jpg'

    ###### Label genre image ################
    labler_url = IMAGE_LABLER_URL % (
        urllib.quote_plus(image_url.encode('raw_unicode_escape')),
        urllib.quote_plus(convert_to_ascii_string(sub_genre)),
        mainGenreString_lower + '_und_' + subGenreString_lower
    )
    print "===> triggering labeler with: ", labler_url
    urllib.urlopen(labler_url).read()

def update_genre_images():
    main_genres = get_main_genres()

    for main_genre in main_genres:
        sub_genres = get_sub_genres(main_genre)
        for sub_genre in sub_genres:
            update_genre_image(main_genre, sub_genre)

if __name__ == '__main__':
    update_genre_images()
