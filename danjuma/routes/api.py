from flask import Blueprint, request, jsonify
from models.database import get_db_connection

api_bp = Blueprint('api', __name__)

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("INSERT OR REPLACE INTO registered_emails (email, is_active) VALUES (?, 1)", (email,))
        db.commit()
        return jsonify({"message": f"Successfully registered {email}"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@api_bp.route('/scans', methods=['GET'])
def get_scans():
    email = request.args.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM scan_history WHERE registered_email = ? ORDER BY scanned_at DESC", (email,))
    scans = [dict(row) for row in cursor.fetchall()]
    db.close()
    
    return jsonify(scans)

@api_bp.route('/status', methods=['GET'])
def get_status():
    email = request.args.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT is_active FROM registered_emails WHERE email = ?", (email,))
    row = cursor.fetchone()
    db.close()
    
    if row:
        return jsonify({"is_active": bool(row['is_active'])})
    else:
        return jsonify({"is_active": False})

@api_bp.route('/gmail/auth-url', methods=['GET'])
def gmail_auth_url():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    gmail_service = GmailService(email=email)
    auth_url, state = gmail_service.get_authorization_url(email=email)

    if not auth_url:
        return jsonify({"error": "Unable to generate Gmail authorization URL"}), 500

    return jsonify({"auth_url": auth_url, "state": state})

@api_bp.route('/gmail/authorize', methods=['POST'])
def gmail_authorize():
    data = request.get_json() or {}
    email = data.get('email')
    code = data.get('code')

    if not email or not code:
        return jsonify({"error": "Email and authorization code are required"}), 400

    gmail_service = GmailService(email=email)
    creds = gmail_service.exchange_code_for_credentials(code, email=email)

    if not creds:
        return jsonify({"error": "Failed to exchange authorization code for credentials"}), 500

    return jsonify({"message": f"Gmail authorized for {email}"}), 200

@api_bp.route('/unregister', methods=['DELETE'])
def unregister():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400

    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("UPDATE registered_emails SET is_active = 0 WHERE email = ?", (email,))
    db.commit()
    db.close()
    
    return jsonify({"message": f"Successfully deactivated protection for {email}"})
