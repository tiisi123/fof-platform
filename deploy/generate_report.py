#!/usr/bin/env python3
"""
生成HTML格式的测试报告
"""

import json
import os
from datetime import datetime

def generate_html_report(business_results=None, performance_results=None):
    """生成HTML测试报告"""
    
    # 读取性能测试结果
    perf_data = None
    if os.path.exists("performance_report.json"):
        with open("performance_report.json", "r", encoding="utf-8") as f:
            perf_data = json.load(f)
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FOF管理平台测试报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            font-size: 24px;
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        
        .stat-card.success {{
            border-left-color: #28a745;
        }}
        
        .stat-card.warning {{
            border-left-color: #ffc107;
        }}
        
        .stat-card.danger {{
            border-left-color: #dc3545;
        }}
        
        .stat-card h3 {{
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-card .unit {{
            font-size: 14px;
            color: #999;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge.success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge.warning {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .badge.danger {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .badge.info {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        .chart {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            transition: width 0.3s ease;
        }}
        
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        
        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 FOF管理平台测试报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="content">
"""
    
    # 性能测试结果
    if perf_data:
        response_tests = perf_data.get("response_time_tests", [])
        concurrent_tests = perf_data.get("concurrent_tests", [])
        
        # 计算统计数据
        if response_tests:
            avg_times = [t["avg"] for t in response_tests]
            avg_response = sum(avg_times) / len(avg_times)
            
            excellent = sum(1 for t in avg_times if t < 200)
            good = sum(1 for t in avg_times if 200 <= t < 500)
            normal = sum(1 for t in avg_times if 500 <= t < 1000)
            slow = sum(1 for t in avg_times if t >= 1000)
            
            html += f"""
            <div class="section">
                <h2>📊 性能测试概览</h2>
                
                <div class="stats">
                    <div class="stat-card">
                        <h3>平均响应时间</h3>
                        <div class="value">{avg_response:.0f}</div>
                        <div class="unit">毫秒</div>
                    </div>
                    <div class="stat-card success">
                        <h3>优秀端点</h3>
                        <div class="value">{excellent}</div>
                        <div class="unit">个 (&lt;200ms)</div>
                    </div>
                    <div class="stat-card success">
                        <h3>良好端点</h3>
                        <div class="value">{good}</div>
                        <div class="unit">个 (200-500ms)</div>
                    </div>
                    <div class="stat-card warning">
                        <h3>一般端点</h3>
                        <div class="value">{normal}</div>
                        <div class="unit">个 (500-1000ms)</div>
                    </div>
                    <div class="stat-card danger">
                        <h3>较慢端点</h3>
                        <div class="value">{slow}</div>
                        <div class="unit">个 (&gt;1000ms)</div>
                    </div>
                </div>
                
                <h3>响应时间详情</h3>
                <table>
                    <thead>
                        <tr>
                            <th>端点</th>
                            <th>平均响应</th>
                            <th>中位数</th>
                            <th>P95</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for test in response_tests:
                avg = test["avg"]
                if avg < 200:
                    badge_class = "success"
                    status = "优秀"
                elif avg < 500:
                    badge_class = "success"
                    status = "良好"
                elif avg < 1000:
                    badge_class = "warning"
                    status = "一般"
                else:
                    badge_class = "danger"
                    status = "较慢"
                
                html += f"""
                        <tr>
                            <td>{test['name']}</td>
                            <td>{test['avg']:.0f} ms</td>
                            <td>{test['median']:.0f} ms</td>
                            <td>{test['p95']:.0f} ms</td>
                            <td><span class="badge {badge_class}">{status}</span></td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        # 并发测试结果
        if concurrent_tests:
            html += """
            <div class="section">
                <h2>🔥 并发性能测试</h2>
                <table>
                    <thead>
                        <tr>
                            <th>测试场景</th>
                            <th>并发数</th>
                            <th>成功请求</th>
                            <th>成功率</th>
                            <th>吞吐量</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for test in concurrent_tests:
                success_rate = test['successful'] / test['concurrent'] * 100
                badge_class = "success" if success_rate >= 95 else "warning" if success_rate >= 80 else "danger"
                
                html += f"""
                        <tr>
                            <td>{test['name']}</td>
                            <td>{test['concurrent']}</td>
                            <td>{test['successful']}/{test['concurrent']}</td>
                            <td><span class="badge {badge_class}">{success_rate:.1f}%</span></td>
                            <td>{test['requests_per_second']:.1f} req/s</td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""
    
    # 性能建议
    html += """
            <div class="section">
                <h2>💡 性能建议</h2>
                <div class="chart">
"""
    
    if perf_data and response_tests:
        slow_endpoints = [t for t in response_tests if t['avg'] > 1000]
        if slow_endpoints:
            html += """
                    <h3>⚠️ 需要优化的端点:</h3>
                    <ul style="margin-left: 20px; margin-top: 10px;">
"""
            for endpoint in slow_endpoints:
                html += f"""
                        <li style="margin: 5px 0;">{endpoint['name']}: {endpoint['avg']:.0f}ms - 建议优化查询或添加缓存</li>
"""
            html += """
                    </ul>
"""
        else:
            html += """
                    <p style="color: #28a745; font-weight: bold;">✅ 所有端点响应时间良好，无需优化</p>
"""
    
    html += """
                    <h3 style="margin-top: 20px;">📈 优化建议:</h3>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li style="margin: 5px 0;">为常用查询添加数据库索引</li>
                        <li style="margin: 5px 0;">对Dashboard等高频接口启用Redis缓存</li>
                        <li style="margin: 5px 0;">优化复杂SQL查询，避免N+1问题</li>
                        <li style="margin: 5px 0;">考虑使用CDN加速静态资源</li>
                        <li style="margin: 5px 0;">监控慢查询日志，定期优化</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>FOF管理平台 v1.0.0 | 技术支持: FOF技术团队</p>
            <p style="margin-top: 5px;">报告生成工具: generate_report.py</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 保存HTML报告
    with open("test_report.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ HTML测试报告已生成: test_report.html")
    print(f"📊 在浏览器中打开查看: file://{os.path.abspath('test_report.html')}")

if __name__ == "__main__":
    generate_html_report()
