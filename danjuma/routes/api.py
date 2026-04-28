from flask import Blueprint, request, jsonify, redirect
from services.gmail_service import GmailService
from models.database import get_db_connection
import traceback
import os

api_bp = Blueprint('api', __name__)

def _build_redirect_uri():
    """
    Returns the OAuth redirect URI.
    Prefers the APP_BASE_URL env var (set this on Render to your public URL).
    Falls back to deriving it from the request, forcing https when behind a proxy.
    """
    base_url = os.environ.get('APP_BASE_URL', '').rstrip('/')
    print(f"[DEBUG] APP_BASE_URL env var: '{base_url}'", flush=True)
    
    if base_url:
        redirect_uri = base_url + '/api/gmail/callback'
        print(f"[DEBUG] Using APP_BASE_URL, redirect_uri: {redirect_uri}", flush=True)
        return redirect_uri

    # Fallback: derive from request, fix http->https when behind Render's proxy
    base = request.url_root.rstrip('/')
    x_forwarded_proto = request.headers.get('X-Forwarded-Proto')
    print(f"[DEBUG] X-Forwarded-Proto: {x_forwarded_proto}", flush=True)
    print(f"[DEBUG] request.url_root: {request.url_root}", flush=True)
    
    if x_forwarded_proto == 'https':
        base = base.replace('http://', 'https://', 1)
    
    redirect_uri = base + '/api/gmail/callback'
    print(f"[DEBUG] Fallback redirect_uri: {redirect_uri}", flush=True)
    return redirect_uri

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

@api_bp.route('/gmail/callback')
def gmail_callback():
    """Handle OAuth callback from Google."""
    code = request.args.get('code')
    state = request.args.get('state')  # This will be the email
    error = request.args.get('error')
    
    print(f"=== gmail_callback invoked ===", flush=True)
    print(f"code present: {bool(code)}", flush=True)
    print(f"state (email): {state}", flush=True)
    print(f"error from Google: {error}", flush=True)
    
    if error:
        print(f"Google returned error: {error}", flush=True)
        return redirect(f"{request.host_url}?error=google_oauth_error_{error}")
    
    if not code or not state:
        print("Missing code or state parameter", flush=True)
        return redirect(f"{request.host_url}?error=missing_code_or_state")
    
    redirect_uri = _build_redirect_uri()
    print(f"gmail_callback: using redirect_uri={redirect_uri}", flush=True)

    try:
        gmail_service = GmailService(email=state)
        creds = gmail_service.exchange_code_for_credentials(code, email=state, redirect_uri=redirect_uri)
    except Exception as e:
        print(f"Exception during exchange_code_for_credentials: {e}", flush=True)
        traceback.print_exc()
        return redirect(f"{request.host_url}?error=exception_during_exchange")
    
    if not creds:
        print("exchange_code_for_credentials returned None", flush=True)
        return redirect(f"{request.host_url}?error=failed_to_exchange_code")
    
    print(f"Successfully obtained credentials for {state}", flush=True)
    
    # Register the email if not already registered
    db = get_db_connection()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO registered_emails (email, is_active) VALUES (?, 1)", (state,))
        db.commit()
        print(f"Registered email {state} in database", flush=True)
    except Exception as e:
        print(f"Error registering email: {e}", flush=True)
    finally:
        db.close()
    
    # Redirect back to homepage with success
    return redirect(f"{request.host_url}?success=gmail_authorized&email={state}")

@api_bp.route('/gmail/auth-url', methods=['GET'])
def gmail_auth_url():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    redirect_uri = _build_redirect_uri()
    print(f"gmail_auth_url: using redirect_uri={redirect_uri}")

    try:
        gmail_service = GmailService(email=email)
        auth_url, state = gmail_service.get_authorization_url(email=email, redirect_uri=redirect_uri)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Exception generating auth URL: {str(e)}"}), 500

    if not auth_url:
        return jsonify({"error": "Unable to generate Gmail authorization URL. Check that credentials.json exists and is valid."}), 500

    return redirect(auth_url)

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
