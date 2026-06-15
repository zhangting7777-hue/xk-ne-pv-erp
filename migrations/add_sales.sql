-- 销售漏斗相关表

CREATE TABLE IF NOT EXISTS sales_persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    role TEXT DEFAULT '业务员',
    status TEXT DEFAULT '在职',
    created_at TEXT DEFAULT (datetime('now'))
;

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT,
    phone TEXT,
    address TEXT,
    industry TEXT,
    annual_power_kwh REAL DEFAULT 0,
    roof_area_sqm REAL DEFAULT 0,
    intended_capacity_kw REAL DEFAULT 0,
    owner_type TEXT DEFAULT '民营',
    credit_level TEXT DEFAULT 'B',
    assigned_to INTEGER REFERENCES sales_persons(id),
    source TEXT DEFAULT '陌生开发',
    created_at TEXT DEFAULT (datetime('now')))
;

CREATE TABLE IF NOT EXISTS biz_opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER REFERENCES customers(id),
    project_name TEXT NOT NULL,
    project_type TEXT DEFAULT '工商业',
    capacity_kw REAL DEFAULT 0,
    electricity_price REAL DEFAULT 0,
    expected_invest REAL DEFAULT 0,
    expected_irr REAL DEFAULT 0,
    stage TEXT DEFAULT '信息搜集',
    stage_order INTEGER DEFAULT 0,
    level TEXT DEFAULT 'B',
    amount REAL DEFAULT 0,
    is_won INTEGER DEFAULT 0,
    is_lost INTEGER DEFAULT 0,
    lost_reason TEXT,
    assigned_to INTEGER REFERENCES sales_persons(id),
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')))
;

CREATE TABLE IF NOT EXISTS follow_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER REFERENCES biz_opportunities(id),
    sales_person_id INTEGER REFERENCES sales_persons(id),
    record_type TEXT DEFAULT '拜访',
    content TEXT,
    location TEXT,
    photo_url TEXT,
    next_plan TEXT,
    next_date TEXT,
    created_at TEXT DEFAULT (datetime('now')))
;

CREATE TABLE IF NOT EXISTS sales_expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER REFERENCES biz_opportunities(id),
    sales_person_id INTEGER REFERENCES sales_persons(id),
    expense_type TEXT,
    amount REAL DEFAULT 0,
    description TEXT,
    receipt_url TEXT,
    expense_date TEXT,
    status TEXT DEFAULT '待审批',
    created_at TEXT DEFAULT (datetime('now')))
;

CREATE TABLE IF NOT EXISTS performance_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sales_person_id INTEGER REFERENCES sales_persons(id),
    target_year INTEGER,
    target_month INTEGER,
    target_contract REAL DEFAULT 0,
    target_collection REAL DEFAULT 0,
    achieved_contract REAL DEFAULT 0,
    achieved_collection REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')))
;

CREATE TABLE IF NOT EXISTS contract_revenues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER REFERENCES biz_opportunities(id),
    project_id INTEGER,
    sales_person_id INTEGER REFERENCES sales_persons(id),
    contract_amount REAL DEFAULT 0,
    signed_date TEXT,
    collection_status TEXT DEFAULT '待收款',
    total_collected REAL DEFAULT 0,
    total_receivable REAL DEFAULT 0,
    overdue_amount REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')))
;
