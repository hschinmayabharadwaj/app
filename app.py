import os
import logging
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
import gspread

# --- Beam Calculator Imports --- (No changes here)
from beam_calculator import BeamCalculator
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# --- Basic Configuration ---
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "a-very-secret-key")

# --- Google Sheets Integration ---
try:
    # Use the JSON key to authenticate
    gc = gspread.service_account(filename='credentials.json')
    # Open the Google Sheet by its name
    sh = gc.open("WebAppUsers").sheet1  # Assumes the first sheet
except FileNotFoundError:
    logging.error("credentials.json not found. Please follow setup instructions.")
    sh = None
except gspread.exceptions.SpreadsheetNotFound:
    logging.error("Spreadsheet 'WebAppUsers' not found. Please create it and share it.")
    sh = None


# --- Authentication Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles user login and signup using Google Sheets as the database."""
    if sh is None:
        flash("Application is not configured correctly to connect to the user database.", "error")
        return render_template('random.html')

    if request.method == 'POST':
        data = request.json
        action = data.get("action")
        email = data.get("email", "").lower()
        password = data.get("password")

        # --- Find all existing users from the sheet ---
        try:
            user_records = sh.get_all_records()
        except gspread.exceptions.GSpreadException as e:
            logging.error(f"Error accessing Google Sheet: {e}")
            return jsonify({"success": False, "message": "Could not connect to user database."}), 500
        
        existing_user = next((user for user in user_records if user.get('Email', '').lower() == email), None)

        if action == "signup":
            name = data.get("name")
            if not all([name, email, password]):
                 return jsonify({"success": False, "message": "Name, email, and password are required."}), 400

            if existing_user:
                return jsonify({"success": False, "message": "This email is already registered."}), 409
            
            # 🔒 Hash the password for security before storing
            hashed_password = generate_password_hash(password)
            
            # Add the new user to the sheet
            sh.append_row([name, email, hashed_password])
            
            session['logged_in'] = True
            session['name'] = name
            flash("Signup successful! Welcome.", "success")
            return jsonify({"success": True, "message": "Signup successful."})

        elif action == "login":
            if not existing_user or not check_password_hash(existing_user.get('Password'), password):
                return jsonify({"success": False, "message": "Invalid email or password."}), 401
            
            # Login successful
            session['logged_in'] = True
            session['name'] = existing_user.get('Name')
            flash(f"Welcome back, {session['name']}!", "success")
            return jsonify({"success": True, "message": "Login successful."})
    
    return render_template('random.html')

# --- Other routes like '/', '/logout', and '/calculate' remain the same ---

@app.route('/')
def index():
    """Main page with the beam calculator form. Redirects to login if not authenticated."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/calculate', methods=['POST'])
def calculate():
    """Process beam calculation and display results. Protected route."""
    if not session.get('logged_in'):
        flash("Please log in to perform a calculation.", "error")
        return redirect(url_for('login'))
        
    # (The entire calculation logic you already have goes here, no changes needed)
    try:
        beam_length = float(request.form.get('beam_length', 0))
        young_modulus = float(request.form.get('young_modulus', 0))
        moment_inertia = float(request.form.get('moment_inertia', 0))
        support_type = request.form.get('support_type', 'simply_supported')
        
        if beam_length <= 0 or young_modulus <= 0 or moment_inertia <= 0:
            flash('All beam properties must be positive values.', 'error')
            return redirect(url_for('index'))
        
        calculator = BeamCalculator(beam_length, young_modulus, moment_inertia, support_type)
        
        load_types = request.form.getlist('load_type[]')
        load_magnitudes = request.form.getlist('load_magnitude[]')
        load_positions = request.form.getlist('load_position[]')
        load_lengths = request.form.getlist('load_length[]')
        
        if not load_types:
            flash('At least one load must be specified.', 'error')
            return redirect(url_for('index'))
        
        for i, load_type in enumerate(load_types):
            try:
                magnitude = float(load_magnitudes[i])
                position = float(load_positions[i])
                
                if load_type == 'point':
                    calculator.add_point_load(magnitude, position)
                elif load_type == 'distributed':
                    length = float(load_lengths[i]) if i < len(load_lengths) and load_lengths[i] else 1.0
                    calculator.add_distributed_load(magnitude, position, length)
            except (ValueError, IndexError) as e:
                flash(f'Invalid load data at position {i+1}: {str(e)}', 'error')
                return redirect(url_for('index'))
        
        calculator.calculate()
        plots = calculator.generate_plots()
        
        plot_data = {}
        for plot_name, fig in plots.items():
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            plot_data[plot_name] = base64.b64encode(img_buffer.getvalue()).decode()
            plt.close(fig)
        
        results = calculator.get_results()
        
        return render_template('results.html', 
                             plots=plot_data, 
                             results=results,
                             beam_length=beam_length,
                             support_type=support_type)
        
    except ValueError as e:
        flash(f'Input error: {str(e)}', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Calculation error: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)