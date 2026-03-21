import pytest

pytestmark = pytest.mark.core
from unittest.mock import AsyncMock, MagicMock
from symposia.core.committee import Committee
from symposia.core.member import CommitteeMember
from symposia.strategies.majority import WeightedMajorityVote
from symposia.core.reputation import ReputationManager


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


@pytest.fixture
def mock_members():
    """Create mock committee members with controlled responses."""
    responses = [
        {"response": '{"vote": "yes", "reasoning": "test1"}', "tokens_used": 10, "cost": 0.001},
        {"response": '{"vote": "no", "reasoning": "test2"}', "tokens_used": 15, "cost": 0.002},
        {"response": '{"vote": "yes", "reasoning": "test3"}', "tokens_used": 12, "cost": 0.0015},
    ]
    
    llm_service = MockLLMService(responses)
    
    members = [
        CommitteeMember("Alice", "role1", llm_service, base_weight=1.0, initial_reputation=1.0),
        CommitteeMember("Bob", "role2", llm_service, base_weight=1.5, initial_reputation=1.0),
        CommitteeMember("Charlie", "role3", llm_service, base_weight=1.0, initial_reputation=1.0),
    ]
    return members


def test_committee_creation():
    """Test committee creation with basic parameters."""
    members = []
    strategy = WeightedMajorityVote()
    committee = Committee("Test Committee", members, strategy)
    
    assert committee.name == "Test Committee"
    assert committee.members == members
    assert committee.voting_strategy == strategy
    assert committee.reputation_manager is None


def test_committee_with_reputation_manager():
    """Test committee creation with reputation manager."""
    members = []
    strategy = WeightedMajorityVote()
    reputation_manager = ReputationManager(members, agreement_bonus=0.1, dissent_penalty=0.05)
    committee = Committee("Test Committee", members, strategy, reputation_manager)
    
    assert committee.reputation_manager == reputation_manager


@pytest.mark.asyncio
async def test_deliberation_success(mock_members):
    """Test successful deliberation with all members voting."""
    strategy = WeightedMajorityVote()
    committee = Committee("Test Committee", mock_members, strategy)
    
    result = await committee.deliberate("Should we proceed?")
    
    assert result.topic == "Should we proceed?"
    assert result.strategy_used == "WeightedMajorityVote"
    assert result.final_result == "yes"  # 2 yes votes vs 1 no vote
    assert len(result.trace) == 3
    assert result.total_tokens == 37  # 10 + 15 + 12
    assert result.total_cost == pytest.approx(0.0045)  # 0.001 + 0.002 + 0.0015


@pytest.mark.asyncio
async def test_deliberation_with_member_failure(mock_members):
    """Test deliberation when one member fails to vote."""
    # Override the second member's LLM service to fail
    mock_members[1].llm_service.responses[1] = {"error": "API Error", "response": "", "tokens_used": 0, "cost": 0.0}
    
    strategy = WeightedMajorityVote()
    committee = Committee("Test Committee", mock_members, strategy)
    
    result = await committee.deliberate("Should we proceed?")
    
    assert result.final_result == "yes"  # 2 yes votes vs 0 no votes (1 failed)
    assert len(result.trace) == 3
    assert result.trace[1]["status"] == "Failed: API Error"


@pytest.mark.asyncio
async def test_deliberation_with_reputation_updates(mock_members):
    """Test deliberation with reputation management enabled."""
    strategy = WeightedMajorityVote()
    reputation_manager = ReputationManager(mock_members, agreement_bonus=0.1, dissent_penalty=0.05)
    committee = Committee("Test Committee", mock_members, strategy, reputation_manager)
    
    # Store initial reputations
    initial_reputations = [m.reputation for m in mock_members]
    
    result = await committee.deliberate("Should we proceed?")
    
    # Check that reputations were updated
    # Check that reputations were updated correctly
    # Final result is "yes", so:
    # - Alice voted "yes" -> should get reputation boost
    # - Bob voted "no" -> should get reputation penalty
    # - Charlie voted "yes" -> should get reputation boost
    assert mock_members[0].reputation > initial_reputations[0]  # Alice agreed
    assert mock_members[1].reputation < initial_reputations[1]  # Bob disagreed
    assert mock_members[2].reputation > initial_reputations[2]  # Charlie agreed


@pytest.mark.asyncio
async def test_deliberation_trace_structure(mock_members):
    """Test that deliberation trace contains all required fields."""
    strategy = WeightedMajorityVote()
    committee = Committee("Test Committee", mock_members, strategy)
    
    result = await committee.deliberate("Test topic")
    
    for trace_step in result.trace:
        required_fields = [
            "member_object", "member_name", "reputation", "effective_weight",
            "llm_service", "raw_opinion", "parsed_vote", "status", "cost", "tokens_used"
        ]
        for field in required_fields:
            assert field in trace_step


@pytest.mark.asyncio
async def test_deliberation_empty_members():
    """Test deliberation with no members."""
    strategy = WeightedMajorityVote()
    committee = Committee("Empty Committee", [], strategy)
    
    result = await committee.deliberate("Test topic")
    
    assert result.final_result == "No valid votes."
    assert len(result.trace) == 0
    assert result.total_tokens == 0
    assert result.total_cost == 0.0


@pytest.mark.asyncio
async def test_deliberation_all_members_fail():
    """Test deliberation when all members fail to vote."""
    # Create members that all fail
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