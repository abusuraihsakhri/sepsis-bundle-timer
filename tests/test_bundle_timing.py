"""Date arithmetic and clinical-pathway boundary tests, without PHI."""
from datetime import datetime, timezone
import pytest
from bundle_timing import evaluate_timing, parse_instant

NOW = datetime(2026, 10, 13, 10, 30, tzinfo=timezone.utc)
T0 = '2026-10-13T10:00:00+00:00'

def test_urgent_target():
    res = evaluate_timing(T0, 'urgent', as_of=NOW)
    assert res['reference_deadline_utc'] == '2026-10-13T11:00:00+00:00'
    assert res['elapsed_minutes'] == 30
    assert res['antibiotic_status'] == 'pending'

def test_possible_target():
    res = evaluate_timing(T0, 'possible', as_of=NOW)
    assert res['reference_hours'] == 3
    assert res['reference_deadline_utc'] == '2026-10-13T13:00:00+00:00'

def test_recorded_and_overdue():
    assert evaluate_timing(T0,'urgent',as_of=datetime(2026,10,13,11,1,tzinfo=timezone.utc))['antibiotic_status'] == 'overdue'
    assert evaluate_timing(T0,'urgent',antibiotic='2026-10-13T10:55Z',as_of=NOW.replace(hour=11))['antibiotic_status'] == 'recorded'
    assert evaluate_timing(T0,'urgent',antibiotic='2026-10-13T11:05Z',as_of=NOW.replace(hour=12))['antibiotic_status'] == 'after-target'

def test_culture_order():
    res = evaluate_timing(T0,'urgent',cultures='2026-10-13T10:20Z',antibiotic='2026-10-13T10:10Z',as_of=NOW)
    assert res['culture_order'] == 'after-antibiotic'

def test_timezone_normalization_and_rollover():
    res = evaluate_timing('2026-10-13T23:45:00+05:30','urgent',as_of=datetime(2026,10,13,19,0,tzinfo=timezone.utc))
    assert res['reference_deadline_utc']=='2026-10-13T19:15:00+00:00'

def test_reject_naive_invalid_and_future():
    with pytest.raises(ValueError,match='offset'): parse_instant('2026-10-13T12:00','recognition')
    with pytest.raises(ValueError,match='ISO'): parse_instant('xxx','recognition')
    with pytest.raises(ValueError,match='pathway'): evaluate_timing(T0,'invalid',as_of=NOW)
    with pytest.raises(ValueError,match='future'): evaluate_timing('2026-10-13T11:00Z','urgent',as_of=NOW)
    with pytest.raises(ValueError,match='future'): evaluate_timing(T0,'urgent',cultures='2026-10-13T11:00Z',as_of=NOW)
