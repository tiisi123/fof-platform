#!/bin/bash

echo "================================================================================"
echo "FOF管理平台 - 业务流程自动化测试"
echo "================================================================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查Selenium
if ! python3 -c "import selenium" &> /dev/null; then
    echo "[提示] 未安装Selenium，正在安装..."
    pip3 install selenium
fi

# 检查ChromeDriver
echo "[提示] 请确保已安装Chrome浏览器和ChromeDriver"
echo ""

# 运行测试
echo "[开始] 运行业务流程自动化测试..."
echo ""
python3 业务流程自动化测试.py

echo ""
echo "================================================================================"
echo "测试完成！"
echo "================================================================================"
