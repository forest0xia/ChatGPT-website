import logging
import uuid

from flask import Flask, g, has_request_context

class RequestIDLogFilter(logging.Filter):
    def filter(self, record):
        if has_request_context():
            record.request_id = getattr(g, "request_id", "NO_REQUEST_ID")
        else:
            # Outside any request, so default
            record.request_id = "NO_REQUEST_ID"
        return True


def create_app():
    app = Flask(__name__)
    
    @app.before_request
    def assign_request_id():
        """
        Generate or retrieve some ID for each request and store it in g.
        In this example, we generate a UUID, but you can use
        steam_id or any custom ID you want.
        """
        g.request_id = str(uuid.uuid4())

    configure_logging(app)

    # Load config from settings.py
    app.config.from_pyfile('config/settings.py')

    # Register routes
    register_routes(app)

    return app


def configure_logging(app):
    # Remove the default handler if you want full control
    if app.logger.handlers:
        for handler in list(app.logger.handlers):
            app.logger.removeHandler(handler)
    logging.getLogger('werkzeug').setLevel(logging.ERROR)

    # Create a custom handler with the desired format
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(message)s'
    )
    handler.setFormatter(formatter)

    # Add our custom filter that sets request_id
    handler.addFilter(RequestIDLogFilter())

    # Attach the handler to the Flask app logger
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False



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
