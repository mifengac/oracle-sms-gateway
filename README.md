# oracle-sms-gateway

内网短信网关。业务项目只调用这个 HTTP 服务，由它统一写入 Oracle 短信表 `yfgadb.dfsdl`，避免每个项目都安装 Oracle 11g 客户端。

## 字段规则

- `ID`：网关使用 `yfgadb.seq_sendsms.nextval` 自动生成。
- `MOBILE`：接收手机号，一条短信一个号码一行记录。
- `CONTENT`：短信内容，最长 4000 字符。
- `DEADTIME`：写入时使用 `sysdate`。
- `STATUS`：写入时使用 `0`。
- `EID`：业务主键编号，例如警情编号、纠纷编号、任务编号。
- `USERID`、`PASSWORD`：从 `.env` 读取，不允许调用方传入覆盖。
- `USERPORT`：按 `.env` 里的 `SMS_BIZ_USERPORTS` 映射，默认 `0006`。

## 本地配置

本地真实配置放在 `.env`，该文件已被 `.gitignore` 忽略。GitHub 上只放 `.env.example`。

主要配置：

```bash
ORACLE_DSN=10.45.100.147:1521/yfgxpt
ORACLE_CLIENT_LIB_DIR=/home/longshao/project/oracle-sms-gateway/instantclient_11_2
SMS_BIZ_USERPORTS=default:0006,yfjcgkzx:0006
API_TOKEN=change-me
```

## 安装

先安装 Oracle 11g Instant Client 需要的系统库：

```bash
sudo apt-get update
sudo apt-get install -y libaio1
```

如果客户端目录缺少标准软链接，执行：

```bash
ln -sf libclntsh.so.11.1 instantclient_11_2/libclntsh.so
ln -sf libocci.so.11.1 instantclient_11_2/libocci.so
```

再安装 Python 依赖：

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

内网无互联网时，先在有网机器下载依赖 wheel 包，再拷到服务器：

```bash
pip download -r requirements.txt -d instantclient_11_2/python-wheels
pip install --no-index --find-links instantclient_11_2/python-wheels -r requirements.txt
```

本项目已经把离线安装需要的文件放在 `instantclient_11_2/` 下：

```text
instantclient_11_2/python-wheels/    Python 依赖包
instantclient_11_2/ubuntu22-debs/    Ubuntu 22 需要的 libaio1 安装包
```

内网服务器上可以直接执行：

```bash
bash scripts/install_offline.sh
```

## 启动

```bash
. .venv/bin/activate
export LD_LIBRARY_PATH=/home/longshao/project/oracle-sms-gateway/instantclient_11_2
uvicorn app.main:app --host 0.0.0.0 --port 18080
```

检查：

```bash
curl http://127.0.0.1:18080/health
curl -H "X-API-Key: $API_TOKEN" http://127.0.0.1:18080/ready
```

## 发送短信

```bash
curl -X POST http://127.0.0.1:18080/api/v1/sms/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_TOKEN" \
  -d '{
    "biz": "yfjcgkzx",
    "eid": "JQ202607110001",
    "mobiles": ["13800138000"],
    "content": "测试短信",
    "dedup_hours": 12
  }'
```

返回示例：

```json
{
  "success": true,
  "inserted": 1,
  "skipped": 0,
  "failed": [],
  "total": 1
}
```

## systemd

```bash
sudo cp systemd/oracle-sms-gateway.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now oracle-sms-gateway
sudo systemctl status oracle-sms-gateway
```

## Docker

构建镜像：

```bash
docker build -t oracle-sms-gateway:latest .
```

推荐宿主机端口使用 `5011`，容器内端口固定 `18080`：

```bash
docker run -d \
  --name oracle-sms-gateway \
  --restart unless-stopped \
  --env-file .env \
  -e ORACLE_CLIENT_LIB_DIR=/opt/oracle/instantclient_11_2 \
  -e LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2 \
  -p 5011:18080 \
  oracle-sms-gateway:latest
```

导出给内网服务器：

```bash
docker save oracle-sms-gateway:latest | gzip > oracle-sms-gateway_20260711.tar.gz
```

## 测试

```bash
python3 -m unittest discover -s tests -v
```
