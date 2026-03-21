
import pytest

pytestmark = pytest.mark.core
import pytest
from symposia.utils.cache import SimpleCache


def test_cache_set_and_get():
    """Test basic cache set and get operations."""
    cache = SimpleCache()
    
    cache.set("key1", "value1")
    cache.set("key2", {"nested": "value"})
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == {"nested": "value"}


def test_cache_get_nonexistent():
    """Test getting a key that doesn't exist."""
    cache = SimpleCache()
    
    assert cache.get("nonexistent") is None


def test_cache_overwrite():
    """Test that setting a key overwrites the previous value."""
    cache = SimpleCache()
    
    cache.set("key", "value1")
    assert cache.get("key") == "value1"
    
    cache.set("key", "value2")
    assert cache.get("key") == "value2"


def test_cache_different_types():
    """Test caching different data types."""
    cache = SimpleCache()
    
    test_data = [
        "string",
        42,
        3.14,
        True,
        False,
        None,
        [1, 2, 3],
        {"a": 1, "b": 2},
        (1, 2, 3),
        {"nested": {"list": [1, 2, 3]}}
    ]
    
    for i, data in enumerate(test_data):
        cache.set(f"key{i}", data)
        assert cache.get(f"key{i}") == data


def test_cache_multiple_keys():
    """Test caching multiple keys independently."""
    cache = SimpleCache()
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


def test_cache_empty_key():
    """Test caching with empty string key."""
    cache = SimpleCache()
    
    cache.set("", "empty_key_value")
    assert cache.get("") == "empty_key_value"


def test_cache_none_value():
    """Test caching None value."""
    cache = SimpleCache()
    
    cache.set("key", None)
    assert cache.get("key") is None


def test_cache_large_data():
    """Test caching larger data structures."""
    cache = SimpleCache()
    
    large_list = list(range(1000))
    large_dict = {f"key{i}": f"value{i}" for i in range(100)}
    
    cache.set("large_list", large_list)
    cache.set("large_dict", large_dict)
    
    assert cache.get("large_list") == large_list
    assert cache.get("large_dict") == large_dict


def test_cache_case_sensitive():
    """Test that cache keys are case sensitive."""
    cache = SimpleCache()
    
    cache.set("Key", "value1")
    cache.set("key", "value2")
    cache.set("KEY", "value3")
    
    assert cache.get("Key") == "value1"
    assert cache.get("key") == "value2"
    assert cache.get("KEY") == "value3"


def test_cache_special_characters():
    """Test caching with special characters in keys."""
    cache = SimpleCache()
    
    special_keys = [
        "key with spaces",
        "key-with-dashes",
        "key_with_underscores",
        "key123",
        "key!@#$%^&*()",
        "key\n\t\r",
        "key with unicode: 🚀"
    ]
    
    for key in special_keys:
        cache.set(key, f"value for {key}")
        assert cache.get(key) == f"value for {key}" 