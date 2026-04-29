"""
数据清洗服务 - 净值数据质量检测与清洗
支持异常值检测、重复数据清理、缺失值处理
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Any
from datetime import date, timedelta
import math

from app.models.nav import NavData
from app.models.product import Product


class DataCleaningService:
    """净值数据清洗服务"""

    def __init__(self, db: Session):
        self.db = db

    def analyze_data_quality(self, product_id: int) -> Dict[str, Any]:
        """
        分析产品净值数据质量

        Returns:
            数据质量报告
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return {"error": f"产品ID {product_id} 不存在"}

        nav_list = self.db.query(NavData).filter(
            NavData.product_id == product_id
        ).order_by(NavData.nav_date.asc()).all()

        total_records = len(nav_list)
        if total_records == 0:
            return {
                "product_id": product_id,
                "product_name": product.product_name,
                "total_records": 0,
                "issues": [],
                "summary": {"score": 100, "level": "无数据"}
            }

        # 1. 重复数据检测
        duplicates = self._detect_duplicates(nav_list)

        # 2. 异常值检测 (IQR方法)
        outliers = self._detect_outliers(nav_list)

        # 3. 缺失值/日期间隔检测
        gaps = self._detect_date_gaps(nav_list)

        # 4. 负净值或零净值检测
        invalid_nav = self._detect_invalid_nav(nav_list)

        # 5. 净值跳跃检测 (单日涨跌幅>20%)
        jumps = self._detect_nav_jumps(nav_list)

        # 汇总所有问题
        issues = []
        issues.extend([{"type": "duplicate", "severity": "warning", **d} for d in duplicates])
        issues.extend([{"type": "outlier", "severity": "error", **o} for o in outliers])
        issues.extend([{"type": "gap", "severity": "info", **g} for g in gaps])
        issues.extend([{"type": "invalid", "severity": "error", **iv} for iv in invalid_nav])
        issues.extend([{"type": "jump", "severity": "warning", **j} for j in jumps])

        # 计算质量评分 (满分100)
        issue_count = len(issues)
        error_count = sum(1 for i in issues if i["severity"] == "error")
        warning_count = sum(1 for i in issues if i["severity"] == "warning")

        score = max(0, 100 - error_count * 10 - warning_count * 3 - (issue_count - error_count - warning_count))
        if score >= 90:
            level = "优秀"
        elif score >= 70:
            level = "良好"
        elif score >= 50:
            level = "一般"
        else:
            level = "较差"

        # 日期范围
        date_range = {
            "start": str(nav_list[0].nav_date) if nav_list else None,
            "end": str(nav_list[-1].nav_date) if nav_list else None
        }

        return {
            "product_id": product_id,
            "product_name": product.product_name,
            "total_records": total_records,
            "date_range": date_range,
            "issues": issues,
            "issue_summary": {
                "total": issue_count,
                "errors": error_count,
                "warnings": warning_count,
                "info": issue_count - error_count - warning_count
            },
            "summary": {
                "score": score,
                "level": level,
                "duplicates": len(duplicates),
                "outliers": len(outliers),
                "gaps": len(gaps),
                "invalid_nav": len(invalid_nav),
                "jumps": len(jumps)
            }
        }

    def clean_data(
        self,
        product_id: int,
        remove_duplicates: bool = True,
        remove_outliers: bool = False,
        fill_missing: bool = False
    ) -> Dict[str, Any]:
        """
        执行数据清洗

        Args:
            product_id: 产品ID
            remove_duplicates: 是否删除重复数据
            remove_outliers: 是否删除异常值
            fill_missing: 是否填充缺失值（线性插值）

        Returns:
            清洗结果报告
        """
        nav_list = self.db.query(NavData).filter(
            NavData.product_id == product_id
        ).order_by(NavData.nav_date.asc()).all()

        if not nav_list:
            return {"message": "无数据", "cleaned": 0}

        removed_count = 0
        filled_count = 0

        # 1. 删除重复数据（保留最新的）
        if remove_duplicates:
            duplicates = self._detect_duplicates(nav_list)
            dup_ids = [d["id"] for d in duplicates]
            if dup_ids:
                self.db.query(NavData).filter(NavData.id.in_(dup_ids)).delete(synchronize_session=False)
                removed_count += len(dup_ids)

        # 2. 删除异常值
        if remove_outliers:
            outliers = self._detect_outliers(nav_list)
            outlier_ids = [o["id"] for o in outliers]
            if outlier_ids:
                self.db.query(NavData).filter(NavData.id.in_(outlier_ids)).delete(synchronize_session=False)
                removed_count += len(outlier_ids)

        # 3. 填充缺失日期（线性插值）
        if fill_missing:
            gaps = self._detect_date_gaps(nav_list)
            for gap in gaps:
                filled_count += self._fill_gap(product_id, gap)

        self.db.commit()

        return {
            "product_id": product_id,
            "removed_count": removed_count,
            "filled_count": filled_count,
            "message": f"清洗完成：删除{removed_count}条，填充{filled_count}条"
        }

    def _detect_duplicates(self, nav_list: List[NavData]) -> List[Dict]:
        """检测重复数据（同一产品同一日期多条记录）"""
        date_map: Dict[str, List[NavData]] = {}
        for nav in nav_list:
            key = str(nav.nav_date)
            if key not in date_map:
                date_map[key] = []
            date_map[key].append(nav)

        duplicates = []
        for date_str, records in date_map.items():
            if len(records) > 1:
                # 保留第一条（最早插入的），标记其余为重复
                for r in records[1:]:
                    duplicates.append({
                        "id": r.id,
                        "nav_date": date_str,
                        "unit_nav": float(r.unit_nav) if r.unit_nav else None,
                        "message": f"日期{date_str}存在{len(records)}条重复数据"
                    })
        return duplicates

    def _detect_outliers(self, nav_list: List[NavData]) -> List[Dict]:
        """使用IQR方法检测异常值"""
        if len(nav_list) < 10:
            return []

        values = [float(n.unit_nav) for n in nav_list if n.unit_nav and float(n.unit_nav) > 0]
        if len(values) < 10:
            return []

        values_sorted = sorted(values)
        n = len(values_sorted)
        q1 = values_sorted[n // 4]
        q3 = values_sorted[3 * n // 4]
        iqr = q3 - q1

        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr

        outliers = []
        for nav in nav_list:
            val = float(nav.unit_nav) if nav.unit_nav else 0
            if val < lower_bound or val > upper_bound:
                outliers.append({
                    "id": nav.id,
                    "nav_date": str(nav.nav_date),
                    "unit_nav": val,
                    "message": f"净值{val:.4f}超出合理范围[{lower_bound:.4f}, {upper_bound:.4f}]"
                })
        return outliers

    def _detect_date_gaps(self, nav_list: List[NavData]) -> List[Dict]:
        """检测日期缺失（周频数据>10天间隔，日频数据>5天间隔）"""
        if len(nav_list) < 2:
            return []

        # 计算平均间隔来判断频率
        dates = [n.nav_date for n in nav_list]
        total_days = (dates[-1] - dates[0]).days
        avg_interval = total_days / max(len(dates) - 1, 1)

        # 根据平均间隔判断：日频(<3天)还是周频(<10天)
        threshold = 5 if avg_interval < 3 else 15

        gaps = []
        for i in range(1, len(nav_list)):
            d1 = nav_list[i - 1].nav_date
            d2 = nav_list[i].nav_date
            gap_days = (d2 - d1).days
            if gap_days > threshold:
                gaps.append({
                    "start_date": str(d1),
                    "end_date": str(d2),
                    "gap_days": gap_days,
                    "start_nav": float(nav_list[i - 1].unit_nav) if nav_list[i - 1].unit_nav else None,
                    "end_nav": float(nav_list[i].unit_nav) if nav_list[i].unit_nav else None,
                    "message": f"{d1}至{d2}间隔{gap_days}天，可能存在数据缺失"
                })
        return gaps

    def _detect_invalid_nav(self, nav_list: List[NavData]) -> List[Dict]:
        """检测无效净值（负值、零值、NULL）"""
        invalid = []
        for nav in nav_list:
            val = float(nav.unit_nav) if nav.unit_nav else None
            if val is None:
                invalid.append({
                    "id": nav.id,
                    "nav_date": str(nav.nav_date),
                    "unit_nav": None,
                    "message": f"日期{nav.nav_date}净值为空"
                })
            elif val <= 0:
                invalid.append({
                    "id": nav.id,
                    "nav_date": str(nav.nav_date),
                    "unit_nav": val,
                    "message": f"日期{nav.nav_date}净值为{val:.4f}（非正数）"
                })
        return invalid

    def _detect_nav_jumps(self, nav_list: List[NavData]) -> List[Dict]:
        """检测净值跳跃（单期涨跌幅>20%）"""
        jumps = []
        for i in range(1, len(nav_list)):
            prev = float(nav_list[i - 1].unit_nav) if nav_list[i - 1].unit_nav else 0
            curr = float(nav_list[i].unit_nav) if nav_list[i].unit_nav else 0
            if prev > 0 and curr > 0:
                change = (curr - prev) / prev
                if abs(change) > 0.20:
                    jumps.append({
                        "id": nav_list[i].id,
                        "nav_date": str(nav_list[i].nav_date),
                        "unit_nav": curr,
                        "prev_nav": prev,
                        "change_pct": round(change * 100, 2),
                        "message": f"日期{nav_list[i].nav_date}净值变动{change*100:.2f}%（前值{prev:.4f}→{curr:.4f}）"
                    })
        return jumps

    def _fill_gap(self, product_id: int, gap: Dict) -> int:
        """线性插值填充缺失日期"""
        start_date = date.fromisoformat(gap["start_date"])
        end_date = date.fromisoformat(gap["end_date"])
        start_nav = gap.get("start_nav")
        end_nav = gap.get("end_nav")

        if not start_nav or not end_nav:
            return 0

        gap_days = (end_date - start_date).days
        if gap_days <= 1:
            return 0

        filled = 0
        for i in range(1, gap_days):
            fill_date = start_date + timedelta(days=i)
            # 跳过周末
            if fill_date.weekday() >= 5:
                continue

            # 检查是否已存在
            existing = self.db.query(NavData).filter(
                and_(NavData.product_id == product_id, NavData.nav_date == fill_date)
            ).first()
            if existing:
                continue

            # 线性插值
            ratio = i / gap_days
            interpolated_nav = start_nav + (end_nav - start_nav) * ratio

            nav_data = NavData(
                product_id=product_id,
                nav_date=fill_date,
                unit_nav=round(interpolated_nav, 6),
                data_source="interpolation"
            )
            self.db.add(nav_data)
            filled += 1

        return filled
