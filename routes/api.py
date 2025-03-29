from flask import Blueprint, request, jsonify
from services.checkin_service import handle_checkin

bp = Blueprint('api', __name__)

@bp.route('/api/checkin', methods=['POST'])
def checkin():
    data = request.json
    success, msg = handle_checkin(data)
    return jsonify({"success": success, "message": msg})
