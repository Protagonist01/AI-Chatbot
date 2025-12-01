#!/usr/bin/env python3
"""
CLI tool to generate JWT tokens for agents
Usage: python generate_agent_token.py agent_id agent_name
"""

import sys
from auth import create_agent_token

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_agent_token.py <agent_id> <agent_name>")
        print("Example: python generate_agent_token.py agent_001 'John Doe'")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    agent_name = sys.argv[2]
    
    token = create_agent_token(agent_id, agent_name)
    
    print("\n" + "="*60)
    print("🎫 AGENT TOKEN GENERATED")
    print("="*60)
    print(f"\nAgent ID:   {agent_id}")
    print(f"Agent Name: {agent_name}")
    print(f"\n🔑 TOKEN:\n{token}")
    print("\n" + "="*60)
    print("\n⚠️  Keep this token secure! It grants access to the agent console.")
    print("📋 Copy this token and paste it into the agent console login.\n")

if __name__ == "__main__":
    main()