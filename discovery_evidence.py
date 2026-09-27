"""Conservative discovery evidence. Search hints never establish audience location."""
from datetime import datetime, timezone, timedelta
import re

MARKETS = {'FI': 'fi', 'DE': 'de', 'FR': 'fr', 'NL': 'nl', 'SE': 'sv', 'EE': 'et', 'GB': 'en'}
MIN_VIEW_SAMPLE = 3


def timestamp(value):
    try:
        date = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date
    except (ValueError, TypeError):
        return None


def recent_view_summary(videos, checked_at, uploads_capped=False):
    """Lifetime public views of videos published in a window, not views gained in it."""
    end = timestamp(checked_at)
    uploads = [v for v in videos if v.get('recentUpload') and
               v.get('broadcastStatus', 'none') == 'none' and
               timestamp(v.get('publishedAt')) and timestamp(v['publishedAt']) <= end]
    def within(days):
        return [v for v in uploads if timestamp(v['publishedAt']) >= end - timedelta(days=days)]
    def measured(items):
        return [v for v in items if isinstance(v.get('views'), (int, float)) and v['views'] >= 0]
    days = 30 if len(measured(within(30))) >= MIN_VIEW_SAMPLE else 90
    eligible, sample = within(days), measured(within(days))
    oldest = min((timestamp(v['publishedAt']) for v in uploads), default=end)
    limited = uploads_capped and oldest >= end - timedelta(days=days)
    sufficient = len(sample) >= MIN_VIEW_SAMPLE
    return {'average': sum(v['views'] for v in sample) / len(sample) if sufficient else None,
            'windowDays': days, 'sampleSize': len(sample), 'minimumSample': MIN_VIEW_SAMPLE,
            'windowStart': (end - timedelta(days=days)).isoformat(), 'windowEnd': checked_at,
            'checkedAt': checked_at, 'videoIds': [v['id'] for v in sample],
            'missingViewCount': len(eligible) - len(sample), 'sampleLimited': limited,
            'status': 'sufficient' if sufficient else 'insufficient',
            'method': 'Mean lifetime public views of sampled uploads published within the window; not views gained during the window.'}


def assess_language(channel_language, videos, language):
    """Prefer audio language; title metadata is only a fallback when audio is absent."""
    sample = sorted((v for v in videos if v.get('recentUpload') and
                     v.get('broadcastStatus', 'none') == 'none'),
                    key=lambda v: v.get('publishedAt') or '', reverse=True)[:5]
    normalize = lambda value: str(value or '').lower().split('-')[0]
    evidence, positive, conflicting = [], 0, False
    for video in sample:
        audio = normalize(video.get('audioLanguage'))
        metadata = normalize(video.get('metadataLanguage'))
        tag = audio or metadata or normalize(video.get('language'))
        mismatch = bool(tag and tag != language)
        matches = tag == language
        conflicting |= mismatch
        positive += int(matches)
        evidence.append({'videoId': video['id'], 'url': video['url'], 'title': video['title'],
                         'audioLanguage': video.get('audioLanguage'),
                         'metadataLanguage': video.get('metadataLanguage'),
                         'basis': 'audio' if audio else 'metadata' if tag else 'unknown',
                         'textExcerpt': video.get('description', '')[:240],
                         'matches': matches, 'mismatch': mismatch})
    # One search hit or a channel-level tag cannot establish the channel's recent language.
    accepted = len(sample) >= 3 and positive >= 2 and not conflicting
    return {'accepted': accepted, 'language': language if accepted else None,
            'status': 'match' if accepted else 'mismatch' if conflicting else 'insufficient',
            'positiveVideos': positive, 'sampleSize': len(sample), 'videos': evidence,
            'method': 'Inspect up to five latest uploads; at least three inspected, two matching. Audio language takes priority; title/description language is a fallback. Conflicting effective video languages fail; channel-title language does not override video evidence. Missing evidence remains unknown.'}


def public_contact(description, source_url):
    """Only explicit contact text in the public channel description; never infer an email."""
    cue = re.compile(r'contact|business|inquir|enquir|collab|yhtey|kaupalli|kontakt|anfrag|geschäft|samarbet', re.I)
    for line in (description or '').splitlines():
        if not cue.search(line):
            continue
        email = re.search(r'[A-Za-z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', line)
        if email:
            return {'value': email.group(), 'kind': 'Public business email', 'sourceUrl': source_url,
                    'source': 'Public channel description; ownership not independently verified'}
        url = re.search(r'https?://[^\s<>"\']+', line)
        if url:
            return {'value': url.group().rstrip('.,);'), 'kind': 'Public contact link', 'sourceUrl': source_url,
                    'source': 'Contact-labelled link in public channel description'}
    return None
