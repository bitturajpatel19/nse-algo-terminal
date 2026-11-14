"""Pure builder and mark-to-market helpers for fixed-width option butterflies.

This module is intentionally broker-agnostic and does not place orders.
Premium sign convention: strategy value = long lower + long upper - 2 * short body.
A positive value is a debit; a negative value is a credit.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any


def build_butterfly_rows(
    contracts: list[dict[str, Any]],
    quotes: dict[str, dict[str, Any]],
    gap: int = 100,
) -> list[dict[str, Any]]:
    """Build every available 3-strike butterfly for each expiry and option type.

    Each contract needs: tradingsymbol, expiry, strike, instrument_type.
    Each quote is keyed by tradingsymbol and may contain last_price, oi, volume,
    depth.buy[0].price and depth.sell[0].price.
    Missing legs are skipped; no synthetic or interpolated prices are created.
    """
    if gap <= 0:
        raise ValueError("gap must be a positive number")

    grouped: dict[tuple[str, str], dict[float, dict[str, dict[str, Any]]]] = defaultdict(dict)
    for contract in contracts:
        option_type = str(contract.get("instrument_type", "")).upper()
        if option_type not in {"CE", "PE"}:
            continue
        expiry = str(contract.get("expiry", ""))
        strike = float(contract.get("strike", 0))
        grouped[(expiry, option_type)].setdefault(strike, {})[option_type] = contract

    rows: list[dict[str, Any]] = []
    for (expiry, option_type), strikes in grouped.items():
        for lower in sorted(strikes):
            middle, upper = lower + gap, lower + (2 * gap)
            if middle not in strikes or upper not in strikes:
                continue
            legs = [strikes[lower].get(option_type), strikes[middle].get(option_type), strikes[upper].get(option_type)]
            if not all(legs):
                continue
            symbols = [leg["tradingsymbol"] for leg in legs]
            leg_quotes = [quotes.get(symbol, {}) for symbol in symbols]
            if not all("last_price" in q for q in leg_quotes):
                continue
            lower_ltp, middle_ltp, upper_ltp = [float(q["last_price"]) for q in leg_quotes]
            net_value = lower_ltp + upper_ltp - (2 * middle_ltp)
            rows.append({
                "strategy": "100_GAP_BUTTERFLY",
                "expiry": expiry,
                "option_type": option_type,
                "lower_strike": lower,
                "middle_strike": middle,
                "upper_strike": upper,
                "gap": gap,
                "legs": [
                    {"side": "BUY", "quantity_ratio": 1, "symbol": symbols[0], "strike": lower, "ltp": lower_ltp, "oi": leg_quotes[0].get("oi"), "volume": leg_quotes[0].get("volume")},
                    {"side": "SELL", "quantity_ratio": 2, "symbol": symbols[1], "strike": middle, "ltp": middle_ltp, "oi": leg_quotes[1].get("oi"), "volume": leg_quotes[1].get("volume")},
                    {"side": "BUY", "quantity_ratio": 1, "symbol": symbols[2], "strike": upper, "ltp": upper_ltp, "oi": leg_quotes[2].get("oi"), "volume": leg_quotes[2].get("volume")},
                ],
                "net_premium": round(net_value, 2),
                "premium_type": "DEBIT" if net_value > 0 else ("CREDIT" if net_value < 0 else "FLAT"),
                "lower_bid": (leg_quotes[0].get("depth", {}).get("buy") or [{}])[0].get("price"),
                "lower_ask": (leg_quotes[0].get("depth", {}).get("sell") or [{}])[0].get("price"),
                "middle_bid": (leg_quotes[1].get("depth", {}).get("buy") or [{}])[0].get("price"),
                "middle_ask": (leg_quotes[1].get("depth", {}).get("sell") or [{}])[0].get("price"),
                "upper_bid": (leg_quotes[2].get("depth", {}).get("buy") or [{}])[0].get("price"),
                "upper_ask": (leg_quotes[2].get("depth", {}).get("sell") or [{}])[0].get("price"),
                "observed_at": max((q.get("timestamp") or q.get("last_trade_time") or "") for q in leg_quotes),
            })
    return sorted(rows, key=lambda row: (row["expiry"], row["option_type"], row["lower_strike"]))


def compare_butterfly_snapshots(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare same butterfly across two snapshots; positive delta means premium rose."""
    old = float(previous["net_premium"])
    new = float(current["net_premium"])
    change = new - old
    pct = (change / abs(old) * 100) if old else None
    return {
        "premium_change": round(change, 2),
        "premium_change_pct": round(pct, 2) if pct is not None else None,
        "direction": "UP" if change > 0 else ("DOWN" if change < 0 else "UNCHANGED"),
    }
