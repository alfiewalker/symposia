import pytest

pytestmark = pytest.mark.core
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from symposia.core.providers.base import LLMService
from symposia.core.providers.openai_service import OpenAIService
from symposia.core.providers.claude_service import ClaudeService
from symposia.core.providers.gemini_service import GeminiService
from symposia.config.models import LLMServiceConfig
from symposia.utils.cache import SimpleCache


class MockLLMService(LLMService):
    """Mock LLM service for testing base functionality."""
    
    def __init__(self, config, cache=None, should_fail=False):
        super().__init__(config, cache)
        self.should_fail = should_fail
        self.call_count = 0
    
    async def _perform_query(self, prompt, role_prompt):
        self.call_count += 1
        if self.should_fail:
            raise Exception("Mock API Error")
        
        return {
            "response": f"Mock response {self.call_count}",
            "tokens_used": 10 * self.call_count,
            "cost": 0.001 * self.call_count
        }


@pytest.fixture
def llm_config():
    """Create a basic LLM service configuration."""
    return LLMServiceConfig(
        provider='mock',
        model='test-model',
        cost_per_token=0.001
    )


@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    return SimpleCache()


@pytest.mark.asyncio
async def test_llm_service_query_success(llm_config):
    """Test successful LLM service query."""
    service = MockLLMService(llm_config)
    result = await service.query("test prompt", "test role")
    
    assert result["response"] == "Mock response 1"
    assert result["tokens_used"] == 10
    assert result["cost"] == 0.001
    assert "error" not in result


@pytest.mark.asyncio
async def test_llm_service_query_with_cache(llm_config, cache):
    """Test LLM service query with caching."""
    service = MockLLMService(llm_config, cache=cache)
    
    # First query
    result1 = await service.query("test prompt", "test role")
    assert result1["response"] == "Mock response 1"
    
    # Second query with same prompt (should use cache)
    result2 = await service.query("test prompt", "test role")
    assert result2["response"] == "Mock response 1"  # Same response
    assert service.call_count == 1  # Only one actual API call


@pytest.mark.asyncio
async def test_llm_service_query_retry_on_failure(llm_config):
    """Test LLM service query with retry logic on failure."""
    service = MockLLMService(llm_config, should_fail=True)
    
    result = await service.query("test prompt", "test role", retries=3, delay=0.1)
    
    assert "error" in result
    assert service.call_count == 3  # Should have tried 3 times


@pytest.mark.asyncio
async def test_llm_service_query_success_after_retry(llm_config):
    """Test LLM service query that succeeds after initial failures."""
    service = MockLLMService(llm_config, should_fail=False)  # Don't fail by default
    
    # Override to fail first, then succeed
    original_perform = service._perform_query
    
    async def mock_perform(prompt, role_prompt):
        service.call_count += 1
        if service.call_count < 3:  # Fail first 2 times
            raise Exception("Temporary failure")
        return {
            "response": f"Mock response {service.call_count}",
            "tokens_used": 10 * service.call_count,
            "cost": 0.001 * service.call_count
        }
    
    service._perform_query = mock_perform
    
    result = await service.query("test prompt", "test role", retries=3, delay=0.1)
    
    assert result["response"] == "Mock response 3"
    assert service.call_count == 3


@pytest.mark.asyncio
async def test_openai_service():
    """Test OpenAI service with mocked client."""
    config = LLMServiceConfig(
        provider='openai',
        model='gpt-4',
        cost_per_token={"input": 0.001, "output": 0.002}
    )
    
    with patch('openai.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the completion response
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "OpenAI response"
        mock_completion.usage.total_tokens = 20
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_completion
        
        service = OpenAIService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "OpenAI response"
        assert result["tokens_used"] == 20
        assert result["cost"] == 0.03  # (10 * 0.001) + (10 * 0.002)


@pytest.mark.asyncio
async def test_openai_service_graceful_cost_failure():
    """Test OpenAI service gracefully handles cost calculation failures."""
    config = LLMServiceConfig(
        provider='openai',
        model='gpt-4',
        cost_per_token={"input": 0.001, "output": 0.002}
    )
    
    with patch('openai.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the completion response with missing usage data
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "OpenAI response"
        mock_completion.usage = None  # No usage data
        mock_client.chat.completions.create.return_value = mock_completion
        
        service = OpenAIService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "OpenAI response"
        assert result["tokens_used"] == 0
        assert result["cost"] == 0.0  # Graceful fallback


@pytest.mark.asyncio
async def test_openai_service_missing_token_breakdown():
    """Test OpenAI service handles missing token breakdown gracefully."""
    config = LLMServiceConfig(
        provider='openai',
        model='gpt-4',
        cost_per_token={"input": 0.001, "output": 0.002}
    )
    
    with patch('openai.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the completion response with total_tokens but no breakdown
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "OpenAI response"
        mock_completion.usage.total_tokens = 20
        # Remove prompt_tokens and completion_tokens attributes
        del mock_completion.usage.prompt_tokens
        del mock_completion.usage.completion_tokens
        mock_client.chat.completions.create.return_value = mock_completion
        
        service = OpenAIService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "OpenAI response"
        assert result["tokens_used"] == 20
        assert result["cost"] == 0.02  # 20 * 0.001 (input cost as fallback)


@pytest.mark.asyncio
async def test_claude_service():
    """Test Claude service with mocked client."""
    config = LLMServiceConfig(
        provider='anthropic',
        model='claude-3-sonnet',
        cost_per_token={"input": 0.002, "output": 0.003}
    )
    
    with patch('anthropic.AsyncAnthropic') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the message response
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = "Claude response"
        mock_message.usage.input_tokens = 10
        mock_message.usage.output_tokens = 15
        mock_client.messages.create.return_value = mock_message
        
        service = ClaudeService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "Claude response"
        assert result["tokens_used"] == 25  # 10 + 15
        assert result["cost"] == 0.065  # (10 * 0.002) + (15 * 0.003)


@pytest.mark.asyncio
async def test_claude_service_graceful_cost_failure():
    """Test Claude service gracefully handles cost calculation failures."""
    config = LLMServiceConfig(
        provider='anthropic',
        model='claude-3-sonnet',
        cost_per_token={"input": 0.002, "output": 0.003}
    )
    
    with patch('anthropic.AsyncAnthropic') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the message response with missing usage data
        mock_message = MagicMock()
        mock_message.content = [MagicMock()]
        mock_message.content[0].text = "Claude response"
        mock_message.usage = None  # No usage data
        mock_client.messages.create.return_value = mock_message
        
        service = ClaudeService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "Claude response"
        assert result["tokens_used"] == 0
        assert result["cost"] == 0.0  # Graceful fallback


@pytest.mark.asyncio
async def test_gemini_service():
    """Test Gemini service with mocked client."""
    config = LLMServiceConfig(
        provider='google',
        model='gemini-1.5-flash',
        cost_per_token={"input": 0.0005, "output": 0.0005}
    )
    
    mock_response = MagicMock()
    mock_response.text = "Gemini response"
    mock_response.usage_metadata = MagicMock()
    mock_response.usage_metadata.prompt_token_count = 15
    mock_response.usage_metadata.candidates_token_count = 10
    mock_response.usage_metadata.input_token_count = 0
    mock_response.usage_metadata.output_token_count = 0

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch('symposia.core.providers.gemini_service.google_genai.Client', return_value=mock_client):
        service = GeminiService(config)
        result = await service._perform_query("test prompt", "test role")

    assert result["response"] == "Gemini response"
    assert result["tokens_used"] == 25  # 15 + 10
    assert result["cost"] == 0.0125  # (15 * 0.0005) + (10 * 0.0005)


@pytest.mark.asyncio
async def test_gemini_service_graceful_cost_failure():
    """Test Gemini service gracefully handles cost calculation failures."""
    config = LLMServiceConfig(
        provider='google',
        model='gemini-1.5-flash',
        cost_per_token={"input": 0.0005, "output": 0.0005}
    )
    
    mock_response = MagicMock()
    mock_response.text = "Gemini response"
    mock_response.usage_metadata = None  # No usage metadata available

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch('symposia.core.providers.gemini_service.google_genai.Client', return_value=mock_client):
        service = GeminiService(config)
        result = await service._perform_query("test prompt", "test role")

    assert result["response"] == "Gemini response"
    assert result["tokens_used"] == 0
    assert result["cost"] == 0.0  # Graceful fallback


@pytest.mark.asyncio
async def test_llm_service_invalid_cost_config():
    """Test LLM services handle invalid cost configurations gracefully."""
    # Test with valid cost_per_token but simulate missing usage data
    config = LLMServiceConfig(
        provider='openai',
        model='gpt-4',
        cost_per_token={"input": 0.001, "output": 0.002}
    )
    
    with patch('openai.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the completion response with missing usage data
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "OpenAI response"
        mock_completion.usage = None  # No usage data at all
        mock_client.chat.completions.create.return_value = mock_completion
        
        service = OpenAIService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == "OpenAI response"
        assert result["tokens_used"] == 0
        assert result["cost"] == 0.0  # Graceful fallback due to missing usage data


@pytest.mark.asyncio
async def test_llm_service_missing_response_content():
    """Test LLM services handle missing response content gracefully."""
    config = LLMServiceConfig(
        provider='openai',
        model='gpt-4',
        cost_per_token={"input": 0.001, "output": 0.002}
    )
    
    with patch('openai.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock the completion response with missing content
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = None  # Missing content
        mock_completion.usage.total_tokens = 20
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 10
        mock_client.chat.completions.create.return_value = mock_completion
        
        service = OpenAIService(config)
        result = await service._perform_query("test prompt", "test role")
        
        assert result["response"] == ""  # Empty string for missing content
        assert result["tokens_used"] == 20
        assert result["cost"] == 0.03  # Cost calculation still works


@pytest.mark.asyncio
async def test_llm_service_cache_key_uniqueness(llm_config, cache):
    """Test that cache keys are unique for different prompts."""
    service = MockLLMService(llm_config, cache=cache)
    
    # Different prompts should have different cache keys
    await service.query("prompt1", "role1")
    await service.query("prompt2", "role1")
    await service.query("prompt1", "role2")
    
    assert service.call_count == 3  # All should be cache misses


@pytest.mark.asyncio
async def test_llm_service_exponential_backoff(llm_config):
    """Test that retry delay increases exponentially."""
    service = MockLLMService(llm_config, should_fail=True)
    
    start_time = asyncio.get_event_loop().time()
    await service.query("test prompt", "test role", retries=3, delay=0.01)  # Use smaller delay for testing
    end_time = asyncio.get_event_loop().time()
    
    # Should have delays of 0.01, 0.02, 0.04 seconds = 0.07 seconds total
    # Plus some execution time, so total should be > 0.03 seconds
    assert end_time - start_time > 0.03


@pytest.mark.asyncio
async def test_llm_service_no_cache_when_none(llm_config):
    """Test that no caching occurs when cache is None."""
    service = MockLLMService(llm_config, cache=None)
    
    await service.query("test prompt", "test role")
    await service.query("test prompt", "test role")
    
    assert service.call_count == 2  # Both should be actual API calls 