import os
import re
import uuid
from flask import Flask, render_template, request, jsonify, send_file, abort
from database import init_db, db_session, execute, fetchone, fetchall, is_postgres
from pdf_gen import generate_pdf, VALID_TEMPLATES

app = Flask(__name__)

MAX_STUDENTS = 500
MAX_FIELD_LEN = 200
UID_PATTERN = re.compile(r"^[a-f0-9]{8}$")


def _clean(text, max_len=MAX_FIELD_LEN):
    return (text or "").strip()[:max_len]


def _get_cert(unique_id):
    if not UID_PATTERN.match(unique_id):
        return None
    with db_session() as conn:
        cur = execute(
            conn,
            "SELECT c.*, b.company_name, b.title, b.template FROM certificates c "
            "JOIN batches b ON c.batch_id = b.id WHERE c.unique_id = ?",
            (unique_id,),
        )
        return fetchone(cur)


def _unique_id(conn):
    for _ in range(5):
        uid = uuid.uuid4().hex[:8]
        cur = execute(conn, "SELECT 1 FROM certificates WHERE unique_id = ?", (uid,))
        if not cur.fetchone():
            return uid
    return uuid.uuid4().hex


@app.route("/health")
def health():
    try:
        with db_session() as conn:
            execute(conn, "SELECT 1")
        return jsonify({"status": "ok", "db": "neon" if is_postgres() else "sqlite"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cert/<unique_id>")
def view_cert(unique_id):
    cert = _get_cert(unique_id)
    if not cert:
        abort(404)
    return render_template("certificate.html", cert=cert)


@app.route("/cert/<unique_id>/download")
def download_cert(unique_id):
    cert = _get_cert(unique_id)
    if not cert:
        abort(404)

    batch_dict = {
        "company_name": cert["company_name"],
        "title": cert["title"],
        "template": cert["template"],
    }
    pdf = generate_pdf(cert, batch_dict)
    safe_name = re.sub(r"[^\w\-]", "_", cert["student_name"])
    return send_file(
        pdf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"certificate_{safe_name}.pdf",
    )


@app.route("/api/batches", methods=["POST"])
def create_batch():
    data = request.get_json(silent=True) or {}
    company = _clean(data.get("company_name"))
    title = _clean(data.get("title"))
    template = _clean(data.get("template"), 20) or "classic"
    students = data.get("students") or []

    if template not in VALID_TEMPLATES:
        return jsonify({"error": "Invalid template"}), 400
    if not company or not title:
        return jsonify({"error": "company_name and title are required"}), 400
    if not isinstance(students, list) or not students:
        return jsonify({"error": "students list is required"}), 400
    if len(students) > MAX_STUDENTS:
        return jsonify({"error": f"Maximum {MAX_STUDENTS} students per batch"}), 400

    results = []

    try:
        with db_session() as conn:
            if is_postgres():
                cur = execute(
                    conn,
                    "INSERT INTO batches (company_name, title, template) VALUES (?, ?, ?) RETURNING id",
                    (company, title, template),
                )
                batch_id = cur.fetchone()["id"]
            else:
                cur = execute(
                    conn,
                    "INSERT INTO batches (company_name, title, template) VALUES (?, ?, ?)",
                    (company, title, template),
                )
                batch_id = cur.lastrowid

            for s in students:
                if not isinstance(s, dict):
                    continue
                name = _clean(s.get("name"))
                if not name:
                    continue
                uid = _unique_id(conn)
                execute(
                    conn,
                    "INSERT INTO certificates (unique_id, batch_id, student_name, course, date) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (uid, batch_id, name, _clean(s.get("course")), _clean(s.get("date"), 50)),
                )
                results.append({
                    "student_name": name,
                    "unique_id": uid,
                    "link": f"/cert/{uid}",
                })
    except Exception as e:
        return jsonify({"error": f"Database error: {e}"}), 500

    if not results:
        return jsonify({"error": "No valid student names provided"}), 400

    return jsonify({"batch_id": batch_id, "count": len(results), "certificates": results})


@app.route("/api/batches/<int:batch_id>")
def get_batch(batch_id):
    with db_session() as conn:
        cur = execute(conn, "SELECT * FROM batches WHERE id = ?", (batch_id,))
        batch = fetchone(cur)
        if not batch:
            abort(404)
        cur = execute(
            conn,
            "SELECT unique_id, student_name, course, date FROM certificates WHERE batch_id = ?",
            (batch_id,),
        )
        certs = fetchall(cur)

    return jsonify({"batch": batch, "certificates": certs})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
