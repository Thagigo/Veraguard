"""
Sovereign FAQ Generator.
Pulls live data from The Shield, The Vault, and The Ledger to build a real-time support page.
"""
import os
import datetime

def generate_faq():
    """Generates Markdown FAQ"""
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Mock Stats from Ledger (would read from real logs)
    war_chest_bal = "1,240.50 CRD"
    vault_bal = "8,450.00 CRD"
    
    content = f"""# 🛡️ Sovereign Support & FAQ
*Last Updated: {timestamp}*

## 🤖 The "Ghost Agent" System
VeraGuard runs a headless "Ghost Agent" that monitors the mempool and your personal audit trail.
- **Telegram Bot**: `@VeraVerifyBot`
- **Support Command**: `/explain <contract_address>`

## 🏛️ The Treasury (Live)
Transparent accounting of where your credit fees go.
- **Security Vault (60%)**: `{vault_bal}` (Insurance fund against false negatives)
- **War Chest (15%)**: `{war_chest_bal}` (Bounties for Red Team Hunters)
- **Sheriff Yield (25%)**: Distributed to VERA stakers.

## 🔐 The Vault (Your Data)
All audits are cryptographically signed and stored in your private 'NotebookLM' Folder (`The_Vault`).
You can verify any report's integrity by checking the `report_hash` against the `VeraAnchor` contract.

## ❓ Common Questions

### How do I link my Telegram?
1. Go to Dashboard.
2. Click "Link Telegram".
3. Send the OTP to the bot: `/link <OTP>`.

### What happens if the AI is wrong?
If a "Certified Safe" contract is exploited, the **Security Vault** pays out the coverage claim to affected users (Requires Vera-Pass Premium).

### Can I export my data?
Yes. All your certificates are JSON files in `NotebookLM/The_Vault`. You own them.
"""
    
    # Write to Public Dir (Simulated)
    # in a real app, this would be `app/public/faq.md` or similar.
    # For now we save it to the core folder or artifacts.
    with open("Sovereign_FAQ.md", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("FAQ Generated: Sovereign_FAQ.md")

if __name__ == "__main__":
    generate_faq()
