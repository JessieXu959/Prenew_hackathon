"""Import PRENEW collaboration CSV exports without inventing measured evidence."""
import csv
import hashlib
import io
import re
from datetime import datetime, timezone
from pathlib import Path

HEADERS = ['Creator key','Market','Country','Creator / channel','Agency','Year-week','Platform','Niche / content','YT subscribers','YT views / video','TikTok followers','TikTok views / video']

def read_rows(text):
    text = text.lstrip('\ufeff')
    first = text.splitlines()[0] if text.splitlines() else ''
    delimiter = ';' if first.count(';') > first.count(',') else ','
    return csv.DictReader(io.StringIO(text), delimiter=delimiter, strict=True)

def import_prenew(text, filename):
    reader = read_rows(text)
    normalized = {h.strip().casefold():h for h in reader.fieldnames or []}
    if 'creator / channel' not in normalized or 'creator key' not in normalized:
        return None
    missing = [h for h in HEADERS if h.casefold() not in normalized]
    if missing:
        raise ValueError('Missing PRENEW headers: '+', '.join(missing))
    records = {}
    for line, raw in enumerate(reader, 2):
        if line > 501:
            raise ValueError('Maximum 500 rows per import.')
        if None in raw or any(v is None for v in raw.values()):
            raise ValueError('Row %s has a different number of fields from its header.' % line)
        row = {h:raw[normalized[h.casefold()]].strip() for h in HEADERS}
        if not any(row.values()):
            continue
        if not row['Creator / channel']:
            raise ValueError('Row %s: Creator / channel is required.' % line)
        if not row['Creator key']:
            raise ValueError('Row %s: Creator key is required for stable record updates.' % line)
        def followers(field):
            value = row[field].replace(' ', '').replace(',', '')
            if not value or value.casefold() in ('n/a','unknown','-'):
                return None
            if not re.fullmatch(r'\d+(?:\.\d+)?[kKmM]?', value):
                raise ValueError('Row %s: %s must be a count, K/M count, or blank.' % (line, field))
            multiplier = 1000 if value[-1:].lower()=='k' else 1000000 if value[-1:].lower()=='m' else 1
            count = float(value[:-1] if multiplier>1 else value)*multiplier
            if not count.is_integer() or count>9007199254740991:
                raise ValueError('Row %s: invalid %s count.' % (line,field))
            return int(count)
        yt, tt = followers('YT subscribers'), followers('TikTok followers')
        platform = row['Platform'] or 'Not supplied'
        # Do not sum followers across platforms or imply a shared audience.
        count = yt if platform.casefold()=='youtube' else tt if platform.casefold()=='tiktok' else None
        identity = row['Creator key'].casefold()
        history = records.get(identity, {}).get('prenewHistory', []) + [row]
        records[identity] = {'id':'prenew-'+hashlib.sha256(identity.encode()).hexdigest()[:20],
            'name':row['Creator / channel'], 'platform':platform, 'sourceType':'imported',
            'source':'PRENEW collaboration CSV: '+Path(filename).name, 'sourceUrl':None,
            'importFile':Path(filename).name, 'fetchedAt':datetime.now(timezone.utc).isoformat(),
            'country':row['Country'] or None, 'countrySource':'PRENEW spreadsheet claim',
            'market':row['Market'] or None, 'language':None, 'topic':row['Niche / content'] or None,
            'followers':count, 'videos':[], 'recentViews':None, 'engagement':None, 'fee':None,
            'audienceCountry':None, 'audienceSource':None, 'contact':None, 'conflict':None,
            'contentTitle':'', 'contentUrl':None, 'prenewImport':row, 'prenewHistory':history,
            'platformMetrics':{'YouTube':{'followers':yt,'viewsClaim':row['YT views / video'] or None},
                               'TikTok':{'followers':tt,'viewsClaim':row['TikTok views / video'] or None}}}
    if not records:
        raise ValueError('No creator rows found in the PRENEW CSV.')
    return {'creators':list(records.values()), 'count':len(records),
            'rowCount':sum(len(c['prenewHistory']) for c in records.values()), 'note':'PRENEW spreadsheet claims preserved. View ranges are not measured averages; platform audiences are not combined. Repeated Creator keys are grouped with their original collaboration rows preserved.'}
