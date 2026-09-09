# 跨境电商运营日报/周报自动化工具

这是一个用于生成跨境电商运营日报和周报的自动化项目。

项目通过 Python、FastAPI、Streamlit、Docker 和 n8n，完成从数据读取、指标计算、风险识别、报告生成到定时发送的完整流程。

> 当前版本主要用于项目演示和流程验证，默认使用演示数据或本地数据文件，不包含任何公司真实数据、账号密码或 API 密钥。

## 一、项目功能

- 读取销售、广告和库存数据
- 计算 GMV、订单量、销量、广告花费、广告销售额、ROAS 等指标
- 计算预计利润和利润率
- 识别销售下降、广告低效和库存风险
- 生成日报和周报
- 通过 n8n 定时触发报告生成
- 自动发送日报和周报邮件
- 提供 Streamlit 数据看板
- 提供 FastAPI 报告生成接口
- 提供接口健康检查
- 支持任务失败排查和服务状态检查

## 二、项目流程

```text
销售、广告、库存数据
          ↓
Python 数据处理与指标计算
          ↓
FastAPI 生成报告接口
          ↓
n8n 定时触发
          ↓
生成日报或周报
          ↓
邮件发送

三、项目结构
cross-border-report-automation/
├─ app.py
├─ api.py
├─ platform_data.py
├─ Dockerfile
├─ docker-compose.yml
├─ requirements.txt
├─ n8n_daily_report_workflow.json
├─ data/
│  └─ README.md
└─ README.md
文件说明：
app.py：Streamlit 数据看板和报告分析逻辑
api.py：FastAPI 报告生成接口
platform_data.py：演示数据和数据读取逻辑
Dockerfile：构建 Python 服务镜像
docker-compose.yml：启动报告 API、数据看板和 n8n
requirements.txt：Python 依赖
n8n_daily_report_workflow.json：日报工作流示例
data/README.md：数据字段说明
如果后续从 n8n 导出周报工作流，可以补充：
n8n_weekly_report_workflow.json
四、当前版本的数据说明
当前项目默认使用演示数据或本地数据文件验证流程。
这意味着：
当前报告中的销售、广告和库存数据不代表真实公司数据
当前版本没有接入任何公司的真实业务 API
项目中的 API 是自己搭建的内部报告 API
n8n 调用的是本项目的 report-api
所有账号、邮箱、密码和 API 密钥都不应上传到 GitHub
当前版本的重点是验证以下业务闭环：
数据读取 → 指标计算 → 风险识别 → 报告生成 → 定时发送
因此，本项目目前定位为：
一个已经完成核心自动化闭环、可继续接入真实业务 API 的跨境电商运营报告自动化 MVP。

五、本地运行方式
1. 创建虚拟环境
python -m venv .venv
2. 激活虚拟环境
.\.venv\Scripts\Activate.ps1
3. 安装依赖
python -m pip install -r requirements.txt
4. 启动数据看板
streamlit run app.py
启动后访问：
http://localhost:8501
六、Docker 运行方式
安装 Docker Desktop 后，在项目根目录执行：
docker compose up --build
启动后可以访问：
数据看板：http://localhost:8501
报告 API：http://localhost:8000/docs
n8n：http://localhost:5678
停止服务：
docker compose down
如果修改了 Python 代码，需要重新构建：
docker compose up --build
七、日报和周报定时任务
日报
日报默认每天早上 08:00 触发：
每天 08:00
    ↓
调用 /generate-report
    ↓
生成日报
    ↓
发送邮件
周报
周报默认每周一早上 08:10 触发：
每周一 08:10
    ↓
调用 /generate-report
    ↓
生成周报
    ↓
发送邮件
实际使用时，需要在 n8n 中：
导入日报或周报工作流
检查报告 API 地址
配置邮箱凭据
修改收件人地址
测试工作流
确认无误后再启用定时任务
八、API 接口
健康检查
GET /health
用于确认报告服务是否正常运行。
生成报告
POST /generate-report
日报示例：
{
  "period": "日报",
  "source": "sample"
}
周报示例：
{
  "period": "周报",
  "source": "sample"
}
当返回状态码为 200 时，说明报告生成接口正常。
九、以后接入真实公司 API 时需要做什么
如果以后要在公司真实环境使用，需要按照下面步骤改造。
第一步：确认数据来源
需要确认公司使用的系统，例如：
电商平台 API
ERP 系统
广告平台 API
订单系统
库存系统
数据仓库
公司内部数据库
需要明确可以获取哪些字段：
日期
店铺
SKU
销售额
订单量
销量
广告花费
广告销售额
库存
在途库存
日均销量
采购周期
第二步：新增真实数据连接层
建议新增独立的数据连接文件：
connectors/
├─ sales_api.py
├─ ads_api.py
└─ inventory_api.py
不要把公司 API 请求代码全部直接写进报告计算逻辑中。
推荐结构：
真实业务 API
      ↓
connectors 数据连接层
      ↓
统一字段格式
      ↓
报告计算逻辑
      ↓
日报和周报
第三步：使用环境变量保存密钥
不要把密钥直接写进 Python 文件或 n8n 工作流。
可以使用：
API_BASE_URL
API_KEY
API_SECRET
DATABASE_URL
本地可以使用 .env 文件，但 .env 必须加入 .gitignore，不能上传到 GitHub。
第四步：统一真实数据字段
真实 API 返回的数据字段可能和当前项目不同，需要先转换成项目统一格式。
例如：
真实平台字段：total_amount
项目统一字段：sales
应该在数据连接层完成字段映射。
第五步：替换演示数据
修改：
platform_data.py
或者新增真实数据连接器，让系统从真实 API 获取数据。
报告计算逻辑尽量保持不变，这样可以降低改造成本。
第六步：重新测试数据口径
接入真实数据后，需要重点检查：
日报统计的是哪一天
周报统计的是哪一周
GMV 是否包含退款
广告花费是否含税
ROAS 的分子和分母是什么
库存是否包含在途库存
时区是否为北京时间
API 失败时是否会重复发送邮件
第七步：配置正式的定时任务
正式使用前，需要确认：
n8n 服务长期运行
Docker 容器设置自动重启
报告 API 有健康检查
工作流有失败通知
邮件凭据已经配置
收件人地址正确
不会因为重复执行而重复发邮件
十、安全注意事项
以下内容禁止上传到 GitHub：
.env
API 密钥
数据库密码
邮箱密码
Cookie
公司真实业务数据
客户信息
订单信息
内部系统地址
n8n_data/
上传代码前应检查：
git status
并确认项目中没有敏感信息。
十一、项目当前状态
当前版本已经完成：
报告生成逻辑
日报和周报逻辑
FastAPI 接口
Streamlit 看板
Docker 服务编排
n8n 定时工作流
接口健康检查
演示数据验证
当前版本尚未完成：
公司真实平台 API 接入
生产环境权限管理
正式数据库部署
完整的日志和监控系统
多账号和多店铺权限隔离
后续接入真实公司 API 时，主要改造数据连接层，保留现有的报告计算、接口和自动化流程。

粘贴完成后，点击右上角「Preview」检查排版，确认无误后再点击「Commit changes」。


14:56
