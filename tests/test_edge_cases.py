import pytest
from symposia.strategies.majority import WeightedMajorityVote
from symposia.strategies.mean import WeightedMeanScore
from symposia.strategies.median import MedianScore
from symposia.core.committee import Committee
from symposia.core.member import CommitteeMember
from symposia.core.reputation import ReputationManager
from symposia.utils.parsing import parse_llm_json_response


class MockLLMService:
    def __init__(self, responses):
        self.responses = responses
        self.call_count = 0
        # Add config attribute for trace compatibility
        self.config = type('Config', (), {'model': 'mock-model'})()
    
    async def query(self, prompt, role_prompt):
        response = self.responses[self.call_count]
        self.call_count += 1
        return response


def test_strategy_empty_votes():
    """Test voting strategies with empty vote lists."""
    majority = WeightedMajorityVote()
    mean = WeightedMeanScore()
    median = MedianScore()
    
    assert majority.tally([]) == "No valid votes."
    assert mean.tally([]) == 0.0
    assert median.tally([]) == 0.0


def test_strategy_invalid_votes():
    """Test voting strategies with invalid votes."""
    majority = WeightedMajorityVote()
    mean = WeightedMeanScore()
    median = MedianScore()
    
    invalid_votes = [
        {'value': None, 'weight': 1.0},
        {'value': 'valid', 'weight': 1.0},
        {'weight': 1.0},  # missing value
        {'value': 'valid2'},  # missing weight
    ]
    
    # Majority should handle None values gracefully
    result = majority.tally(invalid_votes)
    assert result in ['valid', 'valid2']  # Should pick one of the valid votes
    
    # Mean should handle None values gracefully
    result = mean.tally(invalid_votes)
    assert result == 0.0  # No numeric values
    
    # Median should handle None values gracefully
    result = median.tally(invalid_votes)
    assert result == 0.0  # No numeric values


def test_strategy_mixed_numeric_and_string():
    """Test strategies with mixed numeric and string values."""
    majority = WeightedMajorityVote()
    mean = WeightedMeanScore()
    median = MedianScore()
    
    mixed_votes = [
        {'value': 'yes', 'weight': 1.0},
        {'value': 5, 'weight': 1.0},
        {'value': 'no', 'weight': 1.0},
        {'value': 3, 'weight': 1.0},
    ]
    
    # Majority should work with strings
    result = majority.tally(mixed_votes)
    assert result in ['yes', 'no']
    
    # Mean should only consider numeric values
    result = mean.tally(mixed_votes)
    assert result == 4.0  # (5 + 3) / 2
    
    # Median should only consider numeric values
    result = median.tally(mixed_votes)
    assert result == 4.0  # median of [3, 5]


def test_reputation_min_bound():
    """Test that reputation cannot go below minimum bound."""
    from symposia.core.reputation import ReputationManager
    
    class MockMember:
        def __init__(self, name):
            self.name = name
            self.reputation = 0.15
            self.base_weight = 1.0
    
    class MockResult:
        def __init__(self, final_result, trace):
            self.final_result = final_result
            self.trace = trace
    
    member = MockMember("Test")
    trace = [{'member_object': member, 'status': 'Success', 'parsed_vote': {'vote': 'no'}}]
    result = MockResult('yes', trace)
    
    manager = ReputationManager([member], agreement_bonus=0.1, dissent_penalty=0.2)
    manager.update_reputations(result)
    
    # Reputation should not go below 0.1
    assert member.reputation == 0.1


def test_reputation_max_bound():
    """Test that reputation can increase without bounds."""
    from symposia.core.reputation import ReputationManager
    
    class MockMember:
        def __init__(self, name):
            self.name = name
            self.reputation = 10.0
            self.base_weight = 1.0
    
    class MockResult:
        def __init__(self, final_result, trace):
            self.final_result = final_result
            self.trace = trace
    
    member = MockMember("Test")
    trace = [{'member_object': member, 'status': 'Success', 'parsed_vote': {'vote': 'yes'}}]
    result = MockResult('yes', trace)
    
    manager = ReputationManager([member], agreement_bonus=0.1, dissent_penalty=0.05)
    manager.update_reputations(result)
    
    # Reputation should increase
    assert member.reputation == 10.1


def test_reputation_technical_failure():
    """Test that technical failures don't affect reputation."""
    from symposia.core.reputation import ReputationManager
    
    class MockMember:
        def __init__(self, name):
            self.name = name
            self.reputation = 1.0
            self.base_weight = 1.0
    
    class MockResult:
        def __init__(self, final_result, trace):
            self.final_result = final_result
            self.trace = trace
    
    member = MockMember("Test")
    trace = [{'member_object': member, 'status': 'Failed: API Error', 'parsed_vote': {'vote': 'no'}}]
    result = MockResult('yes', trace)
    
    initial_reputation = member.reputation
    manager = ReputationManager([member], agreement_bonus=0.1, dissent_penalty=0.05)
    manager.update_reputations(result)
    
    # Reputation should not change for technical failures
    assert member.reputation == initial_reputation


@pytest.mark.asyncio
async def test_committee_empty_members():
    """Test committee with no members."""
    strategy = WeightedMajorityVote()
    committee = Committee("Empty Committee", [], strategy)
    
    result = await committee.deliberate("Test topic")
    
    assert result.final_result == "No valid votes."
    assert len(result.trace) == 0
    assert result.total_tokens == 0
    assert result.total_cost == 0.0


@pytest.mark.asyncio
async def test_committee_all_members_fail():
    """Test committee when all members fail to vote."""
    responses = [
        {"error": "API Error 1", "response": "", "tokens_used": 0, "cost": 0.0},
        {"error": "API Error 2", "response": "", "tokens_used": 0, "cost": 0.0},
    ]
    
    llm_service = MockLLMService(responses)
    members = [
        CommitteeMember("Alice", "role1", llm_service, base_weight=1.0),
        CommitteeMember("Bob", "role2", llm_service, base_weight=1.0),
    ]
    
    strategy = WeightedMajorityVote()
    committee = Committee("Failing Committee", members, strategy)
    
    result = await committee.deliberate("Test topic")
    
    assert result.final_result == "No valid votes."
    assert len(result.trace) == 2
    assert all(step["status"].startswith("Failed:") for step in result.trace)


def test_parse_llm_json_response_edge_cases():
    """Test parse_llm_json_response with edge cases."""
    # Empty string
    result = parse_llm_json_response("")
    assert "error" in result
    
    # No JSON object
    result = parse_llm_json_response("Just some text without JSON")
    assert "error" in result
    
    # Invalid JSON
    result = parse_llm_json_response('{"incomplete": json')
    assert "error" in result
    
    # JSON with extra text after
    result = parse_llm_json_response('{"vote": "yes"} and some extra text')
    assert result.get("vote") == "yes"
    
    # Multiple JSON objects (should take the first one)
    result = parse_llm_json_response('{"vote": "first"} {"vote": "second"}')
    assert result.get("vote") == "first"


def test_member_effective_weight():
    """Test that member effective weight combines base_weight and reputation."""
    llm_service = MockLLMService([])
    member = CommitteeMember("Test", "role", llm_service, base_weight=2.0, initial_reputation=1.5)
    
    # effective_weight = base_weight * reputation = 2.0 * 1.5 = 3.0
    assert member.effective_weight == 3.0
    
    # Change reputation and verify effective weight updates
    member.reputation = 0.5
    assert member.effective_weight == 1.0  # 2.0 * 0.5 