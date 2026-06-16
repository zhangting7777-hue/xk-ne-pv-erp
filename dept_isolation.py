# -*- coding: utf-8 -*-
"""
多部门数据隔离 (RBAC)
- 用户属部门，部门看自己的项目/数据
- 项目属部门，只有本部门或上级能看
"""
from flask import request, jsonify, session, g
from functools import wraps

def register_dept_isolation(app, get_db):

    def _ensure():
        """延迟创建表（线程安全）"""
        try:
            db = get_db()
            db.execute("""
                CREATE TABLE IF NOT EXISTS dept_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    dept_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    created_at TEXT DEFAULT (datetime('now')),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (dept_id) REFERENCES departments(id)
                )
            """)
            db.execute("PRAGMA table_info(projects)")
            cols = [r[1] for r in db.execute("PRAGMA table_info(projects)").fetchall()]
            if "dept_id" not in cols:
                db.execute("ALTER TABLE projects ADD COLUMN dept_id INTEGER DEFAULT 0")
            db.commit()
        except Exception:
            pass

    # ── 权限检查 ──
    def _is_admin(uid=None):
        if uid is None:
            uid = session.get("user_id") or g.get("user_id")
        if not uid:
            return False
        try:
            db = get_db()
            u = db.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
            return u and u["role"] == "admin"
        except Exception:
            return False

    def _user_dept_ids(uid=None):
        if uid is None:
            uid = session.get("user_id") or g.get("user_id")
        if not uid:
            return []
        try:
            db = get_db()
            rows = db.execute("SELECT dept_id FROM dept_users WHERE user_id=?", (uid,)).fetchall()
            return [r["dept_id"] for r in rows]
        except Exception:
            return []

    def _dept_filter(query, field="dept_id"):
        """追加部门过滤，返回 (query, params)"""
        uid = session.get("user_id") or g.get("user_id")
        if _is_admin(uid):
            return query, []
        ids = _user_dept_ids(uid)
        if not ids:
            return query + f" AND {field}=999999", []
        ph = ",".join(["?"] * len(ids))
        return query + f" AND {field} IN ({ph})", ids

    # ── 公开给其他模块 ──
    app.is_admin_user = _is_admin
    app.user_dept_ids = _user_dept_ids
    app.dept_filter = _dept_filter

    # ════════════════════════════════════════════
    #  过滤后的 API
    # ════════════════════════════════════════════

    @app.route("/api/projects")
    def api_projects_filtered():
        _ensure()
        db = get_db()
        status   = request.args.get("status", "")
        keyword  = request.args.get("keyword", "")
        dept_id  = request.args.get("dept_id", "")

        query = "SELECT * FROM projects WHERE 1=1"
        params = []

        query, dp = _dept_filter(query, "dept_id")
        params.extend(dp)

        if status:
            query += " AND status=?"
            params.append(status)
        if keyword:
            query += " AND (name LIKE ? OR owner_name LIKE ? OR address LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if dept_id and _is_admin():
            query += " AND dept_id=?"
            params.append(int(dept_id))

        query += " ORDER BY created_at DESC"
        rows = db.execute(query, params).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/projects/<int:pid>")
    def api_project_get_filtered(pid):
        _ensure()
        db = get_db()
        p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        if not p:
            return jsonify({"error": "项目不存在"}), 404
        uid = session.get("user_id") or g.get("user_id")
        if not _is_admin(uid):
            ids = _user_dept_ids(uid)
            if p["dept_id"] not in ids:
                return jsonify({"error": "无权访问"}), 403
        return jsonify(dict(p))

    @app.route("/api/projects/<int:pid>", methods=["PUT"])
    def api_project_update_filtered(pid):
        _ensure()
        db = get_db()
        p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        if not p:
            return jsonify({"error": "项目不存在"}), 404
        uid = session.get("user_id") or g.get("user_id")
        if not _is_admin(uid):
            ids = _user_dept_ids(uid)
            if p["dept_id"] not in ids:
                return jsonify({"error": "无权修改"}), 403
        data = request.get_json()
        fields = ["name","owner_name","address","capacity_kw","mode","build_type",
                   "status","total_invest","paid_amount","remaining_amount",
                   "grid_code","grid_date","profit","dept_id"]
        sets, vals = [], []
        for f in fields:
            if f in data:
                sets.append(f"=?")
                vals.append(data[f])
        if not sets:
            return jsonify({"error": "无更新字段"}), 400
        vals.append(pid)
        db.execute(f"UPDATE projects SET {','.join(sets)}, updated_at=datetime('now') WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/dashboard/summary")
    def api_dashboard_filtered():
        _ensure()
        db = get_db()
        dept_id = request.args.get("dept_id", "")
        uid = session.get("user_id") or g.get("user_id")

        dept_where = ""
        dept_params = []
        if dept_id and _is_admin():
            dept_where = "WHERE p.dept_id=?"
            dept_params = [int(dept_id)]
        elif not _is_admin(uid):
            ids = _user_dept_ids(uid)
            if ids:
                ph = ",".join(["?"] * len(ids))
                dept_where = f"WHERE p.dept_id IN ({ph})"
                dept_params = ids
            else:
                return jsonify({"total_projects": 0, "dept_filtered": True})

        def s(sql, p=None):
            p = (dept_params + (p or []))
            r = db.execute(sql, p).fetchone()
            return r[0] if r else 0

        total_projects = s(f"SELECT COUNT(*) FROM projects p {dept_where}")
        grid_projects  = s(f"SELECT COUNT(*) FROM projects p {dept_where} AND p.status='并网'")
        total_cap      = s(f"SELECT COALESCE(SUM(p.capacity_kw),0) FROM projects p {dept_where}")
        total_invest   = s(f"SELECT COALESCE(SUM(p.total_invest),0) FROM projects p {dept_where}")
        total_paid     = s(f"SELECT COALESCE(SUM(p.paid_amount),0) FROM projects p {dept_where}")
        total_remain   = s(f"SELECT COALESCE(SUM(p.remaining_amount),0) FROM projects p {dept_where}")

        if dept_where:
            join_sql = f"JOIN projects p ON pm.project_id=p.id {dept_where}"
            income  = s("SELECT COALESCE(SUM(pm.amount),0) FROM payments pm " + join_sql + " AND pm.direction='收入'", dept_params)
            expense = s("SELECT COALESCE(SUM(pm.amount),0) FROM payments pm " + join_sql + " AND pm.direction='支出'", dept_params)
        else:
            income  = s("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='收入'")
            expense = s("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='支出'")

        from datetime import date, timedelta
        trend_data = []
        for i in range(5, -1, -1):
            m = (date.today() - timedelta(days=i*30)).strftime("%Y-%m")
            inc = s("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='收入' AND payment_date LIKE ?", [f"{m}%"])
            exp = s("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='支出' AND payment_date LIKE ?", [f"{m}%"])
            trend_data.append({"month": m, "income": round(inc, 2), "expense": round(exp, 2)})

        top = db.execute(f"""
            SELECT id, name, owner_name, total_invest, paid_amount, remaining_amount, status
            FROM projects p {dept_where} ORDER BY remaining_amount DESC LIMIT 10
        """, dept_params).fetchall()

        return jsonify({
            "total_projects": total_projects, "grid_projects": grid_projects,
            "total_cap": round(total_cap, 2), "total_invest": round(total_invest, 2),
            "total_paid": round(total_paid, 2), "total_remain": round(total_remain, 2),
            "income": round(income, 2), "expense": round(expense, 2),
            "net_profit": round(income - expense, 2),
            "trend_data": trend_data,
            "top_projects": [dict(r) for r in top],
            "dept_filtered": bool(dept_where),
        })

    # ── 部门成员管理 ──
    @app.route("/api/dept-users")
    def api_dept_users():
        _ensure()
        db = get_db()
        rows = db.execute("""
            SELECT du.*, d.name as dept_name, u.username
            FROM dept_users du
            JOIN departments d ON du.dept_id=d.id
            JOIN users u ON du.user_id=u.id
            ORDER BY du.dept_id
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/dept-users", methods=["POST"])
    def api_dept_user_add():
        _ensure()
        db = get_db()
        data = request.get_json()
        db.execute("INSERT INTO dept_users (user_id, dept_id, role) VALUES (?,?,?)",
            (int(data.get("user_id")), int(data.get("dept_id")), data.get("role", "member")))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/dept-users/<int:uid>/<int:did>", methods=["DELETE"])
    def api_dept_user_remove(uid, did):
        db = get_db()
        db.execute("DELETE FROM dept_users WHERE user_id=? AND dept_id=?", (uid, did))
        db.commit()
        return jsonify({"ok": True})
