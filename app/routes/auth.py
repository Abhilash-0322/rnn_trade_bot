from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash

from ..auth.auth_manager import AuthManager
from ..models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and login processing"""
    if request.method == 'GET':
        return current_app.send_static_file("auth/login.html")
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400
        
        # Get auth manager from app context
        auth_manager = current_app.auth_manager
        
        # Try login by username
        success, message = auth_manager.login_user_by_username(username, password)
        
        if success:
            return jsonify({'success': True, 'message': message, 'redirect': '/'})
        else:
            return jsonify({'success': False, 'message': message}), 401


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and user registration"""
    if request.method == 'GET':
        return current_app.send_static_file("auth/register.html")
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        binance_api_key = data.get('binance_api_key')
        binance_api_secret = data.get('binance_api_secret')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        
        # Get auth manager from app context
        auth_manager = current_app.auth_manager
        
        # Register user
        success, message = auth_manager.register_user(
            username=username,
            email=email,
            password=password,
            binance_api_key=binance_api_key,
            binance_api_secret=binance_api_secret
        )
        
        if success:
            return jsonify({'success': True, 'message': message, 'redirect': '/login'})
        else:
            return jsonify({'success': False, 'message': message}), 400


@auth_bp.route('/logout')
def logout():
    """Logout user"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect('/login')


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page and profile updates"""
    if request.method == 'GET':
        return current_app.send_static_file("auth/profile.html")
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        # Get auth manager from app context
        auth_manager = current_app.auth_manager
        
        updates = {}
        
        # Update email if provided
        if 'email' in data and data['email'] != current_user.email:
            # Check if email is already taken
            existing_user = auth_manager.db.get_user_by_email(data['email'])
            if existing_user and existing_user.user_id != current_user.user_id:
                return jsonify({'success': False, 'message': 'Email already exists'}), 400
            updates['email'] = data['email']
        
        # Update API keys if provided
        if 'binance_api_key' in data:
            updates['binance_api_key'] = data['binance_api_key']
        if 'binance_api_secret' in data:
            updates['binance_api_secret'] = data['binance_api_secret']
        
        # Update password if provided
        if 'new_password' in data and data['new_password']:
            if len(data['new_password']) < 6:
                return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
            updates['password_hash'] = generate_password_hash(data['new_password'])
        
        if updates:
            success = auth_manager.update_user_profile(current_user.user_id, updates)
            if success:
                return jsonify({'success': True, 'message': 'Profile updated successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to update profile'}), 500
        
        return jsonify({'success': False, 'message': 'No changes to update'}), 400



# --- Backward compatibility routes (old '/auth/*' paths) ---

@auth_bp.route('/auth/login', methods=['GET', 'POST'])
def login_compat():
    return login()


@auth_bp.route('/auth/register', methods=['GET', 'POST'])
def register_compat():
    return register()


@auth_bp.route('/auth/logout')
def logout_compat():
    return logout()


@auth_bp.get('/auth/api/check-auth')
def check_auth_compat():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.user_id,
                'username': current_user.username,
                'email': current_user.email
            }
        })
    else:
        return jsonify({'authenticated': False}), 401

