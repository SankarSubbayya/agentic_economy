#!/bin/bash
# Enable real blockchain writes to Arc testnet

set -e

echo "=========================================="
echo "Arc Testnet Blockchain Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ .env created. Edit it with your Circle API key and wallet addresses."
else
    echo "✅ .env file exists"
fi

# Check for Circle API key
if grep -q "CIRCLE_API_KEY=sk_test_demo" .env; then
    echo ""
    echo "⚠️  CIRCLE_API_KEY is still set to demo key"
    echo "   Please update .env with your actual Circle API key:"
    echo "   CIRCLE_API_KEY=sk_test_your_actual_key_here"
    exit 1
fi

# Check for wallet addresses
if grep -q "USER_WALLET=0x742d35" .env; then
    echo ""
    echo "⚠️  Wallet addresses are still set to defaults"
    echo "   Please fund these addresses and update in .env:"
    echo "   - USER_WALLET"
    echo "   - PROVIDER_WALLET"
    echo "   - QUALITY_AGENT_WALLET"
    echo "   - SETTLEMENT_AGENT_WALLET"
    echo "   - HALLUCINATION_AGENT_WALLET"
    exit 1
fi

echo ""
echo "Enabling real blockchain writes..."

# Enable blockchain flags
sed -i '' 's/USE_REAL_RPC=false/USE_REAL_RPC=true/' .env
sed -i '' 's/USE_REAL_CIRCLE_API=false/USE_REAL_CIRCLE_API=true/' .env

echo "✅ Blockchain writes enabled"
echo ""
echo "Configuration:"
grep -E "^(CIRCLE_API_KEY|USE_REAL|ARC_TESTNET)" .env
echo ""
echo "Next steps:"
echo "1. Verify wallets have testnet USDC:"
echo "   https://explorer.arc.testnet.circle.com"
echo ""
echo "2. Run demo to test:"
echo "   uv run python src/day4_demo.py"
echo ""
echo "3. Monitor transactions:"
echo "   https://explorer.arc.testnet.circle.com/tx/{tx_hash}"
echo ""
echo "=========================================="
