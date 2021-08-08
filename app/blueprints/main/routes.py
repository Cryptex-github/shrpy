from quart import Blueprint
from app.helpers.services import FileService

main = Blueprint('main', __name__)

@main.get('/uploads/<filename>')
async def uploads(filename):
    return await FileService.get_by_filename()
