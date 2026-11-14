from app.strategy_scanner import build_butterfly_rows, compare_butterfly_snapshots


def test_builds_every_complete_100_point_butterfly_per_expiry_and_type():
    contracts = []
    quotes = {}
    for expiry in ("2026-11-19", "2026-11-26"):
        for option_type in ("CE", "PE"):
            for strike in (25000, 25100, 25200, 25300):
                symbol = f"{expiry}-{option_type}-{strike}"
                contracts.append({
                    "tradingsymbol": symbol,
                    "expiry": expiry,
                    "strike": strike,
                    "instrument_type": option_type,
                })
                quotes[symbol] = {"last_price": float(strike / 100), "oi": 100, "volume": 50}
    rows = build_butterfly_rows(contracts, quotes, gap=100)
    assert len(rows) == 4 * 2  # two adjacent 3-strike windows × two expiries × two types? see assertion below
    assert all(row["upper_strike"] - row["middle_strike"] == 100 for row in rows)
    assert all(row["middle_strike"] - row["lower_strike"] == 100 for row in rows)
    assert all(row["legs"][1]["quantity_ratio"] == 2 for row in rows)


def test_missing_quote_skips_combination_without_fabricating_price():
    contracts = [
        {"tradingsymbol": str(k), "expiry": "2026-11-19", "strike": k, "instrument_type": "CE"}
        for k in (25000, 25100, 25200)
    ]
    rows = build_butterfly_rows(contracts, {"25000": {"last_price": 10}, "25100": {"last_price": 20}})
    assert rows == []


def test_snapshot_change_sign():
    result = compare_butterfly_snapshots({"net_premium": 100}, {"net_premium": 90})
    assert result["premium_change"] == -10
    assert result["direction"] == "DOWN"
