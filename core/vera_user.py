"""
vera_user.py — VeraGuard Telethon Userbot
==========================================
Monitors Telegram groups for contract addresses (0x + 40 hex chars).
Replies with a scam warning if unified triage suspicion score >= 50%.
Uses audit_engine.triage_address() — same scorer as chain_listener.
Polls /api/internal/heuristic_version every 60s to hot-reload Brain filters.

Anti-ban measures:
  - Human-like random delay (5–15s) before replying
  - Typing indicator while "reading"
  - Rate limit: max 3 replies per hour per group
"""

import os
import re
import time
import random
import asyncio
import logging
import requests
from collections import defaultdict

from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.types import PeerChat, PeerChannel

# Unified triage engine & scout
from core.audit_engine import triage_address, extract_addresses
from core.scout import scout
from core import database as db

# ── Config ───────────────────────────────────────────────────────────────────
load_dotenv()

SESSION_FILE    = "vera_user"
SCORE_THRESHOLD = 50
WARNING_MSG     = "🚨 Scammer detected. Heuristic match found in VeraGuard Brain."

BACKEND_URL     = "http://127.0.0.1:8000"

# Anti-ban: max replies per group per hour
MAX_REPLIES_PER_HOUR = 3

# Heuristic hot-reload: poll interval (seconds)
HEURISTIC_POLL_INTERVAL = 60

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [VERA_USER] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vera_user")

# ── Rate limiter ──────────────────────────────────────────────────────────────
reply_log: dict[int, list[float]] = defaultdict(list)


def is_rate_limited(chat_id: int) -> bool:
    now = time.time()
    reply_log[chat_id] = [t for t in reply_log[chat_id] if now - t < 3600]
    return len(reply_log[chat_id]) >= MAX_REPLIES_PER_HOUR


def record_reply(chat_id: int):
    reply_log[chat_id].append(time.time())


def fire_sse_event(event_type: str, data: dict):
    """Notify the Brain UI via the SSE broadcaster."""
    try:
        requests.post(
            f"{BACKEND_URL}/api/internal/live_event",
            json={"event_type": event_type, "data": data},
            timeout=2,
        )
    except Exception as e:
        log.debug(f"SSE fire failed (backend may be down): {e}")


# ── Heuristic hot-reload ──────────────────────────────────────────────────────
_last_known_version: int = -1


async def heuristic_reload_task():
    """
    Background task: polls /api/internal/heuristic_version every 60s.
    When the version increments, the scout singleton's in-memory filters are updated.
    Falls back gracefully if the backend is unavailable.
    """
    global _last_known_version
    while True:
        await asyncio.sleep(HEURISTIC_POLL_INTERVAL)
        try:
            resp = requests.get(f"{BACKEND_URL}/api/internal/heuristic_version", timeout=3)
            if resp.ok:
                payload = resp.json()
                version = payload.get("version", 0)
                if version != _last_known_version:
                    new_filters = payload.get("filters", [])
                    if new_filters:
                        scout.heuristics["zero_credit_filters"] = new_filters
                        _last_known_version = version
                        log.info(
                            f"🔄 RELOAD_HEURISTICS v{version}: "
                            f"{len(new_filters)} filters active."
                        )
        except Exception as e:
            log.debug(f"Heuristic version poll failed: {e}")


# ── Reply builder ─────────────────────────────────────────────────────────────
def build_reply(result: dict) -> tuple[str, bool]:
    """
    Given a triage result dict, return (reply_text, should_reply).
    Pattern matches always reply. Score-only replies require >= threshold.
    """
    pattern = result.get("pattern_match")
    score   = result.get("score", 0.0)

    if pattern:
        return (
            f"🚨 VeraGuard detected a 100% match for '{pattern.replace('_', ' ')}' "
            f"logic in this contract.",
            True,
        )
    if score >= SCORE_THRESHOLD:
        return WARNING_MSG, True
    return "", False


async def main():
    api_id   = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")

    if api_id == 0 or not api_hash:
        raise EnvironmentError(
            "Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env\n"
            "Get them at https://my.telegram.org"
        )

    client = TelegramClient(SESSION_FILE, api_id, api_hash)

    @client.on(events.NewMessage)
    async def handler(event):
        text = event.raw_text or ""

        # ── Admin Commands (Private DM only) ──────────────────────────────────
        is_private = not isinstance(event.message.peer_id, (PeerChat, PeerChannel))
        admin_id = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
        sender_id = event.sender_id

        if is_private and sender_id == admin_id:
            cmd = text.strip().lower()
            if cmd == "/synced":
                db.mark_brain_synced()
                await event.reply("✅ *Brain synced.* Lag counter reset to zero.")
                log.info("Admin reset brain lag counter via /synced")
                return
            elif cmd == "/status":
                lag = db.get_brain_lag()
                await event.reply(f"📊 *VeraGuard Status*\nBrain Lag: `{lag}` new patterns.")
                return

        # Regular Message Monitoring (Group/Channel only)
        if is_private:
            return

        log.info(f"[MSG] chat={event.chat_id} | {text[:80]!r}")

        addresses = extract_addresses(text)
        if not addresses:
            return

        log.info(f"📡 Found address(es): {addresses}")

        chat_id = event.chat_id

        # ── Rate limit ────────────────────────────────────────────────────────
        if is_rate_limited(chat_id):
            log.warning(f"🛑 Rate limit hit for chat {chat_id}. Skipping.")
            return

        for address in addresses:
            # ── Unified triage (same engine as chain_listener) ────────────────
            result = triage_address(
                address=address,
                context_text=text,
                source="userbot",
            )
            score = result["score"]

            # ── Fire contract_detected SSE ────────────────────────────────────
            fire_sse_event("contract_detected", {
                "address": address,
                "score":   round(score),
                "source":  "userbot",
            })

            # ── Spoof detected → blue alert SSE, stay silent in Telegram ─────
            if result.get("spoof_detected"):
                spoof_msg = f"False Positive Blocked: Bytecode mismatch for {address[:10]}…"
                log.warning(f"[SPOOF] {spoof_msg}")
                fire_sse_event("spoof_alert", {
                    "message": spoof_msg,
                    "address": address,
                })
                continue  # Silent — do not reply in Telegram

            # ── Bytecode-confirmed pattern match → intelligence_update SSE ────
            if result.get("pattern_match"):
                pattern_name = result["pattern_match"]
                log.info(f"🧠 Pattern confirmed (bytecode): {pattern_name}")
                fire_sse_event("intelligence_update", {
                    "heuristic": (
                        f"Analyzing {address[:8]}… "
                        f"Bytecode-confirmed: {pattern_name}"
                    )
                })

            # ── Build reply text ──────────────────────────────────────────────
            reply_text, should_reply = build_reply(result)

            if not should_reply:
                log.info(f"✅ {score:.0f}% < {SCORE_THRESHOLD}% — no action.")
                continue

            log.info(
                f"🚨 {score:.0f}% ≥ {SCORE_THRESHOLD}% "
                f"| pattern={result['pattern_match']} "
                f"| deployer={result['deployer_flag']}"
            )

            # ── 1. Mark as read ───────────────────────────────────────────────
            try:
                await client.send_read_acknowledge(
                    event.chat_id, max_id=event.message.id
                )
            except Exception:
                pass

            # ── 2. Human-like delay ───────────────────────────────────────────
            delay = random.uniform(5, 15)
            log.info(f"⏳ Waiting {delay:.1f}s (human delay)…")
            await asyncio.sleep(delay)

            # ── 3. Typing indicator ───────────────────────────────────────────
            try:
                async with client.action(event.chat_id, "typing"):
                    await asyncio.sleep(random.uniform(2, 4))
            except Exception:
                pass

            # ── 4. Send reply ─────────────────────────────────────────────────
            try:
                await event.reply(reply_text)
                record_reply(chat_id)
                replies_used = len(reply_log[chat_id])
                log.info(
                    f"✅ Reply sent. "
                    f"[{replies_used}/{MAX_REPLIES_PER_HOUR} this hour, "
                    f"{MAX_REPLIES_PER_HOUR - replies_used} remaining]"
                )
            except Exception as e:
                log.error(f"Reply failed: {e}")

    log.info("🤖 Vera Userbot starting…")
    await client.start()
    me = await client.get_me()
    log.info(f"✅ Logged in as: {me.username or me.first_name} (id={me.id})")
    log.info(
        f"⚡ Threshold: >={SCORE_THRESHOLD}%  |  "
        f"Max {MAX_REPLIES_PER_HOUR} replies/hr per group"
    )
    log.info(f"🔄 Heuristic reload: every {HEURISTIC_POLL_INTERVAL}s")
    log.info("Listening… (Ctrl+C to stop)")

    # Start background reload task
    asyncio.ensure_future(heuristic_reload_task())

    await client.run_until_disconnected()


asyncio.run(main())
