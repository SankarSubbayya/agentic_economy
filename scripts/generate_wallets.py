#!/usr/bin/env python3
"""
Generate Ethereum wallet addresses for Arc testnet.

Each wallet has:
- Public address (receiver)
- Private key (signer - KEEP SECRET!)
"""

from eth_account import Account
import json
from datetime import datetime

def generate_wallet(name: str = "User") -> dict:
    """Generate a new Ethereum wallet."""
    account = Account.create()
    return {
        "name": name,
        "address": account.address,
        "private_key": account.key.hex(),
        "generated_at": datetime.now().isoformat(),
    }

def main():
    print("=" * 80)
    print("Arc Testnet Wallet Generator")
    print("=" * 80)
    print()

    # Generate wallets for each role
    wallets = {
        "user": generate_wallet("User Wallet"),
        "provider": generate_wallet("Provider Wallet"),
        "quality_agent": generate_wallet("Quality Agent Wallet"),
        "settlement_agent": generate_wallet("Settlement Agent Wallet"),
        "hallucination_agent": generate_wallet("Hallucination Agent Wallet"),
    }

    # Display wallets
    print("GENERATED WALLETS (Arc Testnet)")
    print("-" * 80)
    print()

    for key, wallet in wallets.items():
        print(f"📭 {wallet['name']}")
        print(f"   Address:     {wallet['address']}")
        print(f"   Private Key: {wallet['private_key']}")
        print()

    # Show .env format
    print("=" * 80)
    print("UPDATE YOUR .env FILE WITH THESE VALUES:")
    print("=" * 80)
    print()

    env_lines = [
        f"# Generated at {datetime.now().isoformat()}",
        f"USER_WALLET={wallets['user']['address']}",
        f"USER_PRIVATE_KEY={wallets['user']['private_key']}",
        f"PROVIDER_WALLET={wallets['provider']['address']}",
        f"QUALITY_AGENT_WALLET={wallets['quality_agent']['address']}",
        f"SETTLEMENT_AGENT_WALLET={wallets['settlement_agent']['address']}",
        f"HALLUCINATION_AGENT_WALLET={wallets['hallucination_agent']['address']}",
    ]

    for line in env_lines:
        print(line)

    print()
    print("=" * 80)
    print("⚠️  SECURITY WARNING")
    print("=" * 80)
    print()
    print("✅ SAVE these private keys in a SECURE location")
    print("❌ NEVER commit private keys to git")
    print("❌ NEVER share private keys publicly")
    print("❌ NEVER push .env file to git (it's in .gitignore)")
    print()

    # Save to file
    output_file = "wallets.json"
    with open(output_file, "w") as f:
        json.dump(wallets, f, indent=2)

    print(f"✅ Wallets saved to: {output_file} (KEEP THIS PRIVATE!)")
    print()

    # Next steps
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print()
    print("1. ✅ Update .env file with wallet addresses above")
    print()
    print("2. 🚰 Fund wallets with testnet USDC:")
    print("   - Visit Circle Arc testnet faucet")
    print("   - Request USDC for each wallet address")
    print()
    print("3. ✅ Verify funding:")
    print("   - Go to: https://explorer.arc.testnet.circle.com")
    print("   - Search for wallet address")
    print("   - Confirm USDC balance")
    print()
    print("4. 🚀 Enable blockchain writes:")
    print("   bash scripts/enable_blockchain.sh")
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
