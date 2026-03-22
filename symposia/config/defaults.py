"""
Default configuration for Symposia.

This module provides minimal default configuration that can be used
as a fallback when no external configuration file is found.
"""

DEFAULT_CONFIG = {
    'llm_services': {
        'openai_gpt4o_mini': {
            'provider': 'openai',
            'model': 'gpt-4o-mini',
            'cost_per_token': {
                'input': 0.00000015,
                'output': 0.0000006
            }
        },
        'claude_sonnet': {
            'provider': 'anthropic',
            'model': 'claude-sonnet-4-5-20250929',
            'cost_per_token': {
                'input': 0.000003,
                'output': 0.000015
            }
        },
        'gemini_1.5': {
            'provider': 'google',
            'model': 'gemini-2.5-flash-lite',
            'cost_per_token': {
                'input': 0.000001,
                'output': 0.0000025
            }
        }
    },
    'intelligence_pools': {
        'default_committee': {
            'name': 'Default Committee',
            'reputation_management': False,
            'members': [
                {
                    'name': 'Default OpenAI',
                    'service': 'openai_gpt4o_mini',
                    'weight': 1.0,
                    'initial_reputation': 1.0,
                    'role_prompt': 'You are a helpful AI assistant.'
                },
                {
                    'name': 'Default Claude',
                    'service': 'claude_sonnet',
                    'weight': 1.0,
                    'initial_reputation': 1.0,
                    'role_prompt': 'You are a helpful AI assistant.'
                },
                {
                    'name': 'Default Gemini',
                    'service': 'gemini_1.5',
                    'weight': 1.0,
                    'initial_reputation': 1.0,
                    'role_prompt': 'You are a helpful AI assistant.'
                }
            ]
        }
    }
} 