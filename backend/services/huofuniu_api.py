"""
火富牛API数据服务
提供私募基金数据的底层数据接口
"""
import requests
import json
from typing import Dict, List, Optional
import time
from datetime import datetime


class HuoFuNiuAPI:
    """火富牛API客户端"""
    
    BASE_URL = "https://mapi.huofuniu.com/goapi"
    
    # 净值数据API的基础URL（不同域名）
    NAV_BASE_URL = "https://pyapi.huofuniu.com/pyapi"
    
    def __init__(self, access_token: str = None, device_id: str = None):
        """
        初始化API客户端
        
        参数:
            access_token: 访问令牌（可选，如果不提供则使用默认）
            device_id: 设备ID（可选）
        """
        self.access_token = access_token or "6b78c78277401603ad60da1789d97e1eadf6a986fe7f6e6b14fa079a0caf9532d99db8a73c6c4ef1050fed145daea374"
        self.device_id = device_id or "5c3d3c3c43f5e0378e1dba7718cfbeaa"
        
        self.headers = {
            'User-Agent': "App/iOS-2.15.1",
            'content-type': "application/json; charset=UTF-8",
            'accept-language': "zh-CN,zh-Hans;q=0.9",
            'access-token': self.access_token,
            'x-device-id': self.device_id,
            'priority': "u=3, i"
        }
    
    def get_fund_list(
        self, 
        page: int = 1, 
        pagesize: int = 20,
        order_by: str = "price_date",
        order: int = 1,
        strategy: List[str] = None,
        year: str = "0",
        cycle_type: int = 0,
        key_value: str = ""
    ) -> Dict:
        """
        获取私募基金列表
        
        参数:
            page: 页码
            pagesize: 每页数量
            order_by: 排序字段 (price_date/return_rate等)
            order: 排序方式 (1=降序, 0=升序)
            strategy: 策略筛选 (如: ["股票多头", "量化策略"])
            year: 年份筛选 ("0"=全部)
            cycle_type: 周期类型
            key_value: 搜索关键词
        
        返回:
            包含基金列表的字典
        """
        url = f"{self.BASE_URL}/home/sm/list"
        
        payload = {
            "order": order,
            "order_by": order_by,
            "page": page,
            "pagesize": pagesize,
            "keyValue": key_value,
            "strategy": strategy or [],
            "fields": [],
            "year": year,
            "cycle_type": cycle_type,
            "price_date": "0"
        }
        
        try:
            response = requests.post(
                url, 
                json=payload,  # 使用json参数自动序列化
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # 统一返回格式，兼容error_code和code
            if "error_code" in result:
                result["code"] = result["error_code"]
            
            return result
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_fund_detail(self, fund_id: str) -> Dict:
        """
        获取基金详情（包含管理人名称）
        
        参数:
            fund_id: 基金ID
        
        返回:
            基金详情字典，包含 advisor (管理人名称) 等完整信息
        """
        url = f"{self.BASE_URL}/funds/analyze"
        
        params = {
            "id": fund_id
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_fund_scale(self, fund_id: str, start_date: str = None, end_date: str = None) -> Dict:
        """
        获取基金规模历史数据
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        返回:
            规模历史数据字典
        """
        url = f"{self.BASE_URL}/fund/scale/list"
        
        params = {
            "fid": fund_id,
            "start_time": start_date or "",
            "end_time": end_date or ""
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_fund_nav_v2(self, fund_id: str, pt: int = 1) -> Dict:
        """
        获取基金净值曲线数据（V2版本，包含完整业绩分析）
        
        参数:
            fund_id: 基金ID
            pt: 数据类型 (1=默认)
        
        返回:
            包含净值曲线、业绩指标、回撤分析等完整数据
            - fund: 基金净值和业绩数据
            - index: 对比指数数据
            - excess_prices: 超额收益曲线
        """
        url = f"{self.NAV_BASE_URL}/fund/viewv2"
        
        params = {
            "fid": fund_id,
            "pt": pt
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_fund_nav(self, fund_id: str, start_date: str = None, end_date: str = None) -> Dict:
        """
        获取基金净值数据
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        返回:
            净值数据字典
        """
        url = f"{self.BASE_URL}/home/sm/nav"
        
        payload = {
            "id": fund_id,
            "start_date": start_date or "",
            "end_date": end_date or ""
        }
        
        try:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_manager_info(self, manager_id: str) -> Dict:
        """
        获取管理人信息
        
        参数:
            manager_id: 管理人ID
        
        返回:
            管理人信息字典
        """
        url = f"{self.BASE_URL}/home/manager/detail"
        
        payload = {
            "id": manager_id
        }
        
        try:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"code": -1, "msg": str(e)}
    
    def get_company_detail(self, company_id: str) -> Dict:
        """
        获取企业（管理人）详情
        
        参数:
            company_id: 企业ID
        
        返回:
            企业详情字典，包含：
            - 基本信息：名称、注册资本、成立日期等
            - 业务信息：管理规模、基金数量、策略等
            - 工商信息：法人、注册地址、经营范围等
            - 代表产品列表
        """
        url = f"{self.BASE_URL}/home/common/company/detail"
        
        params = {
            "token": self.access_token,
            "id": company_id,
            "type": "1"
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_company_changes(self, company_id: str, page: int = 1, pagesize: int = 10) -> Dict:
        """
        获取企业变更记录
        
        参数:
            company_id: 企业ID
            page: 页码
            pagesize: 每页数量
        
        返回:
            企业变更记录列表，包含：
            - 变更项目（注册资本、股东、章程等）
            - 变更前后内容
            - 变更日期
        """
        url = f"{self.BASE_URL}/enterprise/change"
        
        params = {
            "id": company_id,
            "page": str(page),
            "pagesize": str(pagesize)
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_company_shareholders(self, company_id: str, page: int = 1, pagesize: int = 10) -> Dict:
        """
        获取企业股东信息
        
        参数:
            company_id: 企业ID
            page: 页码
            pagesize: 每页数量
        
        返回:
            股东信息列表，包含：
            - 股东名称
            - 股东类型（自然人/法人）
            - 持股比例
            - 认缴出资额
            - 实缴出资额
        """
        url = f"{self.BASE_URL}/enterprise/shareholder"
        
        params = {
            "id": company_id,
            "page": str(page),
            "pagesize": str(pagesize)
        }
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_drawdown_list(
        self, 
        fund_id: str, 
        start_date: str = None, 
        end_date: str = None,
        pt: int = 1,
        cycle: int = 0,
        refer: str = None
    ) -> Dict:
        """
        获取基金回撤列表
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            pt: 数据类型，默认1
            cycle: 周期类型，默认0
            refer: 参考指数ID（可选）
        
        返回:
            回撤数据，包含：
            - drawdown: 绝对回撤列表
              - interval: 回撤区间
              - drawdown: 回撤幅度
              - cover_days: 恢复天数
              - cover_days_interval: 恢复区间
              - index_interval: 指数回撤区间
              - index_retruns: 指数收益率
            - excess_drawdown: 相对回撤列表（相对指数）
        """
        url = f"{self.NAV_BASE_URL}/fund/drawdownList"
        
        params = {
            "fid": fund_id,
            "pt": str(pt),
            "type": "1",
            "cycle": str(cycle)
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        if refer:
            params["refer"] = refer
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_positive_rate(
        self,
        fund_id: str,
        start_date: str = None,
        end_date: str = None,
        cycle: int = 3,
        refer: str = None,
        pt: int = 1
    ) -> Dict:
        """
        获取基金胜率分析
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            cycle: 周期类型
                   1 = 日度
                   2 = 周度
                   3 = 月度
                   4 = 季度
                   5 = 年度
            refer: 参考指数ID（可选）
            pt: 数据类型，默认1
        
        返回:
            胜率分析数据，包含：
            - fund: 基金胜率数据
              - count: 总周期数
              - avg_positive_ratio: 平均盈利幅度
              - avg_negative_ratio: 平均亏损幅度
              - excess_avg_positive_ratio: 超额平均盈利幅度
              - excess_avg_negative_ratio: 超额平均亏损幅度
              - excess_negative_ratio: 超额负收益占比（胜率的反面）
              - excess_max_positive_ratio: 超额最大盈利
              - excess_max_negative_ratio: 超额最大亏损
            - index: 指数胜率数据
        """
        url = f"{self.NAV_BASE_URL}/fund/positive"
        
        params = {
            "fid": fund_id,
            "cycle": str(cycle),
            "pt": str(pt),
            "type": "1"
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        if refer:
            params["refer"] = refer
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_roll_analysis(
        self,
        fund_id: str,
        start_date: str = None,
        end_date: str = None,
        factor: str = "vol",
        window: str = "3m",
        cycle: int = 0,
        refer: str = None,
        pt: int = 1
    ) -> Dict:
        """
        获取基金滚动分析（收益分布）
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            factor: 分析因子
                    - vol: 波动率
                    - return: 收益率
                    - sharpe: 夏普比率
                    - drawdown: 回撤
                    - cVaR: 条件风险价值（CVaR）
                    - sortino: 索提诺比率
                    - calmar: 卡玛比率
            window: 滚动窗口
                    - 1m: 1个月
                    - 3m: 3个月
                    - 6m: 6个月
                    - 1y: 1年
                    - 2y: 2年
                    - 3y: 3年
            cycle: 周期类型，默认0
            refer: 参考指数ID（可选）
            pt: 数据类型，默认1
        
        返回:
            滚动分析数据，包含：
            - distr: 分布数据
              - fund_bars: 基金分布柱状图数据 [[区间起点, 区间终点, 频率], ...]
              - index_bars: 指数分布柱状图数据
            - stats: 统计数据
              - fund: 基金统计指标
              - index: 指数统计指标
        """
        url = f"{self.NAV_BASE_URL}/fund/rollanalysis"
        
        params = {
            "fid": fund_id,
            "factor": factor,
            "window": window,
            "cycle": str(cycle),
            "pt": str(pt),
            "type": "1"
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        if refer:
            params["refer"] = refer
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_interval_returns(
        self,
        fund_id: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "yearly",
        cycle: int = 0,
        refer: str = None,
        pt: int = 1
    ) -> Dict:
        """
        获取基金区间收益
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 区间类型
                      - yearly: 年度收益
                      - quarterly: 季度收益
                      - monthly: 月度收益
                      - weekly: 周度收益
            cycle: 周期类型，默认0
            refer: 参考指数ID（可选）
            pt: 数据类型，默认1
        
        返回:
            区间收益数据，包含：
            - fund_factor: 基金各区间收益数据
            - index_factor: 指数各区间收益数据
            - yearList: 年份列表
        """
        url = f"{self.NAV_BASE_URL}/fund/returns"
        
        params = {
            "fid": fund_id,
            "interval": interval,
            "cycle": str(cycle),
            "pt": str(pt),
            "type": "1"
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        if refer:
            params["refer"] = refer
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_returns(
        self,
        fund_id: str,
        start_date: str = None,
        end_date: str = None,
        interval: str = "quarter",
        pt: int = 1,
        cycle: int = 0,
        refer: str = None
    ) -> Dict:
        """
        获取基金区间收益
        
        参数:
            fund_id: 基金ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            interval: 区间类型 (quarter=季度, month=月度, year=年度)
            pt: 数据类型，默认1
            cycle: 周期类型，默认0
            refer: 参考指数ID（可选）
        
        返回:
            区间收益数据，包含：
            - fund_factor: 基金收益因子
              - quarter: 季度收益列表
                - quarterNum: 季度编号 (如 2022-Q1)
                - pc: 收益率
                - quartile: 分位数
                - s_avg: 同类平均
                - s_median: 同类中位数
                - s_rank: 排名
                - s_total: 总数
              - yearly: 年度收益列表
              - excess_quarter: 超额季度收益
              - excess_yearly: 超额年度收益
            - index_factor: 指数收益因子
              - quarter: 季度收益
              - yearly: 年度收益
        """
        url = f"{self.NAV_BASE_URL}/fund/returns"
        
        params = {
            "fid": fund_id,
            "pt": str(pt),
            "type": "1",
            "cycle": str(cycle),
            "interval": interval
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        if refer:
            params["refer"] = refer
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_correlation(
        self,
        fund_id: str,
        refer: str,
        start_date: str = None,
        end_date: str = None,
        cycle: int = 0,
        pt: int = 1
    ) -> Dict:
        """
        获取基金与指数的相关系数
        
        参数:
            fund_id: 基金ID
            refer: 参考指数ID（必需）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            cycle: 周期类型，默认0
            pt: 数据类型，默认1
        
        返回:
            相关系数数据，包含：
            - interval: 区间相关系数
              - corr: 整体相关系数
              - lastOneMonthCorr: 近1个月相关系数
              - lastThreeMonthCorr: 近3个月相关系数
              - lastSixMonthCorr: 近6个月相关系数
              - lastOneYearCorr: 近1年相关系数
              - lastTwoYearCorr: 近2年相关系数
              - lastThreeYearCorr: 近3年相关系数
              - lastFiveYearCorr: 近5年相关系数
              - ytdCorr: 年初至今相关系数
            - yearly: 年度相关系数
              - 2017Corr: 2017年相关系数
              - 2018Corr: 2018年相关系数
              - ...
        """
        url = f"{self.NAV_BASE_URL}/fund/corr"
        
        params = {
            "fid": fund_id,
            "refer": refer,
            "cycle": str(cycle),
            "pt": str(pt),
            "type": "1"
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_roll_positive(
        self,
        fund_id: str,
        target_return: float,
        refer: str = None,
        start_date: str = None,
        end_date: str = None,
        cycle: int = 0,
        pt: int = 1
    ) -> Dict:
        """
        获取基金滚动盈利概率
        
        参数:
            fund_id: 基金ID
            target_return: 目标收益率（小数形式，如0.15表示15%）
            refer: 参考指数ID（可选）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            cycle: 周期类型，默认0
            pt: 数据类型，默认1
        
        返回:
            盈利概率数据，包含：
            - fund: 基金盈利概率
              - threeMonthPositiveRatio: 3个月滚动盈利概率
              - sixMonthPositiveRatio: 6个月滚动盈利概率
              - oneYearPositiveRatio: 1年滚动盈利概率
              - twoYearPositiveRatio: 2年滚动盈利概率
              - threeYearPositiveRatio: 3年滚动盈利概率
              - fiveYearPositiveRatio: 5年滚动盈利概率
            - index: 指数盈利概率（如果提供refer参数）
        
        示例:
            # 查询达到15%收益的概率
            result = api.get_fund_roll_positive(
                fund_id="f56d280c5131a6c9",
                target_return=0.15,  # 15%
                refer="ca6de5b04aa45f192202420cff2e9599"
            )
            
            # 1年滚动达到15%收益的概率
            prob = result["data"]["fund"]["oneYearPositiveRatio"]
            print(f"1年滚动达到15%收益的概率: {prob*100:.2f}%")
        """
        url = f"{self.NAV_BASE_URL}/fund/rollpositive"
        
        params = {
            "fid": fund_id,
            "returns": str(target_return),
            "cycle": str(cycle),
            "pt": str(pt),
            "type": "1"
        }
        
        if refer:
            params["refer"] = refer
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_fund_style_attribution(
        self,
        fund_id: str,
        refer: str,
        start_date: str = None,
        end_date: str = None,
        style_type: str = "cne5_new",
        excess: int = 1,
        fund_type: int = 0,
        from_type: int = 1,
        price_type: int = 1,
        cycle: int = 0,
        type_param: str = "stock"
    ) -> Dict:
        """
        获取基金风格归因分析
        
        参数:
            fund_id: 基金ID
            refer: 参考指数ID（必需）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            style_type: 风格模型类型
                        - cne5_new: CNE5新模型（推荐）
                        - cne5: CNE5模型
                        - barra: Barra模型
            excess: 是否超额收益（1=是，0=否）
            fund_type: 基金类型（0=默认）
            from_type: 来源类型（1=默认）
            price_type: 价格类型（1=默认）
            cycle: 周期类型（0=默认）
            type_param: 类型（stock=股票）
        
        返回:
            风格归因数据，包含：
            - factor_sensitivity: 因子敏感度
              - interval: 区间敏感度
              - quarter: 季度敏感度
              - yearly: 年度敏感度
              10个风格因子：beta, book_to_price, earnings_yield, growth, 
                           leverage, liquidity, momentum, non_linear_size, 
                           residual_volatility, size
            - revenue_contribution: 收益贡献
            - risk_contribution: 风险贡献
            - regression_analysis: 回归分析（R²、t值、p值等）
            - revenue_resolve: 收益分解时间序列
            - explain_contribution: 解释贡献
        
        示例:
            result = api.get_fund_style_attribution(
                fund_id="b5230a98c9316caa",
                refer="ca6de5b04aa45f192202420cff2e9599",
                start_date="2025-07-14",
                end_date="2026-02-13",
                style_type="cne5_new"
            )
        """
        url = f"{self.NAV_BASE_URL}/attribution/style"
        
        params = {
            "id": fund_id,
            "refer": refer,
            "styleType": style_type,
            "excess": str(excess),
            "fundType": str(fund_type),
            "fromType": str(from_type),
            "priceType": str(price_type),
            "cycle": str(cycle),
            "type": type_param
        }
        
        if start_date:
            params["startTime"] = start_date
        if end_date:
            params["endTime"] = end_date
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_market_roll_vol(
        self,
        codes: str,
        start_date: str = None,
        end_date: str = None,
        window: str = "60d",
        quantile: str = "vol"
    ) -> Dict:
        """
        获取市场情景分析（指数滚动波动率或分位数）
        
        参数:
            codes: 指数代码（如"000300"=沪深300，"000905"=中证500）
                   多个指数用逗号分隔："000300,000905"
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            window: 滚动窗口
                    - 5d: 5天
                    - 20d: 20天
                    - 60d: 60天
                    - 120d: 120天
            quantile: 分析类型
                      - vol: 波动率
                      - lastOneYearQuantile: 近1年分位数
                      - lastTwoYearQuantile: 近2年分位数
                      - lastThreeYearQuantile: 近3年分位数
                      - lastFiveYearQuantile: 近5年分位数
                      - lastTenYearQuantile: 近10年分位数
        
        返回:
            市场分析数据，包含：
            - funds: 指数数据列表
              - fund_name: 指数名称
              - code: 指数代码
              - data: 时间序列数据
                - price_date: 日期
                - value: 波动率或分位数值
        
        示例:
            # 获取沪深300的60天滚动波动率
            result = api.get_market_roll_vol(
                codes="000300",
                start_date="2025-07-14",
                end_date="2026-02-13",
                window="60d",
                quantile="vol"
            )
        """
        url = f"{self.BASE_URL}/market/rollvol"
        
        params = {
            "codes": codes,
            "window": window,
            "quantile": quantile
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def get_index_data(
        self,
        index_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        获取指数数据
        
        参数:
            index_code: 指数代码（如"000300"=沪深300）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
        
        返回:
            指数数据，包含：
            - prices: 价格数据列表
              - date: 日期
              - close: 收盘价
              - return: 收益率
        """
        url = f"{self.NAV_BASE_URL}/index/data"
        
        params = {
            "code": index_code
        }
        
        if start_date:
            params["sd"] = start_date
        if end_date:
            params["ed"] = end_date
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            print(f"请求超时")
            return {"error_code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return {"error_code": -1, "msg": str(e)}
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {"error_code": -1, "msg": "响应格式错误"}
        except Exception as e:
            print(f"未知错误: {e}")
            return {"error_code": -1, "msg": str(e)}
    
    def search_funds(self, keyword: str, page: int = 1, pagesize: int = 20) -> Dict:
        """
        搜索基金
        
        参数:
            keyword: 搜索关键词（基金名称或管理人名称）
            page: 页码
            pagesize: 每页数量
        
        返回:
            搜索结果字典
        """
        return self.get_fund_list(
            page=page,
            pagesize=pagesize,
            key_value=keyword
        )
    
    def get_all_funds(self, max_pages: int = None, delay: float = 1.0) -> List[Dict]:
        """
        获取所有基金数据（分页获取）
        
        参数:
            max_pages: 最大页数（None=获取全部）
            delay: 每次请求间隔（秒），避免被封IP
        
        返回:
            所有基金数据列表
        """
        all_funds = []
        page = 1
        
        while True:
            print(f"正在获取第 {page} 页...")
            
            result = self.get_fund_list(page=page, pagesize=100)
            
            if result.get("code") != 0:
                print(f"获取失败: {result.get('msg')}")
                break
            
            data = result.get("data", {})
            funds = data.get("list", [])
            
            if not funds:
                print("没有更多数据")
                break
            
            all_funds.extend(funds)
            print(f"  获取到 {len(funds)} 条数据，累计 {len(all_funds)} 条")
            
            # 检查是否还有下一页
            total = data.get("total", 0)
            if len(all_funds) >= total:
                print("已获取全部数据")
                break
            
            # 检查是否达到最大页数
            if max_pages and page >= max_pages:
                print(f"已达到最大页数 {max_pages}")
                break
            
            page += 1
            
            # 延迟，避免请求过快
            if delay > 0:
                time.sleep(delay)
        
        return all_funds
    
    def get_strategy_funds(self, strategy: str, max_count: int = None) -> List[Dict]:
        """
        获取指定策略的基金
        
        参数:
            strategy: 策略名称（如："股票策略"、"量化策略"）
            max_count: 最大数量
        
        返回:
            基金列表
        """
        funds = []
        page = 1
        pagesize = 100
        
        while True:
            result = self.get_fund_list(
                page=page,
                pagesize=pagesize,
                strategy=[strategy]
            )
            
            if result.get("code") != 0:
                break
            
            data = result.get("data", {})
            page_funds = data.get("list", [])
            
            if not page_funds:
                break
            
            funds.extend(page_funds)
            
            if max_count and len(funds) >= max_count:
                funds = funds[:max_count]
                break
            
            page += 1
            time.sleep(0.5)
        
        return funds


# 单例模式
_api_instance = None

def get_api_instance(access_token: str = None, device_id: str = None) -> HuoFuNiuAPI:
    """获取API实例（单例）"""
    global _api_instance
    if _api_instance is None:
        _api_instance = HuoFuNiuAPI(access_token, device_id)
    return _api_instance


if __name__ == "__main__":
    # 测试代码
    api = HuoFuNiuAPI()
    
    print("=" * 60)
    print("测试火富牛API")
    print("=" * 60)
    
    # 测试1: 获取基金列表
    print("\n[测试1] 获取基金列表（第1页）")
    result = api.get_fund_list(page=1, pagesize=5)
    
    if result.get("code") == 0:
        data = result.get("data", {})
        funds = data.get("list", [])
        print(f"成功获取 {len(funds)} 条数据")
        
        if funds:
            print("\n示例数据:")
            fund = funds[0]
            print(f"  基金名称: {fund.get('name')}")
            print(f"  管理人: {fund.get('manager_name')}")
            print(f"  策略: {fund.get('strategy')}")
            print(f"  最新净值: {fund.get('nav')}")
            print(f"  成立日期: {fund.get('establish_date')}")
    else:
        print(f"获取失败: {result.get('msg')}")
    
    # 测试2: 搜索基金
    print("\n[测试2] 搜索'玄元'")
    result = api.search_funds("玄元", pagesize=3)
    
    if result.get("code") == 0:
        data = result.get("data", {})
        funds = data.get("list", [])
        print(f"找到 {len(funds)} 条结果")
        
        for fund in funds:
            print(f"  - {fund.get('name')} ({fund.get('manager_name')})")
    else:
        print(f"搜索失败: {result.get('msg')}")
    
    print("\n" + "=" * 60)
    print("测试完成")
