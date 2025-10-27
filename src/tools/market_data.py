"""Market data MCP tool integrated with the Trading orchestrator."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib import error, parse, request

import anyio
from claude_agent_sdk import tool

DEFAULT_BASE_URL = os.getenv("TRADING_APP_BASE_URL", "https://mporenta-trading-app.fly.dev")
API_ENDPOINT_TEMPLATE = "{base}/gpt_poly/{symbol}"


async def _http_get(url: str, timeout: float = 10.0) -> tuple[str, Dict[str, str]]:
    headers = {
        "User-Agent": "claude-swarm-market-data/1.0",
        "Accept": "application/json, text/plain;q=0.9",
    }
    req = request.Request(url, headers=headers)

    def _sync_fetch() -> tuple[str, Dict[str, str]]:
        with request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode(
                resp.headers.get_content_charset("utf-8"), errors="replace"
            )
            return payload, dict(resp.headers)

    return await anyio.to_thread.run_sync(_sync_fetch)


def _normalize_response(payload: str, headers: Dict[str, str]) -> Dict[str, Any]:
    content_type = headers.get("Content-Type", "").lower()
    if "application/json" in content_type:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            pass
    return {"raw": payload, "content_type": content_type}


@tool(
    "get_market_data",
    "Fetch market data for a symbol using the trading application's GPT Poly endpoint.",
    {"symbol": str},
)
async def get_market_data(args: Dict[str, Any]) -> Dict[str, Any]:
    symbol = args.get("symbol")
    if not symbol:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Error: 'symbol' argument is required.",
                }
            ],
            "is_error": True,
        }

    cleaned_symbol = str(symbol).strip().upper()
    base_url = DEFAULT_BASE_URL.rstrip("/")
    url = API_ENDPOINT_TEMPLATE.format(
        base=base_url,
        symbol=parse.quote(cleaned_symbol),
    )

    try:
        payload, headers = await _http_get(url)
        normalized = _normalize_response(payload, headers)
        text = json.dumps(normalized, indent=2, sort_keys=True)
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Market data for {cleaned_symbol}:\n\n{text}",
                }
            ]
        }
    except error.URLError as exc:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Error contacting market data endpoint: "
                        f"{getattr(exc, 'reason', exc)}"
                    ),
                }
            ],
            "is_error": True,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Unexpected error fetching market data: {exc}",
                }
            ],
            "is_error": True,
        }


__all__ = ["get_market_data"]
