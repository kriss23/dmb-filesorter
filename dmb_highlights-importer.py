# -*- coding: utf-8 -*-

'''
(C) 2018 mixd.tv by MWG Media Wedding GmbH
All Rights Reserved.

Kristian Müller <kristian.mueller@mixd.tv>
'''
from __future__ import print_function  # make upward compatbile to python 3

import argparse
import datetime
import os  # to access files in the current directory, create directory
import sys
import pprint

from pymongo import MongoClient

#client = MongoClient('localhost', 27001)
client = MongoClient('primary.db.mixd.tv', 27017)

media_db = client['media_prod']
highlights_collections = media_db['highlights']
ratings_collections = media_db['ratings']


def get_highlights(xml_string):
    highlights_dict = {}
    if '<highlights' in xml_string:
        highlights_string = xml_string.split('<highlights')[1].split('</highlights>')[0]
        highlights_string = '">'.join(highlights_string.split('">')[1:])
        # print (highlights_string)

        highlights = highlights_string.split('<highlight ')
        for highlight in highlights:
            if 'id="' in highlight:
                highlight_id = highlight.split('id="')[1].split('"')[0]
                broadcast_id = highlight.split('ausstrahlung="')[1].split('"')[0]
                highlights_dict[highlight_id] = broadcast_id
    return highlights_dict

def get_ratings(xml_string):
    ratings_dict = {}
    #if '<ratings' in xml_string:
    #    ratings_string = xml_string.split('<ratings')[1].split('</ratings>')[0]

    ratings = []

    if '<ratings' in xml_string or '<dmbext:ratings' in xml_string:
        # if '<ratings' in xml_string:
        #     ratings_string = xml_string.split('<ratings')[1].split('</ratings>')[0]
        if '<dmbext:ratings' in xml_string:
            ratings_string = xml_string.split('<dmbext:ratings')
            for rating_string in ratings_string:
                if 'dmbext:werk_rating' in rating_string:
                    ratings.append(rating_string.split('</dmbext:ratings')[0])
                else:
                    continue

                ratings = rating_string.split('<dmbext:werk_rating ')

                for rating in ratings:
                    if 'werk_id="' in rating:
                        title = rating.split('werk_titel="')[1].split('"')[0]
                        creative_work_id = rating.split('werk_id="')[1].split('"')[0]
                        # broadcast_id = rating.split('<ausstrahlung dmbext:id="')[1].split('"')[0]
                        broadcast_id = rating.split('ausstrahlung dmbext:id="')[1].split('"')[0]
                        genre_ratings = {}
                        for genre_rating in rating.split('dmbext:ratingTyp="'):
                            if 'dmbext:ratingValue="' in genre_rating:
                                rating_type = genre_rating.split('"')[0]
                                rating_value = genre_rating.split('dmbext:ratingValue="')[1].split('"')[0]
                                genre_ratings[rating_type] = rating_value

                        ratings_dict[broadcast_id] = {
                            'title': title,
                            'creative_work_id': creative_work_id,
                            'genre_ratings': genre_ratings
                        }
    #pprint.pprint(ratings_dict)
    return ratings_dict

def save_highlights(highlights):
    for highlight in highlights:
        sys.stdout.write('.')
        sys.stdout.flush()
        # print (highlight, highlights[highlight])
        upsert_result = highlights_collections.update_one({'_id': highlight}, {'$set': {'broadcast_id': highlights[highlight]}}, upsert=True)

def save_ratings(ratings):
    for rating in ratings:
        #print (rating, ratings[rating])
        sys.stdout.write('+')
        sys.stdout.flush()
        upsert_result = ratings_collections.update_one({'_id': rating}, {'$set': {
            'genre_ratings': ratings[rating]['genre_ratings'],
            'creative_work_id': ratings[rating]['creative_work_id'],
            'xml_title': ratings[rating]['title']
        }}, upsert=True)

def handle_highlight_files():
    # get all files in current directory (excluding sub directories)
    files_in_current_directory = [f for f in os.listdir('.') if os.path.isfile(f)]
    # filter only .XML files
    files_in_current_directory = [f for f in files_in_current_directory if f.lower().endswith(".xml")]

    # check content for highlights info
    for xml_file in files_in_current_directory:
        # print()
        print('handling', xml_file)

        with open(xml_file) as xml_file_handle:
            xml_string = xml_file_handle.read()
            highlights = get_highlights(xml_string)
            save_highlights(highlights)
            # print ('highlights', highlights)
            ratings = get_ratings(xml_string)
            save_ratings(ratings)

            import pprint
            #pprint.pprint (ratings)


if __name__ == "__main__":
    # determine default date (2 weeks before today)
    default_start_date = datetime.date.today() - datetime.timedelta(days=14)
    default_start_date = default_start_date.strftime('%Y-%m-%d')

    parser = argparse.ArgumentParser()

    handle_highlight_files()
