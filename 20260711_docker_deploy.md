# oracle-sms-gateway Docker 部署说明

## 镜像包

当前项目会导出 Docker 镜像包：

```text
oracle-sms-gateway_20260711.tar.gz
```

内网服务器导入：

```bash
docker load -i oracle-sms-gateway_20260711.tar.gz
```

## 运行

推荐宿主机端口用 `5011`，容器内端口固定 `18080`：

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

检查：

```bash
curl http://127.0.0.1:5011/health
curl -H "X-API-Key: $API_TOKEN" http://127.0.0.1:5011/ready
```

## 端口建议

`oracle-sms-gateway` 是内部公共基础服务，不建议夹在普通业务项目的 5001、5002 中间。建议固定在 `5011`，以后把 `5010-5019` 留给公共基础服务。
