"""
Symposia CLI - Elegant command-line interface for the Symposia framework.

This module provides a comprehensive CLI for managing and running committee deliberations.
"""

import asyncio
import sys
import argparse
from .services import SymposiaCLI
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env.local'), override=True)


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog='symposia',
        description='🤖 Symposia - AI Committee Deliberation Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  symposia list-pools                    # List available intelligence pools
  symposia list-services                 # List available LLM services
  symposia check                         # Check environment configuration
  symposia ask clone_committee "Is AI safe?"  # Run single deliberation
  symposia interactive                   # Start interactive mode
  symposia --config examples/symposia.yaml list-pools  # Use specific config
        """
    )
    
    # Global options
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file (overrides default search)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List pools command
    list_pools_parser = subparsers.add_parser(
        'list-pools', 
        aliases=['pools', 'lp'],
        help='List available intelligence pools'
    )
    list_pools_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed pool information'
    )
    
    # List services command
    list_services_parser = subparsers.add_parser(
        'list-services',
        aliases=['services', 'ls'],
        help='List available LLM services'
    )
    
    # Check environment command
    check_parser = subparsers.add_parser(
        'check',
        aliases=['env'],
        help='Check environment configuration'
    )
    
    # Ask command
    ask_parser = subparsers.add_parser(
        'ask',
        help='Run a single deliberation'
    )
    ask_parser.add_argument(
        'pool',
        help='Name of the intelligence pool to use'
    )
    ask_parser.add_argument(
        'question',
        help='Question to deliberate on'
    )
    ask_parser.add_argument(
        '--strategy', '-s',
        default='WeightedMajorityVote',
        help='Voting strategy to use (default: WeightedMajorityVote)'
    )
    
    # Interactive command
    interactive_parser = subparsers.add_parser(
        'interactive',
        aliases=['i'],
        help='Start interactive deliberation mode'
    )
    
    return parser


async def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = SymposiaCLI()
    
    # Load configuration for commands that need it
    if args.command not in ['check']:
        if not cli.load_configuration(config_path=args.config):
            print("❌ Failed to load configuration")
            sys.exit(1)
    
    # Execute commands
    if args.command in ['list-pools', 'pools', 'lp']:
        cli.list_pools(args.verbose)
    elif args.command in ['list-services', 'services', 'ls']:
        cli.list_services()
    elif args.command in ['check', 'env']:
        cli.load_configuration(config_path=args.config)  # Load for check, but don't exit on failure
        cli.check_environment()
    elif args.command == 'ask':
        success = await cli.run_deliberation(args.pool, args.question, args.strategy)
        if not success:
            sys.exit(1)
    elif args.command in ['interactive', 'i']:
        await cli.run_interactive()
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())


def entrypoint():
    import asyncio
    asyncio.run(main()) 