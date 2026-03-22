import pytest

pytestmark = pytest.mark.core
from symposia.config.models import LLMServiceConfig, MemberConfig, PoolConfig, AppConfig


def test_llm_service_config():
    cfg = LLMServiceConfig(provider='openai', model='gpt-4', cost_per_token=0.001, api_key='key')
    assert cfg.provider == 'openai'
    assert cfg.model == 'gpt-4'
    assert cfg.cost_per_token.input == 0.001
    assert cfg.cost_per_token.output == 0.001
    assert cfg.api_key == 'key'


def test_member_config_alias():
    cfg = MemberConfig(name='Alice', service='svc', role_prompt='role', weight=2.5)
    assert cfg.base_weight == 2.5
    assert cfg.name == 'Alice'


def test_pool_config():
    member = MemberConfig(name='Bob', service='svc', role_prompt='role')
    pool = PoolConfig(name='pool', members=[member])
    assert pool.name == 'pool'
    assert pool.members[0].name == 'Bob'
    assert pool.reputation_management is False


def test_app_config():
    llm_services = {'svc': LLMServiceConfig(provider='openai', model='gpt-4', cost_per_token=0.001)}
    member = MemberConfig(name='Alice', service='svc', role_prompt='role')
    pools = {'pool': PoolConfig(name='pool', members=[member])}
    app_cfg = AppConfig(llm_services=llm_services, intelligence_pools=pools)
    assert 'svc' in app_cfg.llm_services
    assert 'pool' in app_cfg.intelligence_pools


def test_app_config_decomposition_mode_defaults_to_holistic():
    llm_services = {'svc': LLMServiceConfig(provider='openai', model='gpt-4', cost_per_token=0.001)}
    member = MemberConfig(name='Alice', service='svc', role_prompt='role')
    pools = {'pool': PoolConfig(name='pool', members=[member])}
    app_cfg = AppConfig(llm_services=llm_services, intelligence_pools=pools)
    assert app_cfg.decomposition_mode == "holistic"


def test_invalid_llm_service_config():
    with pytest.raises(Exception):
        LLMServiceConfig(provider='openai', model='gpt-4')  # missing cost_per_token 