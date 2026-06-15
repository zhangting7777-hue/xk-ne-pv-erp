# -*- coding: utf-8 -*-
from flask import request, jsonify
from datetime import datetime, timedelta
import random

def ensure_sales_tables(db):
    stmts = [
        "CREATE TABLE IF NOT EXISTS sales_persons (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,phone TEXT,role TEXT DEFAULT '业务员',status TEXT DEFAULT '在职',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,contact_person TEXT,phone TEXT,address TEXT,industry TEXT,annual_power_kwh REAL DEFAULT 0,roof_area_sqm REAL DEFAULT 0,intended_capacity_kw REAL DEFAULT 0,owner_type TEXT DEFAULT '民营',credit_level TEXT DEFAULT 'B',assigned_to INTEGER,source TEXT DEFAULT '陌生开发',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS biz_opportunities (id INTEGER PRIMARY KEY AUTOINCREMENT,customer_id INTEGER,project_name TEXT NOT NULL,project_type TEXT DEFAULT '工商业',capacity_kw REAL DEFAULT 0,electricity_price REAL DEFAULT 0,expected_invest REAL DEFAULT 0,expected_irr REAL DEFAULT 0,stage TEXT DEFAULT '信息搜集',stage_order INTEGER DEFAULT 0,level TEXT DEFAULT 'B',amount REAL DEFAULT 0,is_won INTEGER DEFAULT 0,is_lost INTEGER DEFAULT 0,lost_reason TEXT,assigned_to INTEGER,note TEXT,created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS follow_records (id INTEGER PRIMARY KEY AUTOINCREMENT,opportunity_id INTEGER,sales_person_id INTEGER,record_type TEXT DEFAULT '拜访',content TEXT,location TEXT,photo_url TEXT,next_plan TEXT,next_date TEXT,created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS sales_expenses (id INTEGER PRIMARY KEY AUTOINCREMENT,opportunity_id INTEGER,sales_person_id INTEGER,expense_type TEXT,amount REAL DEFAULT 0,description TEXT,receipt_url TEXT,expense_date TEXT,status TEXT DEFAULT '待审批',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS contract_revenues (id INTEGER PRIMARY KEY AUTOINCREMENT,opportunity_id INTEGER,project_id INTEGER,sales_person_id INTEGER,contract_amount REAL DEFAULT 0,signed_date TEXT,collection_status TEXT DEFAULT '待收款',total_collected REAL DEFAULT 0,total_receivable REAL DEFAULT 0,overdue_amount REAL DEFAULT 0,created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS performance_targets (id INTEGER PRIMARY KEY AUTOINCREMENT,sales_person_id INTEGER,target_year INTEGER,target_month INTEGER,target_contract REAL DEFAULT 0,target_collection REAL DEFAULT 0,achieved_contract REAL DEFAULT 0,achieved_collection REAL DEFAULT 0,created_at TEXT DEFAULT (datetime('now')))",
    ]
    for sql in stmts:
        try: db.execute(sql)
        except: pass
    db.commit()
    if db.execute("SELECT COUNT(*) FROM sales_persons").fetchone()[0] == 0:
        _seed_sales_data(db)

def _seed_sales_data(db):
    for n,ph in [("杨某某","13912340001"), ("肖某某","13912340002"), ("张某某","13912340003")]:
        db.execute("INSERT INTO sales_persons (name,phone,role,status) VALUES (?,?,'业务员','在职')", (n,ph))
    sp_ids = [r[0] for r in db.execute("SELECT id FROM sales_persons").fetchall()]
    custs = [
        ("福州亿锦纺织有限公司","陈总","13912340011","福州市台江区","纺织",500000,8000,300),
        ("厦门联发仓储公司","林总","13912340012","厦门市湖里区","仓储",800000,12000,500),
        ("泉州恒达制造厂","王总","13912340013","泉州市鲤城区","制造",600000,9500,400),
        ("莆田明辉食品公司","刘总","13912340014","莆田市城厢区","食品",300000,5000,200),
        ("漳州华鑫玻璃厂","周总","13912340015","漳州市芗城区","玻璃",450000,7000,350),
    ]
    for c in custs:
        db.execute("INSERT INTO customers (name,contact_person,phone,address,industry,annual_power_kwh,roof_area_sqm,intended_capacity_kw,assigned_to,source) VALUES (?,?,?,?,?,?,?,?,?,'陌生开发')",
            (c[0],c[1],c[2],c[3],c[4],c[5],c[6],c[7],random.choice(sp_ids)))
    cust_ids = [r[0] for r in db.execute("SELECT id FROM customers").fetchall()]
    stages = ["信息搜集","项目立项","前期可研","方案设计","深化设计","清单编制","项目招标","赢单"]
    for cid in cust_ids:
        st = random.choice(stages)
        cp = random.choice([100,200,300,500])
        inv = cp * random.uniform(2.2,2.8)
        nm = custs[cust_ids.index(cid)][0]
        db.execute("INSERT INTO biz_opportunities (customer_id,project_name,project_type,capacity_kw,electricity_price,expected_invest,expected_irr,stage,stage_order,level,amount,assigned_to) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid,nm+"光伏项目","工商业",cp,random.uniform(0.65,0.85),inv,random.uniform(0.12,0.20),st,stages.index(st),random.choice(["A级","B级","C级","D级"]),inv,random.choice(sp_ids)))
    opp_ids = [r[0] for r in db.execute("SELECT id FROM biz_opportunities").fetchall()]
    for oid in opp_ids[:3]:
        for _ in range(random.randint(1,3)):
            nd = (datetime.now()+timedelta(days=random.randint(3,14))).strftime("%Y-%m-%d")
            db.execute("INSERT INTO follow_records (opportunity_id,sales_person_id,record_type,content,next_plan,next_date) VALUES (?,?,?,?,?,?)",
                (oid,random.choice(sp_ids),"拜访",random.choice(["现场踏勘沟通","电话跟进","方案设计"]),random.choice(["约见业主签约","准备投标文件"]),nd))
    for oid in opp_ids[:3]:
        sg = (datetime.now()-timedelta(days=random.randint(30,180))).strftime("%Y-%m-%d")
        amt = random.uniform(50,200)
        col = amt * random.uniform(0.2,0.8)
        db.execute("INSERT INTO contract_revenues (opportunity_id,sales_person_id,contract_amount,signed_date,collection_status,total_collected,total_receivable) VALUES (?,?,?,?,?,?,?)",
            (oid,random.choice(sp_ids),amt,sg,"部分收款" if col<amt else "已结清",col,amt))
    for _ in range(5):
        ed = (datetime.now()-timedelta(days=random.randint(1,60))).strftime("%Y-%m-%d")
        db.execute("INSERT INTO sales_expenses (opportunity_id,sales_person_id,expense_type,amount,description,expense_date,status) VALUES (?,?,?,?,?,?,?)",
            (random.choice(opp_ids),random.choice(sp_ids),random.choice(["差旅费","招待费","中介费","设计费"]),random.uniform(0.1,2.0),random.choice(["客户拜访交通费","项目洽谈招待","路条中介费"]),ed,random.choice(["已审批","待审批"])))
    db.commit()

def register_sales_routes(app, get_db):
    @app.before_request
    def _init():
        from flask import g
        if not getattr(g,'_sales_inited',False):
            try:
                ensure_sales_tables(get_db())
            except Exception:
                pass
            g._sales_inited = True
    @app.route("/api/sales/funnel")
    def sf_funnel():
        db = get_db()
        rows = db.execute("SELECT stage,stage_order,COUNT(*) as cnt,COALESCE(SUM(capacity_kw),0) as cap,COALESCE(SUM(amount),0) as amt FROM biz_opportunities WHERE is_lost=0 GROUP BY stage ORDER BY stage_order").fetchall()
        won = db.execute("SELECT COUNT(*),COALESCE(SUM(amount),0) FROM biz_opportunities WHERE is_won=1").fetchone()
        lst = db.execute("SELECT COUNT(*) FROM biz_opportunities WHERE is_lost=1").fetchone()
        return jsonify({"stages": [dict(r) for r in rows], "won_cnt": won[0], "won_amt": won[1], "lost_cnt": lst[0]})
    @app.route("/api/sales/opportunities")
    def sf_list():
        db = get_db()
        kw = request.args.get("kw","")
        st = request.args.get("stage","")
        lv = request.args.get("level","")
        q = "SELECT bo.*,c.name as cust_name,c.industry,c.address,sp.name as sales_name FROM biz_opportunities bo LEFT JOIN customers c ON bo.customer_id=c.id LEFT JOIN sales_persons sp ON bo.assigned_to=sp.id WHERE 1=1"
        ps = []
        if kw:
            q += " AND (bo.project_name LIKE ? OR c.name LIKE ? OR bo.note LIKE ?)"
            ps.extend(["%"+kw+"%"]*3)
        if st: q += " AND bo.stage=?"; ps.append(st)
        if lv: q += " AND bo.level=?"; ps.append(lv)
        q += " ORDER BY bo.updated_at DESC"
        return jsonify([dict(r) for r in db.execute(q, ps).fetchall()])
    @app.route("/api/sales/opportunities", methods=["POST"])
    def sf_create():
        db = get_db()
        d = request.get_json()
        db.execute("INSERT INTO biz_opportunities (customer_id,project_name,project_type,capacity_kw,electricity_price,expected_invest,expected_irr,stage,stage_order,level,amount,assigned_to,note) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (d.get("customer_id"), d.get("project_name"), d.get("project_type","工商业"),
             float(d.get("capacity_kw",0)), float(d.get("electricity_price",0)),
             float(d.get("expected_invest",0)), float(d.get("expected_irr",0)),
             d.get("stage","信息搜集"), int(d.get("stage_order",0)),
             d.get("level","B"), float(d.get("amount",0)),
             d.get("assigned_to"), d.get("note","")))
        db.commit()
        return jsonify({"ok":True,"id": db.execute("SELECT last_insert_rowid()").fetchone()[0]})
    @app.route("/api/sales/opportunities/<int:oid>", methods=["PUT"])
    def sf_update(oid):
        db = get_db()
        d = request.get_json()
        flds, vals = [], []
        for f in ["project_name","stage","stage_order","level","amount","note","capacity_kw","electricity_price","expected_invest","expected_irr","is_won","is_lost","lost_reason","assigned_to"]:
            if f in d and d.get(f) is not None:
                flds.append(f+"=?")
                vals.append(d[f])
        if flds:
            vals.append(oid)
            db.execute("UPDATE biz_opportunities SET "+",".join(flds)+" WHERE id=?", vals)
        db.commit()
        return jsonify({"ok":True})
    @app.route("/api/sales/opportunities/<int:oid>/follow")
    def sf_follow_list(oid):
        db = get_db()
        rows = db.execute("SELECT fr.*,sp.name as sales_name FROM follow_records fr LEFT JOIN sales_persons sp ON fr.sales_person_id=sp.id WHERE fr.opportunity_id=? ORDER BY fr.created_at DESC", (oid,)).fetchall()
        return jsonify([dict(r) for r in rows])
    @app.route("/api/sales/opportunities/<int:oid>/follow", methods=["POST"])
    def sf_follow_add(oid):
        db = get_db()
        d = request.get_json()
        db.execute("INSERT INTO follow_records (opportunity_id,sales_person_id,record_type,content,next_plan,next_date) VALUES (?,?,?,?,?,?)",
            (oid, d.get("sales_person_id"), d.get("record_type","拜访"), d.get("content",""), d.get("next_plan",""), d.get("next_date","")))
        db.commit()
        return jsonify({"ok":True})
    @app.route("/api/sales/customers")
    def sf_customers():
        db = get_db()
        rows = db.execute("SELECT c.*,sp.name as sales_name,(SELECT COUNT(*) FROM biz_opportunities WHERE customer_id=c.id) as opp_count FROM customers c LEFT JOIN sales_persons sp ON c.assigned_to=sp.id ORDER BY c.created_at DESC").fetchall()
        return jsonify([dict(r) for r in rows])
    @app.route("/api/sales/customers", methods=["POST"])
    def sf_cust_create():
        db = get_db()
        d = request.get_json()
        db.execute("INSERT INTO customers (name,contact_person,phone,address,industry,annual_power_kwh,roof_area_sqm,intended_capacity_kw,owner_type,credit_level,assigned_to,source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (d.get("name"), d.get("contact_person"), d.get("phone"), d.get("address"), d.get("industry"),
             float(d.get("annual_power_kwh",0)), float(d.get("roof_area_sqm",0)), float(d.get("intended_capacity_kw",0)),
             d.get("owner_type","民营"), d.get("credit_level","B"), d.get("assigned_to"), d.get("source","陌生开发")))
        db.commit()
        return jsonify({"ok":True})
    @app.route("/api/sales/persons")
    def sf_persons():
        return jsonify([dict(r) for r in get_db().execute("SELECT * FROM sales_persons WHERE status='在职' ORDER BY name").fetchall()])
    @app.route("/api/sales/performance")
    def sf_perf():
        db = get_db()
        result = []
        for p in db.execute("SELECT * FROM sales_persons WHERE status='在职'").fetchall():
            cr = db.execute("SELECT COALESCE(SUM(contract_amount),0),COALESCE(SUM(total_collected),0) FROM contract_revenues WHERE sales_person_id=?", (p["id"],)).fetchone()
            er = db.execute("SELECT COALESCE(SUM(amount),0) FROM sales_expenses WHERE sales_person_id=? AND status='已审批'", (p["id"],)).fetchone()
            oc = db.execute("SELECT COUNT(*) FROM biz_opportunities WHERE assigned_to=?", (p["id"],)).fetchone()
            wc = db.execute("SELECT COUNT(*) FROM biz_opportunities WHERE assigned_to=? AND is_won=1", (p["id"],)).fetchone()
            result.append({"id":p["id"],"name":p["name"],"role":p["role"],
                "total_contract":round(cr[0],2),"total_collected":round(cr[1],2),
                "total_expense":round(er[0],2),"opp_count":oc[0],"won_count":wc[0]})
        return jsonify(result)
    @app.route("/api/sales/expenses")
    def sf_expenses():
        db = get_db()
        rows = db.execute("SELECT se.*,sp.name as sales_name,bo.project_name FROM sales_expenses se LEFT JOIN sales_persons sp ON se.sales_person_id=sp.id LEFT JOIN biz_opportunities bo ON se.opportunity_id=bo.id ORDER BY se.expense_date DESC LIMIT 200").fetchall()
        return jsonify([dict(r) for r in rows])
    @app.route("/api/sales/expenses", methods=["POST"])
    def sf_exp_create():
        db = get_db()
        d = request.get_json()
        db.execute("INSERT INTO sales_expenses (opportunity_id,sales_person_id,expense_type,amount,description,expense_date,status) VALUES (?,?,?,?,?,?,?)",
            (d.get("opportunity_id"), d.get("sales_person_id"), d.get("expense_type"), float(d.get("amount",0)),
             d.get("description"), d.get("expense_date"), d.get("status","待审批")))
        db.commit()
        return jsonify({"ok":True})
    @app.route("/api/sales/expenses/<int:eid>", methods=["PUT"])
    def sf_exp_upd(eid):
        d = request.get_json()
        db = get_db()
        db.execute("UPDATE sales_expenses SET status=? WHERE id=?", (d.get("status"), eid))
        db.commit()
        return jsonify({"ok":True})
    print("  market sales routes registered")
