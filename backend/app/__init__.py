from flask import Flask, jsonify
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

from app.extensions import db, migrate


def create_app(test_config=None):
    load_dotenv()

    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    JWTManager(app)

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so migrations can detect them.
    from app.models import User  # noqa: F401

    from app.routes import auth_bp
    from app.routes.wallets import wallets_bp
    from app.routes.deposits import deposits_bp
    from app.routes.balances import balances_bp
    from app.routes.orders import orders_bp
    from app.routes.market import market_bp
    from app.routes.pnl import pnl_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(wallets_bp)
    app.register_blueprint(deposits_bp)
    app.register_blueprint(balances_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(market_bp)
    app.register_blueprint(pnl_bp)

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/v1/database/status")
    def database_status():
        try:
            db.session.execute(db.text("SELECT 1"))

            return jsonify({
                "database": "connected",
                "status": "ok",
            })
        except Exception:
            db.session.rollback()
            app.logger.exception(
                "Database connection test failed"
            )

            return jsonify({
                "database": "disconnected",
                "status": "error",
            }), 503

    return app