from quart import Blueprint
from app.helpers.utils import auth_required
from app.helpers.services import FileService

api = Blueprint('api', __name__)

@api.get('/sharex/upload')
async def upload_config():
    return await FileService.config()

@api.post('/upload')
@auth_required
async def upload():
    return await FileService.create()

@api.get('/delete-file/<hmac_hash>/<filename>')
async def delete_file(hmac_hash, filename):
    return await FileService.delete()
