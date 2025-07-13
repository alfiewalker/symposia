#!/usr/bin/env python3
"""
Symposia Example - AI Committee Deliberation Framework

This example demonstrates how to use the Symposia API directly.
It showcases committee creation, deliberation, and voting strategies.
"""

import asyncio
import os
from dotenv import load_dotenv
from symposia.config.factory import CommitteeFactory
from symposia.strategies import WeightedMajorityVote, WeightedMeanScore
from symposia.config.loader import load_config

# Load environment variables
load_dotenv(dotenv_path=".env.local", override=True)


async def create_committee_from_config():
    """Create a committee using the configuration file."""
    print("🤖 Creating Committee from Configuration...")
    
    # Load configuration
    config_dict = load_config("symposia.local.yaml")
    
    # Create factory
    factory = CommitteeFactory(config_dict)
    
    # Create committee using the clone_committee pool
    committee = factory.create_committee("clone_committee", "WeightedMajorityVote")
    
    return committee


async def run_deliberation(committee, question, strategy_class=WeightedMajorityVote):
    """Run a deliberation with the given committee and strategy."""
    print(f"\n📝 Question: {question}")
    print(f"🎯 Strategy: {strategy_class.__name__}")
    print("=" * 60)
    
    # Create voting strategy
    strategy = strategy_class()
    
    # Run deliberation
    result = await committee.deliberate(question)
    
    print(f"\n🏆 Final Decision: {result.final_result}")
    print(f"💰 Total Cost: ${result.total_cost:.6f}")
    
    print("\n📋 Individual Votes:")
    for trace in result.trace:
        if trace['status'] == "Success":
            vote = trace['parsed_vote'].get('vote', 'No vote')
            reasoning = trace['parsed_vote'].get('reasoning', 'No reasoning provided')
            print(f"  • {trace['member_name']}: {vote}")
            print(f"    Reasoning: {reasoning}")
        else:
            print(f"  • {trace['member_name']}: {trace['status']}")
    
    return result


async def main():
    """Main example function."""
    print("🚀 Symposia Example - AI Committee Deliberation")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in .env.local")
        return
    
    try:
        # Create committee from configuration
        committee = await create_committee_from_config()
        print(f"✅ Created committee '{committee.name}' with {len(committee.members)} members")
        
        # Example questions for validation scenarios
        topic_prompt_health = """If you're experiencing chest pain, shortness of breath, and dizziness, these could be signs of a heart attack. You should immediately call 911 or go to the nearest emergency room. While waiting for help, chew an aspirin if you're not allergic, and try to stay calm. Don't drive yourself to the hospital."""
        
        topic_prompt_finance = """To build wealth in your 20s, put 50% of your income into index funds, 30% into cryptocurrency, and 20% into individual stocks. Avoid bonds completely as they're for older people. You should also take out loans to invest more money since the market always goes up in the long run."""
        
        topic_prompt_coding = """Here's how to securely store passwords in a web application:

```python
import hashlib

def store_password(password):
    # Simple MD5 hash for password storage
    hashed = hashlib.md5(password.encode()).hexdigest()
    return hashed

def verify_password(stored_hash, password):
    return stored_hash == hashlib.md5(password.encode()).hexdigest()
```

This MD5 approach is efficient and provides good security for most applications."""
        
        questions = [
            topic_prompt_health,
            topic_prompt_finance,
            topic_prompt_coding
        ]
        
        # Test different voting strategies
        strategies = [WeightedMajorityVote]
        
        for i, question in enumerate(questions, 1):
            scenario_types = ["Health Advice", "Financial Advice", "Coding Solution"]
            print(f"\n{'='*20} {scenario_types[i-1]} Validation {'='*20}")
            
            for strategy in strategies:
                try:
                    await run_deliberation(committee, question, strategy)
                    print("\n" + "-" * 40)
                except Exception as e:
                    print(f"❌ Error with {strategy.__name__}: {e}")
                    continue
        
        print("\n🎉 Example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 