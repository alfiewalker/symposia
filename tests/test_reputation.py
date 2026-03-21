import pytest

pytestmark = pytest.mark.core
from symposia.core.reputation import ReputationManager

class MockMember:
    def __init__(self, name, rep):
        self.name = name
        self.reputation = rep
        self.base_weight = 1.0

class MockResult:
    def __init__(self, final_result, trace):
        self.final_result = final_result
        self.trace = trace

def test_reputation_increase_and_decrease():
    m1 = MockMember('A', 1.0)
    m2 = MockMember('B', 1.0)
    trace = [
        {'member_object': m1, 'status': 'Success', 'parsed_vote': {'vote': 'yes'}},
        {'member_object': m2, 'status': 'Success', 'parsed_vote': {'vote': 'no'}},
    ]
    result = MockResult('yes', trace)
    mgr = ReputationManager([m1, m2], agreement_bonus=0.2, dissent_penalty=0.1)
    mgr.update_reputations(result)
    assert m1.reputation == 1.2  # agreed
    assert m2.reputation == 0.9  # dissented

def test_reputation_min_bound():
    m = MockMember('A', 0.15)
    trace = [{'member_object': m, 'status': 'Success', 'parsed_vote': {'vote': 'no'}}]
    result = MockResult('yes', trace)
    mgr = ReputationManager([m], agreement_bonus=0.1, dissent_penalty=0.1)
    mgr.update_reputations(result)
    assert m.reputation == 0.1  # should not go below 0.1 