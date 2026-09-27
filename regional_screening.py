"""Auditable, market-specific creator screening without a binary language gate."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence, TypedDict
from urllib.parse import urlparse


@dataclass(frozen=True)
class MarketProfile:
    code: str
    languages: tuple[str, ...]
    countries: tuple[str, ...]
    auxiliary_languages: tuple[str, ...] = ('en',)
    retailers: tuple[str, ...] = ()
    tlds: tuple[str, ...] = ()
    anchors: tuple[str, ...] = ()
    stopwords: tuple[str, ...] = ()


PROFILES = {
    p.code: p for p in (
        MarketProfile('NL', ('nl',), ('NL', 'BE'), retailers=('tweakers.net', 'megekko.nl', 'alternate.nl', 'coolblue.nl', 'azerty.nl'), tlds=('.nl',), anchors=('nederland', 'amsterdam', 'rotterdam', 'dutch', 'nl/be'), stopwords=('de', 'het', 'een', 'van', 'voor', 'met', 'zijn', 'deze', 'dat', 'mijn', 'onze', 'hoe', 'waarom')),
        MarketProfile('FI', ('fi',), ('FI',), retailers=('verkkokauppa.com', 'jimms.fi', 'hinta.fi'), tlds=('.fi',), anchors=('suomi', 'suomalainen', 'helsinki', 'tampere', 'turku'), stopwords=('ja', 'on', 'että', 'minä', 'meidän', 'tämä', 'miten', 'miksi', 'kanssa', 'uusi')),
        MarketProfile('SE', ('sv',), ('SE',), retailers=('inet.se', 'webhallen.com', 'komplett.se', 'prisjakt.nu'), tlds=('.se',), anchors=('sverige', 'svensk', 'stockholm', 'göteborg', 'malmö'), stopwords=('och', 'är', 'det', 'med', 'för', 'min', 'vår', 'den', 'hur', 'varför', 'inte')),
        MarketProfile('EE', ('et',), ('EE',), retailers=('arvutitark.ee', 'hinnavaatlus.ee', '1a.ee'), tlds=('.ee',), anchors=('eesti', 'eestlane', 'tallinn', 'tartu'), stopwords=('ja', 'on', 'see', 'minu', 'meie', 'kuidas', 'miks', 'koos', 'uus', 'eesti')),
        MarketProfile('DE', ('de',), ('DE',), retailers=('mindfactory.de', 'alternate.de', 'caseking.de'), tlds=('.de',), anchors=('deutschland', 'berlin', 'münchen', 'hamburg'), stopwords=('und', 'der', 'die', 'das', 'mit', 'für', 'mein', 'unser', 'wie', 'warum', 'nicht')),
        MarketProfile('FR', ('fr',), ('FR',), retailers=('ldlc.com', 'materiel.net', 'topachat.com'), tlds=('.fr',), anchors=('france', 'français', 'paris', 'lyon', 'marseille'), stopwords=('le', 'la', 'les', 'et', 'avec', 'pour', 'mon', 'notre', 'comment', 'pourquoi', 'pas')),
        MarketProfile('HU', ('hu',), ('HU',), retailers=('ipon.hu', 'alza.hu', 'arukereso.hu'), tlds=('.hu',), anchors=('magyarország', 'magyar', 'budapest', 'debrecen'), stopwords=('és', 'hogy', 'egy', 'az', 'van', 'ezt', 'hogyan', 'miért', 'nem', 'nekem')),
    )
}


class ScreenResult(TypedDict):
    eligibility: str
    market_match_tier: int | None
    language_detected: str | None
    language_confidence: float
    local_market_evidence: list[str]
    failure_reasons: list[str]
    reason_code: str
    is_lingua_franca: bool
    language_signals: dict[str, int]


class TextSanitizer:
    """Remove URLs and universal hardware terms before grammar-based language scoring."""
    JARGON = re.compile(r'\b(?:rtx|gtx|radeon|geforce|gpu|cpu|fps|benchmark(?:s|ing)?|gaming|pc|build(?:ing)?|unboxing|setup|hardware|budget|gameplay|ssd|ddr[345]|\d+(?:gb|tb|mhz|ghz|fps))\b', re.I)

    def clean(self, text: str) -> str:
        text = re.sub(r'https?://\S+|<[^>]+>', ' ', text or '', flags=re.I)
        return re.sub(r'\s+', ' ', self.JARGON.sub(' ', text)).strip()


def clean_hardware_text(text: str) -> str:
    return TextSanitizer().clean(text)


class RegionalScreeningEngine:
    """Screen a creator against one explicit market profile and retain audit signals."""
    ENGLISH = frozenset('the and with this that my our how why best cheap new used buying testing is are for you your'.split())

    def __init__(self, profile: MarketProfile, confidence_threshold: float = .6):
        self.profile = profile
        self.threshold = confidence_threshold
        self.sanitizer = TextSanitizer()

    def _language(self, text: str, tags: Sequence[str | None]) -> tuple[str | None, float, dict[str, int]]:
        words = re.findall(r'[^\W\d_]+', self.sanitizer.clean(text).lower(), re.UNICODE)
        signals = {lang: sum(word in self.profile.stopwords for word in words) for lang in self.profile.languages}
        signals['en'] = sum(word in self.ENGLISH for word in words)
        strongest = max(signals, key=signals.get)
        runner_up = max((score for lang, score in signals.items() if lang != strongest), default=0)
        if signals[strongest] >= 2 and signals[strongest] > runner_up:
            return strongest, min(.95, .55 + signals[strongest] * .1), signals
        normalized = [str(tag).lower().split('-')[0] for tag in tags if tag]
        if normalized and len(set(normalized)) == 1:
            return normalized[0], .65 if len(normalized) > 1 else .45, signals
        return None, .3 if normalized else 0.0, signals

    def detect_creator_market(self, country: str | None, bio: str, videos: Sequence[Mapping[str, Any]], comments: Sequence[str] = ()) -> list[str]:
        evidence = []
        if (country or '').upper() in self.profile.countries:
            evidence.append(f'channel country: {country.upper()}')
        for anchor in self.profile.anchors:
            if re.search(r'(?<!\w)' + re.escape(anchor) + r'(?!\w)', bio or '', re.I):
                evidence.append(f'bio: {anchor}')
        for video in videos:
            for url in re.findall(r'https?://[^\s<>"\']+', str(video.get('description') or ''), re.I):
                url = url.rstrip('.,);')
                host = (urlparse(url).hostname or '').lower()
                if any(host == domain or host.endswith('.' + domain) for domain in self.profile.retailers) or any(host.endswith(tld) for tld in self.profile.tlds):
                    evidence.append(f'local link: {url}')
        if len(comments) >= 5:
            native = sum(self._language(comment, ())[0] in self.profile.languages for comment in comments)
            if native >= 3 and native / len(comments) >= .5:
                evidence.append(f'local-language comments: {native}/{len(comments)} sampled')
        return list(dict.fromkeys(evidence))[:12]

    def screen_candidate(self, country: str | None, channel_language: str | None, bio: str,
                         videos: Sequence[Mapping[str, Any]], search_language: str,
                         comments: Sequence[str] = ()) -> ScreenResult:
        country = (country or '').upper()
        sample = sorted((v for v in videos if v.get('recentUpload') and v.get('broadcastStatus', 'none') == 'none'),
                        key=lambda v: str(v.get('publishedAt') or ''), reverse=True)[:5]
        text = (bio or '') + ' ' + ' '.join(str(v.get('title') or '') + ' ' + str(v.get('description') or '')[:300] for v in sample)
        tags = [channel_language] + [v.get(key) for v in sample for key in ('audioLanguage', 'metadataLanguage')]
        language, confidence, signals = self._language(text, tags)
        evidence = self.detect_creator_market(country, bio, sample, comments)
        secondary = any(item.startswith(('bio:', 'local link:', 'local-language comments:')) for item in evidence)
        reasons = []
        tier = None
        eligibility = 'review'
        code = 'NEEDS_HUMAN_GEO_CONFIRMATION'
        if country and country not in self.profile.countries:
            eligibility, code = 'excluded', 'EXCLUDED_FOREIGN_LEAKAGE'
            reasons.append(f'channel country {country} conflicts with target {self.profile.code}')
        elif country == self.profile.code and language in self.profile.languages and confidence >= self.threshold:
            tier, eligibility, code = 1, 'match', 'NATIVE_DIRECT_MATCH'
        elif country == self.profile.code and language in self.profile.auxiliary_languages and secondary:
            tier, eligibility, code = 2, 'match', 'LOCAL_LINGUA_FRANCA'
        elif country == self.profile.code and language is None and secondary:
            tier, eligibility, code = 2, 'match', 'LOCAL_MIXED_LANGUAGE'
        else:
            tier = 3
            reasons.append('target-language search origin without enough independent local language and market evidence')
        return {'eligibility': eligibility, 'market_match_tier': tier, 'language_detected': language,
                'language_confidence': confidence, 'local_market_evidence': evidence,
                'failure_reasons': reasons, 'reason_code': code,
                'is_lingua_franca': eligibility == 'match' and tier == 2,
                'language_signals': signals}


def screen_candidate(market: str, channel_country: str | None, channel_language: str | None, bio: str,
                     videos: Sequence[Mapping[str, Any]], search_language: str,
                     comments: Sequence[str] = ()) -> ScreenResult:
    return RegionalScreeningEngine(PROFILES[market]).screen_candidate(channel_country, channel_language, bio, videos, search_language, comments)


def detect_creator_market(market: str, channel_country: str | None, bio: str, videos: Sequence[Mapping[str, Any]],
                          comments: Sequence[str] = ()) -> list[str]:
    return RegionalScreeningEngine(PROFILES[market]).detect_creator_market(channel_country, bio, videos, comments)
