import logging

from flask import Flask

def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False

    # Load config from settings.py
    app.config.from_pyfile('config/settings.py')

    # Register routes
    register_routes(app)

    return app

def register_routes(app):
    """
    Imports and registers all route blueprints.
    """
    from .routes.chat_routes import chat_bp
    from .routes.start_routes import start_bp
    from .routes.end_routes import end_bp
    from .routes.general_routes import general_bp

    app.register_blueprint(chat_bp)
    app.register_blueprint(start_bp)
    app.register_blueprint(end_bp)
    app.register_blueprint(general_bp)

# If you use a background scheduler
# def start_scheduler(app):
#     scheduler = BackgroundScheduler()
#     # Add your jobs here...
#     scheduler.start()
