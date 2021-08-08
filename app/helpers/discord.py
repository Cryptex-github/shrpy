# standard library imports
from datetime import datetime
from random import randint
from functools import cached_property

# pip imports
from quart import current_app
from discord import Webhook, Embed

# local imports
from app.helpers.utils import Message

class CustomDiscordWebhook(DiscordWebhook):
    def __init__(self, url=None, adapter=None):
        super().from_url(url, adapter=adapter)

    @cached_property
    def is_enabled(self) -> bool:
        """Checks if Discord webhook is enabled."""
        return self.url is not None and len(self.url) > 0

    def execute(self, embed):
        """Executes the webhook and handles Timeout exception."""
        try:
            return super().execute(embed=embed)
        except Exception as err:
            current_app.logger.error(f'requests.exceptions.Timeout exception has occurred during webhook execution: {err}')

class CustomDiscordEmbed(Embed):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ShareX file URL/short URL and deletion URL
        self.content_url = kwargs.get('content_url')
        self.deletion_url = kwargs.get('deletion_url')
        
        # Add markdown links to embed
        self.add_field(name=Message.URL, value=f'**[{Message.CLICK_HERE_TO_VIEW}]({self.content_url})**')
        self.add_field(name=Message.DELETION_URL, value=f'**[{Message.CLICK_HERE_TO_DELETE}]({self.deletion_url})**')

        # Set random color for embed
        self.color = randint(0, 0xffffff)

        self.timestamp = datetime.utcnow()

class FileEmbed(CustomDiscordEmbed):
    def __init__(self, **kwargs):
        """Represents DiscordEmbed for files."""
        super().__init__(**kwargs)

        self.title = Message.FILE_UPLOADED
        self.description = self.content_url
        self.set_image(url=self.content_url)

