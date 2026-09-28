#!/usr/bin/env bash
# =============================================================================
# Process environment for main_watcher.py and the automation scripts.
# =============================================================================
# Copy to automation/trading_env.sh (gitignored), fill it in, then
#
#     source automation/trading_env.sh
#
# before running the watcher or the helper scripts on a host. In a container,
# inject the same variables as environment variables instead.
#
# Kiwoom credentials do not belong here: they are read from .env (see
# README). This file carries only what the watcher, the Multica dispatcher and
# the notification scripts read from the process environment.
# =============================================================================

# Mock routes every Kiwoom call to mockapi.kiwoom.com (KRX only). Switch both
# lines to live/false only after running in mock mode.
export KIWOOM_TRADING_MODE=mock
export KIWOOM_USE_MOCK=true

# ----- LIVE-ORDER EXECUTION GATE ------------------------------------------
# With KIWOOM_USE_MOCK=false, `main_watcher.py --execute-orders` is REFUSED
# unless this holds exactly this string. It is verbose on purpose, so it is
# hard to set by accident. Leave it commented out until you mean it.
# export KIWOOM_LIVE_CONFIRM=YES_I_REALLY_WANT_TO_TRADE

# ----- Multica agents (optional: Tier-2 judgment) --------------------------
# Project the watcher files its dispatch issues under. Without it Tier-2
# dispatch fails; the Tier-1 rules keep running, and since new entries come
# only from an agent ACTION, no new positions are opened.
export MULTICA_PROJECT=""
# export MULTICA_BIN=/usr/local/bin/multica
# export DAILY_ISSUE_SUFFIX="장중 실거래"   # daily issue title suffix
# export TRADING_MODE_LABEL="🟡 MOCK"       # label on Discord/issue text

# ----- Notifications (optional) -------------------------------------------
# export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/<id>/<token>"
