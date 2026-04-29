"""
净值数据Service - 业务逻辑层
支持4种常见净值文件格式的智能识别和导入
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Tuple, Dict, Any
from fastapi import HTTPException, status, UploadFile
from datetime import datetime, date
import pandas as pd
import io
import os
import shutil

from app.models.nav import NavData
from app.models.product import Product
from app.schemas.nav import NavDataCreate
from app.services.nav_parser import NavDataParser, parse_nav_file, NavFileFormat

# 上传文件保存目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')


def ensure_upload_dir():
    """确保上传目录存在"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)


def delete_old_product_files(product_code: str) -> int:
    """
    删除产品的旧文件，只保留最新的
    
    Args:
        product_code: 产品代码
    
    Returns:
        删除的文件数量
    """
    ensure_upload_dir()
    deleted_count = 0
    
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(f"{product_code}_") and filename != '.gitkeep':
            filepath = os.path.join(UPLOAD_DIR, filename)
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception:
                pass
    
    return deleted_count


def save_uploaded_file(file: UploadFile, product_code: str) -> str:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件
        product_code: 产品代码
    
    Returns:
        保存的文件路径
    """
    ensure_upload_dir()
    
    # 删除旧文件
    delete_old_product_files(product_code)
    
    # 生成新文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = os.path.splitext(file.filename)[1]
    filename = f"{product_code}_{timestamp}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # 保存文件
    file.file.seek(0)
    with open(filepath, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    
    return filepath


def get_product_nav_files(product_code: str) -> List[str]:
    """
    获取产品的所有净值文件
    
    Args:
        product_code: 产品代码
    
    Returns:
        文件路径列表
    """
    ensure_upload_dir()
    files = []
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(f"{product_code}_"):
            files.append(os.path.join(UPLOAD_DIR, filename))
    return sorted(files, reverse=True)  # 按时间倒序


def get_latest_nav_file(product_code: str) -> Optional[str]:
    """
    获取产品最新的净值文件
    
    Args:
        product_code: 产品代码
    
    Returns:
        最新文件路径或None
    """
    files = get_product_nav_files(product_code)
    return files[0] if files else None


def get_nav_data_list(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> Tuple[List[NavData], int]:
    """
    获取净值数据列表
    
    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        product_id: 产品ID筛选
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        (净值数据列表, 总数)
    """
    query = db.query(NavData)
    
    # 产品过滤
    if product_id:
        query = query.filter(NavData.product_id == product_id)
    
    # 日期范围过滤
    if start_date:
        query = query.filter(NavData.nav_date >= start_date)
    if end_date:
        query = query.filter(NavData.nav_date <= end_date)
    
    # 获取总数
    total = query.count()
    
    # 分页查询，按日期倒序
    nav_data = query.order_by(NavData.nav_date.desc()).offset(skip).limit(limit).all()
    
    return nav_data, total


def get_nav_data_by_id(db: Session, nav_id: int) -> Optional[NavData]:
    """根据ID获取净值数据"""
    return db.query(NavData).filter(NavData.id == nav_id).first()


def create_nav_data(db: Session, nav_data: NavDataCreate) -> NavData:
    """
    创建净值数据
    
    Args:
        db: 数据库会话
        nav_data: 净值数据创建数据
    
    Returns:
        创建的净值数据对象
    """
    # 检查产品是否存在
    product = db.query(Product).filter(Product.id == nav_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产品ID {nav_data.product_id} 不存在"
        )
    
    # 检查是否已存在相同日期的数据
    existing = db.query(NavData).filter(
        and_(
            NavData.product_id == nav_data.product_id,
            NavData.nav_date == nav_data.nav_date
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"产品 {nav_data.product_id} 在日期 {nav_data.nav_date} 的净值数据已存在"
        )
    
    # 创建净值数据对象
    db_nav_data = NavData(
        product_id=nav_data.product_id,
        nav_date=nav_data.nav_date,
        unit_nav=nav_data.unit_nav,
        cumulative_nav=nav_data.cumulative_nav
    )
    
    db.add(db_nav_data)
    db.commit()
    db.refresh(db_nav_data)
    
    return db_nav_data


def delete_nav_data(db: Session, nav_id: int) -> bool:
    """删除净值数据"""
    db_nav_data = get_nav_data_by_id(db, nav_id)
    if not db_nav_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"净值数据ID {nav_id} 不存在"
        )
    
    db.delete(db_nav_data)
    db.commit()
    
    return True


def parse_excel_file(file_content: bytes, filename: str) -> pd.DataFrame:
    """
    解析Excel文件
    
    Args:
        file_content: 文件内容
        filename: 文件名
    
    Returns:
        解析后的DataFrame
    """
    try:
        # 读取Excel文件
        excel_data = io.BytesIO(file_content)
        
        # 尝试不同的读取方式
        # 方式1: 直接读取
        df = pd.read_excel(excel_data, engine='openpyxl' if filename.endswith('.xlsx') else 'xlrd')
        
        # 检查列名，判断是否需要跳过第一行
        if '产品净值数据' in df.columns or 'Unnamed' in str(df.columns):
            # 需要跳过第一行
            excel_data.seek(0)
            df = pd.read_excel(
                excel_data,
                skiprows=1,
                engine='openpyxl' if filename.endswith('.xlsx') else 'xlrd'
            )
        
        return df
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Excel文件解析失败: {str(e)}"
        )


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    标准化DataFrame列名和数据
    
    Args:
        df: 原始DataFrame
    
    Returns:
        标准化后的DataFrame
    """
    # 标准化列名（去除空格和单位）
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(r'\s*\(.*?\)', '', regex=True)
    
    # 统一列名
    column_mapping = {
        '产品代码': 'product_code',
        '产品名称': 'product_name',
        '净值日期': 'nav_date',
        '单位净值': 'unit_nav',
        '累计净值': 'cumulative_nav',
        '累计单位净值': 'cumulative_nav'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 检查必需列
    required_columns = ['nav_date', 'unit_nav']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"缺少必需列: {', '.join(missing_columns)}"
        )
    
    # 转换日期格式
    df['nav_date'] = pd.to_datetime(df['nav_date']).dt.date
    
    # 确保净值为数值类型
    df['unit_nav'] = pd.to_numeric(df['unit_nav'], errors='coerce')
    if 'cumulative_nav' in df.columns:
        df['cumulative_nav'] = pd.to_numeric(df['cumulative_nav'], errors='coerce')
    
    # 删除无效行（净值为空或非正数）
    df = df[df['unit_nav'].notna() & (df['unit_nav'] > 0)]
    
    return df


def import_nav_data_from_excel(
    db: Session,
    file: UploadFile,
    product_id: Optional[int] = None,
    product_code: Optional[str] = None,
    skip_duplicates: bool = True,
    update_existing: bool = False,
    auto_detect_product: bool = False
) -> dict:
    """
    从Excel文件导入净值数据（支持4种格式智能识别）
    
    Args:
        db: 数据库会话
        file: 上传的文件
        product_id: 产品ID
        product_code: 产品代码
        skip_duplicates: 是否跳过重复数据
        update_existing: 是否更新已存在的数据
        auto_detect_product: 是否从文件中自动识别产品
    
    Returns:
        导入结果字典
    """
    # 读取文件内容
    file_content = file.file.read()
    
    # 使用智能解析器解析文件
    success, df, parse_info = parse_nav_file(file_content, file.filename)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件解析失败: {parse_info.get('errors', ['未知错误'])}"
        )
    
    
    # 确定产品
    product = None
    
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
    elif product_code:
        product = db.query(Product).filter(Product.product_code == product_code).first()
    elif auto_detect_product and 'product_code' in df.columns:
        # 从文件中自动识别产品代码
        detected_codes = df['product_code'].dropna().unique().tolist()
        if len(detected_codes) == 1:
            product = db.query(Product).filter(Product.product_code == detected_codes[0]).first()
            if product:
                pass
        elif len(detected_codes) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件包含多个产品代码: {detected_codes}，请指定product_id或product_code"
            )
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="产品不存在，请提供有效的product_id或product_code"
        )
    
    # 保存上传的文件到 uploads 目录
    file.file.seek(0)
    saved_filepath = save_uploaded_file(file, product.product_code)
    
    # 导入统计
    total_rows = len(df)
    imported_rows = 0
    skipped_rows = 0
    updated_rows = 0
    error_rows = 0
    errors = []
    
    # 逐行导入
    for index, row in df.iterrows():
        try:
            nav_date = row['nav_date']
            unit_nav = float(row['unit_nav'])
            cumulative_nav = float(row['cumulative_nav']) if 'cumulative_nav' in row and pd.notna(row['cumulative_nav']) else None
            adjusted_nav = float(row['adjusted_nav']) if 'adjusted_nav' in row and pd.notna(row['adjusted_nav']) else None
            
            # 检查是否已存在
            existing = db.query(NavData).filter(
                and_(
                    NavData.product_id == product.id,
                    NavData.nav_date == nav_date
                )
            ).first()
            
            if existing:
                if update_existing:
                    # 更新现有数据
                    existing.unit_nav = unit_nav
                    if cumulative_nav is not None:
                        existing.cumulative_nav = cumulative_nav
                    if adjusted_nav is not None:
                        existing.adjusted_nav = adjusted_nav
                    updated_rows += 1
                elif skip_duplicates:
                    skipped_rows += 1
                else:
                    error_rows += 1
                    errors.append(f"第{index+1}行: 日期{nav_date}的数据已存在")
            else:
                # 创建新数据
                nav_data = NavData(
                    product_id=product.id,
                    nav_date=nav_date,
                    unit_nav=unit_nav,
                    cumulative_nav=cumulative_nav,
                    adjusted_nav=adjusted_nav,
                    data_source='excel_import'
                )
                db.add(nav_data)
                imported_rows += 1
                
        except Exception as e:
            error_rows += 1
            errors.append(f"第{index+1}行: {str(e)}")
    
    # 提交事务
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据库提交失败: {str(e)}"
        )
    
    # 构建返回结果
    result = {
        "success": error_rows == 0,
        "message": f"成功导入{imported_rows}条数据" + (f"，更新{updated_rows}条" if updated_rows > 0 else ""),
        "format_detected": parse_info.get('format'),
        "total_rows": total_rows,
        "imported_rows": imported_rows,
        "updated_rows": updated_rows,
        "skipped_rows": skipped_rows,
        "error_rows": error_rows,
        "errors": errors[:10],
        "warnings": parse_info.get('warnings', []),
        "date_range": parse_info.get('date_range'),
        "saved_file": saved_filepath
    }
    
    return result


def get_nav_statistics(db: Session, product_id: int) -> dict:
    """
    获取产品净值统计信息
    
    Args:
        db: 数据库会话
        product_id: 产品ID
    
    Returns:
        统计信息字典
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"产品ID {product_id} 不存在"
        )
    
    # 统计信息
    total_records = db.query(NavData).filter(NavData.product_id == product_id).count()
    
    if total_records == 0:
        return {
            "product_id": product_id,
            "product_name": product.product_name,
            "total_records": 0,
            "start_date": None,
            "end_date": None,
            "latest_unit_nav": None,
            "latest_cumulative_nav": None,
            "latest_nav_date": None
        }
    
    # 日期范围
    date_range = db.query(
        func.min(NavData.nav_date).label('start_date'),
        func.max(NavData.nav_date).label('end_date')
    ).filter(NavData.product_id == product_id).first()
    
    # 最新净值
    latest_nav = db.query(NavData).filter(
        NavData.product_id == product_id
    ).order_by(NavData.nav_date.desc()).first()
    
    return {
        "product_id": product_id,
        "product_name": product.product_name,
        "total_records": total_records,
        "start_date": date_range.start_date,
        "end_date": date_range.end_date,
        "latest_unit_nav": latest_nav.unit_nav if latest_nav else None,
        "latest_cumulative_nav": latest_nav.cumulative_nav if latest_nav else None,
        "latest_nav_date": latest_nav.nav_date if latest_nav else None
    }


def preview_nav_file(file_content: bytes, filename: str, preview_rows: int = 10) -> Dict[str, Any]:
    """
    预览净值文件解析结果
    
    Args:
        file_content: 文件内容
        filename: 文件名
        preview_rows: 预览行数
    
    Returns:
        预览结果字典
    """
    success, df, parse_info = parse_nav_file(file_content, filename)
    
    if not success:
        return {
            "success": False,
            "format_detected": parse_info.get('format', 'unknown'),
            "errors": parse_info.get('errors', []),
            "preview_data": []
        }
    
    # 获取预览数据
    preview_df = df.head(preview_rows)
    preview_data = []
    
    for _, row in preview_df.iterrows():
        item = {
            "nav_date": str(row['nav_date']) if 'nav_date' in row else None,
            "unit_nav": float(row['unit_nav']) if 'unit_nav' in row and pd.notna(row['unit_nav']) else None,
            "cumulative_nav": float(row['cumulative_nav']) if 'cumulative_nav' in row and pd.notna(row['cumulative_nav']) else None,
        }
        if 'product_code' in row:
            item['product_code'] = str(row['product_code']) if pd.notna(row['product_code']) else None
        if 'product_name' in row:
            item['product_name'] = str(row['product_name']) if pd.notna(row['product_name']) else None
        preview_data.append(item)
    
    # 获取产品信息
    product_codes = df['product_code'].dropna().unique().tolist() if 'product_code' in df.columns else []
    product_names = df['product_name'].dropna().unique().tolist() if 'product_name' in df.columns else []
    
    return {
        "success": True,
        "format_detected": parse_info.get('format'),
        "total_rows": parse_info.get('total_rows', 0),
        "columns": parse_info.get('columns', []),
        "date_range": parse_info.get('date_range'),
        "product_codes": product_codes,
        "product_names": product_names,
        "warnings": parse_info.get('warnings', []),
        "preview_data": preview_data
    }


def batch_import_nav_files(
    db: Session,
    files: List[UploadFile],
    skip_duplicates: bool = True,
    update_existing: bool = False,
    auto_detect_product: bool = True
) -> Dict[str, Any]:
    """
    批量导入多个净值文件
    
    Args:
        db: 数据库会话
        files: 上传的文件列表
        skip_duplicates: 是否跳过重复数据
        update_existing: 是否更新已存在的数据
        auto_detect_product: 是否从文件中自动识别产品
    
    Returns:
        批量导入结果
    """
    results = []
    total_imported = 0
    total_errors = 0
    
    for file in files:
        try:
            result = import_nav_data_from_excel(
                db=db,
                file=file,
                skip_duplicates=skip_duplicates,
                update_existing=update_existing,
                auto_detect_product=auto_detect_product
            )
            results.append({
                "filename": file.filename,
                "success": result.get('success', False),
                "imported_rows": result.get('imported_rows', 0),
                "message": result.get('message', '')
            })
            total_imported += result.get('imported_rows', 0)
        except HTTPException as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "imported_rows": 0,
                "message": str(e.detail)
            })
            total_errors += 1
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "imported_rows": 0,
                "message": str(e)
            })
            total_errors += 1
    
    return {
        "success": total_errors == 0,
        "total_files": len(files),
        "successful_files": len(files) - total_errors,
        "failed_files": total_errors,
        "total_imported_rows": total_imported,
        "results": results
    }
