import logging
import os
from typing import Optional
from symposia.config.factory import CommitteeFactory
from symposia.config.loader import load_config, get_config_path
from symposia.utils import SimpleCache

logger = logging.getLogger(__name__)

class SymposiaCLI:
    def __init__(self):
        self.config = None
        self.config_source = None
        self.cache = SimpleCache()
        self.factory = None
        self._config_dict = None

    def load_configuration(self, config_path: Optional[str] = None):
        """Load and validate configuration without initializing services."""
        try:
            self._config_dict = load_config(config_path)
            self.config_source = get_config_path()
            # Don't initialize factory yet - do it lazily when needed
            logger.info(f"Configuration loaded from: {self.config_source}")
            return True
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def _ensure_factory(self):
        """Ensure factory is initialized when needed."""
        if self.factory is None and self._config_dict is not None:
            try:
                self.factory = CommitteeFactory(self._config_dict, cache=self.cache)
                self.config = self.factory.config
            except Exception as e:
                logger.error(f"Failed to initialize services: {e}")
                raise

    def list_pools(self, verbose: bool = False):
        """List available intelligence pools."""
        if not self._config_dict:
            print("❌ No configuration loaded")
            return False
            
        pools = self._config_dict.get('intelligence_pools', {})
        if not pools:
            print("❌ No intelligence pools found in configuration")
            return False
        
        print("🤖 Available Intelligence Pools:")
        print("=" * 50)
        
        for name, config in pools.items():
            member_count = len(config.get('members', []))
            reputation_enabled = config.get('reputation_management', False)
            status = "🟢 Active" if reputation_enabled else "🟡 Basic"
            
            print(f"\n📋 {name}")
            print(f"   Name: {config.get('name', 'Unnamed')}")
            print(f"   Members: {member_count}")
            print(f"   Reputation: {status}")
            
            if verbose:
                print(f"   Agreement Bonus: {config.get('agreement_bonus', 'N/A')}")
                print(f"   Dissent Penalty: {config.get('dissent_penalty', 'N/A')}")
                
                print("   Members:")
                for member in config.get('members', []):
                    service = member.get('service', 'Unknown')
                    weight = member.get('weight', 1.0)
                    print(f"     • {member.get('name', 'Unnamed')} ({service}, weight: {weight})")
        
        return True

    def list_services(self):
        """List available LLM services."""
        if not self._config_dict:
            print("❌ No configuration loaded")
            return False
            
        services = self._config_dict.get('llm_services', {})
        if not services:
            print("❌ No LLM services found in configuration")
            return False
        
        print("🔧 Available LLM Services:")
        print("=" * 40)
        
        for name, config in services.items():
            provider = config.get('provider', 'Unknown')
            model = config.get('model', 'Unknown')
            cost = config.get('cost_per_token', {})
            
            if isinstance(cost, dict):
                input_cost = cost.get('input', 'N/A')
                output_cost = cost.get('output', 'N/A')
                cost_str = f"Input: ${input_cost}, Output: ${output_cost}"
            else:
                cost_str = f"${cost}"
            
            print(f"\n🔗 {name}")
            print(f"   Provider: {provider}")
            print(f"   Model: {model}")
            print(f"   Cost: {cost_str}")
        
        return True

    async def run_deliberation(self, pool_name: str, question: str, strategy: str = 'WeightedMajorityVote'):
        """Run a single deliberation."""
        if not self._config_dict:
            print("❌ No configuration loaded")
            return False
            
        if pool_name not in self._config_dict['intelligence_pools']:
            available_pools = list(self._config_dict['intelligence_pools'].keys())
            print(f"❌ Pool '{pool_name}' not found")
            print(f"Available pools: {', '.join(available_pools)}")
            return False
        
        try:
            self._ensure_factory()
            committee = self.factory.create_committee(pool_name, strategy)
            print(f"\n🤖 Running deliberation with: {committee.name}")
            print(f"📝 Question: {question}")
            print(f"🎯 Strategy: {strategy}")
            print("=" * 60)
            
            result = await committee.deliberate(question)
            result.display_trace()
            
            return True
            
        except Exception as e:
            logger.error(f"Deliberation failed: {e}")
            return False

    async def run_interactive(self):
        """Run interactive deliberation mode."""
        if not self._config_dict:
            print("❌ No configuration loaded")
            return False
        
        pools = list(self._config_dict['intelligence_pools'].keys())
        if not pools:
            print("❌ No intelligence pools available")
            return False
        
        print("\n🎯 Interactive Deliberation Mode")
        print("=" * 40)
        print("Available pools:", ", ".join(pools))
        print("Type 'quit' to exit, 'help' for commands")
        
        while True:
            try:
                command = input("\n🤖 symposia> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif command.lower() in ['help', 'h']:
                    self.show_interactive_help()
                elif command.lower() in ['pools', 'list']:
                    self.list_pools()
                elif command.lower() in ['services']:
                    self.list_services()
                elif command.startswith('ask '):
                    # Format: ask <pool> <question>
                    parts = command[4:].split(' ', 1)
                    if len(parts) < 2:
                        print("❌ Usage: ask <pool> <question>")
                        continue
                    
                    pool_name, question = parts
                    if pool_name not in pools:
                        print(f"❌ Pool '{pool_name}' not found")
                        continue
                    
                    await self.run_deliberation(pool_name, question)
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def show_interactive_help(self):
        """Show help for interactive mode."""
        help_text = """
📖 Interactive Commands:
  ask <pool> <question>  - Run deliberation with specific pool and question
  pools                  - List available intelligence pools
  services               - List available LLM services
  help                   - Show this help message
  quit                   - Exit interactive mode
        """
        print(help_text)

    def check_environment(self):
        """Check if environment is properly configured."""
        print("🔍 Environment Check:")
        print("=" * 30)
        
        # Check API keys
        required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]
        api_keys_found = []
        
        for key in required_keys:
            if os.getenv(key):
                api_keys_found.append(key.replace('_API_KEY', ''))
        
        if api_keys_found:
            print(f"✅ API Keys found: {', '.join(api_keys_found)}")
        else:
            print("❌ No API keys found")
            print("   Please set at least one API key in your .env file")
        
        # Check configuration
        if self._config_dict:
            print(f"✅ Configuration loaded from: {self.config_source}")
            pool_count = len(self._config_dict.get('intelligence_pools', {}))
            service_count = len(self._config_dict.get('llm_services', {}))
            print(f"✅ Found {pool_count} intelligence pools and {service_count} LLM services")
        else:
            print("❌ Configuration not loaded")
            print("   This may be due to missing API keys or configuration errors")
        
        return len(api_keys_found) > 0 and self._config_dict is not None 