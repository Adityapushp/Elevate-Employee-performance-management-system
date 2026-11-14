import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'generator'))
import schema as S
from gen_core import generate
from generate import validate

def test_starter_scale_has_required_master_and_transaction_entities():
    tables, params = generate(20261022, 0.05)
    assert len(tables['employees']) > 0
    assert len(tables['goals']) > 0
    assert len(tables['check_ins']) > 0
    report, _, _ = validate(tables, params)
    assert report
    assert all(item['passed'] for item in report), [item for item in report if not item['passed']]

def test_ground_truth_is_separate_from_operational_entities():
    tables, _ = generate(20261022, 0.05)
    assert 'ground_truth' in tables
    assert all('issue_type' in row and 'expected_decision' in row for row in tables['ground_truth'])
    assert 'ground_truth' not in [name for name in S.TABLES if name != 'ground_truth']
