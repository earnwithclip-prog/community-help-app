"""
Community Help Request Management System
=========================================
A Flask web application that connects people who need help
with community volunteers using a centralized system.
Features rule-based AI for urgency classification,
admin access control, and volunteer emergency alerts.
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, session)

app = Flask(__name__)
app.secret_key = "community_help_secret_key_2024"

DATABASE = "community_help.db"


# ──────────────────────────────────────────────
# ADMIN ACCESS CONTROL — Volunteer-based Auth
# ──────────────────────────────────────────────

ADMIN_ACCESS_CODE = "UNPAID"


def get_volunteer_by_email(email):
    """Return the volunteer row for the given email, or None."""
    conn = get_db()
    vol = conn.execute(
        "SELECT * FROM volunteers WHERE LOWER(email) = LOWER(?)", (email,)
    ).fetchone()
    conn.close()
    return vol


def admin_required(f):
    """Decorator: protect routes so only authenticated admins can access."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Access denied. Please log in to the Admin Panel.", "error")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────
# DATABASE HELPERS
# ──────────────────────────────────────────────

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Auto-create tables if they don't exist."""
    conn = get_db()
    # Help requests table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS help_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            urgency TEXT NOT NULL DEFAULT 'Low',
            solved_status TEXT NOT NULL DEFAULT 'Unsolved',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Volunteers table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS volunteers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_seen_alert_id INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# RULE-BASED AI — Urgency Prediction
# ──────────────────────────────────────────────

def predict_urgency(description: str) -> str:
    """
    Rule-based AI function that classifies urgency from the
    description text using keyword matching.

    Returns: 'Emergency', 'Medium', or 'Low'
    """
    text = description.lower()

    # Emergency keywords
    emergency_keywords = [
        "accident", "fire", "blood", "hospital", "unconscious",
        "emergency", "urgent", "dying", "collapse", "critical",
        "ambulance", "heart attack", "stroke", "drowning",
        "earthquake", "flood", "trapped", "severe", "life-threatening",
        "choking", "bleeding", "injury", "injured", "wound",
        "electrocution", "poison", "overdose", "suicide", "assault",
        "violence", "gunshot", "stabbing", "burning", "explosion"
    ]

    # Medium keywords
    medium_keywords = [
        "food", "medicine", "support", "need help", "assistance",
        "shelter", "clothes", "clothing", "water", "electricity",
        "medical", "doctor", "prescription", "transport", "repair",
        "broken", "leak", "sick", "ill", "fever", "pain",
        "homeless", "hungry", "stranded", "lost", "disabled",
        "elderly", "child", "baby", "pregnant", "medication"
    ]

    # Check emergency keywords first (highest priority)
    for keyword in emergency_keywords:
        if keyword in text:
            return "Emergency"

    # Check medium keywords
    for keyword in medium_keywords:
        if keyword in text:
            return "Medium"

    # Default to Low
    return "Low"


# ──────────────────────────────────────────────
# ROUTES — Public
# ──────────────────────────────────────────────

@app.route("/")
def index():
    """User Request Page — form to submit a help request."""
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit_request():
    """Handle help request form submission."""
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    # Validate required fields
    if not all([name, phone, address, category, description]):
        flash("All fields are required. Please fill in every field.", "error")
        return redirect(url_for("index"))

    # Predict urgency using rule-based AI
    urgency = predict_urgency(description)

    # Store in database
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db()
    conn.execute(
        """INSERT INTO help_requests
           (name, phone, address, category, description, urgency, solved_status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, phone, address, category, description, urgency, "Unsolved", created_at)
    )
    conn.commit()
    conn.close()

    # Redirect to success page with request details
    return render_template("success.html",
                           name=name,
                           phone=phone,
                           address=address,
                           category=category,
                           description=description,
                           urgency=urgency,
                           created_at=created_at)


@app.route("/requests")
def view_requests():
    """Volunteer View — show all requests in a table."""
    conn = get_db()
    requests_list = conn.execute(
        "SELECT * FROM help_requests ORDER BY created_at DESC"
    ).fetchall()

    # Check for emergency alerts for logged-in volunteers
    emergency_alerts = []
    volunteer = None
    vol_email = session.get("volunteer_email")
    if vol_email:
        volunteer = conn.execute(
            "SELECT * FROM volunteers WHERE email = ?", (vol_email,)
        ).fetchone()
        if volunteer:
            last_seen = volunteer["last_seen_alert_id"]
            emergency_alerts = conn.execute(
                """SELECT * FROM help_requests
                   WHERE urgency = 'Emergency' AND id > ?
                   ORDER BY created_at DESC""",
                (last_seen,)
            ).fetchall()

    conn.close()
    return render_template("requests.html",
                           requests=requests_list,
                           emergency_alerts=emergency_alerts,
                           volunteer=volunteer)


@app.route("/dismiss-alerts", methods=["POST"])
def dismiss_alerts():
    """Dismiss emergency alerts for the logged-in volunteer."""
    vol_email = session.get("volunteer_email")
    if vol_email:
        conn = get_db()
        # Get the latest request ID
        latest = conn.execute(
            "SELECT MAX(id) as max_id FROM help_requests"
        ).fetchone()
        if latest and latest["max_id"]:
            conn.execute(
                "UPDATE volunteers SET last_seen_alert_id = ? WHERE email = ?",
                (latest["max_id"], vol_email)
            )
            conn.commit()
        conn.close()
    return redirect(url_for("view_requests"))


# ──────────────────────────────────────────────
# ROUTES — Volunteer Registration
# ──────────────────────────────────────────────

@app.route("/volunteer/register", methods=["GET", "POST"])
def volunteer_register():
    """Register a new volunteer."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()

        if not all([name, phone, email]):
            flash("All fields are required.", "error")
            return redirect(url_for("volunteer_register"))

        conn = get_db()
        # Check if email already registered
        existing = conn.execute(
            "SELECT id FROM volunteers WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash("This email is already registered as a volunteer.", "error")
            conn.close()
            return redirect(url_for("volunteer_register"))

        # Get current max request ID so they don't see old alerts
        latest = conn.execute(
            "SELECT MAX(id) as max_id FROM help_requests"
        ).fetchone()
        last_seen = latest["max_id"] if latest and latest["max_id"] else 0

        conn.execute(
            """INSERT INTO volunteers (name, phone, email, registered_at, last_seen_alert_id)
               VALUES (?, ?, ?, ?, ?)""",
            (name, phone, email,
             datetime.now().strftime("%Y-%m-%d %H:%M:%S"), last_seen)
        )
        conn.commit()
        conn.close()

        # Auto-login the volunteer
        session["volunteer_email"] = email
        session["volunteer_name"] = name

        flash(f"Welcome, {name}! You are now registered as a volunteer.", "success")
        return redirect(url_for("view_requests"))

    return render_template("volunteer_register.html")


@app.route("/volunteer/login", methods=["GET", "POST"])
def volunteer_login():
    """Login for existing volunteers."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Please enter your email.", "error")
            return redirect(url_for("volunteer_login"))

        conn = get_db()
        vol = conn.execute(
            "SELECT * FROM volunteers WHERE email = ?", (email,)
        ).fetchone()
        conn.close()

        if not vol:
            flash("Email not found. Please register first.", "error")
            return redirect(url_for("volunteer_register"))

        session["volunteer_email"] = vol["email"]
        session["volunteer_name"] = vol["name"]
        flash(f"Welcome back, {vol['name']}!", "success")
        return redirect(url_for("view_requests"))

    return render_template("volunteer_login.html")


@app.route("/volunteer/logout")
def volunteer_logout():
    """Logout the volunteer."""
    session.pop("volunteer_email", None)
    session.pop("volunteer_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("view_requests"))


# ──────────────────────────────────────────────
# ROUTES — Admin (Protected)
# ──────────────────────────────────────────────

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login page — requires volunteer session + access code."""
    # Already logged in?
    if session.get("admin_logged_in"):
        return redirect(url_for("admin"))

    # Must be logged in as a volunteer first
    vol_email = session.get("volunteer_email")
    vol_name = session.get("volunteer_name")
    if not vol_email:
        flash("Please log in as a volunteer first before accessing the Admin Panel.", "error")
        return redirect(url_for("volunteer_login"))

    if request.method == "POST":
        access_code = request.form.get("access_code", "").strip()

        # Validation: access code required
        if not access_code:
            flash("Please enter the access code.", "error")
            return redirect(url_for("admin_login"))

        # Check access code
        if access_code != ADMIN_ACCESS_CODE:
            flash("Incorrect access code. Access denied.", "error")
            return redirect(url_for("admin_login"))

        # Verify email still belongs to a registered volunteer
        volunteer = get_volunteer_by_email(vol_email)
        if not volunteer:
            flash("Access denied. Your volunteer account was not found.", "error")
            return redirect(url_for("admin_login"))

        # ✅ Access granted — use the volunteer's own email
        session["admin_logged_in"] = True
        session["admin_email"] = vol_email
        session["admin_name"] = volunteer["name"]
        flash(f"Welcome, {volunteer['name']}! Admin access granted.", "success")
        return redirect(url_for("admin"))

    return render_template("admin_login.html",
                           volunteer_email=vol_email,
                           volunteer_name=vol_name)


@app.route("/admin/logout")
def admin_logout():
    """Log out of admin session."""
    session.pop("admin_logged_in", None)
    session.pop("admin_email", None)
    session.pop("admin_name", None)
    flash("You have been logged out from Admin Panel.", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    """Admin Module — view all requests with filters and actions."""
    # Get filter parameters
    urgency_filter = request.args.get("urgency", "all")
    status_filter = request.args.get("status", "all")

    conn = get_db()

    # Build query dynamically based on filters
    query = "SELECT * FROM help_requests WHERE 1=1"
    params = []

    if urgency_filter == "emergency":
        query += " AND urgency = ?"
        params.append("Emergency")

    if status_filter == "solved":
        query += " AND solved_status = ?"
        params.append("Solved")
    elif status_filter == "unsolved":
        query += " AND solved_status = ?"
        params.append("Unsolved")

    # Always sort by latest first
    query += " ORDER BY created_at DESC"

    requests_list = conn.execute(query, params).fetchall()

    # Get volunteer count
    volunteer_count = conn.execute("SELECT COUNT(*) as c FROM volunteers").fetchone()["c"]

    conn.close()

    return render_template("admin.html",
                           requests=requests_list,
                           urgency_filter=urgency_filter,
                           status_filter=status_filter,
                           admin_name=session.get("admin_name", "Admin"),
                           volunteer_count=volunteer_count)


@app.route("/admin/toggle/<int:request_id>", methods=["POST"])
@admin_required
def toggle_status(request_id):
    """Toggle the solved/unsolved status of a request."""
    conn = get_db()
    row = conn.execute(
        "SELECT solved_status FROM help_requests WHERE id = ?", (request_id,)
    ).fetchone()

    if row:
        new_status = "Solved" if row["solved_status"] == "Unsolved" else "Unsolved"
        conn.execute(
            "UPDATE help_requests SET solved_status = ? WHERE id = ?",
            (new_status, request_id)
        )
        conn.commit()
        flash(f"Request #{request_id} marked as {new_status}.", "success")
    else:
        flash(f"Request #{request_id} not found.", "error")

    conn.close()

    # Preserve current filters when redirecting back
    urgency_filter = request.form.get("urgency_filter", "all")
    status_filter = request.form.get("status_filter", "all")
    return redirect(url_for("admin", urgency=urgency_filter, status=status_filter))


# ──────────────────────────────────────────────
# APP ENTRY POINT
# ──────────────────────────────────────────────

# Initialize DB at module level so gunicorn can create it on startup
init_db()

if __name__ == "__main__":
    print("=" * 50)
    print("  Community Help Request Management System")
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
