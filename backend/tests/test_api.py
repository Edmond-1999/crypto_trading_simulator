from decimal import Decimal

from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import Asset, Balance, PositionCostBasis, User, Wallet


# ---------- Helpers ----------

def register(client, email="api-user@example.test",
             password="StrongPassword123!"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )


def login(client, email="api-user@example.test",
          password="StrongPassword123!"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def token_for(user_id):
    return create_access_token(identity=str(user_id))


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def create_second_user(app):
    """Create another user to test wallet access isolation."""
    with app.app_context():
        user = User(
            email="another-user@example.test",
            password_hash="test-only-password-hash",
        )
        db.session.add(user)
        db.session.flush()

        wallet = Wallet(
            user_id=user.id,
            name="Private Wallet",
            base_currency="USD",
        )
        db.session.add(wallet)
        db.session.commit()

        return user.id, wallet.id


# ---------- Authentication tests ----------

def test_register_success(client, app):
    response = register(client)

    assert response.status_code == 201
    data = response.get_json()

    assert data["message"] == "Account created successfully."
    assert data["user"]["email"] == "api-user@example.test"
    assert "id" in data["user"]

    with app.app_context():
        user = db.session.execute(
            db.select(User).where(
                User.email == "api-user@example.test"
            )
        ).scalar_one()

        assert user.password_hash != "StrongPassword123!"
        assert check_password_hash(
            user.password_hash,
            "StrongPassword123!",
        )


def test_register_normalizes_email(client):
    response = register(
        client,
        email="  API-USER@EXAMPLE.TEST  ",
    )

    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == (
        "api-user@example.test"
    )


def test_register_rejects_duplicate_email(client):
    first = register(client)
    second = register(client)

    assert first.status_code == 201
    assert second.status_code == 409
    assert "error" in second.get_json()


def test_register_rejects_invalid_email(client):
    response = register(client, email="not-an-email")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_register_rejects_short_password(client):
    response = register(client, password="short")

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_register_requires_json_object(client):
    response = client.post(
        "/api/v1/auth/register",
        data="not-json",
        content_type="text/plain",
    )

    assert response.status_code == 400


def test_login_success_returns_bearer_token(client):
    registration = register(client)
    assert registration.status_code == 201

    response = login(client)

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "Login successful."
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data["user"]["email"] == "api-user@example.test"


def test_login_rejects_wrong_password(client):
    register(client)

    response = login(client, password="WrongPassword123!")

    assert response.status_code == 401
    assert response.get_json()["error"] == (
        "Invalid email or password"
    )


def test_login_rejects_unknown_email(client):
    response = login(client, email="missing@example.test")

    assert response.status_code == 401
    assert "error" in response.get_json()


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 422


def test_me_returns_authenticated_user(client):
    registration = register(client)
    assert registration.status_code == 201

    login_response = login(client)
    token = login_response.get_json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.get_json()
    assert data["user"]["email"] == "api-user@example.test"
    assert "id" in data["user"]
    assert "created_at" in data["user"]


# ---------- Wallet API tests ----------

def test_wallet_list_requires_authentication(client):
    response = client.get("/api/v1/wallets")

    assert response.status_code == 401


def test_wallet_create_requires_authentication(client):
    response = client.post(
        "/api/v1/wallets",
        json={
            "name": "My Wallet",
            "base_currency": "USD",
        },
    )

    assert response.status_code == 401


def test_create_wallet_success(client):
    register(client)

    token = login(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/wallets",
        json={
            "name": "My Test Wallet",
            "base_currency": "USD",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201

    wallet = response.get_json()["wallet"]
    assert wallet["name"] == "My Test Wallet"
    assert wallet["base_currency"] == "USD"
    assert "id" in wallet


def test_create_wallet_normalizes_currency(client):
    register(client)

    token = login(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/wallets",
        json={
            "name": "USDT Wallet",
            "base_currency": " usdt ",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.get_json()["wallet"]["base_currency"] == "USDT"


def test_create_wallet_rejects_unsupported_currency(client):
    register(client)

    token = login(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/wallets",
        json={
            "name": "Bitcoin Wallet",
            "base_currency": "BTC",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_create_wallet_rejects_blank_name(client):
    register(client)

    token = login(client).get_json()["access_token"]

    response = client.post(
        "/api/v1/wallets",
        json={
            "name": "   ",
            "base_currency": "USD",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400


def test_wallet_list_only_returns_current_users_wallets(
    client, app, trading_wallet
):
    other_user_id, other_wallet_id = create_second_user(app)

    current_user_token = token_for(trading_wallet["user_id"])

    response = client.get(
        "/api/v1/wallets",
        headers=auth_headers(current_user_token),
    )

    assert response.status_code == 200

    wallet_ids = {
        wallet["id"]
        for wallet in response.get_json()["wallets"]
    }

    assert trading_wallet["wallet_id"] in wallet_ids
    assert other_wallet_id not in wallet_ids


# ---------- Order API security and validation ----------

def test_order_history_requires_authentication(client, trading_wallet):
    response = client.get(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/orders"
    )

    assert response.status_code == 401


def test_order_creation_requires_authentication(client, trading_wallet):
    response = client.post(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/orders",
        json={
            "base_asset": "BTC",
            "quote_currency": "USD",
            "side": "BUY",
            "quantity": "0.001",
        },
    )

    assert response.status_code == 401


def test_order_creation_rejects_missing_quantity(
    client, trading_wallet
):
    token = token_for(trading_wallet["user_id"])

    response = client.post(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/orders",
        json={
            "base_asset": "BTC",
            "quote_currency": "USD",
            "side": "BUY",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Quantity is required."


def test_order_creation_rejects_boolean_quantity(
    client, trading_wallet
):
    token = token_for(trading_wallet["user_id"])

    response = client.post(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/orders",
        json={
            "base_asset": "BTC",
            "quote_currency": "USD",
            "side": "BUY",
            "quantity": True,
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Quantity is required."


def test_order_creation_rejects_invalid_quantity(
    client, trading_wallet, monkeypatch
):
    from app.services import trading_service

    monkeypatch.setattr(
        trading_service,
        "get_market_price",
        lambda base, quote: __import__("decimal").Decimal("100"),
    )

    token = token_for(trading_wallet["user_id"])

    response = client.post(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/orders",
        json={
            "base_asset": "BTC",
            "quote_currency": "USD",
            "side": "BUY",
            "quantity": "NaN",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


def test_user_cannot_view_another_users_order_history(
    client, app, trading_wallet
):
    _, other_wallet_id = create_second_user(app)

    token = token_for(trading_wallet["user_id"])

    response = client.get(
        f"/api/v1/wallets/{other_wallet_id}/orders",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Wallet not found."


def test_user_cannot_place_order_on_another_users_wallet(
    client, app, trading_wallet, monkeypatch
):
    from decimal import Decimal
    from app.services import trading_service

    monkeypatch.setattr(
        trading_service,
        "get_market_price",
        lambda base, quote: Decimal("100"),
    )

    _, other_wallet_id = create_second_user(app)

    token = token_for(trading_wallet["user_id"])

    response = client.post(
        f"/api/v1/wallets/{other_wallet_id}/orders",
        json={
            "base_asset": "BTC",
            "quote_currency": "USD",
            "side": "BUY",
            "quantity": "0.001",
        },
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Wallet not found."


# ---------- Wallet P&L endpoint ----------

def test_wallet_pnl_requires_authentication(client, trading_wallet):
    response = client.get(
        f"/api/v1/wallets/{trading_wallet['wallet_id']}/pnl"
    )

    assert response.status_code == 401


def test_user_cannot_view_another_users_pnl(client, app, trading_wallet):
    _, other_wallet_id = create_second_user(app)
    token = token_for(trading_wallet["user_id"])

    response = client.get(
        f"/api/v1/wallets/{other_wallet_id}/pnl",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Wallet not found."


def test_empty_wallet_pnl_returns_complete_zero_totals(client, app):
    register(client, email="pnl-user@example.test")
    token = login(client, email="pnl-user@example.test").get_json()["access_token"]
    create_response = client.post(
        "/api/v1/wallets",
        json={"name": "Empty PnL Wallet", "base_currency": "USD"},
        headers=auth_headers(token),
    )
    assert create_response.status_code == 201
    wallet_id = create_response.get_json()["wallet"]["id"]

    response = client.get(
        f"/api/v1/wallets/{wallet_id}/pnl",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["realized_pnl_usd"] == "0E-18"
    assert data["realized_pnl_complete"] is True
    assert data["unrealized_pnl_complete"] is True
    assert data["total_pnl_usd"] is not None


def test_wallet_pnl_values_unknown_cost_holdings_without_inventing_pnl(
    client, app, monkeypatch
):
    from decimal import Decimal
    import app.services.pnl_service as pnl_service

    register(client, email="pnl-market-user@example.test")
    token = login(client, email="pnl-market-user@example.test").get_json()["access_token"]
    create_response = client.post(
        "/api/v1/wallets",
        json={"name": "Funded PnL Wallet", "base_currency": "USD"},
        headers=auth_headers(token),
    )
    wallet_id = create_response.get_json()["wallet"]["id"]

    with app.app_context():
        btc = db.session.execute(
            db.select(Asset).where(Asset.symbol == "BTC")
        ).scalar_one()
        balance = db.session.execute(
            db.select(Balance).where(
                Balance.wallet_id == wallet_id,
                Balance.asset_id == btc.id,
            )
        ).scalar_one()
        balance.available = Decimal("0.01")
        db.session.commit()

    monkeypatch.setattr(
        pnl_service,
        "get_market_price",
        lambda symbol, currency: Decimal("50000") if symbol == "BTC" else Decimal("2000"),
    )

    response = client.get(
        f"/api/v1/wallets/{wallet_id}/pnl",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.get_json()
    btc_position = next(row for row in data["positions"] if row["asset"] == "BTC")
    assert btc_position["total_quantity"] == "0.010000000000000000"
    assert btc_position["market_value_usd"] == "500.000000000000000000"
    assert btc_position["unrealized_pnl_usd"] is None
    assert btc_position["unrealized_pnl_complete"] is False
    assert data["total_pnl_usd"] is None


def test_simulated_crypto_deposit_tracks_unknown_cost_basis(client, app):
    register(client, email="deposit-cost-user@example.test")
    token = login(client, email="deposit-cost-user@example.test").get_json()["access_token"]
    create_response = client.post(
        "/api/v1/wallets",
        json={"name": "Deposit Cost Wallet", "base_currency": "USD"},
        headers=auth_headers(token),
    )
    wallet_id = create_response.get_json()["wallet"]["id"]

    response = client.post(
        f"/api/v1/wallets/{wallet_id}/deposits",
        json={"asset": "BTC", "amount": "0.025"},
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    with app.app_context():
        btc = db.session.execute(
            db.select(Asset).where(Asset.symbol == "BTC")
        ).scalar_one()
        position = db.session.execute(
            db.select(PositionCostBasis).where(
                PositionCostBasis.wallet_id == wallet_id,
                PositionCostBasis.asset_id == btc.id,
            )
        ).scalar_one()
        assert position.known_quantity == Decimal("0")
        assert position.known_cost_basis_usd == Decimal("0")
        assert round(position.unknown_quantity, 8) == Decimal("0.025")