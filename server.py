"""Local-only Prenew server. Standard library; credentials never served to browsers."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import threading
import time
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                k, v = line.split('=', 1)
                if k.strip() in ('YOUTUBE_API_KEY', 'PORT'):
                    os.environ.setdefault(k.strip(), v.strip().strip('\"\''))
load_env()

class APIError(Exception):
    def __init__(self, message, status=400):
        self.status = status
        super().__init__(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def number(value):
    return int(value) if value is not None else None

def language_tag(value):
    return str(value or '').lower().split('-')[0]

def matches_search_language(channel_language, videos, language):
    tags = [language_tag(channel_language)] + [language_tag(v.get('language')) for v in videos]
    return language in tags

def safe_url(value, required=False):
    value = (value or '').strip()
    if not value and not required:
        return None
    p = urlparse(value)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
        raise APIError('Source and evidence URLs must be full http(s) URLs without credentials.')
    return value

class YouTube:
    def __init__(self, key=None):
        self.key = os.environ.get('YOUTUBE_API_KEY', '') if key is None else key
        self.cache = {}
        self.result_cache = {}
        self.lock = threading.RLock()
        self.day = ''
        self.searches = 0
        self.calls = 0
        self.ttl = 1800

    def get(self, endpoint, **params):
        if not self.key:
            raise APIError('YouTube is not configured. Add YOUTUBE_API_KEY to the project .env and restart python3 server.py. No demo results were substituted.', 503)
        cache_key = endpoint + '?' + urlencode(sorted(params.items()))
        with self.lock:
            hit = self.cache.get(cache_key)
            if hit and time.time() - hit[0] < self.ttl:
                return hit[1]
            day = datetime.now(timezone.utc).date().isoformat()
            if day != self.day:
                self.day, self.searches, self.calls = day, 0, 0
            if self.calls >= 1000 or (endpoint == 'search' and self.searches >= 40):
                raise APIError('Local request budget reached (40 searches / 1,000 total API calls per UTC day per server run). Try cached queries or wait until tomorrow.', 429)
            self.calls += 1
            self.searches += int(endpoint == 'search')
            params['key'] = self.key
            try:
                request = Request('https://www.googleapis.com/youtube/v3/' + endpoint + '?' + urlencode(params), headers={'Accept': 'application/json'})
                with urlopen(request, timeout=15) as response:
                    data = json.load(response)
            except HTTPError as error:
                # Never include upstream URL, key, request or raw response in errors/logs.
                if error.code in (401, 403):
                    raise APIError('YouTube denied this request. Check that Data API v3 is enabled, the server key restrictions are correct, and quota remains. Comments may also be disabled.', 502) from None
                raise APIError('YouTube could not complete this request (HTTP %s). Check the query or try again later.' % error.code, 502) from None
            except (URLError, TimeoutError, OSError, ValueError):
                raise APIError('YouTube is unreachable or returned an invalid response. Check the server network connection and retry.', 502) from None
            if len(self.cache) >= 500:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = (time.time(), data)
            return data

    def search(self, query, language, size, token=''):
        identity = (query, language, size, token)
        with self.lock:
            cached = self.result_cache.get(identity)
            if cached and time.time() - cached[0] < self.ttl:
                return dict(cached[1], cached=True)
            result = self._search(query, language, size, token)
            if len(self.result_cache) >= 100:
                self.result_cache.pop(next(iter(self.result_cache)))
            self.result_cache[identity] = (time.time(), result)
            return dict(result, cached=False)

    def _search(self, query, language, size, token=''):
        if not query or len(query) > 220:
            raise APIError('Enter a search query between 1 and 220 characters.')
        if language not in ('fi', 'de', 'fr', 'nl', 'sv', 'en'):
            raise APIError('Choose a supported language.')
        if size not in ('all', 'nano', 'micro', 'mid', 'large') or len(token) > 500:
            raise APIError('Invalid size or pagination token.')
        params = dict(part='snippet', type='video', q=query, relevanceLanguage=language,
                      maxResults=25, order='relevance',
                      publishedAfter=(datetime.now(timezone.utc)-timedelta(days=365)).strftime('%Y-%m-%dT00:00:00Z'))
        if token:
            params['pageToken'] = token
        page = self.get('search', **params)
        ids = list(dict.fromkeys(x['snippet']['channelId'] for x in page.get('items', [])))
        matched = {}
        for item in page.get('items', []):
            vid = item.get('id', {}).get('videoId')
            if vid:
                matched.setdefault(item['snippet']['channelId'], []).append(vid)
        if not ids:
            return {'creators': [], 'nextPageToken': page.get('nextPageToken'), 'fetchedAt': now(), 'warnings': []}
        channels = self.get('channels', part='snippet,statistics,contentDetails', id=','.join(ids))['items']
        def count(c):
            s = c.get('statistics', {})
            return None if s.get('hiddenSubscriberCount') else number(s.get('subscriberCount'))
        ranges = {'nano': (0,10000), 'micro': (10000,100000), 'mid': (100000,500000), 'large': (500000,float('inf'))}
        if size != 'all':
            lo, hi = ranges[size]
            channels = [c for c in channels if count(c) is not None and lo <= count(c) < hi]
        channels.sort(key=lambda c: count(c) if count(c) is not None else float('inf'))
        records, warnings = [], []
        for channel in channels:
            cid, snippet = channel['id'], channel['snippet']
            playlist = channel.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            videos, hits = [], matched.get(cid, [])[:3]
            vids = list(hits)
            if playlist:
                uploads = self.get('playlistItems', part='contentDetails', playlistId=playlist, maxResults=5)
