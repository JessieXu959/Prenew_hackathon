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
from discovery_evidence import MARKETS, recent_view_summary, assess_language, public_contact

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

def safe_url(value, required=False):
    value = (value or '').strip()
    if not value and not required:
        return None
    p = urlparse(value)
    if p.scheme not in ('https', 'http') or not p.hostname or p.username or p.password:
        raise APIError('Source and evidence URLs must be full http(s) URLs without credentials.')
    return value

class YouTube:
    CHANNEL_TARGET = 200
    SEARCH_REQUEST_LIMIT = 12

    def __init__(self, key=None):
        self.key = os.environ.get('YOUTUBE_API_KEY', '') if key is None else key
        self.cache = {}
        self.result_cache = {}
        self.lock = threading.RLock()
        self.day = ''
        self.searches = 0
        self.calls = 0
        self.ttl = 1800
        self.retry_after = 0

    def get(self, endpoint, **params):
        if not self.key:
            raise APIError('YouTube is not configured. Add YOUTUBE_API_KEY to the project .env and restart python3 server.py. No demo results were substituted.', 503)
        cache_key = endpoint + '?' + urlencode(sorted(params.items()))
        with self.lock:
            hit = self.cache.get(cache_key)
            if hit and time.time() - hit[0] < self.ttl:
                return hit[1]
            remaining = self.retry_after - time.time()
            if remaining > 0:
                raise APIError('YouTube rate-limited requests. Wait %s seconds before searching again. Your query is not the cause.' % (int(remaining) + 1), 429)
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
                if error.code == 429:
                    try:
                        delay = max(60, int(error.headers.get('Retry-After', '60'))) if error.headers else 60
                    except (ValueError, TypeError):
                        delay = 60
                    self.retry_after = time.time() + delay
                    raise APIError('YouTube rate-limited requests. Wait %s seconds before searching again. Existing results are kept; changing the query will not remove this limit.' % delay, 429) from None
                if error.code in (401, 403):
                    raise APIError('YouTube denied this request. Check that Data API v3 is enabled, the server key restrictions are correct, and quota remains. Comments may also be disabled.', 502) from None
                raise APIError('YouTube could not complete this request (HTTP %s). Check the query or try again later.' % error.code, 502) from None
            except (URLError, TimeoutError, OSError, ValueError):
                raise APIError('YouTube is unreachable or returned an invalid response. Check the server network connection and retry.', 502) from None
            if len(self.cache) >= 500:
                self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key] = (time.time(), data)
            return data

    def search(self, query, language, size, token='', market=None, mode='video', min_subscribers=0, min_average_views=0, max_subscribers=0, sort='views'):
        market = market or next((m for m, lang in MARKETS.items() if lang == language), None)
        if mode not in ('video', 'channel'):
            raise APIError('Choose channel or video search.')
        try:
            min_subscribers, min_average_views = int(min_subscribers), int(min_average_views)
            if min_subscribers < 0 or min_average_views < 0: raise ValueError
        except (ValueError, TypeError):
            raise APIError('Minimum metrics must be nonnegative integers.') from None
        try:
            max_subscribers = int(max_subscribers)
            if max_subscribers != 0 and max_subscribers < max(800, min_subscribers): raise ValueError
        except (TypeError, ValueError):
            raise APIError('Subscriber cap must be 0 (no cap), or at least the minimum and 800.') from None
        if sort not in ('views', 'subscribers', 'fit'):
            raise APIError('Invalid sort order.')
        identity = (query, language, size, token, market, mode, min_subscribers, min_average_views, max_subscribers, sort)
        with self.lock:
            cached = self.result_cache.get(identity)
            if cached and time.time() - cached[0] < self.ttl:
                return dict(cached[1], cached=True)
            result = self._search(query, language, size, token, market, mode, min_subscribers, min_average_views, max_subscribers, sort)
            if len(self.result_cache) >= 100:
                self.result_cache.pop(next(iter(self.result_cache)))
            self.result_cache[identity] = (time.time(), result)
            return dict(result, cached=False)

    def collect_candidates(self, query, language, market, mode, token=''):
        # Rotate through native query alternatives before going deeper into any one.
        queries = list(dict.fromkeys(term.strip().strip('"') for term in query.split('|') if term.strip()))
        if not queries or len(queries) > 8:
            raise APIError('Use between one and eight search terms separated by |.')
        queue = [(term, token if i == 0 else '') for i, term in enumerate(queries)]
        seen_pages, ids, matched, origins = set(), [], {}, {}
        stats = {term: dict(query=term, pages=0, matches=0, newChannels=0) for term in queries}
        warnings, requests, matches = [], 0, 0
        reason = None
        while queue and len(ids) < self.CHANNEL_TARGET and requests < self.SEARCH_REQUEST_LIMIT:
            term, page_token = queue.pop(0)
            if (term, page_token) in seen_pages:
                continue
            seen_pages.add((term, page_token))
            params = dict(part='snippet', type=mode, q=term, relevanceLanguage=language,
                          regionCode=market, maxResults=50, order='relevance')
            if mode == 'video':
                params['publishedAfter'] = (datetime.now(timezone.utc)-timedelta(days=365)).strftime('%Y-%m-%dT00:00:00Z')
            if page_token:
                params['pageToken'] = page_token
            try:
                page = self.get('search', **params)
            except APIError as error:
                if not ids:
                    raise
                warnings.append(str(error))
                reason = 'upstream_limit'
                break
            requests += 1
            items = page.get('items', [])
            matches += len(items)
            stats[term]['pages'] += 1
            stats[term]['matches'] += len(items)
            for item in items:
                identifier, snippet = item.get('id', {}), item.get('snippet', {})
                cid = identifier.get('channelId') or snippet.get('channelId')
                if not cid:
                    continue
                if cid not in origins:
                    if len(ids) >= self.CHANNEL_TARGET:
                        continue
                    ids.append(cid)
                    origins[cid] = []
                    stats[term]['newChannels'] += 1
                if term not in origins[cid]:
                    origins[cid].append(term)
                vid = identifier.get('videoId')
                if vid and vid not in matched.setdefault(cid, []) and len(matched[cid]) < 3:
                    matched[cid].append(vid)
            next_page = page.get('nextPageToken')
            if next_page and (term, next_page) not in seen_pages:
                queue.append((term, next_page))
        reason = reason or ('target_reached' if len(ids) >= self.CHANNEL_TARGET else 'request_budget' if queue else 'results_exhausted')
        discovery = dict(targetChannels=self.CHANNEL_TARGET, uniqueChannels=len(ids), searchRequests=requests,
                         maxSearchRequests=self.SEARCH_REQUEST_LIMIT, stopReason=reason, queries=list(stats.values()))
        return ids, matched, origins, matches, discovery, warnings

    def _search(self, query, language, size, token='', market=None, mode='video', min_subscribers=0, min_average_views=0, max_subscribers=0, sort='views'):
        if not query or len(query) > 220:
            raise APIError('Enter a search query between 1 and 220 characters.')
        if market not in MARKETS:
            raise APIError('Choose a supported country / market.')
        if language not in MARKETS.values():
            raise APIError('Choose a supported language.')
        if size not in ('all', 'nano', 'micro', 'mid', 'large') or len(token) > 500:
            raise APIError('Invalid size or pagination token.')
        ids, matched, origins, matches, discovery, warnings = self.collect_candidates(query, language, market, mode, token)
        funnel = dict(matches=matches, channels=len(ids), subscribers=0, size=0, country=0, language=0, views=0)
        if not ids:
            return {'creators': [], 'nextPageToken': None, 'fetchedAt': now(), 'warnings': warnings, 'funnel': funnel, 'discovery': discovery}
        channels = []
        for start in range(0, len(ids), 50):
            channels.extend(self.get('channels', part='snippet,statistics,contentDetails', id=','.join(ids[start:start+50])).get('items', []))
        def count(c):
            s = c.get('statistics', {})
            return None if s.get('hiddenSubscriberCount') else number(s.get('subscriberCount'))
        channels = [c for c in channels if count(c) is not None and count(c) >= max(800, min_subscribers)
                    and (max_subscribers == 0 or count(c) <= max_subscribers)]
        funnel['subscribers'] = len(channels)
        ranges = {'nano': (0,10000), 'micro': (10000,100000), 'mid': (100000,500000), 'large': (500000,float('inf'))}
        if size != 'all':
            lo, hi = ranges[size]
            channels = [c for c in channels if count(c) is not None and lo <= count(c) < hi]
        funnel['size'] = len(channels)
        records = []
        excluded = {'countryMismatch': 0, 'countryUnknown': 0, 'languageMismatch': 0, 'languageInsufficient': 0}
        prepared = []
        for channel in channels:
            cid, snippet = channel['id'], channel['snippet']
            country = snippet.get('country')
            if country != market:
                excluded['countryMismatch' if country else 'countryUnknown'] += 1
                continue
            playlist = channel.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads')
            videos, hits = [], matched.get(cid, [])[:3]
            vids = list(hits)
            upload_ids, uploads_capped = [], False
            if playlist:
                uploads = self.get('playlistItems', part='contentDetails', playlistId=playlist, maxResults=50)
                upload_ids = [x['contentDetails']['videoId'] for x in uploads.get('items', [])]
                uploads_capped = bool(uploads.get('nextPageToken'))
                vids += upload_ids
            vids = list(dict.fromkeys(vids))
            prepared.append((channel, vids, hits, upload_ids, uploads_capped))
        funnel['country'] = len(prepared)
        all_ids = list(dict.fromkeys(vid for _, vids, _, _, _ in prepared for vid in vids))
        lookup = {}
        for start in range(0, len(all_ids), 50):
            items = self.get('videos', part='snippet,statistics,contentDetails', id=','.join(all_ids[start:start+50])).get('items', [])
            lookup.update((item['id'], item) for item in items)
        for channel, vids, hits, upload_ids, uploads_capped in prepared:
            cid, snippet = channel['id'], channel['snippet']
            country, videos = snippet.get('country'), []
            for vid in vids:
                video = lookup.get(vid)
                if video is None:
                    continue
                sn, st = video['snippet'], video.get('statistics', {})
                videos.append({'id': video['id'], 'matchedSearch': video['id'] in hits, 'recentUpload': video['id'] in upload_ids, 'title': sn['title'], 'description': sn.get('description', '')[:2000],
                    'url': 'https://www.youtube.com/watch?v=' + video['id'], 'publishedAt': sn['publishedAt'],
                    'audioLanguage': sn.get('defaultAudioLanguage'), 'metadataLanguage': sn.get('defaultLanguage'),
                    'broadcastStatus': sn.get('liveBroadcastContent', 'none'),
                    'language': sn.get('defaultAudioLanguage') or sn.get('defaultLanguage'),
                    'views': number(st.get('viewCount')), 'likes': number(st.get('likeCount')), 'comments': number(st.get('commentCount'))})
            language_evidence = assess_language(snippet.get('defaultLanguage'), videos, language)
            if not language_evidence['accepted']:
                excluded['languageMismatch' if language_evidence['status'] == 'mismatch' else 'languageInsufficient'] += 1
                continue
            funnel['language'] += 1
            checked_at = now()
            view_stats = recent_view_summary(videos, checked_at, uploads_capped)
            if min_average_views > 0 and (view_stats['average'] is None or view_stats['average'] <= min_average_views):
                continue
            funnel['views'] += 1
            engagement = [100*(v['likes']+v['comments'])/v['views'] for v in videos if v['views'] and v['likes'] is not None and v['comments'] is not None]
            records.append({'id': 'yt-'+cid, 'channelId': cid, 'name': snippet['title'], 'platform': 'YouTube',
                'sourceType': 'live', 'source': 'YouTube Data API v3', 'sourceUrl': 'https://www.youtube.com/channel/'+cid,
                'country': country, 'countrySource': 'YouTube channel-declared country',
                'language': snippet.get('defaultLanguage'), 'contentLanguage': language_evidence['language'],
                'languageEvidence': language_evidence, 'topic': None,
                'contact': public_contact(snippet.get('description', ''), 'https://www.youtube.com/channel/'+cid+'/about'),
                'followers': count(channel), 'recentViews': view_stats['average'], 'recentViewStats': view_stats,
                'engagement': sum(engagement)/len(engagement) if engagement else None, 'engagementSamples':len(engagement),
                'fee': None, 'audienceCountry': None, 'videos': videos, 'fetchedAt': checked_at, 'market': market,
                'searchLanguage': language, 'query': query, 'contentTitle': videos[0]['title'] if videos else '',
                'discoveryQueries': origins[cid],
                'contentUrl': videos[0]['url'] if videos else None, 'conflict': None})
        return {'creators': records, 'nextPageToken': None, 'fetchedAt': now(), 'warnings': warnings, 'discovery': discovery,
                'funnel': funnel, 'excluded': excluded, 'searchedChannels': len(ids), 'matchingChannels':len(records), 'searchesThisRun':self.searches,
                'note':'Up to 200 unique channels before eligibility filters, using relevance-first query rotation and at most 12 search pages. Search matches are separate from the upload-based average. Up to 50 latest public uploads; 30/90-day view window, minimum 3 measured videos. Declared country and audio-first language evidence required. Audience geography remains unverified.'}

    def comments(self, video_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise APIError('Invalid YouTube video ID.')
        response = self.get('commentThreads', part='snippet', videoId=video_id, maxResults=20, order='relevance', textFormat='plainText')
        results = []
        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']
            text = comment['snippet'].get('textDisplay', '')
            if '?' in text and len(text) >= 35:
                results.append({'text': text[:1800], 'url': 'https://www.youtube.com/watch?v='+video_id+'&lc='+comment['id'],
                    'publishedAt': comment['snippet'].get('publishedAt')})
        return {'comments':results[:8], 'fetchedAt':now(), 'note':'Question-mark and length filter over up to 20 top-level comments. Relevance and substance require human review; not representative of the whole audience.'}


def import_csv(text, filename):
    if len(text.encode('utf-8')) > 1_000_000:
        raise APIError('CSV is too large. Maximum size is 1 MB.')
    reader = csv.DictReader(io.StringIO(text.lstrip('\ufeff')), strict=True)
    required = {'name','platform','source_url','provenance'}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise APIError('Required CSV headers: name, platform, source_url, provenance. Download the template for optional evidence fields.')
    records, errors, seen = [], [], set()
    for line, row in enumerate(reader, 2):
        if line > 501:
            raise APIError('Maximum 500 rows per import.')
        try:
            if None in row or any(v is None for v in row.values()):
                raise APIError('Row has a different number of fields from its header.')
            row = {k:v.strip() for k,v in row.items()}
            if not row['name'] or not row['provenance']:
                raise APIError('Name and provenance are required.')
            if row['platform'] not in ('YouTube','Twitch','TikTok','Instagram'):
                raise APIError('Platform must be YouTube, Twitch, TikTok or Instagram.')
            url = safe_url(row['source_url'], True)
            hosts = {'YouTube':('youtube.com','youtu.be'), 'Twitch':('twitch.tv',), 'TikTok':('tiktok.com',), 'Instagram':('instagram.com',)}
            host = urlparse(url).hostname.lower()
            if not any(host == h or host.endswith('.'+h) for h in hosts[row['platform']]):
                raise APIError('Source URL must belong to the selected platform.')
            parsed = urlparse(url)
            identity = row['platform']+'|'+parsed.hostname.lower()+parsed.path.rstrip('/')
            if identity in seen:
                continue
            def metric(k):
                value = row.get(k, '')
                if not value: return None
                if not re.fullmatch(r'\d+',value): raise APIError(k+' must be a nonnegative integer or blank.')
                if int(value) > 9007199254740991: raise APIError(k+' is too large.')
                return int(value)
            date = row.get('published_at', '')
            if date:
                try: datetime.fromisoformat(date.replace('Z','+00:00'))
                except ValueError: raise APIError('published_at must be an ISO date (YYYY-MM-DD or timestamp).')
            video_url = safe_url(row.get('video_url'))
            videos = []
            if video_url:
                if not row.get('video_title'): raise APIError('video_title is required with video_url.')
                videos = [{'title':row['video_title'], 'description':row.get('video_description',''), 'url':video_url,
                    'publishedAt':date or None, 'language':row.get('language') or None,
                    'views':metric('views'), 'likes':metric('likes'), 'comments':metric('comments')}]
            verified_source = safe_url(row.get('audience_source'))
            audience = row.get('audience_country') if verified_source else None
            records.append({'id':'import-'+hashlib.sha256(identity.encode()).hexdigest()[:20], 'name':row['name'],
                'platform':row['platform'], 'sourceType':'imported', 'source':row['provenance'], 'sourceUrl':url,
                'importFile':Path(filename).name, 'fetchedAt':now(), 'country':row.get('country') or None,
                'language':row.get('language') or None, 'market':row.get('market') or None,
                'topic':row.get('topic') or None, 'followers':metric('followers'), 'videos':videos,
                'recentViews':None, 'countrySource':'CSV uploader claim' if row.get('country') else None, 'contact':None, 'engagement':None, 'fee':None,
                'audienceCountry':audience, 'audienceSource':verified_source, 'conflict':None,
                'contentTitle':row.get('video_title',''), 'contentUrl':video_url})
            seen.add(identity)
        except APIError as e:
            errors.append('Row %s: %s' % (line,e))
    if errors:
        raise APIError('Import rejected; no rows saved. '+' '.join(errors[:10]))
    if not records:
        raise APIError('No creator rows found. Fill the template with sourced records first.')
    return {'creators':records, 'count':len(records), 'note':'Imported claims are supplied by the uploader, not verified by platform APIs.'}

YOUTUBE = YouTube()
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT/'dist'),**kwargs)
    def log_message(self, format, *args): pass  # do not log queries or credentials
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()
    def allowed(self):
        host = self.headers.get('Host','')
        return host in ('127.0.0.1:'+str(self.server.server_port),'localhost:'+str(self.server.server_port))
    def respond(self,data,status=200):
        encoded=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(encoded))); self.end_headers(); self.wfile.write(encoded)
    def do_GET(self):
        if not self.allowed(): return self.respond({'error':'Localhost access only.'},403)
        route=urlparse(self.path)
        params={k:v[0] for k,v in parse_qs(route.query).items()}
        try:
            if route.path == '/api/status': return self.respond({'youtubeConfigured':bool(YOUTUBE.key),'cacheMinutes':30,'searchLimit':40,'searchesThisRun':YOUTUBE.searches})
            if route.path == '/api/youtube/search': return self.respond(YOUTUBE.search(params.get('q',''),params.get('language','fi'),params.get('size','all'),params.get('pageToken',''),params.get('market'),params.get('mode','video'),params.get('minSubscribers','0'),params.get('minAverageViews','0'),params.get('maxSubscribers','0'),params.get('sort','views')))
            if route.path == '/api/youtube/comments': return self.respond(YOUTUBE.comments(params.get('videoId','')))
            if route.path.startswith('/api/'): raise APIError('Unknown API endpoint.',404)
            if route.path == '/creator-template.csv':
                data=(ROOT/'creator-template.csv').read_bytes();self.send_response(200);self.send_header('Content-Type','text/csv');self.send_header('Content-Length',str(len(data)));self.end_headers();return self.wfile.write(data)
            if route.path not in ('/','/index.html','/app.js','/style.css','/data.js','/discovery.js','/research-core.js','/examples.html','/examples.js'):
                raise APIError('File not found.',404)
            return super().do_GET()
        except APIError as e: self.respond({'error':str(e)},e.status)
        except Exception: self.respond({'error':'Unable to complete request. No sample data substituted.'},500)
    def do_POST(self):
        if not self.allowed(): return self.respond({'error':'Localhost access only.'},403)
        origin=self.headers.get('Origin')
        if origin and origin not in ('http://127.0.0.1:'+str(self.server.server_port),'http://localhost:'+str(self.server.server_port)):
            return self.respond({'error':'Cross-origin request blocked.'},403)
        try:
            if self.path != '/api/import': raise APIError('Unknown API endpoint.',404)
            if self.headers.get('Content-Type') != 'application/json': raise APIError('Expected application/json.',415)
            length=int(self.headers.get('Content-Length','0'))
            if length < 1 or length > 1_100_000: raise APIError('Request must be between 1 byte and 1 MB.',413)
            payload=json.loads(self.rfile.read(length))
            if not isinstance(payload.get('csv'),str): raise APIError('CSV text is required.')
            self.respond(import_csv(payload['csv'],str(payload.get('filename','creators.csv'))))
        except APIError as e: self.respond({'error':str(e)},e.status)
        except (ValueError,csv.Error,AttributeError): self.respond({'error':'Invalid JSON or CSV. No rows saved.'},400)

if __name__=='__main__':
    port=int(os.environ.get('PORT','4173'))
    print('Prenew: http://127.0.0.1:%s — YouTube %s' % (port,'configured' if YOUTUBE.key else 'not configured'),flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
