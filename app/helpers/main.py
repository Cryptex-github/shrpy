# standard library imports
import os
import secrets
from urllib.parse import urlparse
from functools import cached_property
from mimetypes import guess_extension

# pip imports
from magic import from_buffer
from quart import url_for, current_app, run_sync
from quart.datastructures import FileStorage
from quart import safe_join, secure_filename

# local imports
from app import config
from app.helpers.utils import create_hmac_hexdigest
from app.helpers.discord import FileEmbed


class File:
    def __init__(self, file_instance: FileStorage, use_original_filename=True):
        """Class for uploaded files which takes the `werkzeug.datastructures.FileStorage` from `flask.Request.files` as first parameter."""
        if isinstance(file_instance, FileStorage) is False:
            raise InvalidFileException(file_instance)

        self.use_original_filename = use_original_filename

        # Private FileStorage instance
        self.__file = file_instance

    @cached_property
    def filename(self) -> str:
        """Returns random filename."""
        custom_filename = secrets.token_urlsafe(config.FILE_TOKEN_BYTES)

        if self.use_original_filename:
            filename = f'{custom_filename}-{self.original_filename_root[:config.ORIGINAL_FILENAME_LENGTH]}'
        else:
            filename = custom_filename

        return f'{filename}.{self.extension}'

    @cached_property
    async def extension(self) -> str:
        """Returns extension using `python-magic` and `mimetypes`."""
        file_bytes = await self.__file.read(config.MAGIC_BUFFER_BYTES)
        mime = (await run_sync(from_buffer)(file_bytes, mime=True)).lower()
        ext = guess_extension(mime)

        if ext is None:
            current_app.logger.error(f'Unable to determine file extension for file {self.__file.filename} - MIME type {mime}')

        return ext.replace('.', '')

    @cached_property
    def original_filename_root(self):
        """Returns the original filename without extension."""
        sec_filename = secure_filename(self.__file.filename.lower())
        root, ext = os.path.splitext(sec_filename)
        return root

    @cached_property
    def hmac(self) -> str:
        """Returns HMAC digest calculated from filename, `flask.current_app.secret_key` is used as secret."""
        return create_hmac_hexdigest(self.filename, current_app.secret_key)
    
    @cached_property
    def url(self) -> str:
        """Returns file URL using `flask.url_for`."""
        return url_for('main.uploads', filename=self.filename, _external=True)
    
    @cached_property
    def deletion_url(self) -> str:
        """Returns deletion URL using `flask.url_for`."""
        return url_for('api.delete_file', hmac_hash=self.hmac, filename=self.filename, _external=True)

    @staticmethod
    def delete(filename: str) -> bool:
        """Deletes the file from `config.UPLOAD_DIR`, if it exists."""
        file_path = safe_join(config.UPLOAD_DIR, filename)

        if os.path.isfile(file_path) is False:
            return False

        current_app.logger.info(f'Deleted file {file_path}')

        os.remove(file_path)

        return True

    def is_allowed(self) -> bool:
        """Check if file is allowed, based on `config.ALLOWED_EXTENSIONS`."""
        if not config.ALLOWED_EXTENSIONS:
            return True
        
        allowed = self.extension in config.ALLOWED_EXTENSIONS

        if allowed is False:
            current_app.logger.warning(f'File {self.__file.filename} (detected extension {self.extension}) is not allowed')        

        return allowed

    async def save(self, save_directory = config.UPLOAD_DIR) -> None:
        """Saves the file to `UPLOAD_DIR`."""
        if os.path.isdir(save_directory) is False:
            os.makedirs(save_directory)

        save_path = safe_join(save_directory, self.filename)

        current_app.logger.info(f'Saving file {self.__file.filename} to {save_path}')
        current_app.logger.info(f'URLs: {self.url} - {self.deletion_url}')

        # Set file descriptor back to beginning of the file so save works correctly
        self.__file.seek(os.SEEK_SET)

        await self.__file.save(save_path)

    def embed(self) -> FileEmbed:
        """Returns FileEmbed instance for this file."""
        return FileEmbed(
            content_url=self.url, 
            deletion_url=self.deletion_url
        )

class InvalidFileException(Exception):
    """Raised when `File` is initialized using wrong `file_instance`."""
    def __init__(self, file_instance, *args):
        self.file_instance = file_instance
        super().__init__(*args)

    def __str__(self):
        file_instance_type = type(self.file_instance)
        return f'{self.file_instance} ({file_instance_type}) is not an instance of werkzeug.datastructures.FileStorage ({FileStorage})'

