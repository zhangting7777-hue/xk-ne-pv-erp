# -*- coding: utf-8 -*-
"""
部门目标管理
年/季/月目标 + 达成率统计
"""
from flask import request, jsonify
from datetime import datetime

def register_department_target_routes(app, get_db):

    def _ensure_tables():
        """在请求上下文中确保表存在"""
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER DEFAULT 0,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS dept_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id INTEGER NOT NULL,
                target_year INTEGER NOT NULL,
                target_month INTEGER DEFAULT 0,
                target_quarter INTEGER DEFAULT 0,
                target_type TEXT DEFAULT '装机容量',
                target_value REAL DEFAULT 0,
                unit TEXT DEFAULT 'kW',
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (dept_id) REFERENCES departments(id)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS dept_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dept_id INTEGER NOT NULL,
                record_year INTEGER NOT NULL,
                record_month INTEGER DEFAULT 0,
                record_quarter INTEGER DEFAULT 0,
                metric_type TEXT NOT NULL,
                metric_value REAL DEFAULT 0,
                record_date TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (dept_id) REFERENCES departments(id)
            )
        """)
        if db.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0:
            for name, oid in [("工商一部", 0), ("工商二部", 0), ("工商三部", 0), ("户用事业部", 0), ("运维部", 0)]:
                db.execute("INSERT INTO departments (name, parent_id) VALUES (?,?)", (name, oid))
        db.commit()

    # ── 部门 CRUD ──
    @app.route("/api/departments")
    def api_depts_list():
        _ensure_tables()
        db = get_db()
        rows = db.execute("SELECT * FROM departments ORDER BY sort_order, id").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/departments", methods=["POST"])
    def api_dept_create():
        _ensure_tables()
        db = get_db()
        data = request.get_json()
        db.execute("INSERT INTO departments (name, parent_id) VALUES (?,?)",
            (data.get("name"), data.get("parent_id", 0)))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/departments/<int:did>", methods=["DELETE"])
    def api_dept_del(did):
        db = get_db()
        db.execute("DELETE FROM departments WHERE id=?", (did,))
        db.execute("DELETE FROM dept_targets WHERE dept_id=?", (did,))
        db.execute("DELETE FROM dept_performance WHERE dept_id=?", (did,))
        db.commit()
        return jsonify({"ok": True})

    # ── 目标设置 ──
    @app.route("/api/dept-targets")
    def api_dept_targets():
        _ensure_tables()
        db = get_db()
        year    = int(request.args.get("year", datetime.now().year))
        dept_id = request.args.get("dept_id", "")
        query = "SELECT t.*, d.name as dept_name FROM dept_targets t JOIN departments d ON t.dept_id=d.id WHERE t.target_year=?"
        params = [year]
        if dept_id:
            query += " AND t.dept_id=?"
            params.append(int(dept_id))
        query += " ORDER BY d.sort_order, t.target_month"
        rows = db.execute(query, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/dept-targets", methods=["POST"])
    def api_dept_target_set():
        _ensure_tables()
        db = get_db()
        data = request.get_json()
        existing = db.execute("""
            SELECT id FROM dept_targets
            WHERE dept_id=? AND target_year=? AND target_type=?
            AND (? = 0 OR target_month = ?)
            AND (? = 0 OR target_quarter = ?)
        """, (
            int(data.get("dept_id")), int(data.get("target_year")),
            data.get("target_type", "装机容量"),
            int(data.get("target_month", 0)), int(data.get("target_month", 0)),
            int(data.get("target_quarter", 0)), int(data.get("target_quarter", 0)),
        )).fetchone()

        if existing:
            db.execute("""UPDATE dept_targets SET target_value=?, unit=? WHERE id=?""",
                (float(data.get("target_value", 0)), data.get("unit", "kW"), existing[0]))
        else:
            db.execute("""INSERT INTO dept_targets
                (dept_id, target_year, target_month, target_quarter, target_type, target_value, unit)
                VALUES (?,?,?,?,?,?,?)""",
                (int(data.get("dept_id")), int(data.get("target_year")),
                 int(data.get("target_month", 0)), int(data.get("target_quarter", 0)),
                 data.get("target_type", "装机容量"),
                 float(data.get("target_value", 0)), data.get("unit", "kW")))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/dept-targets/<int:tid>", methods=["DELETE"])
    def api_dept_target_del(tid):
        db = get_db()
        db.execute("DELETE FROM dept_targets WHERE id=?", (tid,))
        db.commit()
        return jsonify({"ok": True})

    # ── 实际业绩录入 ──
    @app.route("/api/dept-performance")
    def api_dept_perf():
        _ensure_tables()
        db = get_db()
        year    = int(request.args.get("year", datetime.now().year))
        dept_id = request.args.get("dept_id", "")
        query = """SELECT p.*, d.name as dept_name FROM dept_performance p
                   JOIN departments d ON p.dept_id=d.id
                   WHERE p.record_year=?"""
        params = [year]
        if dept_id:
            query += " AND p.dept_id=?"
            params.append(int(dept_id))
        query += " ORDER BY p.record_year DESC, p.record_month DESC"
        rows = db.execute(query, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/dept-performance", methods=["POST"])
    def api_dept_perf_add():
        _ensure_tables()
        db = get_db()
        data = request.get_json()
        db.execute("""INSERT INTO dept_performance
            (dept_id, record_year, record_month, record_quarter, metric_type, metric_value)
            VALUES (?,?,?,?,?,?)""",
            (int(data.get("dept_id")), int(data.get("record_year")),
             int(data.get("record_month", 0)), int(data.get("record_quarter", 0)),
             data.get("metric_type", "装机容量"), float(data.get("metric_value", 0))))
        db.commit()
        return jsonify({"ok": True})

    # ── 达成率看板 ──
    @app.route("/api/dept-targets/achievement")
    def api_dept_achievement():
        _ensure_tables()
        db = get_db()
        year    = int(request.args.get("year", datetime.now().year))
        month   = int(request.args.get("month", datetime.now().month))
        quarter = (month - 1) // 3 + 1

        depts = db.execute("SELECT * FROM departments ORDER BY sort_order").fetchall()
        result = []
        for dept in depts:
            did = dept["id"]
            dname = dept["name"]

            y_target = db.execute("""
                SELECT COALESCE(SUM(target_value),0) FROM dept_targets
                WHERE dept_id=? AND target_year=? AND target_type='装机容量' AND target_month=0 AND target_quarter=0
            """, (did, year)).fetchone()[0]

            y_actual = db.execute("""
                SELECT COALESCE(SUM(metric_value),0) FROM dept_performance
                WHERE dept_id=? AND record_year=? AND metric_type='装机容量'
            """, (did, year)).fetchone()[0]

            m_target = db.execute("""
                SELECT COALESCE(SUM(target_value),0) FROM dept_targets
                WHERE dept_id=? AND target_year=? AND target_month=? AND target_type='装机容量'
            """, (did, year, month)).fetchone()[0]

            m_actual = db.execute("""
                SELECT COALESCE(SUM(metric_value),0) FROM dept_performance
                WHERE dept_id=? AND record_year=? AND record_month=? AND metric_type='装机容量'
            """, (did, year, month)).fetchone()[0]

            q_target = db.execute("""
                SELECT COALESCE(SUM(target_value),0) FROM dept_targets
                WHERE dept_id=? AND target_year=? AND target_quarter=? AND target_type='装机容量'
            """, (did, year, quarter)).fetchone()[0]

            q_actual = db.execute("""
                SELECT COALESCE(SUM(metric_value),0) FROM dept_performance
                WHERE dept_id=? AND record_year=? AND record_quarter=? AND metric_type='装机容量'
            """, (did, year, quarter)).fetchone()[0]

            result.append({
                "dept_id": did, "dept_name": dname,
                "year_target": y_target, "year_actual": y_actual,
                "year_rate": round(y_actual / y_target * 100, 1) if y_target > 0 else 0,
                "month_target": m_target, "month_actual": m_actual,
                "month_rate": round(m_actual / m_target * 100, 1) if m_target > 0 else 0,
                "quarter_target": q_target, "quarter_actual": q_actual,
                "quarter_rate": round(q_actual / q_target * 100, 1) if q_target > 0 else 0,
            })

        return jsonify(result)
