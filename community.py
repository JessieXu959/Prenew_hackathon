"""Bounded, transparent public-comment evidence; no authenticity inference."""
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone

PATTERNS = {
    'Purchase consideration': r'buy|buying|purchase|price|budget|worth|ostaa|hinta|kaufen|preis|acheter|prix|kopen|prijs|köpa|osta|hind|venni|ár',
    'Hardware discussion': r'\bpc\b|gpu|cpu|ram|fps|rtx|ryzen|intel|radeon|warranty|takuu|garantie|garantii|garancia',
    'Ownership experience': r'i bought|i own|my pc|ostin|gekauft|acheté|gekocht|köpte|ostsin|vettem',
}

def classify(text):
    labels = [label for label, pattern in PATTERNS.items() if re.search(pattern, text, re.I)]
    return labels or ['Uncertain / general reaction']

def analyze(client, channel_id, video_ids):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', channel_id):
        raise ValueError('Invalid channel ID.')
    ids = list(dict.fromkeys(video_ids))
    if not 1 <= len(ids) <= 3 or any(not re.fullmatch(r'[A-Za-z0-9_-]{11}', x) for x in ids):
        raise ValueError('Select one to three valid video IDs.')
    # Verify ownership rather than attributing arbitrary comments to a creator.
    metadata = client.get('videos', part='snippet', id=','.join(ids)).get('items', [])
    allowed = [v['id'] for v in metadata if v['snippet'].get('channelId') == channel_id]
    examples, seen, failures = [], set(), []
    authors = defaultdict(set)
    counts = Counter()
    reply_threads = 0
    for vid in allowed:
        for order in ('relevance', 'time'):
            try:
                data = client.get('commentThreads', part='snippet,replies', videoId=vid,
                                  maxResults=20, order=order, textFormat='plainText')
            except Exception as error:
                # Use only our sanitized API errors, never upstream request details.
                if not hasattr(error, 'status'):
                    raise
                failures.append({'videoId': vid, 'order': order, 'reason': str(error)})
                if error.status == 429:
                    raise
                continue
            for thread in data.get('items', []):
                top = thread['snippet']['topLevelComment']
                if top['id'] in seen:
                    continue
                seen.add(top['id'])
                sn = top['snippet']
                if sn.get('authorChannelId', {}).get('value') == channel_id:
                    continue
                text = sn.get('textDisplay', '')[:2000]
                categories = classify(text)
                for category in categories:
                    counts[category] += 1
                author = sn.get('authorChannelId', {}).get('value')
                if author:
                    authors[author].add(vid)
                replies = [r['snippet'].get('textDisplay', '')[:1000] for r in thread.get('replies', {}).get('comments', [])
                           if r['snippet'].get('authorChannelId', {}).get('value') == channel_id]
                reply_threads += bool(replies)
                examples.append({'text': text, 'categories': categories, 'creatorReplies': replies,
                                 'url': 'https://www.youtube.com/watch?v='+vid+'&lc='+top['id'], 'videoId': vid})
    total = len(examples)
    relevant = sum('Uncertain / general reaction' not in c['categories'] for c in examples)
    return {'sampleSize': total, 'videoCount': len(set(x['videoId'] for x in examples)),
            'requestedVideos': len(ids), 'counts': dict(counts),
            'discussionShare': round(relevant/total*100, 1) if total else None,
            'creatorReplyShare': round(reply_threads/total*100, 1) if total else None,
            'repeatParticipants': sum(len(v)>1 for v in authors.values()),
            'examples': examples, 'failures': failures,
            'checkedAt': datetime.now(timezone.utc).isoformat(),
            'method': 'Up to 20 popular and 20 recent top-level comments per video, deduplicated across both samples. Keyword-assisted labels require human review. Creator replies use only replies returned with threads; not a complete reply census. Repeat participants means observed on at least two sampled videos. No score predicts trust or sales.'}
