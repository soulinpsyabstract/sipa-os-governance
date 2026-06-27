# SIPA Token — Technical Specification

**Version:** 1.0 · **Date:** 2026-06-27  
**Issuer:** Soul In PsyAbstract LLC, Delaware · EIN 30-1491964

---

## 1. Token Properties

| Property | Value |
|----------|-------|
| Name | SIPA |
| Standard | ERC-20 |
| Network | Base mainnet (Ethereum L2, Coinbase) |
| Total supply | 100,000,000 (100M) — fixed, no additional minting |
| Decimals | 18 |
| Upgradeable | No |
| Mintable after deploy | No |
| Contract address | *(published on Base mainnet — verify on basescan.org)* |

---

## 2. Allocation

| Category | Amount | % | Lock |
|----------|--------|---|------|
| Founder | 40,000,000 | 40% | Locked until September 2026 |
| Treasury | 15,000,000 | 15% | LLC-controlled |
| Ecosystem / Grants | 15,000,000 | 15% | Milestone-based |
| Liquidity Pool | 20,000,000 | 20% | Aerodrome DEX (Base) |
| Community / Rewards | 10,000,000 | 10% | Platform milestones |

---

## 3. Liquidity

- **DEX:** Aerodrome Finance on Base mainnet
- **Positions:** 2 active LP positions
- All LP activity is publicly verifiable on-chain

---

## 4. Utility

| Use Case | Description |
|----------|-------------|
| Platform access | Unlock premium tiers on SIPA OS apps |
| Governance (future) | Community proposals after September 2026 unlock |
| Creator rewards | Art sales and content milestones |
| AI credits | Pay-per-use for SIPA AI services |

---

## 5. Developer Integration

```
Network: Base Mainnet
Chain ID: 8453
RPC: https://mainnet.base.org
Standard ABI: ERC-20 (IERC20)
Explorer: https://basescan.org
```

Standard ERC-20 interface — compatible with all Base-supporting wallets (MetaMask, Coinbase Wallet, Rainbow).

---

## 6. Important Notice

SIPA Token is a **utility token**. It does NOT represent:
- Equity in Soul In PsyAbstract LLC
- A security or investment contract
- A promise of profit or return

Verify contract address on basescan.org before any transaction. Official address published only via sipa-os.org and this repository.

---

*For developer integration: sipa-core@sipa-os.org*
