#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBHOOK_FILE="${SCRIPT_DIR}/discord_webhook_url"
SENDER="${SCRIPT_DIR}/send_discord_webhook.py"

if [[ ! -f "$WEBHOOK_FILE" ]]; then
  echo "Discord webhook file is missing: $WEBHOOK_FILE" >&2
  exit 1
fi

if [[ ! -f "$SENDER" ]]; then
  echo "Discord sender is missing: $SENDER" >&2
  exit 1
fi

DISCORD_WEBHOOK_URL="$(<"$WEBHOOK_FILE")"
export DISCORD_WEBHOOK_URL

DESCRIPTION=""
if [[ ! -t 0 ]]; then
  DESCRIPTION="$(cat)"
fi

if [[ -z "${DESCRIPTION}" ]]; then
  echo "Provide the Discord summary via stdin." >&2
  exit 2
fi

if (( ${#DESCRIPTION} > 3900 )); then
  DESCRIPTION="${DESCRIPTION:0:3897}..."
fi

LOWER_DESCRIPTION="$(printf '%s' "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')"
EMBED_TITLE="KRX 모의투자 업데이트"
EMBED_COLOR=3447003

if [[ "$LOWER_DESCRIPTION" == *"fail"* || "$LOWER_DESCRIPTION" == *"error"* || "$LOWER_DESCRIPTION" == *"unavailable"* || "$LOWER_DESCRIPTION" == *"blocker"* || "$DESCRIPTION" == *"실패"* || "$DESCRIPTION" == *"오류"* || "$DESCRIPTION" == *"불가"* || "$DESCRIPTION" == *"차단"* ]]; then
  EMBED_TITLE="KRX 모의투자 경고"
  EMBED_COLOR=15158332
elif [[ "$LOWER_DESCRIPTION" == *"skip trading"* || "$LOWER_DESCRIPTION" == *"no orders"* || "$LOWER_DESCRIPTION" == *"closed-hours"* || "$DESCRIPTION" == *"거래 보류"* || "$DESCRIPTION" == *"주문 없음"* || "$DESCRIPTION" == *"장외"* || "$DESCRIPTION" == *"장 종료"* ]]; then
  EMBED_TITLE="KRX 모의투자 보류"
  EMBED_COLOR=16705372
elif [[ "$LOWER_DESCRIPTION" == *"executed orders"* || "$LOWER_DESCRIPTION" == *"mock orders sent"* || "$LOWER_DESCRIPTION" == *"executed mock orders"* || "$DESCRIPTION" == *"주문 실행"* || "$DESCRIPTION" == *"모의 주문 실행"* || "$DESCRIPTION" == *"매수 실행"* || "$DESCRIPTION" == *"매도 실행"* ]]; then
  EMBED_TITLE="KRX 모의투자 주문 실행"
  EMBED_COLOR=3066993
fi

python3 "$SENDER" \
  --username "KRX 모의투자" \
  --embed-title "$EMBED_TITLE" \
  --embed-description "$DESCRIPTION" \
  --embed-color "$EMBED_COLOR" \
  "$@"
