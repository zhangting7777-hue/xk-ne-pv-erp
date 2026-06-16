# -*- coding: utf-8 -*-
"""
施工日报 + 整改单管理
拍照上传 → 自动生成日报 / 整改单
"""
from flask import request, jsonify, render_template
from datetime import datetime, date
import os, uuid, base64

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def register_construction_routes(app, get_db):

    def _ensure_tables():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS construction_daily_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                report_date TEXT,
                weather TEXT,
                builder_name TEXT,
                content TEXT,
                progress_percent INTEGER DEFAULT 0,
                photos TEXT DEFAULT '[]',
                status TEXT DEFAULT '待发送',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS construction_rectifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                report_id INTEGER,
                rect_title TEXT,
                rect_desc TEXT,
                severity TEXT DEFAULT '一般',
                due_date TEXT,
                assigned_to TEXT,
                photos TEXT DEFAULT '[]',
                status TEXT DEFAULT '待整改',
                整改_feedback TEXT,
                feedback_photos TEXT DEFAULT '[]',
                completed_at TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (report_id) REFERENCES construction_daily_reports(id)
            )
        """)
        db.commit()

    # ══════════════════════════════════════════════
    #  施工日报
    # ══════════════════════════════════════════════

    @app.route("/construction/daily-reports")
    def construction_daily_reports_page():
        return render_template("construction_daily_report.html")

    @app.route("/construction/rectifications")
    def construction_rectifications_page():
        return render_template("construction_rectification.html")

    @app.route("/api/daily-reports")
    def api_daily_reports():
        _ensure_tables()
        db = get_db()
        pid = request.args.get("project_id", "")
        query = """SELECT r.*, p.name as project_name
                   FROM construction_daily_reports r
                   LEFT JOIN projects p ON r.project_id=p.id
                   WHERE 1=1"""
        params = []
        if pid:
            query += " AND r.project_id=?"
            params.append(int(pid))
        query += " ORDER BY r.report_date DESC, r.created_at DESC"
        rows = db.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["photos"] = __import__("json").loads(d["photos"]) if d["photos"] else []
            result.append(d)
        return jsonify(result)

    @app.route("/api/daily-reports", methods=["POST"])
    def api_daily_report_create():
        _ensure_tables()
        db = get_db()
        data = request.get_json()
        photos = data.get("photos", [])
        saved_photos = []
        for p in photos:
            if p.startswith("data:image"):
                fmt = p.split(";")[0].split("/")[1]
                fname = f"{uuid.uuid4().hex}.{fmt}"
                fpath = os.path.join(UPLOAD_DIR, fname)
                with open(fpath, "wb") as f:
                    f.write(base64.b64decode(p.split(",")[1]))
                saved_photos.append(f"/static/uploads/{fname}")
            elif p.startswith("/") or p.startswith("http"):
                saved_photos.append(p)

        db.execute("""INSERT INTO construction_daily_reports
            (project_id, report_date, weather, builder_name, content, progress_percent, photos, status)
            VALUES (?,?,?,?,?,?,?,?)""",
            (data.get("project_id"), data.get("report_date", date.today().isoformat()),
             data.get("weather", ""), data.get("builder_name", ""),
             data.get("content", ""), int(data.get("progress_percent", 0)),
             __import__("json").dumps(saved_photos),
             data.get("status", "待发送")))
        db.commit()
        return jsonify({"ok": True, "id": db.execute("SELECT last_insert_rowid()").fetchone()[0]})

    @app.route("/api/daily-reports/<int:rid>", methods=["PUT"])
    def api_daily_report_update(rid):
        db = get_db()
        data = request.get_json()
        db.execute("""UPDATE construction_daily_reports SET
            report_date=?, weather=?, builder_name=?, content=?,
            progress_percent=?, status=? WHERE id=?""",
            (data.get("report_date"), data.get("weather"), data.get("builder_name"),
             data.get("content"), int(data.get("progress_percent", 0)),
             data.get("status", "待发送"), rid))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/daily-reports/<int:rid>", methods=["DELETE"])
    def api_daily_report_del(rid):
        db = get_db()
        db.execute("DELETE FROM construction_daily_reports WHERE id=?", (rid,))
        db.commit()
        return jsonify({"ok": True})

    # ══════════════════════════════════════════════
    #  整改单
    # ══════════════════════════════════════════════

    @app.route("/api/rectifications")
    def api_rectifications():
        _ensure_tables()
        db = get_db()
        pid = request.args.get("project_id", "")
        status = request.args.get("status", "")
        query = """SELECT r.*, p.name as project_name
                   FROM construction_rectifications r
                   LEFT JOIN projects p ON r.project_id=p.id
                   WHERE 1=1"""
        params = []
        if pid:
            query += " AND r.project_id=?"
            params.append(int(pid))
        if status:
            query += " AND r.status=?"
            params.append(status)
        query += " ORDER BY r.created_at DESC"
        rows = db.execute(query, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["photos"] = __import__("json").loads(d["photos"]) if d["photos"] else []
            d["feedback_photos"] = __import__("json").loads(d["feedback_photos"]) if d["feedback_photos"] else []
            result.append(d)
        return jsonify(result)

    @app.route("/api/rectifications", methods=["POST"])
    def api_rectification_create():
        _ensure_tables()
        db = get_db()
        data = request.get_json()
        photos = data.get("photos", [])
        saved_photos = []
        for p in photos:
            if p.startswith("data:image"):
                fmt = p.split(";")[0].split("/")[1]
                fname = f"{uuid.uuid4().hex}.{fmt}"
                with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
                    f.write(base64.b64decode(p.split(",")[1]))
                saved_photos.append(f"/static/uploads/{fname}")

        db.execute("""INSERT INTO construction_rectifications
            (project_id, report_id, rect_title, rect_desc, severity, due_date, assigned_to, photos)
            VALUES (?,?,?,?,?,?,?,?)""",
            (data.get("project_id"), data.get("report_id"),
             data.get("rect_title", ""), data.get("rect_desc", ""),
             data.get("severity", "一般"), data.get("due_date", ""),
             data.get("assigned_to", ""),
             __import__("json").dumps(saved_photos)))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/rectifications/<int:rid>", methods=["PUT"])
    def api_rectification_update(rid):
        db = get_db()
        data = request.get_json()
        feedback_photos = data.get("feedback_photos", [])
        saved_feedback = []
        for p in feedback_photos:
            if p.startswith("data:image"):
                fmt = p.split(";")[0].split("/")[1]
                fname = f"{uuid.uuid4().hex}.{fmt}"
                with open(os.path.join(UPLOAD_DIR, fname), "wb") as f:
                    f.write(base64.b64decode(p.split(",")[1]))
                saved_feedback.append(f"/static/uploads/{fname}")

        completed_at = datetime.now().strftime("%Y-%m-%d") if data.get("status") == "已完成" else None
        db.execute("""UPDATE construction_rectifications SET
            status=?, 整改_feedback=?, feedback_photos=?, completed_at=? WHERE id=?""",
            (data.get("status"), data.get("整改_feedback", ""),
             __import__("json").dumps(saved_feedback), completed_at, rid))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/rectifications/<int:rid>", methods=["DELETE"])
    def api_rectification_del(rid):
        db = get_db()
        db.execute("DELETE FROM construction_rectifications WHERE id=?", (rid,))
        db.commit()
        return jsonify({"ok": True})

    # ══════════════════════════════════════════════
    #  照片上传
    # ══════════════════════════════════════════════

    @app.route("/api/uploads/photo", methods=["POST"])
    def api_upload_photo():
        if "photo" not in request.files:
            return jsonify({"error": "No file"}), 400
        f = request.files["photo"]
        ext = os.path.splitext(f.filename)[1] or ".jpg"
        fname = f"{uuid.uuid4().hex}{ext}"
        f.save(os.path.join(UPLOAD_DIR, fname))
        return jsonify({"url": f"/static/uploads/{fname}"})
