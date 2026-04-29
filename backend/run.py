"""
启动脚本 - 设置正确的Python路径
"""
import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 导入并运行应用
if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量获取端口，默认8506
    port = int(os.getenv("PORT", 8506))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
