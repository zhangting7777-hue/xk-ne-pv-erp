# -*- coding: utf-8 -*-
"""
电站运维模块 - 多品牌电站统一监控、自动账单生成、电费应收四级闭环、梯度逾期预警、质保金管理
"""

def ensure_station_tables(db):
    stmts = [
        "CREATE TABLE IF NOT EXISTS station_info (id INTEGER PRIMARY KEY AUTOINCREMENT,station_name TEXT NOT NULL,station_type TEXT DEFAULT '工商业',installed_capacity_kw REAL DEFAULT 0,location TEXT,province TEXT,city TEXT,grid_connection_date TEXT,inverter_brand TEXT,inverter_model TEXT,inverter_count INTEGER DEFAULT 1,inverter_total_kw REAL DEFAULT 0,panel_brand TEXT,panel_power_w REAL DEFAULT 0,panel_count INTEGER DEFAULT 0,design_annual_kwh REAL DEFAULT 0,station_status TEXT DEFAULT '并网运行',ops_mode TEXT DEFAULT '自主运维',ops_company TEXT,person_in_charge TEXT,phone TEXT,created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS inverter_brand (id INTEGER PRIMARY KEY AUTOINCREMENT,brand_name TEXT NOT NULL,manufacturer TEXT,country TEXT DEFAULT '中国',contact_person TEXT,phone TEXT,warranty_years INTEGER DEFAULT 5,support_protocol TEXT,rated_power_kw REAL DEFAULT 0,efficiency REAL DEFAULT 0,status TEXT DEFAULT '合格',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS generation_record (id INTEGER PRIMARY KEY AUTOINCREMENT,station_id INTEGER,record_date TEXT NOT NULL,record_type TEXT DEFAULT '日',total_generation_kwh REAL DEFAULT 0,equivalent_hours REAL DEFAULT 0,pr_value REAL DEFAULT 0,grid_export_kwh REAL DEFAULT 0,self_use_kwh REAL DEFAULT 0,revenue_yuan REAL DEFAULT 0,panel_temp_c REAL,irradiance_kwh REAL,ambient_temp_c REAL,peak_power_kw REAL DEFAULT 0,availability REAL DEFAULT 0,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (station_id) REFERENCES station_info(id))",
        "CREATE TABLE IF NOT EXISTS electricity_bill (id INTEGER PRIMARY KEY AUTOINCREMENT,bill_no TEXT UNIQUE,station_id INTEGER,bill_type TEXT DEFAULT '应收账单',billing_period TEXT NOT NULL,total_generation_kwh REAL DEFAULT 0,unit_price_yuan REAL DEFAULT 0,gross_amount_yuan REAL DEFAULT 0,net_amount_yuan REAL DEFAULT 0,tax_amount_yuan REAL DEFAULT 0,bill_status TEXT DEFAULT '待确认',invoice_no TEXT,invoice_date TEXT,invoice_amount_yuan REAL DEFAULT 0,due_date TEXT,paid_date TEXT,paid_amount_yuan REAL DEFAULT 0,remark TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (station_id) REFERENCES station_info(id))",
        "CREATE TABLE IF NOT EXISTS receivable_account (id INTEGER PRIMARY KEY AUTOINCREMENT,station_id INTEGER,bill_id INTEGER,receivable_type TEXT NOT NULL,period TEXT NOT NULL,amount_yuan REAL DEFAULT 0,received_yuan REAL DEFAULT 0,overdue_days INTEGER DEFAULT 0,overdue_level TEXT DEFAULT '正常',penalty_rate REAL DEFAULT 0,penalty_amount_yuan REAL DEFAULT 0,write_off_date TEXT,write_off_reason TEXT,confirmed_by TEXT,confirmed_at TEXT,created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (station_id) REFERENCES station_info(id),FOREIGN KEY (bill_id) REFERENCES electricity_bill(id))",
        "CREATE TABLE IF NOT EXISTS collection_record (id INTEGER PRIMARY KEY AUTOINCREMENT,station_id INTEGER,receivable_id INTEGER,collection_date TEXT,collector TEXT,collection_type TEXT DEFAULT '电话催收',collection_result TEXT DEFAULT '未响应',promised_amount_yuan REAL DEFAULT 0,promised_date TEXT,actual_amount_yuan REAL DEFAULT 0,next_action TEXT,next_follow_date TEXT,remark TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (station_id) REFERENCES station_info(id),FOREIGN KEY (receivable_id) REFERENCES receivable_account(id))",
        "CREATE TABLE IF NOT EXISTS warranty_deposit (id INTEGER PRIMARY KEY AUTOINCREMENT,deposit_no TEXT UNIQUE,station_id INTEGER,project_id INTEGER,deposit_type TEXT DEFAULT '工程质保金',total_contract_amount_yuan REAL DEFAULT 0,deposit_ratio REAL DEFAULT 0.03,deposit_amount_yuan REAL DEFAULT 0,start_date TEXT,end_date TEXT,maturity_date TEXT,deposit_status TEXT DEFAULT '质保中',refund_amount_yuan REAL DEFAULT 0,refund_date TEXT,quality_issues TEXT,deduction_amount_yuan REAL DEFAULT 0,deduction_reason TEXT,created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (station_id) REFERENCES station_info(id),FOREIGN KEY (project_id) REFERENCES projects(id))",
    ]
    for sql in stmts:
        try: db.execute(sql)
        except: pass
    db.commit()
    _seed_station_data(db)


def _seed_station_data(db):
    brands = [
        ("华为技术有限公司", "华为", "中国", "张工", "400-800-9009", 5, "Modbus TCP", 100, 0.985),
        ("阳光电源股份有限公司", "阳光电源", "中国", "李工", "400-888-0101", 5, "Modbus RTU", 110, 0.980),
        ("固德威技术股份有限公司", "固德威", "中国", "王工", "400-600-9009", 5, "Modbus RTU", 50, 0.978),
        ("锦浪科技股份有限公司", "锦浪", "中国", "刘工", "400-700-8009", 5, "Modbus TCP", 70, 0.982),
        ("SMA Solar Technology", "SMA", "德国", "Hans", "+49-561-9522-0", 5, "Sunny Webbox", 100, 0.990),
        ("SolarEdge Technologies", "SolarEdge", "以色列", "David", "+972-3-763-5100", 12, "SolarEdge API", 100, 0.990),
    ]
    for b in brands:
        db.execute("INSERT INTO inverter_brand (brand_name,manufacturer,country,contact_person,phone,warranty_years,support_protocol,rated_power_kw,efficiency,status) VALUES (?,?,?,?,?,?,?,?,?,?)", b)

    stations = [
        ("福州亿锦纺织厂 2MW光伏电站", "工商业", 2000, "福州市台江区", "福建", "福州", "2023-06-01", "华为技术有限公司", "SUN2000-100KTL", 2, 196, "隆基绿能", 545, 1900, "福州亿锦纺织有限公司", "陈总", "13912340011", "自主运维"),
        ("厦门联发仓储 1.5MW光伏电站", "工商业", 1500, "厦门市湖里区", "福建", "厦门", "2023-09-15", "阳光电源股份有限公司", "SG110HX", 2, 147, "晶科能源", 545, 1400, "厦门联发仓储公司", "林总", "13912340012", "委托运维"),
        ("泉州恒达制造厂 1MW光伏电站", "工商业", 1000, "泉州市鲤城区", "福建", "泉州", "2024-01-20", "固德威技术股份有限公司", "GW100K-HT", 2, 98, "天合光能", 550, 950, "泉州恒达制造厂", "王总", "13912340013", "自主运维"),
    ]
    for s in stations:
        db.execute("INSERT INTO station_info (station_name,station_type,installed_capacity_kw,location,province,city,grid_connection_date,inverter_brand,inverter_model,inverter_count,inverter_total_kw,panel_brand,panel_power_w,panel_count,design_annual_kwh,person_in_charge,phone,ops_mode) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", s)
    db.commit()


def register_station_routes(app, get_db):
    @app.before_request
    def _init():
        from flask import g
        if not getattr(g, '_station_inited', False):
            try:
                ensure_station_tables(get_db())
            except Exception:
                pass
            g._station_inited = True

    @app.route("/api/station/list")
    def st_list():
        db = get_db()
        rows = db.execute("SELECT * FROM station_info ORDER BY created_at DESC").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/station/<int:sid>")
    def st_get(sid):
        db = get_db()
        row = db.execute("SELECT * FROM station_info WHERE id=?", (sid,)).fetchone()
        if not row:
            return jsonify({"error": "电站不存在"}), 404
        return jsonify(dict(row))

    @app.route("/api/station/<int:sid>/generation")
    def st_gen(sid):
        db = get_db()
        p = request.args.get("period", "")
        q = "SELECT * FROM generation_record WHERE station_id=?"
        ps = [sid]
        if p:
            q += " AND record_date LIKE ?"
            ps.append(p + "%")
        q += " ORDER BY record_date DESC LIMIT 365"
        return jsonify([dict(r) for r in db.execute(q, ps).fetchall()])

    @app.route("/api/station/<int:sid>/generation", methods=["POST"])
    def st_gen_add(sid):
        db = get_db()
        d = request.get_json()
        db.execute("""INSERT INTO generation_record (station_id,record_date,record_type,total_generation_kwh,equivalent_hours,pr_value,grid_export_kwh,self_use_kwh,revenue_yuan,panel_temp_c,irradiance_kwh,ambient_temp_c,peak_power_kw,availability) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sid, d.get("record_date"), d.get("record_type", "日"),
             float(d.get("total_generation_kwh", 0)), float(d.get("equivalent_hours", 0)),
             float(d.get("pr_value", 0)), float(d.get("grid_export_kwh", 0)),
             float(d.get("self_use_kwh", 0)), float(d.get("revenue_yuan", 0)),
             float(d.get("panel_temp_c") or 0), float(d.get("irradiance_kwh") or 0),
             float(d.get("ambient_temp_c") or 0), float(d.get("peak_power_kw", 0)),
             float(d.get("availability", 0))))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/<int:sid>/bills")
    def st_bills(sid):
        db = get_db()
        rows = db.execute("""SELECT eb.*, (SELECT SUM(received_yuan) FROM receivable_account WHERE bill_id=eb.id) as received_yuan FROM electricity_bill eb WHERE eb.station_id=? ORDER BY eb.billing_period DESC""", (sid,)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/station/<int:sid>/bills", methods=["POST"])
    def st_bill_add(sid):
        from datetime import datetime
        db = get_db()
        d = request.get_json()
        bill_no = "EB" + datetime.now().strftime("%Y%m%d%H%M%S")
        db.execute("""INSERT INTO electricity_bill (bill_no,station_id,bill_type,billing_period,total_generation_kwh,unit_price_yuan,gross_amount_yuan,net_amount_yuan,tax_amount_yuan,bill_status,due_date,remark) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (bill_no, sid, d.get("bill_type", "应收账单"), d.get("billing_period"),
             float(d.get("total_generation_kwh", 0)), float(d.get("unit_price_yuan", 0)),
             float(d.get("gross_amount_yuan", 0)), float(d.get("net_amount_yuan", 0)),
             float(d.get("tax_amount_yuan", 0)), d.get("bill_status", "待确认"),
             d.get("due_date"), d.get("remark", "")))
        db.commit()
        return jsonify({"ok": True, "bill_no": bill_no})

    @app.route("/api/station/bills/<int:bid>", methods=["PUT"])
    def st_bill_upd(bid):
        db = get_db()
        d = request.get_json()
        flds, vals = [], []
        for f in ["bill_status", "invoice_no", "invoice_date", "invoice_amount_yuan", "paid_date", "paid_amount_yuan", "remark"]:
            if f in d and d.get(f) is not None:
                flds.append(f + "=?")
                vals.append(d[f])
        if flds:
            vals.append(bid)
            db.execute("UPDATE electricity_bill SET " + ",".join(flds) + " WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/<int:sid>/receivables")
    def st_recv(sid):
        db = get_db()
        rows = db.execute("""SELECT ra.*, eb.bill_no, eb.billing_period as eb_period FROM receivable_account ra LEFT JOIN electricity_bill eb ON ra.bill_id=eb.id WHERE ra.station_id=? ORDER BY ra.period DESC""", (sid,)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/station/receivables", methods=["POST"])
    def st_recv_add():
        db = get_db()
        d = request.get_json()
        db.execute("""INSERT INTO receivable_account (station_id,bill_id,receivable_type,period,amount_yuan,received_yuan,overdue_days,overdue_level,penalty_rate,penalty_amount_yuan) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (d.get("station_id"), d.get("bill_id"), d.get("receivable_type"),
             d.get("period"), float(d.get("amount_yuan", 0)), float(d.get("received_yuan", 0)),
             int(d.get("overdue_days", 0)), d.get("overdue_level", "正常"),
             float(d.get("penalty_rate", 0)), float(d.get("penalty_amount_yuan", 0))))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/receivables/<int:rid>", methods=["PUT"])
    def st_recv_upd(rid):
        db = get_db()
        d = request.get_json()
        flds, vals = [], []
        for f in ["receivable_type", "amount_yuan", "received_yuan", "overdue_days", "overdue_level", "penalty_amount_yuan", "write_off_date", "write_off_reason", "confirmed_by", "confirmed_at"]:
            if f in d and d.get(f) is not None:
                flds.append(f + "=?")
                vals.append(d[f])
        if flds:
            vals.append(rid)
            db.execute("UPDATE receivable_account SET " + ",".join(flds) + ", updated_at=datetime('now') WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/<int:sid>/collections")
    def st_collections(sid):
        db = get_db()
        rows = db.execute("""SELECT cr.*, ra.period, ra.amount_yuan as receivable_amount FROM collection_record cr LEFT JOIN receivable_account ra ON cr.receivable_id=ra.id WHERE cr.station_id=? ORDER BY cr.collection_date DESC""", (sid,)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/station/receivables/<int:rid>/collections", methods=["POST"])
    def st_collection_add(rid):
        db = get_db()
        d = request.get_json()
        db.execute("""INSERT INTO collection_record (station_id,receivable_id,collection_date,collector,collection_type,collection_result,promised_amount_yuan,promised_date,actual_amount_yuan,next_action,next_follow_date,remark) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (d.get("station_id"), rid, d.get("collection_date"), d.get("collector"),
             d.get("collection_type", "电话催收"), d.get("collection_result", "未响应"),
             float(d.get("promised_amount_yuan", 0)), d.get("promised_date"),
             float(d.get("actual_amount_yuan", 0)), d.get("next_action"),
             d.get("next_follow_date"), d.get("remark", "")))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/<int:sid>/warranty")
    def st_warranty(sid):
        db = get_db()
        rows = db.execute("""SELECT wd.*, p.project_name FROM warranty_deposit wd LEFT JOIN projects p ON wd.project_id=p.id WHERE wd.station_id=? ORDER BY wd.created_at DESC""", (sid,)).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/station/warranty", methods=["POST"])
    def st_warranty_add():
        from datetime import datetime
        db = get_db()
        d = request.get_json()
        deposit_no = "WD" + datetime.now().strftime("%Y%m%d%H%M%S")
        db.execute("""INSERT INTO warranty_deposit (deposit_no,station_id,project_id,deposit_type,total_contract_amount_yuan,deposit_ratio,deposit_amount_yuan,start_date,end_date,maturity_date,deposit_status) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (deposit_no, d.get("station_id"), d.get("project_id"), d.get("deposit_type", "工程质保金"),
             float(d.get("total_contract_amount_yuan", 0)), float(d.get("deposit_ratio", 0.03)),
             float(d.get("deposit_amount_yuan", 0)), d.get("start_date"), d.get("end_date"),
             d.get("maturity_date"), d.get("deposit_status", "质保中")))
        db.commit()
        return jsonify({"ok": True, "deposit_no": deposit_no})

    @app.route("/api/station/warranty/<int:wid>", methods=["PUT"])
    def st_warranty_upd(wid):
        db = get_db()
        d = request.get_json()
        flds, vals = [], []
        for f in ["deposit_status", "refund_amount_yuan", "refund_date", "quality_issues", "deduction_amount_yuan", "deduction_reason"]:
            if f in d and d.get(f) is not None:
                flds.append(f + "=?")
                vals.append(d[f])
        if flds:
            vals.append(wid)
            db.execute("UPDATE warranty_deposit SET " + ",".join(flds) + ", updated_at=datetime('now') WHERE id=?", vals)
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/station/dashboard")
    def st_dashboard():
        db = get_db()
        from datetime import datetime
        stations = db.execute("SELECT * FROM station_info").fetchall()
        result = []
        for s in stations:
            sid = s["id"]
            cur_month = db.execute("""SELECT COALESCE(SUM(total_generation_kwh),0) as kwh, COALESCE(SUM(revenue_yuan),0) as rev, COALESCE(AVG(pr_value),0) as pr, COALESCE(AVG(equivalent_hours),0) as eqh FROM generation_record WHERE station_id=? AND record_date LIKE ?""",
                (sid, datetime.now().strftime("%Y-%m") + "%")).fetchone()
            total_gen = db.execute("SELECT COALESCE(SUM(total_generation_kwh),0) FROM generation_record WHERE station_id=?", (sid,)).fetchone()[0]
            total_rev = db.execute("SELECT COALESCE(SUM(revenue_yuan),0) FROM generation_record WHERE station_id=?", (sid,)).fetchone()[0]
            recv = db.execute("""SELECT COALESCE(SUM(amount_yuan),0) as total_recv, COALESCE(SUM(received_yuan),0) as received, COALESCE(SUM(CASE WHEN overdue_level IN ('一级预警','二级预警','三级预警','呆账') THEN amount_yuan-received_yuan ELSE 0 END),0) as overdue FROM receivable_account WHERE station_id=?""", (sid,)).fetchone()
            wd = db.execute("""SELECT COALESCE(SUM(deposit_amount_yuan),0) as total_deposit, COALESCE(SUM(CASE WHEN deposit_status='到期待退' THEN deposit_amount_yuan ELSE 0 END),0) as pending FROM warranty_deposit WHERE station_id=?""", (sid,)).fetchone()
            result.append({
                "station_id": sid, "station_name": s["station_name"],
                "capacity_kw": s["installed_capacity_kw"],
                "this_month_kwh": round(cur_month["kwh"], 1),
                "this_month_rev": round(cur_month["rev"], 2),
                "this_month_pr": round(cur_month["pr"], 4),
                "this_month_eqh": round(cur_month["eqh"], 2),
                "total_generation_kwh": round(total_gen, 1),
                "total_revenue_yuan": round(total_rev, 2),
                "total_receivable_yuan": round(recv["total_recv"], 2),
                "total_received_yuan": round(recv["received"], 2),
                "overdue_yuan": round(recv["overdue"], 2),
                "warranty_deposit_yuan": round(wd["total_deposit"], 2),
                "warranty_pending_yuan": round(wd["pending"], 2),
            })
        return jsonify(result)

    @app.route("/api/station/inverter_brands")
    def st_inverter_brands():
        return jsonify([dict(r) for r in get_db().execute("SELECT * FROM inverter_brand ORDER BY brand_name").fetchall()])

    print("  station ops routes registered")
