from src.main import create_app

from src.config.settings import (
    PRODUCTION_SERVER_PORT,
    DEV_SERVER_PORT,
    REQUEST_TIMEOUT,
    STAGE
)

app = create_app()
if __name__ == "__main__":
    try:
        if STAGE == 'prod':
            app.logger.info('Start production server')
            app.run(debug = False, port = PRODUCTION_SERVER_PORT)
        else:
            app.logger.info('Start development server')
            app.run(debug = True, port = DEV_SERVER_PORT)
    except (KeyboardInterrupt, SystemExit) as e:
        app.logger.error(f'Error while running server: {str(e)}')
