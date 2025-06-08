"""
GPT Router CLI
--------------
Test tool for the prompt routing system.
"""

import argparse
from pathlib import Path
from .prompt_router import PromptRouter


def main():
    parser = argparse.ArgumentParser(description="Test GPT prompt routing")
    parser.add_argument("context", help="Conversation context or URL to route")
    parser.add_argument(
        "--profiles-dir",
        type=Path,
        default=Path(__file__).parent / "profiles",
        help="Directory containing profile YAML files",
    )
    
    args = parser.parse_args()
    
    router = PromptRouter(profiles_dir=args.profiles_dir)
    profile = router.decide_prompt(args.context)
    
    print("\nRouting Result:")
    print("--------------")
    print(f"Context: {args.context}")
    print(f"Selected Profile: {profile['gpt_profile']}")
    print(f"Temperature: {profile.get('temperature', 'N/A')}")
    print(f"Max Tokens: {profile.get('max_tokens', 'N/A')}")
    print("\nPrompt:")
    print(profile['prompt'])
    print("\nValidation Rules:")
    for rule in profile.get('validation_rules', []):
        print(f"- {rule['type']} (required: {rule['required']})")


if __name__ == "__main__":
    main() 