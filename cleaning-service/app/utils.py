from flask import jsonify


def error(message, status=400):
    response = jsonify({"error": message})
    response.status_code = status
    return response


def missing_fields(data, required):
    return [field for field in required if field not in data or data[field] in (None, "")]
