 # Image Comparison Tool

一个用于比较和标记图像差异的Web工具。该工具允许用户并排查看原始图像和标记后的图像，帮助识别和记录有问题的图像。

## 功能特性

- 并排显示原始图像和标记后的图像
- 支持标记和保存有问题的图像
- 导出问题图像列表
- 保存和加载工作配置
- 支持多个配置管理
- 自动保存工作状态

## 系统要求

- Python 3.6+
- Flask 3.0.2

## 安装说明

1. 克隆或下载此仓库到本地

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动服务器：
```bash
python server.py
```

2. 在浏览器中访问：
```
http://localhost:5000
```

3. 设置工作目录：
   - 设置原始图像目录（Raw Directory）
   - 设置标记图像目录（Labeled Directory）

4. 使用界面功能：
   - 浏览并比较图像
   - 标记有问题的图像
   - 导出问题图像列表
   - 保存/加载工作配置

## 配置管理

- 配置文件保存在 `configs` 目录下
- 每个配置包含：
  - 原始图像目录路径
  - 标记图像目录路径
  - 已标记的问题图像列表
  - 时间戳

## 文件结构

```
.
├── server.py              # Flask服务器主程序
├── image_comparison.html  # 主界面HTML文件
├── image_viewer.html      # 图像查看器HTML文件
├── app_state.json        # 应用程序状态文件
├── requirements.txt      # Python依赖文件
└── configs/             # 配置文件目录
```

## 注意事项

- 确保原始图像和标记图像的文件名完全匹配
- 建议定期保存工作配置
- 导出的问题图像列表将包含时间戳

## 许可证

MIT License