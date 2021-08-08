# standard library imports
from http import HTTPStatus

# pip imports
from quart import (
    Response, request, jsonify, 
    current_app, abort, url_for, 
    send_from_directory, redirect,
)

# local imports
from app import discord_webhook
from app.helpers.main import File, ShortUrl
from app.helpers.utils import Message, response, create_hmac_hexdigest, is_valid_digest

class FileService:
    @staticmethod
    async def create() -> Response:
        uploaded_file = await request.files.get('file')
        
        if uploaded_file is None:
            return response(HTTPStatus.BAD_REQUEST, Message.INVALID_FILE)

        # Our own class which utilises werkzeug.datastructures.FileStorage
        use_og_filename = bool(request.headers.get('X-Use-Original-Filename', type=int))
        f = File(uploaded_file, use_og_filename)

        # Check if file is allowed
        if f.is_allowed() is False:
            return response(HTTPStatus.UNPROCESSABLE_ENTITY, Message.INVALID_FILE_TYPE)

        # Save the file
        await f.save()

        # Send data to Discord webhook
        if discord_webhook.is_enabled:
            discord_webhook.add_embed(
                f.embed()
            )
            await discord_webhook.execute()

        # Return JSON
        return jsonify(url=f.url, delete_url=f.deletion_url)

    @staticmethod
    async def delete() -> Response:
        filename = request.view_args.get('filename')
        hmac_hash = request.view_args.get('hmac_hash')
        new_hmac_hash = create_hmac_hexdigest(filename, current_app.secret_key)

        # If digest is invalid
        if is_valid_digest(hmac_hash, new_hmac_hash) is False:
            abort(HTTPStatus.NOT_FOUND)

        if await File.delete(filename) is False:
            abort(HTTPStatus.GONE)

        return response(message=Message.FILE_DELETED)
    
    @staticmethod
    async def config() -> Response:
        cfg = {
            "Name": "{} (File uploader)".format(request.host),
            "Version": "1.0.0",
            "DestinationType": "ImageUploader, FileUploader",
            "RequestMethod": "POST",
            "RequestURL": url_for('api.upload', _external=True),
            "Body": "MultipartFormData",
            "FileFormName": "file",
            "URL": "$json:url$",
            "DeletionURL": "$json:delete_url$",
            "Headers": {
                "Authorization": "YOUR-UPLOAD-PASSWORD-HERE",
                "X-Use-Original-Filename": 1,
            },
            "ErrorMessage": "$json:status$"
        }
        return jsonify(cfg)

    @staticmethod
    def get_by_filename() -> Response:
        filename = request.view_args.get('filename')
        upload_dir = current_app.config['UPLOAD_DIR']
        return send_from_directory(upload_dir, filename)
