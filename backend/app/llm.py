"""LLM integration via LiteLLM → OpenRouter (Cerebras) with mock mode."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from pydantic import ValidationError

from .config import settings
from .schemas import LLMResponse, PortfolioOut

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant embedded in a simulated trading workstation.
You help the user analyze their portfolio, suggest trades, execute trades when asked, and manage their watchlist.

Rules:
- This is a simulated portfolio with fake money — execute trades when the user asks or clearly agrees.
- Be concise, data-driven, and professional (Bloomberg-terminal energy).
- Always respond with valid JSON matching the schema (structured output).
- Only propose trades for tickers you have price context for, unless the user insists.
- For buys, ensure quantity * price roughly fits available cash; for sells, do not exceed holdings.
- watchlist_changes actions are "add" or "remove".
- If the user is only chatting / asking analysis, leave trades and watchlist_changes empty arrays.
"""


def build_portfolio_context(
    portfolio: PortfolioOut,
    watchlist: list[dict[str, Any]],
) -> str:
    lines = [
        f"Cash: ${portfolio.cash_balance:,.2f}",
        f"Total portfolio value: ${portfolio.total_value:,.2f}",
        f"Unrealized P&L: ${portfolio.unrealized_pnl:,.2f} ({portfolio.total_return_percent:.2f}% vs start)",
        "Positions:",
    ]
    if not portfolio.positions:
        lines.append("  (none)")
    for p in portfolio.positions:
        lines.append(
            f"  {p.ticker}: qty={p.quantity}, avg_cost={p.avg_cost}, "
            f"price={p.current_price}, pnl={p.unrealized_pnl}, weight={p.weight}%"
        )
    lines.append("Watchlist:")
    for w in watchlist:
        price = w.get("price")
        chg = w.get("change_percent")
        lines.append(f"  {w.get('ticker')}: price={price}, change%={chg}")
    return "\n".join(lines)


def _mock_response(user_message: str, portfolio: PortfolioOut) -> LLMResponse:
    lower = user_message.lower()

    # Simple intent mocks for demos/tests
    buy_match = re.search(r"buy\s+(\d+(?:\.\d+)?)\s+([a-zA-Z.]+)", lower)
    sell_match = re.search(r"sell\s+(\d+(?:\.\d+)?)\s+([a-zA-Z.]+)", lower)
    add_match = re.search(r"add\s+([a-zA-Z.]+)\s+to\s+watchlist", lower)
    remove_match = re.search(r"remove\s+([a-zA-Z.]+)\s+from\s+watchlist", lower)

    trades = []
    watchlist_changes = []

    if buy_match:
        qty, ticker = float(buy_match.group(1)), buy_match.group(2).upper()
        trades.append({"ticker": ticker, "side": "buy", "quantity": qty})
        msg = f"Buying {qty} shares of {ticker}."
    elif sell_match:
        qty, ticker = float(sell_match.group(1)), sell_match.group(2).upper()
        trades.append({"ticker": ticker, "side": "sell", "quantity": qty})
        msg = f"Selling {qty} shares of {ticker}."
    elif add_match:
        ticker = add_match.group(1).upper()
        watchlist_changes.append({"ticker": ticker, "action": "add"})
        msg = f"Adding {ticker} to the watchlist."
    elif remove_match:
        ticker = remove_match.group(1).upper()
        watchlist_changes.append({"ticker": ticker, "action": "remove"})
        msg = f"Removing {ticker} from the watchlist."
    elif "portfolio" in lower or "summary" in lower or "how am i" in lower:
        msg = (
            f"Portfolio value is ${portfolio.total_value:,.2f} with "
            f"${portfolio.cash_balance:,.2f} cash and "
            f"{len(portfolio.positions)} open positions. "
            f"Unrealized P&L: ${portfolio.unrealized_pnl:,.2f} "
            f"({portfolio.total_return_percent:.2f}%)."
        )
    else:
        msg = (
            f"I'm FinAlly (mock mode). Cash ${portfolio.cash_balance:,.2f}, "
            f"total ${portfolio.total_value:,.2f}. "
            "Try: 'buy 5 AAPL', 'sell 2 TSLA', or 'add NVDA to watchlist'."
        )

    return LLMResponse.model_validate(
        {"message": msg, "trades": trades, "watchlist_changes": watchlist_changes}
    )


def call_llm(
    user_message: str,
    history: list[dict[str, str]],
    portfolio: PortfolioOut,
    watchlist: list[dict[str, Any]],
) -> LLMResponse:
    if settings.llm_mock or not settings.openrouter_api_key:
        if not settings.openrouter_api_key and not settings.llm_mock:
            logger.warning("OPENROUTER_API_KEY missing — falling back to LLM mock")
        return _mock_response(user_message, portfolio)

    context = build_portfolio_context(portfolio, watchlist)
    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Current portfolio context:\n{context}",
        },
    ]
    for h in history[-12:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        from litellm import completion

        response = completion(
            model=MODEL,
            messages=messages,
            response_format=LLMResponse,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
            api_key=settings.openrouter_api_key,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty LLM response")
        return LLMResponse.model_validate_json(content)
    except (ValidationError, json.JSONDecodeError, Exception) as e:
        logger.exception("LLM call failed: %s", e)
        # Best-effort parse raw JSON from content
        try:
            if "content" in dir() and content:  # type: ignore[name-defined]
                data = json.loads(content)  # type: ignore[name-defined]
                return LLMResponse.model_validate(data)
        except Exception:
            pass
        return LLMResponse(
            message=(
                "I hit an error talking to the model. "
                f"Details: {e}. Portfolio still shows "
                f"${portfolio.total_value:,.2f} total value."
            ),
            trades=[],
            watchlist_changes=[],
        )
