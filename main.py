# -*- coding: utf-8 -*-
"""
鑫科新能源光伏企业全链路ERP系统
入口：python main.py
访问：http://localhost:8000
"""
import os
import sys
import sqlite3
import hashlib
from datetime import datetime, date, timedelta
from pathlib import Path
import random

from flask import Flask, request, jsonify, g, render_template, redirect
from sales_routes import register_sales_routes
from station_routes import register_station_routes

app = Flask(__name__, template_folder="templates")
app.config['SECRET_KEY'] = 'xkne-erp-secret-2026'
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "xkne_erp.db"

# ============================================================
# 数据库初始化
# ============================================================

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(str(DB_PATH), detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """初始化数据库表"""
    db = get_db()
    db.executescript("""
    -- 项目表
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        owner_name TEXT,
        address TEXT,
        capacity_kw REAL DEFAULT 0,
        mode TEXT DEFAULT 'EPC',
        build_type TEXT DEFAULT '阵列式',
        status TEXT DEFAULT '商机',
        total_invest REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        remaining_amount REAL DEFAULT 0,
        grid_code TEXT,
        grid_date TEXT,
        profit REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    -- 项目成本
    CREATE TABLE IF NOT EXISTS project_costs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        cost_type TEXT,
        amount REAL DEFAULT 0,
        description TEXT,
        record_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- 资金流水
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        direction TEXT,
        category TEXT,
        amount REAL DEFAULT 0,
        payment_date TEXT,
        description TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- 电费账单
    CREATE TABLE IF NOT EXISTS electricity_bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        bill_month TEXT,
        gen_kwh REAL DEFAULT 0,
        grid_price REAL DEFAULT 0,
        revenue REAL DEFAULT 0,
        payment_status TEXT DEFAULT '待收款',
        paid_amount REAL DEFAULT 0,
        record_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- 物料主数据
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT,
        unit TEXT DEFAULT '个',
        unit_price REAL DEFAULT 0,
        supplier TEXT,
        stock_qty REAL DEFAULT 0,
        safe_stock REAL DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 物料出入库流水
    CREATE TABLE IF NOT EXISTS material_flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER NOT NULL,
        project_id INTEGER,
        flow_type TEXT,
        qty REAL DEFAULT 0,
        price REAL DEFAULT 0,
        flow_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (material_id) REFERENCES materials(id),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- WBS施工进度
    CREATE TABLE IF NOT EXISTS wbs_nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        node_name TEXT,
        node_order INTEGER DEFAULT 0,
        is_done INTEGER DEFAULT 0,
        done_date TEXT,
        done_by TEXT,
        note TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );

    -- 用户（简化认证）
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 运维工单
    CREATE TABLE IF NOT EXISTS maintenance_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        order_type TEXT,
        title TEXT,
        description TEXT,
        status TEXT DEFAULT '待处理',
        assigned_to TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        done_at TEXT,
        FOREIGN KEY (project_id) REFERENCES projects(id)
    );
    """)


    # 插入示例项目数据（如果表为空）
    count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if count == 0:
        _insert_sample_data(db)

    db.commit()

def _insert_sample_data(db):
    """插入示例项目数据"""
    sample_projects = [
        ("福建彬发陶瓷光伏项目", "福建彬发陶瓷有限公司", "福建省福州市", 162.54, "EMC", "阵列式", "并网", 39.0, 28.5, 10.5, "FD-2026-001", "2026-03-15"),
        ("泉州阳光棚分布式项目", "泉州某科技有限公司", "福建省泉州市", 380.0, "EPC", "阳光棚", "施工", 95.0, 45.0, 50.0, "FD-2026-002", ""),
        ("厦门港务仓储光伏", "厦门港务仓储有限公司", "福建省厦门市", 520.0, "EMC", "阵列式", "商机", 130.0, 0, 130.0, "FD-2026-003", ""),
        ("福州某工厂屋顶光伏", "福州某制造有限公司", "福建省福州市", 240.0, "EPC", "彩钢", "签约", 60.0, 20.0, 40.0, "FD-2026-004", ""),
        ("泉州车棚光伏项目", "泉州某商业广场", "福建省泉州市", 120.0, "EMC", "车棚", "并网", 30.0, 30.0, 0, "FD-2026-005", "2026-05-20"),
    ]
    for p in sample_projects:
        db.execute("""INSERT INTO projects
            (name, owner_name, address, capacity_kw, mode, build_type, status,
             total_invest, paid_amount, remaining_amount, grid_code, grid_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", p)

    # 示例电费账单
    for i in range(1, 4):
        db.execute("""INSERT INTO electricity_bills
            (project_id, bill_month, gen_kwh, grid_price, revenue, payment_status, paid_amount, record_date)
            VALUES (?,?,?,?,?,?,?,?)""",
            (i, f"2026-0{i}", random.uniform(15000,25000), 0.73,
             random.uniform(10,18), random.choice(["待收款","部分收款","已结清"]),
             random.uniform(0,15), datetime.now().strftime("%Y-%m-%d")))

    # 示例资金流水
    categories = ["EPC工程款", "设备采购款", "施工费", "运维费", "电费结算"]
    for i in range(1, 4):
        for j in range(3):
            db.execute("""INSERT INTO payments
                (project_id, direction, category, amount, payment_date, description)
                VALUES (?,?,?,?,?,?)""",
                (i, random.choice(["收入","支出"]),
                 random.choice(categories),
                 random.uniform(5,50),
                 (date.today() - timedelta(days=j*30)).strftime("%Y-%m-%d"),
                 random.choice(["进度款","设备款","施工款","电费收益","运维费"])))

    # 示例物料
    materials = [
        ("高效TopCon N型组件（645W双玻）", "组件", "块", 498, "晶科"),
        ("并网逆变器（组串式）", "逆变器", "台", 90, "华为"),
        ("光伏支架及夹具", "支架", "套", 59.4, "锌铝镁"),
        ("直流线缆 PV1-F-4铜", "线缆", "米", 3.6, "玖开"),
        ("交流电缆 3×95+1×50", "线缆", "米", 63, "玖开"),
    ]
    for m in materials:
        db.execute("INSERT INTO materials (name, category, unit, unit_price, supplier, stock_qty, safe_stock) VALUES (?,?,?,?,?,?,?)",
                   (*m, random.randint(50,500), 20))

    # 示例WBS节点
    wbs_templates = [
        ("立项审批", 1), ("现场踏勘", 2), ("设计方案", 3),
        ("设备采购", 4), ("施工安装", 5), ("并网验收", 6), ("移交运维", 7)
    ]
    for i in range(1, 6):
        for name, order in wbs_templates:
            db.execute("INSERT INTO wbs_nodes (project_id, node_name, node_order, is_done) VALUES (?,?,?,?)",
                       (i, name, order, random.randint(0,1)))

    db.commit()

# ============================================================
# 页面路由
# ============================================================

@app.route("/")
def index():
    return redirect("/dashboard")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/projects")
def projects_page():
    return render_template("projects.html")

@app.route("/projects/<int:pid>")
def project_detail_page(pid):
    return render_template("project_detail.html")

@app.route("/electricity")
def electricity_page():
    return render_template("electricity.html")

@app.route("/inventory")
def inventory_page():
    return render_template("inventory.html")

@app.route("/maintenance")
def maintenance_page():
    return render_template("maintenance.html")

@app.route("/quotation")
def quotation_page():
    return render_template("quotation.html")

@app.route("/sales")
def sales_page():
    return render_template("sales_funnel.html")

@app.route("/sales/performance")
def sales_perf_page():
    return render_template("sales_performance.html")

@app.route("/sales/customers")
def sales_customers_page():
    return render_template("sales_customers.html")

@app.route("/sales/expenses")
def sales_expenses_page():
    return render_template("sales_expenses.html")

@app.route("/materials")
def materials_page():
    return render_template("materials.html")

@app.route("/materials/budget")
def materials_budget_page():
    return render_template("materials_budget.html")

@app.route("/materials/purchase")
def materials_purchase_page():
    return render_template("materials_purchase.html")

@app.route("/materials/stock")
def materials_stock_page():
    return render_template("materials_stock.html")

# ====== 电站运维 page routes ======
@app.route("/station")
def station_page():
    return render_template("station.html")

@app.route("/station/<int:sid>")
def station_detail_page(sid):
    return render_template("station_detail.html")

@app.route("/station/dashboard")
def station_dashboard_page():
    return render_template("station_dashboard.html")

# ============================================================
# API: 老板资金看板
# ============================================================

@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    db = get_db()
    # 总项目数
    total_projects = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    # 并网项目数
    grid_projects = db.execute("SELECT COUNT(*) FROM projects WHERE status='并网'").fetchone()[0]
    # 总装机容量
    total_cap = db.execute("SELECT COALESCE(SUM(capacity_kw),0) FROM projects").fetchone()[0]
    # 总投资额
    total_invest = db.execute("SELECT COALESCE(SUM(total_invest),0) FROM projects").fetchone()[0]
    # 已付款
    total_paid = db.execute("SELECT COALESCE(SUM(paid_amount),0) FROM projects").fetchone()[0]
    # 未付款
    total_remain = db.execute("SELECT COALESCE(SUM(remaining_amount),0) FROM projects").fetchone()[0]

    # 收入总计
    income = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='收入'").fetchone()[0]
    # 支出总计
    expense = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='支出'").fetchone()[0]

    # 电费应收总额
    total_ebill = db.execute("SELECT COALESCE(SUM(revenue),0) FROM electricity_bills").fetchone()[0]
    total_paid_ebill = db.execute("SELECT COALESCE(SUM(paid_amount),0) FROM electricity_bills").fetchone()[0]

    # 项目状态分布
    status_dist = db.execute("""
        SELECT status, COUNT(*) as cnt, COALESCE(SUM(total_invest),0) as invest
        FROM projects GROUP BY status
    """).fetchall()

    # 近6个月资金趋势
    trend_data = []
    for i in range(5, -1, -1):
        month = (date.today() - timedelta(days=i*30)).strftime("%Y-%m")
        inc = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='收入' AND payment_date LIKE ?", (f"{month}%",)).fetchone()[0]
        exp = db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE direction='支出' AND payment_date LIKE ?", (f"{month}%",)).fetchone()[0]
        trend_data.append({"month": month, "income": round(inc, 2), "expense": round(exp, 2)})

    # 项目垫资排行
    top_projects = db.execute("""
        SELECT id, name, owner_name, total_invest, paid_amount, remaining_amount, status
        FROM projects ORDER BY remaining_amount DESC LIMIT 10
    """).fetchall()

    # 延期/超支预警项目
    overdue = db.execute("""
        SELECT id, name, status, total_invest FROM projects
        WHERE status NOT IN ('并网','运维') ORDER BY total_invest DESC
    """).fetchall()

    return jsonify({
        "total_projects": total_projects,
        "grid_projects": grid_projects,
        "total_cap": round(total_cap, 2),
        "total_invest": round(total_invest, 2),
        "total_paid": round(total_paid, 2),
        "total_remain": round(total_remain, 2),
        "income": round(income, 2),
        "expense": round(expense, 2),
        "net_profit": round(income - expense, 2),
        "total_ebill": round(total_ebill, 2),
        "total_paid_ebill": round(total_paid_ebill, 2),
        "total_unpaid_ebill": round(total_ebill - total_paid_ebill, 2),
        "status_dist": [dict(r) for r in status_dist],
        "trend_data": trend_data,
        "top_projects": [dict(r) for r in top_projects],
        "overdue_projects": [dict(r) for r in overdue[:5]],
    })

# ============================================================
# API: 项目管理
# ============================================================

@app.route("/api/projects")
def api_projects_list():
    db = get_db()
    status = request.args.get("status", "")
    keyword = request.args.get("keyword", "")
    query = "SELECT * FROM projects WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(status)
    if keyword:
        query += " AND (name LIKE ? OR owner_name LIKE ? OR address LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
    query += " ORDER BY created_at DESC"
    rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/projects", methods=["POST"])
def api_projects_create():
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO projects
        (name, owner_name, address, capacity_kw, mode, build_type, status, total_invest)
        VALUES (?,?,?,?,?,?,?,?)""",
        (data.get("name"), data.get("owner_name"), data.get("address"),
         float(data.get("capacity_kw", 0)), data.get("mode", "EPC"),
         data.get("build_type", "阵列式"), data.get("status", "商机"),
         float(data.get("total_invest", 0))))
    db.commit()
    return jsonify({"ok": True, "id": db.execute("SELECT last_insert_rowid()").fetchone()[0]})

@app.route("/api/projects/<int:pid>")
def api_project_get(pid):
    db = get_db()
    p = db.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if not p:
        return jsonify({"error": "项目不存在"}), 404
    return jsonify(dict(p))

@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_project_update(pid):
    db = get_db()
    data = request.get_json()
    fields = ["name","owner_name","address","capacity_kw","mode","build_type",
               "status","total_invest","paid_amount","remaining_amount",
               "grid_code","grid_date","profit"]
    sets = []
    vals = []
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

@app.route("/api/projects/<int:pid>/costs")
def api_project_costs(pid):
    db = get_db()
    rows = db.execute("SELECT * FROM project_costs WHERE project_id=? ORDER BY record_date DESC", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/projects/<int:pid>/costs", methods=["POST"])
def api_project_cost_add(pid):
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO project_costs
        (project_id, cost_type, amount, description, record_date)
        VALUES (?,?,?,?,?)""",
        (pid, data.get("cost_type"), float(data.get("amount", 0)),
         data.get("description"), data.get("record_date", datetime.now().strftime("%Y-%m-%d"))))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/projects/<int:pid>/payments")
def api_project_payments(pid):
    db = get_db()
    rows = db.execute("SELECT * FROM payments WHERE project_id=? ORDER BY payment_date DESC", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

# ============================================================
# API: 电费结算
# ============================================================

@app.route("/api/electricity-bills")
def api_ebills_list():
    db = get_db()
    rows = db.execute("""
        SELECT eb.*, p.name as project_name, p.owner_name, p.capacity_kw
        FROM electricity_bills eb
        LEFT JOIN projects p ON eb.project_id=p.id
        ORDER BY eb.record_date DESC
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/electricity-bills", methods=["POST"])
def api_ebills_create():
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO electricity_bills
        (project_id, bill_month, gen_kwh, grid_price, revenue, payment_status, record_date)
        VALUES (?,?,?,?,?,?,?)""",
        (data.get("project_id"), data.get("bill_month"),
         float(data.get("gen_kwh", 0)), float(data.get("grid_price", 0)),
         float(data.get("revenue", 0)), data.get("payment_status", "待收款"),
         data.get("record_date", datetime.now().strftime("%Y-%m-%d"))))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/electricity-bills/<int:eid>", methods=["PUT"])
def api_ebill_update(eid):
    db = get_db()
    data = request.get_json()
    db.execute("""UPDATE electricity_bills SET
        payment_status=?, paid_amount=?, record_date=?
        WHERE id=?""",
        (data.get("payment_status"), float(data.get("paid_amount", 0)),
         data.get("record_date", datetime.now().strftime("%Y-%m-%d")), eid))
    db.commit()
    return jsonify({"ok": True})

# ============================================================
# API: 资金流水
# ============================================================

@app.route("/api/payments")
def api_payments_list():
    db = get_db()
    rows = db.execute("""
        SELECT pm.*, p.name as project_name
        FROM payments pm
        LEFT JOIN projects p ON pm.project_id=p.id
        ORDER BY pm.payment_date DESC LIMIT 200
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/payments", methods=["POST"])
def api_payment_create():
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO payments
        (project_id, direction, category, amount, payment_date, description)
        VALUES (?,?,?,?,?,?)""",
        (data.get("project_id"), data.get("direction"),
         data.get("category"), float(data.get("amount", 0)),
         data.get("payment_date", datetime.now().strftime("%Y-%m-%d")),
         data.get("description")))
    db.commit()
    return jsonify({"ok": True})

# ============================================================
# API: 库存物料
# ============================================================

@app.route("/api/materials")
def api_materials_list():
    db = get_db()
    rows = db.execute("SELECT * FROM materials ORDER BY category, name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/materials", methods=["POST"])
def api_material_create():
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO materials
        (name, category, unit, unit_price, supplier, stock_qty, safe_stock)
        VALUES (?,?,?,?,?,?,?)""",
        (data.get("name"), data.get("category"), data.get("unit", "个"),
         float(data.get("unit_price", 0)), data.get("supplier"),
         float(data.get("stock_qty", 0)), float(data.get("safe_stock", 0))))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/materials/<int:mid>", methods=["PUT"])
def api_material_update(mid):
    db = get_db()
    data = request.get_json()
    db.execute("""UPDATE materials SET
        name=?, category=?, unit=?, unit_price=?, supplier=?, stock_qty=?, safe_stock=?
        WHERE id=?""",
        (data.get("name"), data.get("category"), data.get("unit"),
         float(data.get("unit_price", 0)), data.get("supplier"),
         float(data.get("stock_qty", 0)), float(data.get("safe_stock", 0)), mid))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/material-flows")
def api_material_flows_list():
    db = get_db()
    rows = db.execute("""
        SELECT mf.*, m.name as material_name, p.name as project_name
        FROM material_flows mf
        LEFT JOIN materials m ON mf.material_id=m.id
        LEFT JOIN projects p ON mf.project_id=p.id
        ORDER BY mf.flow_date DESC LIMIT 200
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/material-flows", methods=["POST"])
def api_material_flow_create():
    db = get_db()
    data = request.get_json()
    material_id = data.get("material_id")
    qty = float(data.get("qty", 0))
    db.execute("""INSERT INTO material_flows
        (material_id, project_id, flow_type, qty, price, flow_date)
        VALUES (?,?,?,?,?,?)""",
        (material_id, data.get("project_id"), data.get("flow_type"),
         qty, float(data.get("price", 0)),
         data.get("flow_date", datetime.now().strftime("%Y-%m-%d"))))
    # 更新库存
    if data.get("flow_type") == "入库":
        db.execute("UPDATE materials SET stock_qty=stock_qty+? WHERE id=?", (qty, material_id))
    elif data.get("flow_type") == "出库":
        db.execute("UPDATE materials SET stock_qty=stock_qty-? WHERE id=?", (qty, material_id))
    db.commit()
    return jsonify({"ok": True})

# ============================================================
# API: WBS施工进度
# ============================================================

@app.route("/api/wbs/<int:pid>")
def api_wbs_list(pid):
    db = get_db()
    rows = db.execute("SELECT * FROM wbs_nodes WHERE project_id=? ORDER BY node_order", (pid,)).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/wbs/<int:pid>", methods=["POST"])
def api_wbs_update(pid):
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE wbs_nodes SET is_done=?, done_date=?, done_by=?, note=? WHERE id=?",
        (data.get("is_done"), data.get("done_date"), data.get("done_by"), data.get("note"), data.get("id")))
    db.commit()
    return jsonify({"ok": True})

# ============================================================
# API: 运维工单
# ============================================================

@app.route("/api/maintenance-orders")
def api_mo_list():
    db = get_db()
    rows = db.execute("""
        SELECT mo.*, p.name as project_name
        FROM maintenance_orders mo
        LEFT JOIN projects p ON mo.project_id=p.id
        ORDER BY mo.created_at DESC
    """).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/maintenance-orders", methods=["POST"])
def api_mo_create():
    db = get_db()
    data = request.get_json()
    db.execute("""INSERT INTO maintenance_orders
        (project_id, order_type, title, description, assigned_to)
        VALUES (?,?,?,?,?)""",
        (data.get("project_id"), data.get("order_type"),
         data.get("title"), data.get("description"), data.get("assigned_to")))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/maintenance-orders/<int:oid>", methods=["PUT"])
def api_mo_update(oid):
    db = get_db()
    data = request.get_json()
    db.execute("UPDATE maintenance_orders SET status=?, done_at=? WHERE id=?",
        (data.get("status"), datetime.now().strftime("%Y-%m-%d") if data.get("status")=="已完成" else None, oid))
    db.commit()
    return jsonify({"ok": True})

# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    with app.app_context():
        init_db()
        register_sales_routes(app, get_db)
        register_station_routes(app, get_db)
    port = int(os.environ.get("PORT", 8000))
    print("=" * 55)
    print("  鑫科新能源光伏企业全链路ERP系统")
    print(f"  访问地址：http://localhost:{port}")
    print("  账号：admin  密码：admin888")
    print("=" * 55)
    app.run(host="0.0.0.0", port=port, debug=False)