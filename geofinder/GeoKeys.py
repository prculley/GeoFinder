#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#  Copyright (c) 2019.       Mike Herbert
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
import collections
import os
import re

import phonetics
import unidecode


class Entry:
    NAME = 0
    ISO = 1
    ADM1 = 2
    ADM2 = 3
    LAT = 4
    LON = 5
    FEAT = 6
    ID = 7
    SDX = 8
    PREFIX = 8  # Note - item 8 is overloaded with Soundex in DB and Prefix for result
    SCORE = 9
    MAX = 9
    POP = 14


class Result:
    # Result codes for lookup
    STRONG_MATCH = 8
    MULTIPLE_MATCHES = 7
    PARTIAL_MATCH = 6
    WILDCARD_MATCH = 5
    SOUNDEX_MATCH = 4
    DELETE = 3
    NO_COUNTRY = 2
    NO_MATCH = 1
    NOT_SUPPORTED = 0


# Result types that are successful matches
successful_match = [Result.STRONG_MATCH, Result.PARTIAL_MATCH, Result.WILDCARD_MATCH, Result.SOUNDEX_MATCH, Result.MULTIPLE_MATCHES]

Query = collections.namedtuple('Query', 'where args result')


def get_soundex(txt):
    res = phonetics.dmetaphone(txt)
    return res[0]

def get_directory_name() -> str:
    return "geoname_data"

def get_cache_directory(dirname):
    """ Return the directory for cache files """
    return os.path.join(dirname, "cache")

def remove_noise_words(res):
    # Calculate score with noise word removal
    # inp = re.sub('shire', '', inp)

    # Clean up odd case for Normandy American cemetery having only English spelling
    res = re.sub(r"normandy american ", 'normandie american ', res)
    """
    res = re.sub(r' county', ' ', res)
    res = re.sub(r' stadt', ' ', res)
    res = re.sub(r' departement', ' ', res)
    res = re.sub(r'regierungsbezirk ', ' ', res)
    res = re.sub(r' departement', ' ', res)
    res = re.sub(r'gemeente ', ' ', res)
    res = re.sub(r'provincia ', ' ', res)
    res = re.sub(r'provincie ', ' ', res)
    """

    res = re.sub(r'nouveau brunswick', ' ', res)

    res = re.sub(r' de ', ' ', res)
    res = re.sub(r' di ', ' ', res)

    res = re.sub(r' du ', ' ', res)
    res = re.sub(r' of ', ' ', res)
    res = re.sub(r'city of ', ' ', res)

    res = re.sub(r"politischer bezirk ", ' ', res)
    return res

def lowercase_match_group(matchobj):
        return matchobj.group().lower()

def capwords(nm):
    if nm is not None:
        # Use title(), then fix the title() apostrophe defect
        nm = nm.title()

        # Fix handling for contractions not handled correctly by title()
        poss_regex = r"(?<=[a-z])[\']([A-Z])"
        nm = re.sub(poss_regex, lowercase_match_group, nm)

    return nm

def normalize_match_title(full_title:str, iso:str)->str:
    # Normalize the title we use to determine how close a match we got
    full_title = search_normalize(full_title, iso)
    full_title = remove_noise_words(full_title)
    full_title = re.sub(', ', ',', full_title)
    return full_title

def search_normalize(res, iso)->str:
    res = semi_normalize(res)
    return res

def admin1_normalize(res, iso):
    #res = re.sub(r"'", '', res)  # Normalize hyphens
    if iso == 'de':
        res = re.sub(r'bayern', 'bavaria', res)

    if iso == 'fr':
        res = re.sub(r'normandy', 'normandie', res)
        res = re.sub(r'brittany', 'bretagne', res)

        res = re.sub(r'burgundy', 'bourgogne franche comte', res)
        res = re.sub(r'franche comte', 'bourgogne franche comte', res)
        res = re.sub(r'aquitaine', 'nouvelle aquitaine', res)
        res = re.sub(r'limousin', 'nouvelle aquitaine', res)
        res = re.sub(r'poitou charentes', 'nouvelle aquitaine', res)
        res = re.sub(r'alsace', 'grand est', res)
        res = re.sub(r'champagne ardenne', 'grand est', res)
        res = re.sub(r'lorraine', 'grand est', res)
        res = re.sub(r'languedoc roussillon', 'occitanie', res)
        res = re.sub(r'midi pyrenees', 'occitanie', res)
        res = re.sub(r'nord pas de calais', 'hauts de france', res)
        res = re.sub(r'picardy', 'hauts de france', res)
        res = re.sub(r'auvergne', 'auvergne rhone alpes', res)
        res = re.sub(r'rhone alpes', 'auvergne rhone alpes', res)

    return res

def admin2_normalize(res, iso)->(str, bool):
    """
    Some English counties have had Shire removed from name, try doing that
    :param res:
    :return: (result, modified)
    result - new string
    modified - True if modified
    """
    mod = False
    #if 'shire' in res:
    #    res = re.sub('shire', '', res)
    #   mod = True

    if iso == 'gb':
        res = re.sub(r'middlesex', ' ', res)
        res = re.sub(r'breconshire', 'sir powys', res)
        mod = True

    return res, mod

def country_normalize(res)->(str,bool):
    """
    normalize local language Country name to standardized English country name for lookups
    :param res:
    :return: (result, modified)
    result - new string
    modified - True if modified
    """
    res = re.sub(r'\.', '', res)  # remove .

    natural_names = {
    'norge': 'norway',
    'sverige': 'sweden',
    'osterreich' : 'austria',
    'belgie' : 'belgium',
    'brasil' : 'brazil',
    'danmark' : 'denmark',
    'magyarorszag' : 'hungary',
    'italia' : 'italy',
    'espana' : 'spain',
    'deutschland' : 'germany',
    'prussia' : 'germany',
    'suisse' : 'switzerland',
    'schweiz' : 'switzerland',

    }
    if natural_names.get(res):
        res = natural_names.get(res)
        return res, True
    else:
        return res, False

def _phrase_normalize(res) -> str:
    """ Strip spaces and normalize spelling for items such as Saint and County """
    # Replacement patterns to clean up entries
    res = re.sub('r.k. |r k ', 'rooms katholieke ',res)
    res = re.sub('saints |sainte |sint |saint |sankt |st. ', 'st ', res)  # Normalize Saint
    res = re.sub(r' co\.', ' county', res)  # Normalize County
    res = re.sub(r'united states', 'usa', res)  # Normalize USA
    res = re.sub(r'town of ', ' ', res)  # Normalize

    if 'amt' not in res:
        res = re.sub(r'^mt ', 'mount ', res)

    res = re.sub('  +', ' ', res)  # Strip multiple space
    res = re.sub('county of ([^,]+)', r'\g<1> county', res)  # Normalize 'Township of X' to 'X Township'
    res = re.sub('township of ([^,]+)', r'\g<1> township', res)  # Normalize 'Township of X' to 'X Township'
    res = re.sub('cathedral of ([^,]+)', r'\g<1> cathedral', res)  # Normalize 'Township of X' to 'X Township'
    return res


def normalize(res) -> str:
    """ Strip commas. Also strip spaces and normalize spelling for items such as Saint and County and chars   ø ß """

    # Convert UT8 to ascii
    res = unidecode.unidecode(res)

    res = str(res).lower()

    # remove all punctuation
    res = re.sub(r"[^a-zA-Z0-9 $.*']+", " ", res)

    res = _phrase_normalize(res)
    return res.strip(' ')


def semi_normalize(res) -> str:
    """ Do NOT Strip commas.  strip spaces and normalize spelling for items such as Saint and County and chars   ø ß """

    # Convert UT8 to ascii
    res = unidecode.unidecode(res)

    res = str(res).lower()

    # remove all punctuation
    res = re.sub(r"[^a-zA-Z0-9 $*,']+", " ", res)

    res = _phrase_normalize(res)
    return res.strip(' ')


type_names = {
    "CH": 'Church',
    "CSTL": 'Castle',
    "CMTY": 'Cemetery',
    "EST": 'Estate',
    "HSP": 'Hospital',
    "HSTS": 'Historical',
    "ISL": 'Island',
    "MT": 'Mountain',
    "MUS": 'Museum',
    "PAL": 'Palace',
    "PRK": 'Park',
    "PRN": 'Prison',
    "RUIN": 'Ruin',
    "SQR": 'Square',
    "VAL": 'Valley',
    "ADM1": 'State',
    "ADM2": 'County',
    "ADM3": 'Township',
    "ADM4": 'Township',
    "PPL": 'City',
    "PPLA": 'City',
    "PPLA2": 'City',
    "PPLA3": 'City',
    "PPLA4": 'City',
    "PPLC": 'City',
    "PPLG": 'City',
    "PPLH": 'City',
    "PPLL": 'Village',
    "PPLQ": 'Historical',
    "PPLX": 'Neighborhood'
}
