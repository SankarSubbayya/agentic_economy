# Blockchain Integration Setup Guide

This guide explains how to enable real blockchain writes to Arc testnet and submit nanopayments through Circle's API.

## Overview

The system supports two modes:

1. **Simulation Mode (Default)** - All blockchain operations are simulated in memory
2. **Real Blockchain Mode** - Actually writes to Arc testnet via RPC and Circle Nanopayments API

## Arc Testnet Details

- **Network**: Arc Testnet (powered by Circle)
- **Chain ID**: 5042002 (0x4cef52)
- **RPC Endpoint**: https://rpc.arc.testnet.circle.com
- **USDC Token**: 0xA2F67F45938e3cBEc8d6D92c25b3E3E49ED69767
- **Block Explorer**: https://explorer.arc.testnet.circle.com

## Step 1: Get Circle API Credentials

Circle provides testnet credentials for the Agentic Economy on Arc Hackathon:

1. **Sign up for Circle Developer Console**:
   - Go to https://www.circle.com/en/developers
   - Create an account
   - Navigate to API Keys section

2. **Create a Testnet API Key**:
   - In the developer console, create a new API key for testnet
   - Copy the key (format: `sk_test_...`)

3. **Add to .env**:
   ```bash
   CIRCLE_API_KEY=sk_test_your_actual_key_here
   ```

## Step 2: Fund Your Testnet Wallets

To send nanopayments, you need testnet USDC:

1. **Claim from Arc Testnet Faucet**:
   - Circle provides a testnet faucet for participants
   - Check the hackathon documentation for faucet URL
   - Request testnet USDC for your wallet addresses

2. **Update wallet addresses in .env**:
   ```bash
   USER_WALLET=your_funded_wallet_address
   PROVIDER_WALLET=your_funded_wallet_address
   QUALITY_AGENT_WALLET=your_funded_wallet_address
   SETTLEMENT_AGENT_WALLET=your_funded_wallet_address
   HALLUCINATION_AGENT_WALLET=your_funded_wallet_address
   ```

3. **Verify balance** (via block explorer):
   - Go to https://explorer.arc.testnet.circle.com
   - Search for your wallet address
   - Confirm USDC balance

## Step 3: Enable Real Blockchain Writes

Update your `.env` file:

```bash
# Circle API Configuration
CIRCLE_API_KEY=sk_test_your_actual_key_here

# Enable real blockchain writes
USE_REAL_RPC=true
USE_REAL_CIRCLE_API=true

# Arc Testnet RPC
ARC_TESTNET_RPC=https://rpc.arc.testnet.circle.com
ARC_TESTNET_CHAIN_ID=5042002
```

## Step 4: Run a Test Transaction

Test the blockchain integration:

```bash
# Run Day 4 demo with real blockchain writes
uv run python src/day4_demo.py
```

Expected output:
- Transactions submitted to Arc testnet
- Block Explorer links for each transaction
- On-chain confirmation receipts

## Step 5: Monitor Transactions

### Via Block Explorer:
1. Visit https://explorer.arc.testnet.circle.com
2. Paste transaction hash in search
3. View transaction status, from/to addresses, amounts

### Via Python:
```python
from src.blockchain.arc_testnet import ArcTestnet
from src.config import settings

arc = ArcTestnet(
    rpc_url=settings.ARC_TESTNET_RPC,
    use_real_rpc=True
)

# Check transaction status
receipt = arc.get_transaction_receipt("0x...")
print(f"Status: {receipt['status']}")

# Verify on-chain
confirmed = arc.verify_transaction_on_chain("0x...")
print(f"Confirmed: {confirmed}")
```

## Troubleshooting

### "Could not connect to Arc testnet RPC"
- Verify RPC endpoint is correct: `https://rpc.arc.testnet.circle.com`
- Check your internet connection
- The RPC endpoint may be temporarily down (fallback to simulation mode)

### "Circle API returned 401: Invalid API key"
- Verify your Circle API key is correct
- Make sure you're using a testnet key (starts with `sk_test_`)
- Keys don't have leading/trailing spaces

### "Insufficient balance for transaction"
- You don't have enough testnet USDC
- Request more from the Arc testnet faucet
- Verify funding was successful on Block Explorer

### "Transaction pending for too long"
- Arc testnet may have slow block times (typical: 12s per block)
- Check Block Explorer to see if transaction is included
- Maximum wait: 12 blocks (~2 minutes)

## Reverting to Simulation Mode

If you encounter issues, revert to simulation mode:

```bash
USE_REAL_RPC=false
USE_REAL_CIRCLE_API=false
```

The system automatically falls back to local simulation, allowing all tests to pass.

## Cost Analysis

**Arc Testnet (via Circle Nanopayments):**
- USDC transfer: < $0.0001
- Circle service fee: < 1% of transaction value
- Total per $0.001 transaction: ~$0.00001

**vs Traditional (Ethereum mainnet):**
- Gas cost: $0.30 - $5.00
- Visa/Mastercard: 2-3% + $0.30 fixed fee

**Savings: 50-300x cheaper** ✅

## Security Notes

⚠️ **NEVER commit `.env` to git** - It contains API keys and private keys

Recommended practices:
1. Use environment-specific `.env` files (`.env.local`, `.env.production`)
2. Add `.env` to `.gitignore` (already done)
3. Rotate API keys regularly
4. Use separate wallets for testnet and production

## Next Steps

1. ✅ Have Circle API key
2. ✅ Fund testnet wallets
3. ✅ Enable real blockchain mode
4. ✅ Monitor transactions on Block Explorer
5. 🚀 Deploy to production Arc mainnet (when ready)

For production deployment:
- Use mainnet Circle API key (starts with `sk_live_`)
- Use Arc mainnet RPC endpoint
- Ensure real USDC funding
- Update ARC_TESTNET_CHAIN_ID to mainnet value

## References

- [Circle Developer Docs](https://developers.circle.com)
- [Arc Testnet Explorer](https://explorer.arc.testnet.circle.com)
- [EIP-3009 Standard](https://eips.ethereum.org/EIPS/eip-3009)
- [Hackathon Documentation](https://agentic-economy-on-arc.circle.com)
