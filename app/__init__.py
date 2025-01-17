# standard library imports
import asyncio
import logging

# pip imports
import aiohttp
import uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
from quart import Quart
from werkzeug.exceptions import HTTPException

# local imports
from app.helpers.utils import response, add_unsupported_mimetypes, logger_handler
from app.helpers.discord import CustomDiscordWebhook

discord_webhook = None

def create_app():
    app = Quart(__name__)

    # Setup logging
    handler = logger_handler()
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Load config.py
    app.config.from_pyfile('config.py')

    # Set Discord webhook URLs
    discord_webhook = CustomDiscordWebhook(app.config.get('DISCORD_WEBHOOKS'), adapter=discord.AsyncWebhookAdapter(aiohttp.ClientSession()))

    # Add unsupported mimetypes to mimetypes module
    add_unsupported_mimetypes()

    # jsonify HTTP errors
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        return response(e.code, e.name)

    # Import blueprints
    from app.blueprints.api.routes import api
    from app.blueprints.main.routes import main

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix='/api')

    return app
