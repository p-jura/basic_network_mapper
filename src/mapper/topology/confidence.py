from datetime import datetime


def seconds(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


def assess(observations, runs, max_skew, reasons=()):
    reasons = set(reasons)
    if any(r['status'] not in {'ok', 'empty'} or not r['exhausted'] for r in runs):
        reasons.add('PARTIAL_SOURCE')
    times = [seconds(o['observed_at']) for o in observations]
    if times and max(times) - min(times) > max_skew:
        reasons.add('TIME_SKEW')
    if any(o['freshness'] != 'fresh' and not o['evidence_at'] for o in observations):
        reasons.add('CACHE_AGE_UNKNOWN')
    if any(o['evidence_at'] and abs(seconds(o['observed_at']) - seconds(o['evidence_at'])) > max_skew for o in observations):
        reasons.add('STALE_EVIDENCE')
    severe = {'TIME_SKEW', 'STALE_EVIDENCE', 'PORT_MAPPING_MISSING', 'PORT_MAPPING_CONFLICT', 'PARTIAL_SOURCE', 'INVALID_FDB', 'CONTEXT_UNKNOWN'}
    level = 'low' if severe & reasons else 'medium' if reasons else 'high'
    return {'level': level, 'reasons': sorted(reasons), 'observation_ids': sorted({o['observation_id'] for o in observations})}
