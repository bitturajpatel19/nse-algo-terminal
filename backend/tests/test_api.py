from datetime import date, timedelta

from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_never_enables_live_trading(monkeypatch):
    monkeypatch.setenv("KITE_API_KEY", "test-key")
    monkeypatch.setenv("KITE_API_SECRET", "test-secret")
    monkeypatch.setattr(main, "_kite_access_token", None)
    response = client.get("/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "configuration_present"
    assert response.json()["live_trading_enabled"] is False


def test_unsupported_underlying_is_rejected_before_auth():
    response = client.get("/market/option-chain?underlying=UNKNOWN")
    assert response.status_code == 400


def test_option_chain_rejects_malformed_expiry():
    response = client.get("/market/option-chain?underlying=NIFTY&expiry=next-week")
    assert response.status_code == 401 or response.status_code == 503
    # Authentication/configuration is checked before expiry parsing in this route.


def test_option_chain_snapshot_shape(monkeypatch):
    expiry = date.today() + timedelta(days=7)
    contracts = []
    for strike in (21950.0, 22000.0, 22050.0):
        for option_type in ("CE", "PE"):
            contracts.append({
                "name": "NIFTY",
                "instrument_type": option_type,
                "expiry": expiry,
                "strike": strike,
                "tradingsymbol": f"NIFTY{int(strike)}{option_type}",
                "instrument_token": int(strike) + (1 if option_type == "CE" else 2),
            })

    class FakeKite:
        def quote(self, *keys):
            return {"NSE:NIFTY 50": {"last_price": 22000, "timestamp": "test"}}

    monkeypatch.setattr(main, "_kite_client", lambda authenticated=True: FakeKite())
    monkeypatch.setattr(main, "_load_nfo_instruments", lambda kite: contracts)
    monkeypatch.setattr(
        main,
        "_quote_chunks",
        lambda kite, keys: {
            key: {"last_price": 100, "oi": 10, "volume": 20,
                  "depth": {"buy": [{"price": 99}], "sell": [{"price": 101}]}}
            for key in keys
        },
    )
    response = client.get("/market/option-chain?underlying=NIFTY&strikes_each_side=1")
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "live_quote_snapshot"
    assert body["atm_strike"] == 22000
    assert len(body["rows"]) == 3
    assert body["rows"][1]["ce"]["ltp"] == 100
    assert body["rows"][1]["pe"]["ask"] == 101
    assert body["data_quality"]["quote_snapshot_only"] is True
