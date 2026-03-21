import pytest

pytestmark = pytest.mark.core
from unittest.mock import MagicMock
from symposia.config.factory import CommitteeFactory
from symposia.config.models import LLMServiceConfig, MemberConfig, PoolConfig, AppConfig
from symposia.strategies.majority import WeightedMajorityVote
from symposia.strategies.mean import WeightedMeanScore
from symposia.strategies.median import MedianScore


@pytest.fixture
def valid_config():
    """Create a valid configuration for testing."""
    return {
        'llm_services': {
            'mock_service': {
                'provider': 'mock',
                'model': 'mock-model',
                'cost_per_token': 0.001
            }
        },
        'intelligence_pools': {
            'test_pool': {
                'name': 'Test Pool',
                'reputation_management': True,
                'agreement_bonus': 0.1,
                'dissent_penalty': 0.05,
                'members': [
                    {
                        'name': 'Alice',
                        'service': 'mock_service',
                        'role_prompt': 'You are a scientist.',
                        'weight': 1.5,
                        'initial_reputation': 1.0
                    },
                    {
                        'name': 'Bob',
                        'service': 'mock_service',
                        'role_prompt': 'You are an ethicist.',
                        'weight': 1.0,
                        'initial_reputation': 1.0
                    }
                ]
            }
        }
    }


def test_factory_creation(valid_config):
    """Test factory creation with valid configuration."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    
    assert factory.config is not None
    assert len(factory.services) == 1
    assert 'mock_service' in factory.services


def test_factory_invalid_config():
    """Test factory creation with invalid configuration."""
    invalid_config = {
        'llm_services': {},
        'intelligence_pools': {}
    }
    
    # This should pass validation since empty dicts are valid
    factory = CommitteeFactory(invalid_config)
    assert factory.config is not None


def test_factory_unknown_provider():
    """Test factory with unknown LLM provider."""
    config = {
        'llm_services': {
            'unknown_service': {
                'provider': 'unknown_provider',
                'model': 'unknown-model',
                'cost_per_token': 0.001
            }
        },
        'intelligence_pools': {}
    }
    
    with pytest.raises(ValueError, match="Unknown provider"):
        factory = CommitteeFactory(config)
        factory._init_services()


def test_create_committee_success(valid_config):
    """Test successful committee creation."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    committee = factory.create_committee('test_pool', 'WeightedMajorityVote')
    
    assert committee.name == 'Test Pool'
    assert len(committee.members) == 2
    assert committee.reputation_manager is not None
    assert isinstance(committee.voting_strategy, WeightedMajorityVote)


def test_create_committee_unknown_pool(valid_config):
    """Test committee creation with unknown pool."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    
    with pytest.raises(ValueError, match="Pool 'unknown_pool' not found"):
        factory.create_committee('unknown_pool', 'WeightedMajorityVote')


def test_create_committee_unknown_strategy(valid_config):
    """Test committee creation with unknown strategy."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    
    with pytest.raises(ValueError, match="Strategy 'UnknownStrategy' not found"):
        factory.create_committee('test_pool', 'UnknownStrategy')


def test_create_committee_missing_service(valid_config):
    """Test committee creation with missing LLM service."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    # Modify config to reference non-existent service
    valid_config['intelligence_pools']['test_pool']['members'][0]['service'] = 'missing_service'
    factory = CommitteeFactory(valid_config)
    
    with pytest.raises(ValueError, match="Service 'missing_service' not found"):
        factory.create_committee('test_pool', 'WeightedMajorityVote')


def test_create_committee_without_reputation(valid_config):
    """Test committee creation without reputation management."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    valid_config['intelligence_pools']['test_pool']['reputation_management'] = False
    factory = CommitteeFactory(valid_config)
    committee = factory.create_committee('test_pool', 'WeightedMajorityVote')
    
    assert committee.reputation_manager is None


def test_create_committee_all_strategies(valid_config):
    """Test committee creation with all available strategies."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    
    strategies = ['WeightedMajorityVote', 'WeightedMeanScore', 'MedianScore']
    strategy_classes = [WeightedMajorityVote, WeightedMeanScore, MedianScore]
    
    for strategy_name, expected_class in zip(strategies, strategy_classes):
        committee = factory.create_committee('test_pool', strategy_name)
        assert isinstance(committee.voting_strategy, expected_class)


def test_factory_with_cache(valid_config):
    """Test factory creation with cache."""
    from symposia.utils.cache import SimpleCache
    
    # Create a proper mock service class that accepts cache
    class MockServiceClass:
        def __init__(self, config, cache=None):
            self.config = config
            self.cache = cache
    
    CommitteeFactory.PROVIDER_MAP['mock'] = MockServiceClass
    
    cache = SimpleCache()
    factory = CommitteeFactory(valid_config, cache=cache)
    
    # Verify cache is passed to services
    for service in factory.services.values():
        assert service.cache == cache


def test_member_weight_alias(valid_config):
    """Test that member weight alias works correctly."""
    # Add mock provider to factory for testing
    mock_service = MagicMock()
    CommitteeFactory.PROVIDER_MAP['mock'] = mock_service
    
    factory = CommitteeFactory(valid_config)
    committee = factory.create_committee('test_pool', 'WeightedMajorityVote')
    
    # Check that weight alias was properly converted to base_weight
    assert committee.members[0].base_weight == 1.5
    assert committee.members[1].base_weight == 1.0 