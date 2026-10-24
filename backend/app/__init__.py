"""VeriScope — reviewer copilot for application validation (SIH26261)."""
from __future__ import annotations

import uuid
from pathlib import Path

from flask import Flask, g, request, send_from_directory

from .api.routes import api, health
from .container import Services, build_services
from .core.config import Settings
from .core.errors import register_error_handlers
from .core.logging import configure_logging
from .core.security import install_security_headers

__version__ = "1.0.0"


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    configure_logging(settings.log_level)
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_bytes + 1024 * 1024
    app.config["JSON_SORT_KEYS"] = False
    services: Services = build_services(settings)
    app.extensions["veriscope"] = services

    @app.before_request
    def _correlation() -> None:
        incoming = request.headers.get("X-Request-ID", "")
        g.correlation_id = incoming if 8 <= len(incoming) <= 64 and incoming.replace("-", "").isalnum() else str(uuid.uuid4())

    @app.teardown_appcontext
    def _close(_: BaseException | None) -> None:
        # Release thread-local SQLite connections when the app context tears down
        # so that WSGI server threads that are recycled do not hold open handles.
        services.db.close()

    register_error_handlers(app)
    install_security_headers(app, settings.cors_origins)
    app.register_blueprint(api)
    app.register_blueprint(health)

    dist = settings.frontend_dist
    if dist and Path(dist).joinpath("index.html").exists():
        dist_path = Path(dist).resolve()

        @app.get("/")
        @app.get("/<path:path>")
        def spa(path: str = ""):  # type: ignore[no-untyped-def]
            target = (dist_path / path).resolve()
            if path and dist_path in target.parents and target.is_file():
                return send_from_directory(dist_path, path)
            return send_from_directory(dist_path, "index.html")

    return app
