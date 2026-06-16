# -*- coding: utf-8 -*-
"""
项目投资决策计算器
IRR、内部收益率、回本年限测算
"""
from flask import request, jsonify
from datetime import datetime
import math

def register_investment_routes(app, get_db):
    """注册投决计算器相关路由"""

    # ─────────────────────────────────────────────
    # 投决计算器 — 保存方案
    # ─────────────────────────────────────────────
    @app.route("/api/investment/calc", methods=["POST"])
    def api_investment_calc():
        """IRR + 回本年限计算"""
        data = request.get_json()

        capacity_kw    = float(data.get("capacity_kw", 0))       # kW
        invest_total   = float(data.get("invest_total", 0))       # 总投资 万元
        tariff         = float(data.get("tariff", 0))             # 电价 元/kWh
        annual_gen     = float(data.get("annual_gen", 0))         # 年发电量 万kWh
        opex_year      = float(data.get("opex_year", 0))         # 年运维成本 万元
        tax_rate       = float(data.get("tax_rate", 0))          # 税率 %
        sub_year       = float(data.get("sub_year", 0))          # 补贴年限 年
        sub_per_kwh    = float(data.get("sub_per_kwh", 0))       # 补贴金额 元/kWh
        deprec_years   = int(data.get("deprec_years", 20))       # 折旧年限
        debt_ratio     = float(data.get("debt_ratio", 0))        # 贷款比例 %
        loan_rate      = float(data.get("loan_rate", 0))          # 贷款利率 %
        loan_years     = int(data.get("loan_years", 10))         # 贷款年限
        oper_days      = int(data.get("oper_days", 365))          # 运营天数
        deprec_cost    = invest_total / deprec_years if deprec_years > 0 else 0  # 年折旧 万元

        # ── 收入计算 ──
        annual_revenue = annual_gen * tariff          # 年度发电收入 万元
        annual_sub     = annual_gen * sub_per_kwh    # 年度补贴 万元
        total_sub     = annual_sub * sub_year        # 总补贴 万元

        # ── 成本计算 ──
        annual_cost = opex_year + deprec_cost         # 年度成本（不含利息）
        debt_amount = invest_total * debt_ratio / 100  # 贷款本金 万元

        # ── 年度现金流（简化版，适合自投EMC） ──
        years = 25  # 测算25年
        cashflows = []

        # 第0年：初始投资（支出）
        cf0 = -invest_total
        cashflows.append(cf0)

        # 第1-n年：运营现金流
        for y in range(1, years + 1):
            is_sub_year = (y <= sub_year)
            revenue = annual_revenue + (annual_sub if is_sub_year else 0)
            cost   = annual_cost
            # 利润总额
            profit_before_tax = revenue - cost
            # 所得税（如果盈利）
            income_tax = max(0, profit_before_tax * tax_rate / 100) if profit_before_tax > 0 else 0
            net_profit = profit_before_tax - income_tax
            # 现金流 = 净利润 + 折旧（不付出现金）
            annual_cf = net_profit + deprec_cost
            cashflows.append(annual_cf)

        # ── IRR 计算（牛顿迭代法） ──
        def npv(rate, cfs):
            return sum(cf / (1 + rate) ** t for t, cf in enumerate(cfs))

        def irr(cfs, guess=0.10):
            rate = guess
            for _ in range(1000):
                npv_val = npv(rate, cfs)
                # 导数
                deriv = sum(-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cfs))
                if abs(deriv) < 1e-12:
                    break
                rate_new = rate - npv_val / deriv
                if abs(rate_new - rate) < 1e-8:
                    rate = rate_new
                    break
                rate = rate_new
            return rate

        irr_value = irr(cashflows)

        # ── 静态回本年限 ──
        cum_cf = 0
        payback_years = 0
        for t, cf in enumerate(cashflows[1:], 1):  # skip year 0
            cum_cf += cf
            if cum_cf >= invest_total:
                # 线性插值
                prev_cum = cum_cf - cf
                fraction = (invest_total - prev_cum) / cf if cf > 0 else 0
                payback_years = t - 1 + fraction
                break
        if payback_years == 0 and cum_cf < invest_total:
            payback_years = None  # 25年内未回本

        # ── 25年累计净现金流 ──
        total_net_cf = sum(cashflows)
        total_revenue_25y = sum(
            (annual_revenue + (annual_sub if y <= sub_year else 0))
            for y in range(1, 26)
        )
        total_cost_25y = annual_cost * 25

        # ── 年化投资收益率 ──
        annual_roi = (sum(cashflows[1:]) / years) / invest_total if invest_total > 0 else 0

        return jsonify({
            "ok": True,
            "irr": round(irr_value * 100, 2),          # %形式
            "irr_raw": round(irr_value, 4),
            "payback_years": round(payback_years, 2) if payback_years else None,
            "annual_roi": round(annual_roi * 100, 2),
            "total_net_cf": round(total_net_cf, 2),
            "total_revenue_25y": round(total_revenue_25y, 2),
            "total_cost_25y": round(total_cost_25y, 2),
            "annual_revenue": round(annual_revenue, 2),
            "annual_cost": round(annual_cost, 2),
            "deprec_cost": round(deprec_cost, 2),
            "invest_total": round(invest_total, 2),
            "capacity_kw": round(capacity_kw, 2),
            # 每年现金流明细（用于图表）
            "yearly": [
                {
                    "year": t,
                    "cf": round(cf, 2),
                    "cum_cf": round(sum(cashflows[:t+1]), 2)
                }
                for t, cf in enumerate(cashflows)
            ]
        })

    # ─────────────────────────────────────────────
    # 保存/查询历史方案
    # ─────────────────────────────────────────────
    @app.route("/api/investment/scenarios", methods=["GET"])
    def api_investment_scenarios():
        db = get_db()
        rows = db.execute("""
            SELECT * FROM investment_scenarios
            ORDER BY created_at DESC LIMIT 50
        """).fetchall()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/investment/scenarios", methods=["POST"])
    def api_investment_scenario_save():
        db = get_db()
        data = request.get_json()
        db.execute("""INSERT INTO investment_scenarios
            (name, capacity_kw, invest_total, tariff, annual_gen,
             opex_year, tax_rate, sub_year, sub_per_kwh,
             irr_result, payback_years, note)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (data.get("name"), float(data.get("capacity_kw", 0)),
             float(data.get("invest_total", 0)), float(data.get("tariff", 0)),
             float(data.get("annual_gen", 0)), float(data.get("opex_year", 0)),
             float(data.get("tax_rate", 0)), float(data.get("sub_year", 0)),
             float(data.get("sub_per_kwh", 0)),
             float(data.get("irr_result", 0)), float(data.get("payback_years", 0)),
             data.get("note", "")))
        db.commit()
        return jsonify({"ok": True})

    @app.route("/api/investment/scenarios/<int:sid>", methods=["DELETE"])
    def api_investment_scenario_del(sid):
        db = get_db()
        db.execute("DELETE FROM investment_scenarios WHERE id=?", (sid,))
        db.commit()
        return jsonify({"ok": True})

    # ─────────────────────────────────────────────
    # 确保数据库表存在
    # ─────────────────────────────────────────────
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS investment_scenarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            capacity_kw REAL DEFAULT 0,
            invest_total REAL DEFAULT 0,
            tariff REAL DEFAULT 0,
            annual_gen REAL DEFAULT 0,
            opex_year REAL DEFAULT 0,
            tax_rate REAL DEFAULT 0,
            sub_year REAL DEFAULT 0,
            sub_per_kwh REAL DEFAULT 0,
            irr_result REAL DEFAULT 0,
            payback_years REAL DEFAULT 0,
            note TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    db.commit()
