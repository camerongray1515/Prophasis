from flask import jsonify

def error_response(error_message):
    return jsonify({"success": False, "message": error_message})