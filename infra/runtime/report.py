#!/usr/bin/env python3
"""Fail closed unless every M09 runtime gate has verified passing evidence."""
import argparse
import hashlib
import json
from pathlib import Path

REQUIRED = {f'R{i:02}' for i in range(1, 11)}


def evaluate(repo, ledger, manifest, catalog=None,
             catalog_name='docs/project/PH1/P1M09/testing/constituents.json',
             results=None, results_name='docs/project/PH1/P1M09/testing/constituent-results.json'):
    reasons = []
    if not isinstance(ledger, dict) or not isinstance(manifest, dict):
        return {'milestone': 'P1-M09', 'status': 'INCOMPLETE', 'reasons': ['invalid ledger or manifest']}

    def verified_path(name):
        path = Path(name)
        candidate = repo / path
        return (not path.is_absolute() and '..' not in path.parts and not candidate.is_symlink()
                and candidate.resolve().is_relative_to(repo.resolve()) and candidate.is_file())

    def evidence(names, label):
        if not names:
            reasons.append(label+': missing evidence')
        for name in names:
            if not verified_path(name) or name not in manifest.get('evidence', {}):
                reasons.append(label+': unverified evidence')

    def frozen_json(name, value, label):
        if not verified_path(name) or name not in manifest.get('evidence', {}):
            reasons.append('unverified '+label)
            return None
        raw = (repo/name).read_bytes()
        if len(raw) > 1 << 20 or json.loads(raw) != value:
            reasons.append(label+' differs from frozen file')
        return hashlib.sha256(raw).hexdigest()

    if ledger.get('milestone') != 'P1-M09':
        reasons.append('wrong milestone')
    cases = ledger.get('cases', [])
    ids = [case.get('id') for case in cases]
    if set(ids) != REQUIRED or len(ids) != len(REQUIRED):
        reasons.append('missing, duplicated or unknown required gates')
    for case in cases:
        if case.get('status') != 'PASS':
            reasons.append(f'{case.get("id", "unknown")}: not PASS')
        evidence(case.get('evidence', []), case.get('id', 'unknown'))

    # Definitions stay immutable while execution results accumulate separately.
    catalog_hash = frozen_json(catalog_name, catalog, 'constituent catalog')
    frozen_json(results_name, results, 'constituent results')
    definitions = catalog.get('cases', []) if isinstance(catalog, dict) else []
    definition_ids = [case.get('id') for case in definitions]
    if (not definitions or catalog.get('schema') != 2 or catalog.get('milestone') != 'P1-M09'
            or len(set(definition_ids)) != len(definition_ids)
            or {case.get('gate') for case in definitions} != REQUIRED):
        reasons.append('missing, duplicated or invalid constituent catalog')
    executions = results.get('cases', []) if isinstance(results, dict) else []
    execution_ids = [case.get('id') for case in executions]
    if (not isinstance(results, dict) or results.get('milestone') != 'P1-M09'
            or results.get('scope') != 'real-runtime-acceptance'
            or catalog_hash is None or results.get('catalog_sha256') != catalog_hash
            or len(set(execution_ids)) != len(execution_ids) or set(execution_ids) != set(definition_ids)):
        reasons.append('missing, duplicated, changed or non-acceptance constituent results')
    by_id = {case.get('id'): case for case in executions}
    for definition in definitions:
        name, gate = definition.get('id'), definition.get('gate')
        result = by_id.get(name, {})
        if (gate not in REQUIRED or not isinstance(name, str) or not name.startswith(str(gate)+'.')
                or definition.get('required') is not True or result.get('gate') != gate
                or result.get('status') != 'PASS'):
            reasons.append(f'{name}: constituent incomplete')
        evidence(result.get('evidence', []), str(name))

    for section in ('source', 'evidence'):
        items = manifest.get(section, {})
        if not items:
            reasons.append(f'missing {section} manifest')
        for name, expected in items.items():
            if not verified_path(name):
                reasons.append('invalid manifest path')
                continue
            actual = hashlib.sha256((repo/name).read_bytes()).hexdigest()
            if expected != actual:
                reasons.append(f'changed {section}: {name}')
    if not manifest.get('isolated_runtime_acceptance'):
        reasons.append('isolated runtime acceptance incomplete')
    return {'milestone': 'P1-M09', 'status': 'INCOMPLETE' if reasons else 'PASS', 'reasons': reasons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--catalog', default='docs/project/PH1/P1M09/testing/constituents.json')
    parser.add_argument('--constituent-results', default='docs/project/PH1/P1M09/testing/constituent-results.json')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    try:
        catalog_path = Path(args.catalog).resolve()
        results_path = Path(args.constituent_results).resolve()
        report = evaluate(repo, json.loads(Path(args.ledger).read_text()), json.loads(Path(args.manifest).read_text()), json.loads(catalog_path.read_text()), str(catalog_path.relative_to(repo)), json.loads(results_path.read_text()), str(results_path.relative_to(repo)))
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        report = {'milestone': 'P1-M09', 'status': 'INCOMPLETE', 'reasons': ['invalid or unavailable evidence']}
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
