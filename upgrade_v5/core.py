"""Separate historical prediction, clinical uncertainty and train-only memory."""
import hashlib
import json


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def parse_codes(raw, allowed, fallback=()):
    """Salvage valid members, but never silently label repaired JSON as raw-valid."""
    text = raw.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    try:
        obj = json.loads(text)
        codes = obj['codes']
        if not isinstance(codes, list):
            raise ValueError('codes is not an array')
    except (ValueError, KeyError, TypeError):
        return {'codes': list(fallback), 'raw_valid': False, 'parse_status': 'invalid_json_or_schema_fallback'}
    accepted = list(dict.fromkeys(c for c in codes if isinstance(c, str) and c in allowed))[:5]
    valid = len(accepted) == len(codes)
    # A genuine [] is distinct from an invalid nonempty response with no valid members.
    if codes and not accepted:
        return {'codes': list(fallback), 'raw_valid': False, 'parse_status': 'invalid_members_fallback'}
    return {'codes': accepted, 'raw_valid': valid,
            'parse_status': 'valid_empty' if not codes else 'valid' if valid else 'partial_repair'}


def clinical_review(codes, flags=(), verified_evidence=()):
    """Flags do not mutate historical predictions. Clinical actions remain unapproved.

    Only an externally verified, case-specific contradiction can mark a candidate
    blocked. The current experiment supplies no such clinical knowledge resource.
    """
    verified = set(verified_evidence)
    items = []
    for code in codes:
        blockers = [f for f in flags if f.get('code') == code
                    and f.get('verdict') == 'contradicted'
                    and f.get('evidence_id') in verified]
        items.append({'code': code, 'clinical_status': 'blocked' if blockers else 'needs_information',
                      'verified_contradictions': blockers})
    return {'historical_candidates': list(codes), 'clinical_items': items,
            'executable_orders': [], 'clinical_clearance': False}


class ExperienceLedger:
    """Append-only train episode registry; explicit validation promotion/rollback."""
    def __init__(self):
        self.episodes = []
        self.versions = []
        self.best_validation = float('-inf')
        self.active = None

    def append(self, episode):
        if episode.get('split') != 'train':
            raise ValueError('Only training feedback can enter experience memory')
        if episode['case_key'] in {x['case_key'] for x in self.episodes}:
            raise ValueError('Duplicate episode')
        self.episodes.append(episode)

    def checkpoint(self, validation_score, metadata):
        version = {'episode_count': len(self.episodes), 'episode_sha256': digest(self.episodes),
                   'validation_f1': validation_score, **metadata}
        version['version'] = digest(version)
        version['promoted'] = validation_score > self.best_validation + 1e-12
        if version['promoted']:
            self.best_validation = validation_score
            self.active = version['version']
        version['active_version'] = self.active
        self.versions.append(version)
        return version
