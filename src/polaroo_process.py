"""
polaroo_process.py
--------------------

This module defines a helper function to process usage data exported from
Polaroo and compute over‑usage ("extra") charges for electricity and
water.  The function can read a local CSV file or a publicly accessible
remote URL, skip any summary section prior to the actual header (the
header line starts with ``name;``), filter the rows to a list of
specified flats or buildings, convert cost columns to numeric values,
and calculate extra charges based on user‑defined allowances.

Typical usage involves downloading the Polaroo CSV (either via your
scraper or manually), defining a list of flats/buildings to include,
and then calling :func:`process_usage` with the path to that CSV and the
desired allowances.  The resulting DataFrame can be written to an
Excel file by providing an ``output_path``.

Example::

    from polaroo_process import process_usage

    # List of flats or buildings to include (only the street names are
    # used for filtering).  For example, to include all units at
    # ARIBAU 126 and PADILLA 260 you can use:
    filter_addresses = [
        "ARIBAU 126",
        "PADILLA 260",
        # ...add other street names as needed...
    ]

    df = process_usage(
        usage_path="/path/to/polaro_report.csv",
        allowances={'electricity': 100.0, 'water': 50.0},
        delimiter=';',
        decimal=',',
        addresses=filter_addresses,
        output_path="/path/to/xl.xlsx",
    )

The ``addresses`` parameter is optional; if omitted, all rows from the
CSV will be processed.  When provided, it should be a list of
human‑readable strings identifying flats or buildings (e.g.
"ARIBAU 126 1*2").  Only the first token (typically the street name)
is used to filter the data.  See the documentation of
``process_usage`` for further details.
"""

from __future__ import annotations

import io
import urllib.request
import unicodedata
import re
from pathlib import Path
from typing import Dict, Iterable, Optional

import pandas as pd

# ---------------------------------------------------------------------------
# User configuration
# ---------------------------------------------------------------------------
#
# The following list defines the exact flats (addresses) to include in the
# over‑usage calculation.  Each entry should correspond to one flat in the
# ``name`` column of the Polaroo CSV.  You can adjust this list as needed
# without having to specify addresses on the command line.  If the
# ``addresses`` argument to :func:`process_usage` is omitted or set to
# ``None``, this list will be used by default.

# Room-based allowance limits
ROOM_LIMITS = {
    1: 50,   # 1 room: €50
    2: 70,   # 2 room: €70  
    3: 100,  # 3 room: €100
    4: 130,  # 4 room: €130
}

# Special limits for specific addresses
SPECIAL_LIMITS = {
    "Padilla 1º 3ª": 150,  # Only Padilla 1º 3ª: €150
}

# Address to room mapping - Updated based on Excel sheet data
ADDRESS_ROOM_MAPPING = {
    # Aribau properties - Updated from Excel data
    "Aribau 1º 1ª": 1,
    "Aribau 1º 2ª": 1,
    "Aribau 2º 1º": 1,
    "Aribau 2º 2º": 3,
    "Aribau 2º 3ª": 1,
    "Aribau 126-128 3-1": 3,  # Excel shows empty, keeping current value
    "Aribau 3º 2ª": 3,
    "Aribau 4º 1ª": 3,
    "Aribau 4º 1ª B": 2,
    "Aribau 4º 2ª": 3,
    "Aribau Escalera": 1,
    
    # Bisbe Laguarda properties - Updated from Excel data
    "Bisbe Laguarda 14, Pral-2": 3,
    "Bisbe Laguarda 14, 2-2": 3,
    
    # Blasco de Garay properties - Updated from Excel data
    "Blasco de Garay Pral 1ª": 3,
    "Blasco de Garay Pral 2ª": 3,
    "Blasco de Garay 1º 1ª": 3,
    "Blasco de Garay 1º-2": 2,
    "Blasco de Garay 2º 1ª": 3,
    "Blasco de Garay 2º 2ª": 3,
    "Blasco de Garay 3º 1ª": 3,
    "Blasco de Garay 3º 2ª": 3,
    "Blasco de Garay 4º 1ª": 3,
    "Blasco de Garay 5º 1ª": 1,
    
    # Comte Borrell properties - Updated from Excel data
    "Comte Borrell Pral 1ª": 3,
    "Comte Borrell 5º 1ª": 1,
    "Comte Borrell 5º 2ª": 1,
    
    # Llull 250 properties - Updated from Excel data
    "Llull 250 Pral 3": 2,
    "Llull 250 Pral 5": 2,
    "Llull 250 1-1": 2,
    "Llull 250 1-3": 2,
    "Llull 250 1-4": 2,
    "Llull 250 1-5": 2,
    "Llull 250 1-6": 2,
    "Llull 250 2-3": 2,
    "Llull 250 2-5": 2,
    "Llull 250 2-6": 2,
    "Llull 250 3-2": 2,
    "Llull 250 3-4": 2,
    "Llull 250 3-5": 2,
    "Llull 250 3-6": 2,
    "Llull 250 4-3": 2,
    "Llull 250 4-5": 2,
    "Llull 250 5-1": 2,
    "Llull 250 5-2": 2,
    "Llull 250 5-3": 2,
    "Llull 250 5-4": 2,
    "Llull 250 5-5": 2,
    
    # Padilla properties - Updated from Excel data
    "Padilla 1º 1ª": 3,  # Excel shows 3 rooms
    "Padilla 1º 2ª": 3,  # Excel shows 3 rooms
    "Padilla 1º 3ª": 3,  # Excel shows 3 rooms, but special limit €150 applies
    "Padilla Entl 1ª": 1,  # From book1 image
    "Padilla Entl 2ª": 1,  # From book1 image
    "Padilla Entl 4ª": 1,  # From book1 image
    "Padilla Pral 2ª": 1,  # From book1 image
    "Padilla Pral 3ª": 1,  # From book1 image
    "Padilla 2º 1ª": 1,  # From book1 image
    "Padilla 2-2": 1,  # From book1 image
    "Padilla 2º 3ª": 1,  # From book1 image
    "Padilla 2-4": 1,  # From book1 image
    "Padilla 3º 2ª": 1,  # From book1 image
    "Padilla 3º 3ª": 1,  # From book1 image
    "Padilla 4º 2ª": 1,  # From book1 image
    "Padilla 4º 3ª": 1,  # From book1 image
    "Padilla 5º 1ª": 1,  # From book1 image
    "Padilla 5º 2ª": 1,  # From book1 image
    
    # Psg Sant Joan properties - From book1 image
    "Psg Sant Joan Entl 1ª": 1,
    "Psg Sant Joan Entl 2ª": 1,
    "Psg Sant Joan Pral 1ª": 1,
    "Psg Sant Joan Pral 2ª": 1,
    "Psg Sant Joan 1º 1ª": 1,
    "Pg Sant Joan 161 2-1": 1,
    "Pg Sant Joan 161 2-2": 1,
    "Psg Sant Joan 3º 2ª": 1,
    "Pg Sant Joan 4-1": 1,
    "Psg Sant Joan 4º 2ª": 1,
    "Psg Sant Joan 5º 2ª": 1,
    
    # Providencia properties - From book1 image
    "Providencia Bajs 2ª": 2,
    "Providencia Pral 2ª": 2,
    "Providencia 1º 1ª": 1,
    "Providencia 1º 2ª": 1,
    "Providencia 2º 1ª": 1,
    "Providencia 2º 2ª": 1,
    "Providencia 3º 2ª": 1,
    "Providencia 4º 2ª": 1,
    
    # Sardenya properties - From book1 image
    "Sardenya 1º 2ª": 2,
    "Sardenya 3º 2ª": 2,
    "Sardenya 4º 2ª": 2,
    "Sardenya 5º 2ª": 2,
    "Sardenya Pral": 1,
    
    # Torrent Olla properties - From book1 image
    "Torrent Olla Pral 1ª": 1,
    "Torrent Olla 1º 1ª": 1,
    "Torrent Olla 1º 2ª": 1,
    "Torrent Olla 2º 1ª": 1,
    "Torrent Olla 2º 2ª": 1,
    "Torrent Olla 3º 2ª": 1,
    "Torrent Olla Ático": 1,
    
    # Valencia properties - From book1 image
    "Valencia Pral 1ª": 1,
    "Valencia 2º 1ª": 1,
}

USER_ADDRESSES: list[str] = [
    # Aribau properties (10)
    "Aribau 1º 1ª",
    "Aribau 1º 2ª",
    "Aribau 2º 1º",
    "Aribau 2º 2º",
    "Aribau 2º 3ª",
    "Aribau 126-128 3-1",
    "Aribau 3º 2ª",
    "Aribau 4º 1ª",
    "Aribau 4º 1ª B",
    "Aribau 4º 2ª",
    
    # Bisbe Laguarda properties (2)
    "Bisbe Laguarda 14, Pral-2",
    "Bisbe Laguarda 14, 2-2",

    # Blasco de Garay properties (10)
    "Blasco de Garay Pral 1ª",
    "Blasco de Garay Pral 2ª",
    "Blasco de Garay 1º 1ª",
    "Blasco de Garay 1º-2",
    "Blasco de Garay 2º 1ª",
    "Blasco de Garay 2º 2ª",
    "Blasco de Garay 3º 1ª",
    "Blasco de Garay 3º 2ª",
    "Blasco de Garay 4º 1ª",
    "Blasco de Garay 5º 1ª",

    # Comte Borrell properties (3)
    "Comte Borrell Pral 1ª",
    "Comte Borrell 5º 1ª",
    "Comte Borrell 5º 2ª",

    # Llull 250 properties (21)
    "Llull 250 Pral 3",
    "Llull 250 Pral 5",
    "Llull 250 1-1",
    "Llull 250 1-3",
    "Llull 250 1-4",
    "Llull 250 1-5",
    "Llull 250 1-6",
    "Llull 250 2-3",
    "Llull 250 2-5",
    "Llull 250 2-6",
    "Llull 250 3-2",
    "Llull 250 3-4",
    "Llull 250 3-5",
    "Llull 250 3-6",
    "Llull 250 4-3",
    "Llull 250 4-5",
    "Llull 250 5-1",
    "Llull 250 5-2",
    "Llull 250 5-3",
    "Llull 250 5-4",
    "Llull 250 5-5",
    
    # Padilla properties (18)
    "Padilla Entl 1ª",
    "Padilla Entl 2ª",
    "Padilla Entl 4ª",
    "Padilla Pral 2ª",
    "Padilla Pral 3ª",
    "Padilla 1º 1ª",
    "Padilla 1º 2ª",
    "Padilla 1º 3ª",
    "Padilla 2º 1ª",
    "Padilla 2-2",
    "Padilla 2º 3ª",
    "Padilla 2-4",
    "Padilla 3º 2ª",
    "Padilla 3º 3ª",
    "Padilla 4º 2ª",
    "Padilla 4º 3ª",
    "Padilla 5º 1ª",
    "Padilla 5º 2ª",
    
    # Psg Sant Joan properties (11)
    "Psg Sant Joan Entl 1ª",
    "Psg Sant Joan Entl 2ª",
    "Psg Sant Joan Pral 1ª",
    "Psg Sant Joan Pral 2ª",
    "Psg Sant Joan 1º 1ª",
    "Pg Sant Joan 161 2-1",
    "Pg Sant Joan 161 2-2",
    "Psg Sant Joan 3º 2ª",
    "Pg Sant Joan 4-1",
    "Psg Sant Joan 4º 2ª",
    "Psg Sant Joan 5º 2ª",
    
    # Providencia properties (8)
    "Providencia Bajs 2ª",
    "Providencia Pral 2ª",
    "Providencia 1º 1ª",
    "Providencia 1º 2ª",
    "Providencia 2º 1ª",
    "Providencia 2º 2ª",
    "Providencia 3º 2ª",
    "Providencia 4º 2ª",
    
    # Sardenya properties (5)
    "Sardenya 1º 2ª",
    "Sardenya 3º 2ª",
    "Sardenya 4º 2ª",
    "Sardenya 5º 2ª",
    "Sardenya Pral",
    
    # Torrent Olla properties (7)
    "Torrent Olla Pral 1ª",
    "Torrent Olla 1º 1ª",
    "Torrent Olla 1º 2ª",
    "Torrent Olla 2º 1ª",
    "Torrent Olla 2º 2ª",
    "Torrent Olla 3º 2ª",
    "Torrent Olla Ático",
    
    # Valencia properties (2)
    "Valencia Pral 1ª",
    "Valencia 2º 1ª",
]

def get_allowance_for_address(address: str) -> float:
    """
    Get the allowance limit for a specific address based on room count or special limits.
    
    Parameters
    ----------
    address : str
        The address to look up
        
    Returns
    -------
    float
        The allowance limit in euros
    """
    # Check for exact special limits first
    if address in SPECIAL_LIMITS:
        return SPECIAL_LIMITS[address]
    
    # Check room-based mapping
    if address in ADDRESS_ROOM_MAPPING:
        room_count = ADDRESS_ROOM_MAPPING[address]
        return ROOM_LIMITS.get(room_count, 50)  # Default to €50 if room count not found
    
    # Default fallback
    return 50.0


# Synonyms mapping from user building keys to dataset building keys.  Some
# buildings are referred to differently in the dataset (e.g. "Comte Borrell"
# corresponds to user input "Borrell").  This mapping ensures that the
# correct dataset rows are matched when filtering by flat.  You can extend
# this dictionary if additional buildings require custom mapping.
_SYNONYMS: dict[str, list[str]] = {
    'ARIBAU': ['ARIBAU'],
    'BLASCO': ['BLASCOGARAY'],
    'GARAY': ['BLASCOGARAY'],
    'BORRELL': ['COMTEBORRELL'],
    'COMTE': ['COMTEBORRELL'],
    'TORRENT': ['TORRENTOLLA'],
    'OLLA': ['TORRENTOLLA'],
    'PROVIDENCIA': ['PROVIDENCIA'],
    'SARDENYA': ['SARDENYA'],
    'PADILLA': ['PADILLA'],
    'VALENCIA': ['VALENCIA'],
}


# ---------------------------------------------------------------------------
# Name parsing helpers
# ---------------------------------------------------------------------------

def _normalize_tokens(s: str) -> str:
    """Normalize a string by removing accents and non‑alphanumeric characters.

    Parameters
    ----------
    s : str
        Input string.

    Returns
    -------
    str
        Uppercase string containing only letters and digits.
    """
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if c.isalnum()).upper()


def _base_code(code: str) -> str:
    """Return the base floor code without trailing letter (if present).

    Examples
    --------
    >>> _base_code('4-1-A')
    '4-1'
    >>> _base_code('PRAL-1')
    'PRAL-1'
    >>> _base_code('5-2')
    '5-2'
    """
    if not code:
        return ''
    parts = code.split('-')
    if len(parts) >= 2 and parts[-1].isalpha():
        return '-'.join(parts[:-1])
    return code


def _parse_floor_dataset(tokens: list[str]) -> str:
    """Parse the floor code from a sequence of tokens for dataset names.

    The function scans the tokens for patterns indicating the floor and
    apartment number.  It recognises special floor words (PRAL, ENTL,
    BAJO, ATICO) with optional numeric suffix, hyphen‑delimited patterns
    like ``3-2``, and ordinal patterns like ``4º 1ª``.  If multiple
    patterns are present, the last one is taken (to avoid confusion
    with building numbers such as "126-128").  Building numbers (e.g.
    "126") and connector words (DE, DEL, etc.) are ignored.

    Parameters
    ----------
    tokens : list of str
        Tokens from the part of the address suspected to contain floor
        information.

    Returns
    -------
    str
        A standardised floor code such as ``'4-1'``, ``'PRAL-1'``,
        ``'ENTL-2'``, or ``''`` if no floor information is detected.
    """
    floor_code = ''
    i = 0
    n = len(tokens)
    while i < n:
        token_orig = tokens[i]
        t = unicodedata.normalize('NFD', token_orig).upper()
        # Check for special floor words
        matched = False
        for variant, code in [
            ('PRINCIPAL', 'PRAL'),
            ('PRAL', 'PRAL'),
            ('ENTRESUELO', 'ENTL'),
            ('ENTL', 'ENTL'),
            ('BAJO', 'BAJO'),
            ('BJO', 'BAJO'),
            ('ATICO', 'ATICO'),
            ('ÁTICO', 'ATICO'),
            ('ATIC', 'ATICO'),
        ]:
            if t.startswith(variant):
                rest = t[len(variant):].lstrip('- ')
                apt = None
                if rest:
                    rest_clean = re.sub('[ºª\\.]', '', rest)
                    if rest_clean:
                        apt = rest_clean
                else:
                    # Check next token for apartment number/letter
                    if i + 1 < n:
                        next_tok = unicodedata.normalize('NFD', tokens[i + 1]).upper()
                        next_clean = re.sub('[ºª\\.]', '', next_tok)
                        if next_clean and (next_clean.isdigit() or re.fullmatch(r'[A-Z]', next_clean)):
                            apt = next_clean
                            i += 1
                floor_code = f"{code}-{apt}" if apt else code
                matched = True
                break
        if matched:
            i += 1
            continue
        # Handle hyphen patterns like '3-2' or '4-1A'
        t_clean = t.replace('º', '').replace('ª', '')
        m = re.fullmatch(r'([0-9]{1,2})[-]([0-9A-Za-z]{1,2})', t_clean)
        if m:
            floor, apt = m.groups()
            if len(floor) <= 2 and len(apt) <= 2:
                floor_code = f"{floor}-{apt}"
        else:
            # Ordinal pattern like '4º' optionally followed by apartment number/letter
            m2 = re.fullmatch(r'([0-9]{1,2})[ºª]?', t)
            if m2:
                floor = m2.group(1)
                apt = None
                if i + 1 < n:
                    next_tok = unicodedata.normalize('NFD', tokens[i + 1]).upper()
                    next_clean = re.sub('[ºª\\.]', '', next_tok)
                    if next_clean and (next_clean.isdigit() or re.fullmatch(r'[A-Z]', next_clean)):
                        apt = next_clean
                        i += 1
                floor_code = f"{floor}-{apt}" if apt else floor
        i += 1
    return floor_code


def _parse_name_dataset(name: str) -> tuple[str, str]:
    """Extract the building key and floor code from a dataset address.

    Parameters
    ----------
    name : str
        Full address string from the Polaroo CSV.

    Returns
    -------
    (str, str)
        ``(building_key, floor_code)`` where ``building_key`` is a
        normalised alphanumeric string representing the building and
        ``floor_code`` is a standardised code for the floor/apartment.
    """
    norm = unicodedata.normalize('NFD', name)
    tokens = norm.split()
    building_tokens: list[str] = []
    floor_tokens: list[str] = []
    found_floor = False
    for token in tokens:
        t = unicodedata.normalize('NFD', token).upper()
        if not found_floor:
            # Detect start of floor part (digits, hyphen, ordinal, or special words)
            if (re.search(r'[0-9]', t) or '-' in t or 'º' in t or 'ª' in t or
                any(t.startswith(w) for w in ['PRAL', 'PRINCIPAL', 'ENTL', 'ENTRESUELO', 'BAJO', 'BJO', 'ATICO', 'ÁTICO', 'ATIC'])):
                found_floor = True
                floor_tokens.append(token)
            else:
                # Skip connectors
                if t not in ['DE', 'DEL', 'DA', 'D', 'Y', 'LA', 'LAS', 'LOS', 'AL', 'EL']:
                    building_tokens.append(token)
        else:
            floor_tokens.append(token)
    building_key = _normalize_tokens(' '.join(building_tokens))
    floor_code = _parse_floor_dataset(floor_tokens)
    return building_key, floor_code


def _parse_floor_user(floor_tokens: list[str]) -> str:
    """Parse a user‑provided floor code from floor tokens.

    This helper interprets patterns like ``1*2``, ``1-2``, ``3º 1ª``,
    ``Principal 1``, ``Entresuelo 2`` or ``Atico`` into a standardised
    code.  Building numbers are ignored.  If no floor information is
    detected, an empty string is returned.

    Parameters
    ----------
    floor_tokens : list of str
        Tokens representing the floor portion of a user address.  These
        tokens are assumed to have been identified by
        ``_parse_name_user``.

    Returns
    -------
    str
        Standard floor code such as ``'3-1'``, ``'PRAL-2'``, ``'ENTL-1'``,
        ``'BAJO'``, ``'ATICO'``, or ``''``.
    """
    if not floor_tokens:
        return ''
    # Replace '*' with '-' to normalise star patterns
    tokens = [t.replace('*', '-') for t in floor_tokens]
    s = ' '.join(tokens)
    s_norm = unicodedata.normalize('NFD', s).upper()
    # Remove accents for pattern matching
    s_basic = ''.join(c for c in unicodedata.normalize('NFKD', s_norm) if not unicodedata.combining(c))
    # Check for special floor words first
    for variant, code in [
        ('PRINCIPAL', 'PRAL'),
        ('PRAL', 'PRAL'),
        ('ENTRESUELO', 'ENTL'),
        ('ENTL', 'ENTL'),
        ('BAJO', 'BAJO'),
        ('BJO', 'BAJO'),
        ('ATICO', 'ATICO'),
        ('ATIC', 'ATICO'),
        ('ÁTICO', 'ATICO'),
    ]:
        m = re.search(rf'{variant}\s*-?\s*([0-9A-Z]{{1,2}})?', s_basic)
        if m:
            apt = m.group(1)
            return f"{code}-{apt}" if apt else code
    # Hyphen pattern like '3-2' or '3-1A'
    m = re.search(r'([0-9]{1,2})\s*-\s*([0-9A-Z]{1,2})', s_basic)
    if m:
        floor, apt = m.groups()
        return f"{floor}-{apt}"
    # Ordinal or plain numeric pattern: extract first two alphanumeric tokens
    s_clean = s_basic.replace('º', '').replace('ª', '')
    parts = re.findall(r'([0-9]{1,2}|[A-Z])', s_clean)
    if parts:
        floor = parts[0]
        apt = parts[1] if len(parts) > 1 else None
        return f"{floor}-{apt}" if apt else floor
    return ''


def _parse_name_user(addr: str) -> tuple[str, str]:
    """Parse a user address into building key and floor code.

    Building numbers (e.g. ``126``, ``147``) are ignored.  The floor
    portion starts at the first token containing a digit, an ordinal
    symbol, a hyphen or star, or one of the special floor words.  All
    tokens prior to that are considered part of the building name.

    Parameters
    ----------
    addr : str
        Human‑readable flat identifier provided by the user.

    Returns
    -------
    (str, str)
        Normalised ``(building_key, floor_code)``.
    """
    norm = unicodedata.normalize('NFD', addr)
    tokens = norm.split()
    building_tokens: list[str] = []
    floor_tokens: list[str] = []
    found_floor = False
    for token in tokens:
        t_upper = unicodedata.normalize('NFD', token).upper()
        if not found_floor:
            # Identify the beginning of the floor portion
            if ('*' in t_upper or '-' in t_upper or 'º' in t_upper or 'ª' in t_upper or
                any(t_upper.startswith(w) for w in ['PRAL', 'PRINCIPAL', 'ENTRESUELO', 'ENTL', 'BAJO', 'BJO', 'ATICO', 'ÁTICO', 'ATIC']) or
                t_upper.isdigit()):
                # If token is purely digits, assume it's a building number and skip it
                if t_upper.isdigit() and not any(c in t_upper for c in ['*', '-', 'º', 'ª']):
                    # skip building number
                    continue
                found_floor = True
                floor_tokens.append(token)
            else:
                if t_upper not in ['DE', 'DEL', 'DA', 'D', 'Y', 'LA', 'LAS', 'LOS', 'AL', 'EL']:
                    building_tokens.append(token)
        else:
            floor_tokens.append(token)
    building_key = _normalize_tokens(' '.join(building_tokens))
    floor_code = _parse_floor_user(floor_tokens)
    return building_key, floor_code



def _sanitize(text: str) -> str:
    """Normalize a string by removing accents and converting to uppercase."""
    nfkd = unicodedata.normalize('NFKD', text)
    no_acc = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return no_acc.upper()


def _read_polaro_file(path: str | Path, *, delimiter: str, decimal: str) -> pd.DataFrame:
    """Load a Polaroo usage file (CSV or Excel), skipping any preamble before the header.

    Polaroo exports typically include a few summary lines before the
    actual data header.  This helper reads the file (either from a
    local path or URL), identifies the header row, and then parses
    the remainder with the appropriate method.

    Parameters
    ----------
    path : str or Path
        Local filesystem path or URL pointing to the file.  URLs
        must be publicly accessible (no authorization headers).
    delimiter : str
        The column delimiter used in CSV files (e.g. ';' for Polaroo exports).
    decimal : str
        The decimal separator used in numeric fields (e.g. ',' for Polaroo exports).

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing all columns from the file.  Numeric
        columns are not converted at this stage.
    """
    path_str = str(path)
    
    # Check if it's an Excel file
    if path_str.lower().endswith(('.xlsx', '.xls')):
        # Handle Excel files
        if path_str.startswith(('http://', 'https://')):
            # Download Excel file from URL
            with urllib.request.urlopen(path_str) as resp:
                excel_data = resp.read()
            df = pd.read_excel(io.BytesIO(excel_data), engine='openpyxl')
        else:
            # Read local Excel file
            df = pd.read_excel(path, engine='openpyxl')
        
        # Simple detection: scan column A for 'name' and use that row as header
        header_index = None
        
        print(f"🔍 [EXCEL] Scanning column A for 'name' in {len(df)} rows...")
        
        for idx, row in df.iterrows():
            # Check if column A (first column) contains 'name'
            first_cell = str(row.iloc[0]).lower().strip() if len(row) > 0 and pd.notna(row.iloc[0]) else ""
            if first_cell == 'name':
                header_index = idx
                print(f"✅ [EXCEL] Found 'name' in column A at row {idx}")
                break
        
        if header_index is None:
            print(f"⚠️ [EXCEL] No 'name' found in column A, using default header (row 0)")
            header_index = 0
        
        if header_index is not None and header_index > 0:
            # Manually set header and delete everything before the 'name' row
            print(f"🔍 [EXCEL] Found 'name' at row {header_index}, deleting everything before it...")
            
            # Get the header row (the row with 'name')
            header_row = df.iloc[header_index]
            print(f"🔍 [EXCEL] Header row values: {list(header_row)}")
            
            # Clean and set column names from the header row
            clean_headers = []
            for i, val in enumerate(header_row):
                if pd.isna(val) or str(val).strip() == '':
                    clean_headers.append(f'Column_{i}')
                else:
                    clean_headers.append(str(val).strip())
            
            print(f"🔍 [EXCEL] Clean headers: {clean_headers}")
            df.columns = clean_headers
            
            # Delete everything before and including the header row
            df = df.iloc[header_index + 1:].reset_index(drop=True)
            
            print(f"🔍 [EXCEL] After transformation, columns: {list(df.columns)}")
            print(f"🔍 [EXCEL] First few rows after transformation:")
            print(df.head().to_string())
        
        return df
    
    else:
        # Handle CSV files (original logic)
        if path_str.startswith(('http://', 'https://')):
            with urllib.request.urlopen(path_str) as resp:
                raw = resp.read().decode('utf-8')
        else:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                raw = f.read()

        lines = raw.splitlines()
        header_index: Optional[int] = None
        for idx, line in enumerate(lines):
            if line.lower().startswith('name;'):
                header_index = idx
                break
        if header_index is None:
            raise ValueError("Unable to locate the header row starting with 'name;' in the provided CSV.")
        csv_content = '\n'.join(lines[header_index:])
        # Parse using pandas
        df = pd.read_csv(io.StringIO(csv_content), sep=delimiter, decimal=decimal, on_bad_lines='skip')
        return df


def process_usage(
    usage_path: str | Path,
    *,
    output_path: Optional[str | Path] = None,
    allowances: Optional[Dict[str, float]] = None,
    delimiter: str = ';',
    decimal: str = ',',
    addresses: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Read and process a Polaroo usage CSV, returning over‑usage details.

    This function reads the Polaroo CSV from a local file or a public URL,
    extracts the building and floor information from each row in order to
    match against a predefined list of flats, computes over‑usage costs
    based on user allowances, and returns a tidy DataFrame ready for
    export.  If ``addresses`` is not provided, the predefined
    :data:`USER_ADDRESSES` list is used.

    Parameters
    ----------
    usage_path : str or Path
        Path or URL to the Polaroo usage CSV file.  For remote URLs
        the file must be publicly accessible without authentication.
    output_path : str or Path, optional
        If provided, the processed DataFrame will be written to this
        Excel file.  Parent directories are created if necessary.
    allowances : dict, optional
        Mapping of service names to allowed cost thresholds.  Keys
        ``'electricity'`` and ``'water'`` are expected; missing keys
        default to zero.  If ``allowances`` is None or empty, no
        allowances are applied and the extra equals the cost.
    delimiter : str, optional
        Column delimiter used in the CSV.  Polaroo files typically use
        ``';'``.
    decimal : str, optional
        Character used to denote the decimal part in numeric fields.
        Polaroo files typically use ``,``, which will be converted
        appropriately.
    addresses : iterable of str, optional
        List of flat identifiers to include.  If ``None``, the
        predefined :data:`USER_ADDRESSES` is used.  Each address
        should correspond to a flat in the dataset; the parsing logic
        extracts building and floor codes for matching.

    Returns
    -------
    pandas.DataFrame
        A DataFrame with the following columns:

        - ``unit``: full address from the CSV (renamed from ``name``)
        - ``water_provider``: water provider (string or NaN)
        - ``electricity_provider``: electricity provider (string or NaN)
        - ``elec_code``: electricity contract code (string or NaN)
        - ``water_code``: water contract code (string or NaN)
        - ``service_owner``: service owner (electricity or water) if available
        - ``electricity_cost``: electricity cost (float)
        - ``water_cost``: water cost (float)
        - ``elec_extra``: over‑usage electricity cost (float)
        - ``water_extra``: over‑usage water cost (float)
    """
    # Determine addresses to filter by
    if not addresses:
        flat_addresses = USER_ADDRESSES
    else:
        flat_addresses = list(addresses)

    # Read the file (CSV or Excel) into a DataFrame
    usage_df = _read_polaro_file(usage_path, delimiter=delimiter, decimal=decimal)

    # Parse each dataset name into building key and floor code
    bkeys: list[str] = []
    fcodes: list[str] = []
    base_codes: list[str] = []
    letters: list[Optional[str]] = []
    # Debug: Check what columns are available
    print(f"🔍 [DEBUG] Available columns: {list(usage_df.columns)}")
    print(f"🔍 [DEBUG] Looking for 'name' column...")
    
    # Try different possible column names for the name column
    name_column = None
    for col_name in ['name', 'Name', 'NAME', 'unit', 'Unit', 'UNIT']:
        if col_name in usage_df.columns:
            name_column = col_name
            print(f"✅ [DEBUG] Found name column: '{col_name}'")
            break
    
    if name_column is None:
        print(f"❌ [DEBUG] No name column found! Available columns: {list(usage_df.columns)}")
        raise ValueError(f"No 'name' column found in DataFrame. Available columns: {list(usage_df.columns)}")
    
    # Debug: Show what's actually in the name column
    print(f"🔍 [DEBUG] Name column '{name_column}' contains {len(usage_df)} values")
    print(f"🔍 [DEBUG] First 10 values in name column: {list(usage_df[name_column].head(10))}")
    
    for name in usage_df[name_column].astype(str):
        bkey, fcode = _parse_name_dataset(name)
        bkeys.append(bkey)
        fcodes.append(fcode)
        base = _base_code(fcode)
        base_codes.append(base)
        # extract letter if present
        letter = None
        parts = fcode.split('-') if fcode else []
        if len(parts) >= 2 and parts[-1].isalpha():
            letter = parts[-1]
        letters.append(letter)
    usage_df['_building_key'] = bkeys
    usage_df['_floor_code'] = fcodes
    usage_df['_base_code'] = base_codes
    usage_df['_letter'] = letters

    # Process ALL properties from the Excel file (no filtering)
    print(f"🔍 [PROCESSING] Processing ALL {len(usage_df)} properties from Excel file...")
    
    # Use all data instead of filtering
    filtered_df = usage_df.copy()

    # Ensure cost columns are numeric
    for cost_col in ['electricityCost', 'waterCost']:
        if cost_col in filtered_df.columns:
            print(f"🔍 [DEBUG] Converting {cost_col} to numeric...")
            print(f"🔍 [DEBUG] First 5 values before conversion: {list(filtered_df[cost_col].head())}")
            filtered_df[cost_col] = pd.to_numeric(filtered_df[cost_col], errors='coerce').fillna(0.0)
            print(f"🔍 [DEBUG] First 5 values after conversion: {list(filtered_df[cost_col].head())}")
        else:
            print(f"⚠️ [DEBUG] Column {cost_col} not found, setting to 0.0")
            filtered_df[cost_col] = 0.0

    # Select the first available service owner (prefer electricity, then water)
    if 'electricityServiceOwner' in filtered_df.columns or 'waterServiceOwner' in filtered_df.columns:
        so_elec = filtered_df.get('electricityServiceOwner', pd.Series([pd.NA] * len(filtered_df)))
        so_water = filtered_df.get('waterServiceOwner', pd.Series([pd.NA] * len(filtered_df)))
        filtered_df['service_owner'] = so_elec.fillna(so_water)
    else:
        filtered_df['service_owner'] = pd.NA

    # Compute extra charges using room-based allowances
    allowances_list = []
    total_costs = []
    total_extras = []
    elec_extras = []
    water_extras = []
    
    for _, row in filtered_df.iterrows():
        unit_name = row[name_column]  # Use the detected name column
        
        # Get allowance for this specific address
        allowance = get_allowance_for_address(unit_name)
        allowances_list.append(allowance)
        
        # Calculate costs
        elec_cost = row.get('electricityCost', 0.0)
        water_cost = row.get('waterCost', 0.0)
        
        total_cost = elec_cost + water_cost
        
        # Calculate total extra only (when combined cost exceeds allowance)
        total_extra = max(0.0, total_cost - allowance)
        
        total_costs.append(total_cost)
        total_extras.append(total_extra)
        elec_extras.append(0.0)  # No individual elec extra
        water_extras.append(0.0)  # No individual water extra
    
    filtered_df['allowance'] = allowances_list
    filtered_df['total_cost'] = total_costs
    filtered_df['total_extra'] = total_extras
    filtered_df['elec_extra'] = elec_extras
    filtered_df['water_extra'] = water_extras

    # Rename columns to user‑friendly names
    rename_map = {
        name_column: 'Property',  # Use the detected name column
        'waterProvider': 'water_provider',
        'electricityProvider': 'electricity_provider',
        'electricityCode': 'elec_code',
        'waterCode': 'water_code',
        'electricityCost': 'Electricity Cost',
        'waterCost': 'Water Cost',
    }
    for orig, new in rename_map.items():
        if orig in filtered_df.columns:
            filtered_df.rename(columns={orig: new}, inplace=True)
        else:
            filtered_df[new] = pd.NA

    # Rename allowance column
    filtered_df.rename(columns={'allowance': 'Allowance'}, inplace=True)
    filtered_df.rename(columns={'total_cost': 'Total Cost'}, inplace=True)
    filtered_df.rename(columns={'total_extra': 'Total Extra'}, inplace=True)

    # Debug: Show what's in the DataFrame before final selection
    print(f"🔍 [DEBUG] DataFrame before final selection has {len(filtered_df)} rows")
    print(f"🔍 [DEBUG] Available columns: {list(filtered_df.columns)}")
    print(f"🔍 [DEBUG] First 3 rows of key columns:")
    key_cols = ['Property', 'Allowance', 'Electricity Cost', 'Water Cost', 'Total Cost', 'Total Extra', 'elec_extra', 'water_extra']
    for col in key_cols:
        if col in filtered_df.columns:
            print(f"  {col}: {list(filtered_df[col].head(3))}")
        else:
            print(f"  {col}: COLUMN NOT FOUND")
    
    # Debug: Show the actual Property column values
    if 'Property' in filtered_df.columns:
        print(f"🔍 [DEBUG] Property column values (first 5): {list(filtered_df['Property'].head(5))}")
    else:
        print(f"❌ [DEBUG] Property column not found!")
    
    # Select final columns in the exact order requested
    final_columns = [
        'Property',
        'Allowance', 
        'Electricity Cost',
        'Water Cost',
        'Total Cost',
        'Total Extra',
        'elec_extra',
        'water_extra',
    ]
    final_df = filtered_df[final_columns].copy()
    
    # Sort alphabetically by Property name
    final_df = final_df.sort_values('Property').reset_index(drop=True)
    
    print(f"🔍 [DEBUG] Final DataFrame has {len(final_df)} rows")
    print(f"🔍 [DEBUG] Final DataFrame first 3 rows:")
    print(final_df.head(3).to_string())

    # Write to Excel if requested
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_excel(out_path, index=False)

    return final_df


if __name__ == '__main__':  # pragma: no cover
    import argparse

    parser = argparse.ArgumentParser(description='Process Polaroo usage data to compute over‑usage charges.')
    parser.add_argument('usage_path', help='Local path or public URL to the usage CSV file.')
    parser.add_argument('-o', '--output', dest='output_path', help='Path to save the processed Excel file.')
    parser.add_argument('--elec-allowance', type=float, default=0.0, help='Allowed electricity cost before extra charges are incurred.')
    parser.add_argument('--water-allowance', type=float, default=0.0, help='Allowed water cost before extra charges are incurred.')
    parser.add_argument('--delimiter', type=str, default=';', help="Delimiter used in the CSV file (default ';').")
    parser.add_argument('--decimal', type=str, default=',', help="Decimal separator used in the CSV file (default ',').")
    parser.add_argument(
        '--addresses',
        nargs='*',
        help=(
            'Optional list of flat identifiers to filter by.  If omitted, '
            'the built‑in USER_ADDRESSES list is used.  Each address should '
            'correspond to a specific flat (e.g. "ARIBAU 126 1*2").'
        ),
    )

    args = parser.parse_args()
    allowances = {
        'electricity': args.elec_allowance,
        'water': args.water_allowance,
    }
    df = process_usage(
        usage_path=args.usage_path,
        output_path=args.output_path,
        allowances=allowances,
        delimiter=args.delimiter,
        decimal=args.decimal,
        addresses=args.addresses,
    )
    print(f"Processed {len(df)} records. Preview:")
    print(df.head())