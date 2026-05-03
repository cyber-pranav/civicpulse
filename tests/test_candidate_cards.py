from backend.logic.candidate_cards import parse_candidate, parse_candidates, compare_candidates, _format_inr

def test_format_inr():
    assert '1.5 Lakh' in _format_inr(150000)
    assert '1.5 Crore' in _format_inr(15000000)

def test_parse_candidate():
    raw = {'name': 'A', 'criminal_cases': 0, 'assets_inr': 150000}
    c = parse_candidate(raw)
    assert 'No criminal cases' in c['criminal_record']

def test_parse_candidates():
    raw = [{'name': 'A'}, {'name': 'B'}]
    cs = parse_candidates(raw)
    assert len(cs) == 2

def test_compare_candidates():
    c1 = {'id': '1', 'name': 'A', 'party': 'P1', 'education': 'E1', 'criminal_record': 'CR1', 'declared_assets': 'DA1', 'key_promises': ['P1']}
    c2 = {'id': '2', 'name': 'B', 'party': 'P2', 'education': 'E2', 'criminal_record': 'CR2', 'declared_assets': 'DA2', 'key_promises': ['P2']}
    comp = compare_candidates([c1, c2])
    assert comp['candidates'][0] == 'A'
