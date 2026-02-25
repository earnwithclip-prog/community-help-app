"""
Community Help Request Management System
=========================================
A Flask web application that connects people who need help
with community volunteers using a centralized system.
Features rule-based AI for urgency classification.
"""

import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

app = Flask(__name__)
app.secret_key = "community_help_secret_key_2024"

DATABASE = "community_help.db"


# ──────────────────────────────────────────────
# DATABASE HELPERS
# ──────────────────────────────────────────────

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Auto-create the help_requests table if it doesn't exist."""
    conn = get_db()
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
# ROUTES
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
    conn.close()
    return render_template("requests.html", requests=requests_list)


@app.route("/admin")
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
    conn.close()

    return render_template("admin.html",
                           requests=requests_list,
                           urgency_filter=urgency_filter,
                           status_filter=status_filter)


@app.route("/admin/toggle/<int:request_id>", methods=["POST"])
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

import os

# Initialize DB at module level so gunicorn can create it on startup
init_db()

if __name__ == "__main__":
    print("=" * 50)
    print("  Community Help Request Management System")
    print("  Running at: http://127.0.0.1:5000")
    print("=" * 50)
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
