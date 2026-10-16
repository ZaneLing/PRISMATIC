"""Recount physical response receipts; never sum logical method-use reports.

Read only known response stores, never credential files. No network requests.
Earlier stores lack generation IDs: report the narrow overlap ambiguity rather
than pretend that byte-identical deterministic replies prove cache reuse.
"""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT.parent / 'upgrade_v2/.local/rxrsi-v8'


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def cost(row):
    return Decimal(str(row.get('cost_usd') or 0))


def leaves(obj, context=()):
    if isinstance(obj, dict):
        if 'case_id' in obj and ('cost_usd' in obj or 'error' in obj):
            yield context, obj
        else:
            for key, value in obj.items():
                yield from leaves(value, context + (key,))
    elif isinstance(obj, list):
        for value in obj:
            yield from leaves(value, context)


def main():
    blob = (LOCAL / 'usage.jsonl').read_bytes()
    assert not blob or blob.endswith(b'\n'), 'Incomplete ledger write; rerun after completion'
    rows = [json.loads(line) for line in blob.splitlines()]
    signatures = Counter(r['request_sha256'] for r in rows)
    by_model = defaultdict(lambda: {'responses': 0, 'usd': Decimal(0), 'input_tokens': 0, 'output_tokens': 0})
    by_role = defaultdict(lambda: {'responses': 0, 'usd': Decimal(0)})
    for row in rows:
        model = row.get('model_returned') or 'unknown'
        by_model[model]['responses'] += 1
        by_model[model]['usd'] += cost(row)
        by_model[model]['input_tokens'] += row.get('input_tokens') or 0
        by_model[model]['output_tokens'] += row.get('output_tokens') or 0
        role = row.get('role') or 'unknown'
        by_role[role]['responses'] += 1
        by_role[role]['usd'] += cost(row)
    # Caches are copies, not extra spend. A successful reply absent from the
    # append-only ledger may survive a crash between cache write and append.
    orphans = []
    cache_n = 0
    for path in (LOCAL / 'cache').glob('*.json'):
        cache_n += 1
        if path.stem in signatures:
            continue
        row = json.loads(path.read_text())
        assert row.get('request_sha256') == path.stem
        if not row.get('error'):
            orphans.append(row)
    failures_path = LOCAL / 'transport_failures.jsonl'
    failures = [json.loads(line) for line in failures_path.read_text().splitlines()] if failures_path.exists() else []
    legacy_files = []
    unique_legacy = {}
    all_legacy = []
    legacy_errors = Counter()
    # Canonical repository copies only; sibling upgrade_v2 is a mirror.
    for path in sorted(ROOT.glob('upgrade_v[23]/results/openrouter*predictions.json')):
        content = path.read_bytes()
        successful = []
        for ctx, row in leaves(json.loads(content)):
            if row.get('error'):
                legacy_errors[row['error']] += 1
                continue
            successful.append(row)
            # Include model and arm, so distinct follow-up operations are not
            # collapsed merely because they happened to produce the same letter.
            identity = json.dumps([ctx, row], sort_keys=True, ensure_ascii=False)
            unique_legacy.setdefault(identity, row)
        all_legacy.extend(successful)
        legacy_files.append({'path': str(path.relative_to(ROOT)), 'sha256': sha(content),
                             'successful_records': len(successful),
                             'recorded_usd': float(sum(map(cost, successful), Decimal(0)))})
    low = sum(map(cost, unique_legacy.values()), Decimal(0))
    high = sum(map(cost, all_legacy), Decimal(0))
    main_cost = sum(map(cost, rows), Decimal(0))
    orphan_cost = sum(map(cost, orphans), Decimal(0))
    out = {
        'snapshot_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Located PRISMATIC upgrade experiments; successful provider-reported response costs. Not an invoice, account balance, or all-time account spend.',
        'network_calls_in_this_audit': 0,
        'main_ledger': {
            'sha256': sha(blob), 'successful_response_events': len(rows),
            'distinct_request_signatures': len(signatures),
            'repeated_signature_events': len(rows) - len(signatures),
            'repeated_signatures': sum(n > 1 for n in signatures.values()),
            'exact_duplicate_ledger_lines': len(rows) - len(set(blob.splitlines())),
            'reported_usd': float(main_cost),
            'null_or_absent_cost_records': sum(r.get('cost_usd') is None for r in rows),
            'zero_cost_records': sum(cost(r) == 0 for r in rows),
            'by_model': dict(by_model), 'by_role': dict(by_role),
            'counting_rule': 'Every ledger event is a new successful response. Repeated request signatures are retained: request equality does not imply only one paid execution. Cached rereads do not append.',
            'schema_limitation': 'Client defaults absent provider cost to zero; provider generation IDs and completion timestamps were not preserved. Zero prices cannot all be verified as free calls.'},
        'cache_reconciliation': {'files': cache_n, 'successful_orphan_records': len(orphans), 'orphan_recorded_usd': float(orphan_cost),
                                 'counting_rule': 'Cached replies already represented by the ledger are never added again.'},
        'legacy': {'files': legacy_files, 'successful_records': len(all_legacy), 'distinct_full_records': len(unique_legacy),
                   'ambiguous_repeat_records': len(all_legacy) - len(unique_legacy),
                   'deduplicated_recorded_usd': float(low), 'all_records_usd': float(high),
                   'recorded_error_records': dict(legacy_errors),
                   'missing_cost_records': sum(r.get('cost_usd') is None for r in all_legacy),
                   'note': 'Pilot/full-run overlap has no provider generation IDs. Exact record overlap could be copied results or separate identical deterministic calls. Endpoints bound only this overlap ambiguity, not missing historical spend.'},
        'located_successful_reported_usd_range': [float(main_cost + orphan_cost + low), float(main_cost + orphan_cost + high)],
        'transport_failure_attempts': len(failures),
        'transport_failure_types': dict(Counter(r.get('error', 'unknown') for r in failures)),
        'excluded_or_unknown': [
            'Timed-out or failed requests may incur charges without a locally received priced response.',
            'Superseded legacy receipts, ad hoc requests without receipts and original 2025 work cannot be reconstructed from these stores.',
            'Local CPU/MPS inference and training have no dollar meter; available fit time is reported separately.',
            'Chat/Codex subscription or token costs, taxes, top-up fees, credits and refunds are not included.',
            'Logical cost sums across methods/versions include reused replies and must not be added to this total.'],
    }
    def encode(value):
        if isinstance(value, Decimal):
            return float(value)
        raise TypeError(type(value))
    target = ROOT / 'paper/total_spend_audit.json'
    target.write_text(json.dumps(out, indent=2, default=encode) + '\n')
    print(json.dumps({k: out[k] for k in ('located_successful_reported_usd_range', 'cache_reconciliation', 'transport_failure_attempts')}))


if __name__ == '__main__':
    main()
