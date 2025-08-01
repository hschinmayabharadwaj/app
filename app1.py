from flask import Flask, request, jsonify, render_template
import importlib
import app

app = Flask(__name__)
users_db = {"test@example.com": {"name": "Test", "password": "1234"}}  # Demo user

@app.route("/")
def home():
    return render_template("./templates/hi.html")

@app.route("/api/auth", methods=["POST"])
def auth():
    data = request.json
    action = data.get("action")
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not email or not password or (action == "signup" and not name):
        return "❌ Missing fields", 400

    if action == "signup":
        if email in users_db:
            return "❌ User already exists", 400
        users_db[email] = {"name": name, "password": password}
        return f"✅ Signup successful. Welcome, {name}!"

    elif action == "login":
        user = users_db.get(email)
        if not user or user["password"] != password:
            return "❌ Invalid email or password", 400

        # 🔥 Run san.py logic
        result = app.run_app()
        return f"✅ Login successful. {result}"

    return "❌ Invalid action", 400

if __name__ == "__main__":
    app.run(debug=True)
