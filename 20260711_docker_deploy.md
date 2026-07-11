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

推荐宿主机端口用 `5011`，容器内端口固定 `18080`。参数已经写进 `docker-compose.yml`，内网服务器只需要：

```bash
docker compose up -d
```

查看状态：

```bash
docker compose ps
docker compose logs -f oracle-sms-gateway
```

停止：

```bash
docker compose down
```

检查：

```bash
curl http://127.0.0.1:5011/health
curl -H "X-API-Key: $API_TOKEN" http://127.0.0.1:5011/ready
```

## 端口建议

`oracle-sms-gateway` 是内部公共基础服务，不建议夹在普通业务项目的 5001、5002 中间。建议固定在 `5011`，以后把 `5010-5019` 留给公共基础服务。
