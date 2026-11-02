# PantryKind · 食光有数

**看见家里已有的食材，少买重复的东西，多做一顿刚刚好的饭。**

[English](README.md) · [部署说明](docs/DEPLOYMENT.md) · [备份恢复](docs/BACKUPS.md)

PantryKind 是可自托管的家庭食材与购物管理工具。使用 Python、Django、SQLite 和服务端模板，不需要 Node.js 构建、不需要付费 AI 接口，也不绑定云端食材数据库。核心应用没有内置广告或统计追踪脚本。目前界面为英文，本说明提供中文上手方法。

## 能解决什么问题

- **食材放哪了、还剩多少：** 按批次记录名称、数量、单位、分类、储存位置和标签日期；相同食材可以有不同批次。
- **先吃什么：** 首页优先展示临近日期的食材；可以记录部分消耗、补货和丢弃原因，保留操作历史。
- **今晚做什么：** 保存自己的菜谱，按家中现有食材匹配，调整份数，把缺少的数量加入购物清单。确认做过后，才会按日期先后扣除对应批次。
- **家人不要重复买：** 家庭成员共享购物清单，同名同单位条目合并；低库存建议按所有匹配批次的合计数量计算。
- **计划和复盘：** 周菜单、ICS 日历下载、按单位分别统计的消耗与损耗记录。
- **数据自己掌握：** CSV 导出、预览后确认导入、只读 API、SQLite 一致性备份和本地提醒命令。

标签日期只是整理依据，不代表软件判断食物是否安全；请依照食品标签和实际情况处理。统计只反映你主动记录的数据，不虚构节省金额或环保效果。

## 本地运行

需要 Python 3.12 或更新版本。以下以 Windows PowerShell 为例：

```powershell
git clone https://github.com/AngelHuang5335/pantrykind.git
cd pantrykind
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

打开 http://127.0.0.1:8000，注册账号并创建自己的厨房即可。Linux/macOS 的启动方法见英文说明。

想先体验完整数据，可以运行：

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo
```

按提示设置密码，再用 `demo` 登录。演示数据包含食材、三个原创示例菜谱和菜单计划，不覆盖已有用户或清空数据库。没有统一的默认密码。

## 使用时注意

菜谱名称与库存名称需要归一化后精确匹配；软件不会擅自认为“番茄”和“西红柿”相同。克／千克、毫升／升可以换算，但“包”不会自动转换成重量。新增购买日期不同的食材时请创建新批次。购物打勾和菜单排期不会自动改动库存。

多个家庭的数据分别隔离；可以通过七天有效、仅可使用一次的邀请链接共享厨房。只有所有者可以管理邀请、成员和设置。

## 部署与贡献

本地开发默认仅适用于个人电脑。对外部署前，请按 [部署指南](docs/DEPLOYMENT.md) 配置唯一密钥、主机名、HTTPS 和登录限速，并安排 [备份](docs/BACKUPS.md)。程序原生读取环境变量，不自动读取 `.env` 文件；Docker Compose 会读取其指定的 `.env`。适用于小规模可信家庭，不以公开多租户服务为定位。

开发与校验命令、功能边界和贡献方式见 [英文说明](README.md)、[CONTRIBUTING](CONTRIBUTING.md) 与 [SECURITY](SECURITY.md)。项目使用 MIT 许可证，欢迎提交能解决实际家庭需求的小改进。
