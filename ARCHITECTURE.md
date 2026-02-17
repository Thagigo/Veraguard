# VeraGuard Architecture

## System Overview
VeraGuard consists of a Python-based core for signature-based security auditing and a React-based frontend for user management. It relies on a "NotebookLM Ledger" to store and update threat patterns ("Signatures of Malice").

## Components

### 1. Core (`/core`)
- **Framework**: FastAPI + Web3.py
- **Responsibilities**:
    - **Signature-Based Auditing**: Scans for known 2026 exploit patterns (Hidden Mint, Liquidity Unlocks).
    - **Intelligence Merging**: Scheduled Cron Jobs to fetch new patterns from NotebookLM.
    - Blockchain Interaction (EVM/Base/Ethereum).

### 2. App (`/app`)
- **Framework**: React (Vite) + Tailwind CSS
- **Responsibilities**:
    - User Dashboard
    - Audit Request Submission
    - Result Visualization

## Data Flow
1.  User submits a contract address via the **App**.
2.  **App** sends request to **Core**.
3.  **Core** fetches contract bytecode via RPC.
4.  **Core** checks bytecode against `SIGNATURES_OF_MALICE` (e.g., Hidden Mint).
5.  **Core** returns Risk Score and Warnings to **App**.
