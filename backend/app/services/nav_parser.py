"""
净值数据智能解析器 - 支持4种常见格式自动识别
"""
import pandas as pd
import io
import re
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class NavFileFormat(Enum):
    """净值文件格式类型"""
    FORMAT_A = "format_a"  # 标题行+数据行（第一行是"产品净值数据"）
    FORMAT_B = "format_b"  # 直接数据行（列名带单位）
    FORMAT_C = "format_c"  # 列顺序不同（产品名称在前）
    FORMAT_D = "format_d"  # 中英文双语表头
    UNKNOWN = "unknown"


class NavDataParser:
    """净值数据智能解析器"""
    
    # 列名映射表
    COLUMN_MAPPINGS = {
        # 产品代码
        'product_code': ['产品代码', '基金代码', 'product_code', 'fund_code', 'code', '协会备案编码'],
        # 产品名称
        'product_name': ['产品名称', '基金名称', 'product_name', 'fund_name', 'name'],
        # 净值日期
        'nav_date': ['净值日期', '日期', 'nav_date', 'date', '估值日期'],
        # 单位净值 - 注意顺序，更具体的放前面
        'unit_nav': ['单位净值', '净值', 'unit_nav', 'nav'],
        # 累计净值 - 累计单位净值要放在前面优先匹配
        'cumulative_nav': ['累计单位净值', '累计净值', 'cumulative_nav', 'cum_nav'],
        # 复权净值
        'adjusted_nav': ['复权净值', '复权单位净值', 'adjusted_nav'],
    }
    
    def __init__(self, file_content: bytes, filename: str):
        self.file_content = file_content
        self.filename = filename
        self.format_type: NavFileFormat = NavFileFormat.UNKNOWN
        self.raw_df: Optional[pd.DataFrame] = None
        self.parsed_df: Optional[pd.DataFrame] = None
        self.parse_errors: List[str] = []
        self.parse_warnings: List[str] = []
        
    def detect_format(self) -> NavFileFormat:
        """检测文件格式类型"""
        try:
            excel_data = io.BytesIO(self.file_content)
            engine = 'openpyxl' if self.filename.endswith('.xlsx') else 'xlrd'
            
            # 读取前10行用于格式检测
            df_preview = pd.read_excel(excel_data, nrows=10, header=None, engine=engine)
            
            # 检查第一行内容
            first_row = df_preview.iloc[0].astype(str).tolist()
            first_cell = str(first_row[0]).strip() if first_row else ""
            
            # 格式D: 中英文双语（第一行是"净值浏览表"或包含英文）
            if '净值浏览表' in first_cell or 'NAV' in first_cell.upper():
                self.format_type = NavFileFormat.FORMAT_D
                return self.format_type
            
            # 格式A: 标题行+数据行（第一行是"产品净值数据"）
            if '产品净值数据' in first_cell or '净值数据' in first_cell:
                self.format_type = NavFileFormat.FORMAT_A
                return self.format_type
            
            # 检查第一行是否是表头
            header_keywords = ['产品代码', '产品名称', '净值日期', '单位净值', '基金代码', '基金名称']
            first_row_str = ' '.join([str(x) for x in first_row])
            
            if any(kw in first_row_str for kw in header_keywords):
                # 格式B或C: 直接数据行
                # 区分B和C: B的列名可能带单位，C的产品名称在前
                if '产品名称' in first_cell or '基金名称' in first_cell:
                    self.format_type = NavFileFormat.FORMAT_C
                else:
                    self.format_type = NavFileFormat.FORMAT_B
                return self.format_type
            
            # 默认尝试格式B
            self.format_type = NavFileFormat.FORMAT_B
            return self.format_type
            
        except Exception as e:
            self.parse_errors.append(f"格式检测失败: {str(e)}")
            self.format_type = NavFileFormat.UNKNOWN
            return self.format_type
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """找到表头所在行"""
        header_keywords = ['产品代码', '产品名称', '净值日期', '单位净值', 'Fund Name', 'NAV']
        
        for idx in range(min(10, len(df))):
            row_values = df.iloc[idx].tolist()
            row_str = ' '.join([str(x).replace('\n', ' ') for x in row_values if pd.notna(x)])
            # 检查是否包含多个关键词（至少2个），这样更准确
            keyword_count = sum(1 for kw in header_keywords if kw in row_str)
            if keyword_count >= 2:
                return idx
        return 0
    
    def _clean_column_name(self, col_name: str) -> str:
        """清理列名"""
        if pd.isna(col_name):
            return ""
        col_name = str(col_name).strip()
        # 移除换行符和多余空格
        col_name = col_name.replace('\n', ' ')
        col_name = re.sub(r'\s+', ' ', col_name)
        # 移除括号内的单位说明
        col_name = re.sub(r'\s*[\(（].*?[\)）]', '', col_name)
        # 移除英文部分（如果有中文）
        if re.search(r'[\u4e00-\u9fff]', col_name):
            # 保留中文部分
            chinese_parts = re.findall(r'[\u4e00-\u9fff]+', col_name)
            if chinese_parts:
                col_name = ''.join(chinese_parts)
        return col_name.strip()
    
    def _map_column_name(self, col_name: str) -> Optional[str]:
        """将原始列名映射到标准列名"""
        cleaned = self._clean_column_name(col_name)
        
        # 优先匹配更长的别名（更具体的）
        best_match = None
        best_match_len = 0
        
        for standard_name, aliases in self.COLUMN_MAPPINGS.items():
            for alias in aliases:
                alias_cleaned = self._clean_column_name(alias)
                # 精确匹配优先
                if cleaned == alias_cleaned:
                    return standard_name
                # 包含匹配，选择最长的匹配
                if alias_cleaned in cleaned and len(alias_cleaned) > best_match_len:
                    best_match = standard_name
                    best_match_len = len(alias_cleaned)
        
        return best_match
    
    def parse(self) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
        """
        解析净值文件
        
        Returns:
            (成功标志, 解析后的DataFrame, 解析信息)
        """
        # 检测格式
        self.detect_format()
        
        if self.format_type == NavFileFormat.UNKNOWN:
            return False, pd.DataFrame(), {
                "format": "unknown",
                "errors": self.parse_errors
            }
        
        try:
            excel_data = io.BytesIO(self.file_content)
            engine = 'openpyxl' if self.filename.endswith('.xlsx') else 'xlrd'
            
            # 先读取原始数据用于分析
            df_raw = pd.read_excel(io.BytesIO(self.file_content), header=None, engine=engine)
            
            # 找到真正的表头行
            header_row = self._find_header_row(df_raw)
            
            # 重新读取，使用正确的表头行
            excel_data.seek(0)
            self.raw_df = pd.read_excel(excel_data, skiprows=header_row, engine=engine)
            
            # 映射列名
            column_mapping = {}
            for col in self.raw_df.columns:
                mapped = self._map_column_name(str(col))
                if mapped:
                    column_mapping[col] = mapped
            
            # 重命名列
            df = self.raw_df.rename(columns=column_mapping)
            
            # 检查必需列
            required_cols = ['nav_date', 'unit_nav']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                self.parse_errors.append(f"缺少必需列: {missing_cols}")
                # 尝试从产品代码或名称列推断
                if 'product_code' not in df.columns and 'product_name' not in df.columns:
                    self.parse_errors.append("无法识别产品信息列")
                return False, pd.DataFrame(), {
                    "format": self.format_type.value,
                    "errors": self.parse_errors
                }
            
            # 数据清洗
            df = self._clean_data(df.copy())
            
            self.parsed_df = df
            
            return True, df, {
                "format": self.format_type.value,
                "total_rows": len(df),
                "columns": list(df.columns),
                "date_range": {
                    "start": str(df['nav_date'].min()) if 'nav_date' in df.columns and len(df) > 0 else None,
                    "end": str(df['nav_date'].max()) if 'nav_date' in df.columns and len(df) > 0 else None
                },
                "warnings": self.parse_warnings,
                "errors": self.parse_errors
            }
            
        except Exception as e:
            self.parse_errors.append(f"解析失败: {str(e)}")
            return False, pd.DataFrame(), {
                "format": self.format_type.value,
                "errors": self.parse_errors
            }
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        # 删除全空行
        df = df.dropna(how='all').copy()
        
        # 删除重复的列名（保留第一个）
        df = df.loc[:, ~df.columns.duplicated()]
        
        # 转换日期
        if 'nav_date' in df.columns:
            # 先尝试转换为datetime
            try:
                df.loc[:, 'nav_date'] = pd.to_datetime(df['nav_date'], errors='coerce')
            except Exception:
                pass
            
            # 检查是否成功转换为datetime
            if pd.api.types.is_datetime64_any_dtype(df['nav_date']):
                # 删除日期无效的行
                invalid_dates = df['nav_date'].isna().sum()
                if invalid_dates > 0:
                    self.parse_warnings.append(f"跳过{invalid_dates}行无效日期数据")
                df = df[df['nav_date'].notna()].copy()
                # 提取date部分
                df.loc[:, 'nav_date'] = df['nav_date'].dt.date
            else:
                # 如果不是datetime类型，尝试直接转换
                try:
                    df.loc[:, 'nav_date'] = pd.to_datetime(df['nav_date'].astype(str), errors='coerce').dt.date
                    df = df[df['nav_date'].notna()].copy()
                except Exception as e:
                    self.parse_warnings.append(f"日期转换警告: {str(e)}")
        
        # 转换净值为数值
        for col in ['unit_nav', 'cumulative_nav', 'adjusted_nav']:
            if col in df.columns:
                df.loc[:, col] = pd.to_numeric(df[col], errors='coerce')
        
        # 删除单位净值无效的行
        if 'unit_nav' in df.columns:
            invalid_nav = df['unit_nav'].isna().sum()
            if invalid_nav > 0:
                self.parse_warnings.append(f"跳过{invalid_nav}行无效净值数据")
            df = df[df['unit_nav'].notna() & (df['unit_nav'] > 0)].copy()
        
        # 清理产品代码（去除括号内容如"(总)"）
        if 'product_code' in df.columns:
            df.loc[:, 'product_code'] = df['product_code'].astype(str).str.replace(r'\(.*?\)', '', regex=True).str.strip()
        
        return df
    
    def get_product_info(self) -> Dict[str, Any]:
        """获取文件中的产品信息"""
        if self.parsed_df is None or len(self.parsed_df) == 0:
            return {}
        
        df = self.parsed_df
        result = {}
        
        if 'product_code' in df.columns:
            codes = df['product_code'].dropna().unique().tolist()
            result['product_codes'] = codes
        
        if 'product_name' in df.columns:
            names = df['product_name'].dropna().unique().tolist()
            result['product_names'] = names
        
        return result


def parse_nav_file(file_content: bytes, filename: str) -> Tuple[bool, pd.DataFrame, Dict[str, Any]]:
    """
    解析净值文件的便捷函数
    
    Args:
        file_content: 文件内容
        filename: 文件名
    
    Returns:
        (成功标志, 解析后的DataFrame, 解析信息)
    """
    parser = NavDataParser(file_content, filename)
    return parser.parse()
