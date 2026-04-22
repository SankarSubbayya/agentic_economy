# Quick Start: Enable Real Blockchain Writes

Follow these 5 steps to start writing nanopayments to Arc testnet.

## Step 1: Generate Wallet Addresses (2 minutes)

```bash
uv run python scripts/generate_wallets.py
```

**Output:**
- 5 wallet addresses (buyer, seller, agents)
- Private keys for each wallet
- `.env` configuration template
- `wallets.json` file with all keys (keep private!)

**Example Output:**
```
📭 User Wallet
   Address:     0x72c0E62aF6509970F0C2CBF8DF8755fCD1172bab
   Private Key: 58049cf0f68b15410cf7e18b6b04f4c15a1b0ccaf38c1c73b49d0dd38f09bd0e

📭 Provider Wallet
   Address:     0xB53d912Bcf2b26B61f2396bF179AE83235646342
   ...
```

---

## Step 2: Update .env File (3 minutes)

Copy the wallet addresses from the script output into your `.env`:

```bash
# Open .env
nano .env

# Add these values:
USER_WALLET=0x72c0E62aF6509970F0C2CBF8DF8755fCD1172bab
USER_PRIVATE_KEY=58049cf0f68b15410cf7e18b6b04f4c15a1b0ccaf38c1c73b49d0dd38f09bd0e
PROVIDER_WALLET=0xB53d912Bcf2b26B61f2396bF179AE83235646342
QUALITY_AGENT_WALLET=0x65EBdbA13c452f90A8F9b008444F67aDa797BBd8
SETTLEMENT_AGENT_WALLET=0xbC9a0EF2B922C15867f7564387129b2461919694
HALLUCINATION_AGENT_WALLET=0xcFBef1F9518b14A53E63ED1844fCeabDd7c9700E

# Add Circle API key (get from Circle console)
CIRCLE_API_KEY=sk_test_your_actual_key_here
```

---

## Step 3: Get Circle API Key (5 minutes)

### For Hackathon Participants:
1. Check the hackathon documentation/email for:
   - Circle console access link
   - Pre-generated testnet API key
   - Or instructions to create one

### If Creating Your Own:
1. Visit: https://www.circle.com/en/developers
2. Sign up / Log in
3. Navigate to **Developer Console** → **API Keys**
4. Create a **Testnet** API key
5. Copy the key (format: `sk_test_...`)
6. Add to `.env`:
   ```
   CIRCLE_API_KEY=sk_test_your_key_here
   ```

**⚠️ IMPORTANT:**
- ❌ Never share your API key
- ❌ Never commit to git (already in .gitignore)
- ✅ Use testnet key for testing
- ✅ Save backup in secure location

---

## Step 4: Fund Testnet Wallets (10 minutes)

Arc testnet requires USDC to pay for nanopayments.

### Request Testnet USDC:

**Option A - Hackathon Faucet (Recommended):**
1. Check hackathon documentation for faucet URL
2. Paste wallet address
3. Click "Request USDC"
4. Wait for confirmation (usually instant)

**Option B - Circle Developer Console:**
1. Go to: https://console.circle.com
2. Navigate to: **Settings** → **Testnet Faucet**
3. Paste wallet address
4. Request amount (e.g., 100 USDC)

### Verify Funding:

```bash
# Check on Block Explorer
# Go to: https://explorer.arc.testnet.circle.com
# Search for your wallet address
# Confirm USDC balance appears
```

**Expected timing:**
- ⚡ Instant to 30 seconds for testnet faucet
- 💰 Amount: typically 10-100 USDC per request

---

## Step 5: Enable Blockchain Mode (1 minute)

Update `.env` to enable real blockchain writes:

```bash
# Edit .env and set:
USE_REAL_RPC=true
USE_REAL_CIRCLE_API=true

# Or run the helper script:
bash scripts/enable_blockchain.sh
```

**That's it!** ✅

---

## Test the Setup

### Run a Demo Transaction:

```bash
uv run python src/day4_demo.py
```

**Expected output:**
```
DAY 4: X402 PAYMENT PROTOCOL + CIRCLE NANOPAYMENTS + ARC SETTLEMENT
...
PHASE 1: EIP-3009 NANOPAYMENT AUTHORIZATIONS
✓ Payment 1: 0.0010 USDC | Tx: 0x1234567890ab...
✓ Payment 2: 0.0011 USDC | Tx: 0xabcdef1234...
...
```

### Monitor on Block Explorer:

1. Copy a transaction hash from the output
2. Visit: https://explorer.arc.testnet.circle.com
3. Paste the hash in the search box
4. View live transaction details:
   - From address
   - To address
   - Amount
   - Status (Confirmed/Pending)
   - Gas used

---

## Troubleshooting

### ❌ "Connection refused" / "Could not connect to Arc RPC"
**Solution:** The RPC endpoint might be temporarily down. System automatically falls back to simulation mode.

### ❌ "Invalid API key" / "401 Unauthorized"
**Check:**
- ✅ API key starts with `sk_test_` (testnet)
- ✅ No leading/trailing spaces
- ✅ Key is from Circle console, not documentation

### ❌ "Insufficient balance"
**Solution:** Your wallets don't have testnet USDC
- Request more from faucet
- Verify funding: https://explorer.arc.testnet.circle.com
- Wait 30 seconds and try again

### ❌ "Transaction pending for too long"
**Normal behavior:** Arc testnet blocks take ~12 seconds
- Maximum wait: 2 minutes
- Check status on Block Explorer

### ✅ Revert to Simulation
If you hit issues, revert to local simulation:
```bash
USE_REAL_RPC=false
USE_REAL_CIRCLE_API=false
```

---

## What Happens Next

### 1. Test Complete Payment Flow
```bash
# Run all tests
uv run pytest src/tests/ -v

# All 85 tests should pass
# Coverage: 73%
```

### 2. Monitor Real Transactions
```
Block Explorer: https://explorer.arc.testnet.circle.com
```

### 3. When Ready for Production
Update configuration:
```bash
USE_REAL_RPC=true (already set)
CIRCLE_API_KEY=sk_live_... (use mainnet key)
# Ensure wallets have REAL USDC
```

---

## Security Checklist

✅ **DO:**
- Store private keys securely (encrypted file, password manager)
- Use testnet keys for testing
- Keep `.env` file locally only
- Rotate API keys regularly
- Use separate wallets for mainnet

❌ **DON'T:**
- Commit `.env` to git (already prevented)
- Share API keys or private keys
- Use mainnet keys for testing
- Post wallet addresses publicly
- Log or print private keys

---

## Key Metrics

| Operation | Cost | Speed | Confirmation |
|-----------|------|-------|--------------|
| Nanopayment | < $0.0001 | < 1s | 12 blocks (~2 min) |
| vs Ethereum | $0.30-5.00 | 15-30s | 12+ blocks (~3 min) |
| vs Visa | 2-3% + $0.30 | 1-3 days | Instant |

**Result:** ✅ **50-300x cheaper** than traditional payments

---

## Support

- **Block Explorer:** https://explorer.arc.testnet.circle.com
- **Circle Docs:** https://developers.circle.com
- **Hackathon Docs:** Check email/dashboard
- **This Project:** `BLOCKCHAIN_SETUP.md`

---

## Files Reference

| File | Purpose |
|------|---------|
| `scripts/generate_wallets.py` | Create wallet addresses |
| `scripts/enable_blockchain.sh` | Enable real blockchain |
| `.env.example` | Configuration template |
| `BLOCKCHAIN_SETUP.md` | Detailed setup guide |
| `wallets.json` | Generated wallet keys (private!) |

---

**Ready to go!** 🚀

Any questions? Check:
1. `BLOCKCHAIN_SETUP.md` - Full documentation
2. Block Explorer - Monitor transactions
3. `.env.example` - See all config options
