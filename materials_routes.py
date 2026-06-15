# -*- coding: utf-8 -*-
"""
物资管控模块 - 材料预算/申购/采购/入库/库存/领用/成本归集 全链路管理
"""

def ensure_material_tables(db):
    stmts = [
        "CREATE TABLE IF NOT EXISTS material_bom (id INTEGER PRIMARY KEY AUTOINCREMENT,bom_name TEXT NOT NULL,project_type TEXT DEFAULT '工商业',capacity_kw REAL DEFAULT 0,version TEXT DEFAULT 'V1',status TEXT DEFAULT '启用',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS material_bom_items (id INTEGER PRIMARY KEY AUTOINCREMENT,bom_id INTEGER,category TEXT NOT NULL,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',quantity REAL DEFAULT 0,loss_rate REAL DEFAULT 0,unit_price REAL DEFAULT 0,supplier TEXT,remark TEXT,FOREIGN KEY (bom_id) REFERENCES material_bom(id))",
        "CREATE TABLE IF NOT EXISTS material_suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT,supplier_name TEXT NOT NULL,contact_person TEXT,phone TEXT,address TEXT,category TEXT,rating TEXT DEFAULT 'B',payment_terms TEXT,delivery_days INTEGER DEFAULT 7,status TEXT DEFAULT '合格',created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS material_purchase_orders (id INTEGER PRIMARY KEY AUTOINCREMENT,po_no TEXT UNIQUE,supplier_id INTEGER,project_id INTEGER,total_amount REAL DEFAULT 0,order_date TEXT,expected_date TEXT,actual_date TEXT,delivery_status TEXT DEFAULT '待发货',payment_status TEXT DEFAULT '未付款',created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (supplier_id) REFERENCES material_suppliers(id))",
        "CREATE TABLE IF NOT EXISTS material_purchase_items (id INTEGER PRIMARY KEY AUTOINCREMENT,po_id INTEGER,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,amount REAL DEFAULT 0,delivered_qty REAL DEFAULT 0,accepted_qty REAL DEFAULT 0,rejected_qty REAL DEFAULT 0,FOREIGN KEY (po_id) REFERENCES material_purchase_orders(id))",
        "CREATE TABLE IF NOT EXISTS materialrequisition (id INTEGER PRIMARY KEY AUTOINCREMENT,req_no TEXT UNIQUE,project_id INTEGER,department TEXT,applicant TEXT,apply_date TEXT,status TEXT DEFAULT '待审批',total_amount REAL DEFAULT 0,approved_by TEXT,approved_at TEXT,note TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id))",
        "CREATE TABLE IF NOT EXISTS material_requisition_items (id INTEGER PRIMARY KEY AUTOINCREMENT,req_id INTEGER,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,amount REAL DEFAULT 0,source_type TEXT DEFAULT '采购',FOREIGN KEY (req_id) REFERENCES materialrequisition(id))",
        "CREATE TABLE IF NOT EXISTS material_stock (id INTEGER PRIMARY KEY AUTOINCREMENT,warehouse_type TEXT DEFAULT '中心仓',warehouse_name TEXT DEFAULT '公司中心仓',project_id INTEGER,batch_no TEXT,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',quantity REAL DEFAULT 0,available_qty REAL DEFAULT 0,reserved_qty REAL DEFAULT 0,unit_price REAL DEFAULT 0,total_amount REAL DEFAULT 0,supplier_id INTEGER,incoming_date TEXT,QC_status TEXT DEFAULT '合格',serial_nos TEXT,remark TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id),FOREIGN KEY (supplier_id) REFERENCES material_suppliers(id))",
        "CREATE TABLE IF NOT EXISTS material_out (id INTEGER PRIMARY KEY AUTOINCREMENT,out_no TEXT UNIQUE,project_id INTEGER,warehouse_type TEXT,warehouse_name TEXT,applicant TEXT,out_date TEXT,status TEXT DEFAULT '待出库',total_amount REAL DEFAULT 0,approved_by TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id))",
        "CREATE TABLE IF NOT EXISTS material_out_items (id INTEGER PRIMARY KEY AUTOINCREMENT,out_id INTEGER,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,amount REAL DEFAULT 0,construction_part TEXT,worker_name TEXT,stock_id INTEGER,serial_nos TEXT,FOREIGN KEY (out_id) REFERENCES material_out(id),FOREIGN KEY (stock_id) REFERENCES material_stock(id))",
        "CREATE TABLE IF NOT EXISTS material_cost_record (id INTEGER PRIMARY KEY AUTOINCREMENT,project_id INTEGER,cost_type TEXT DEFAULT '领用',material_name TEXT NOT NULL,spec TEXT,quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,amount REAL DEFAULT 0,out_id INTEGER,record_date TEXT,operator TEXT,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id))",
        "CREATE TABLE IF NOT EXISTS material_transfer (id INTEGER PRIMARY KEY AUTOINCREMENT,transfer_no TEXT UNIQUE,from_project_id INTEGER,to_project_id INTEGER,material_name TEXT NOT NULL,spec TEXT,quantity REAL DEFAULT 0,unit_price REAL DEFAULT 0,transfer_date TEXT,status TEXT DEFAULT '待调拨',approved_by TEXT,created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS material_inventory_check (id INTEGER PRIMARY KEY AUTOINCREMENT,check_no TEXT UNIQUE,warehouse_type TEXT,warehouse_name TEXT,check_date TEXT,checker TEXT,status TEXT DEFAULT '盘点中',profit_loss_amount REAL DEFAULT 0,created_at TEXT DEFAULT (datetime('now')))",
        "CREATE TABLE IF NOT EXISTS material_inventory_check_items (id INTEGER PRIMARY KEY AUTOINCREMENT,check_id INTEGER,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',stock_qty REAL DEFAULT 0,check_qty REAL DEFAULT 0,profit_loss_qty REAL DEFAULT 0,profit_loss_amount REAL DEFAULT 0,reason TEXT,FOREIGN KEY (check_id) REFERENCES material_inventory_check(id))",
        "CREATE TABLE IF NOT EXISTS material_budget (id INTEGER PRIMARY KEY AUTOINCREMENT,project_id INTEGER,category TEXT,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',budget_qty REAL DEFAULT 0,budget_price REAL DEFAULT 0,budget_amount REAL DEFAULT 0,approved_qty REAL DEFAULT 0,requisition_qty REAL DEFAULT 0,purchased_qty REAL DEFAULT 0,delivered_qty REAL DEFAULT 0,issued_qty REAL DEFAULT 0,on_site_qty REAL DEFAULT 0,loss_rate REAL DEFAULT 0,version TEXT DEFAULT 'V1',status TEXT DEFAULT '编制中',created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id))",
        "CREATE TABLE IF NOT EXISTS material_budget_warn (id INTEGER PRIMARY KEY AUTOINCREMENT,project_id INTEGER,budget_id INTEGER,category TEXT,material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',budget_qty REAL DEFAULT 0,requisition_qty REAL DEFAULT 0,purchased_qty REAL DEFAULT 0,delivered_qty REAL DEFAULT 0,issued_qty REAL DEFAULT 0,warn_level TEXT DEFAULT '正常',warn_reason TEXT,freeze_requisition INTEGER DEFAULT 0,created_at TEXT DEFAULT (datetime('now')),updated_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (project_id) REFERENCES projects(id),FOREIGN KEY (budget_id) REFERENCES material_budget(id))",
        "CREATE TABLE IF NOT EXISTS material_stock_flow (id INTEGER PRIMARY KEY AUTOINCREMENT,stock_id INTEGER,project_id INTEGER,warehouse_type TEXT DEFAULT '中心仓',warehouse_name TEXT DEFAULT '公司中心仓',material_name TEXT NOT NULL,spec TEXT,unit TEXT DEFAULT '件',period TEXT NOT NULL,opening_qty REAL DEFAULT 0,opening_amount REAL DEFAULT 0,inbound_qty REAL DEFAULT 0,inbound_amount REAL DEFAULT 0,outbound_qty REAL DEFAULT 0,outbound_amount REAL DEFAULT 0,closing_qty REAL DEFAULT 0,closing_amount REAL DEFAULT 0,created_at TEXT DEFAULT (datetime('now')),FOREIGN KEY (stock_id) REFERENCES material_stock(id),FOREIGN KEY (project_id) REFERENCES projects(id))",
    ]
    for sql in stmts:
        try: db.execute(sql)
        except: pass
    db.commit()
    _seed_material_data(db)


def _seed_material_data(db):
    """种子数据：标准BOM库 + 合格供应商"""
    # 标准BOM库
    boms = [
        ("工商业标准BOM 100kW", "工商业", 100),
        ("工商业标准BOM 500kW", "工商业", 500),
        ("户用标准BOM 10kW", "户用", 10),
        ("别墅标准BOM 20kW", "别墅", 20),
    ]
    for name, ptype, cap in boms:
        cur = db.execute("INSERT INTO material_bom (bom_name,project_type,capacity_kw) VALUES (?,?,?)", (name, ptype, cap))
        bom_id = cur.lastrowid
        items = [
            ("光伏组件", "单晶580W", "块", 1.0, 0.005, 1.5),
            ("光伏组件", "单晶550W", "块", 1.0, 0.005, 1.4),
            ("逆变器", "组串式110kW", "台", 1.0, 0.001, 0.6),
            ("直流线缆", "4mm² PV1-F", "米", 1.5, 0.02, 0.015),
            ("交流线缆", "YJV-4×95", "米", 0.3, 0.01, 0.08),
            ("配电箱", "交流汇流箱", "台", 1.0, 0.005, 0.3),
            ("支架", "热镀锌碳钢", "吨", 0.015, 0.03, 0.8),
            ("螺栓", "不锈钢M10", "套", 0.05, 0.03, 0.05),
            ("接地材料", "扁钢/接地棒", "套", 0.01, 0.02, 0.3),
        ]
        for cat, mname, unit, qty, loss, price in items:
            db.execute("INSERT INTO material_bom_items (bom_id,category,material_name,spec,unit,quantity,loss_rate,unit_price) VALUES (?,?,?,?,?,?,?,?)",
                (bom_id, cat, mname, unit, qty, loss, price))

    # 合格供应商
    suppliers = [
        ("隆基绿能科技股份有限公司", "李总", "13812340021", "西安", "光伏组件", "A"),
        ("阳光电源股份有限公司", "王总", "13812340022", "合肥", "逆变器", "A"),
        ("浙江正泰电器股份有限公司", "张总", "13812340023", "杭州", "配电箱/线缆", "A"),
        ("江苏中天科技股份有限公司", "刘总", "13812340024", "南通", "直流线缆", "B"),
        ("厦门唯而不锈钢制品有限公司", "陈总", "13812340025", "厦门", "支架/紧固件", "B"),
    ]
    for s in suppliers:
        db.execute("INSERT INTO material_suppliers (supplier_name,contact_person,phone,address,category,rating) VALUES (?,?,?,?,?,?)", s)

    db.commit()