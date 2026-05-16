import threading
import time
from canal.client import Client
from canal.protocol import EntryProtocol_pb2
# 1. 确保导入的是同步的客户端
from elasticsearch import Elasticsearch
import logging

from app.core.config import settings

logger=logging.getLogger(__name__)
# 2. 这里的客户端不要用异步的，直接用标准的同步连接
es_client = Elasticsearch(
    settings.ELASTICSEARCH_HOST,
    basic_auth=("elastic", settings.ES_PASSWORD),
    verify_certs=False,
)
stop_event = threading.Event()


def start_canal_worker():
    client = Client()
    client.connect(host=settings.CANAL_HOST, port=settings.CANAL_PORT)
    client.check_valid()
    client.subscribe(client_id="1001", destination="example", filter="fastapi\\.article")
    logger.info("🚀 Python Canal 监听服务已成功启动...")


    try:
        # 👈 核心修改：把 while True 改成判断 stop_event 是否被触发
        while not stop_event.is_set():
            # 获取数据，设置超时时间为 1 秒（防止一直死等卡住退出信号）
            message = client.get_without_ack(100, timeout=1000)
            entries = message.get('entries', [])

            for entry in entries:
                # ... 这里保持你原本的解析和 sync_to_es 逻辑不变 ...
                pass

            if message.get('id'):
                client.ack(message['id'])

            time.sleep(0.5)

    except Exception as e:
        logger.error(f"❌ 后台线程发生异常: {e}")
    finally:
        logger.info("🔒 正在释放 Canal 连接并关闭后台线程...")
        client.disconnect()


def parse_columns(columns):
    """将 Canal 的数据列对象优雅地转换为干净的 Python 字典，并清洗类型"""
    data = {}
    for col in columns:
        # 💡 核心类型清洗：确保 ID 和状态码在线上是以数字形态存入 ES9
        if col.name in ['article_id', 'author_id']:
            try:
                data[col.name] = int(col.value) if col.value else 0
            except ValueError:
                data[col.name] = col.value
        elif col.name in ['create_time','updated_time']:
            try:
                data[col.name] = int(time.mktime(time.strptime(col.value, "%Y-%m-%d %H:%M:%S")))
                print(data[col.name])
            except ValueError:
                data[col.name] = col.value
        elif col.name in ['alive']:
            try:
                data[col.name] = col.value=='1'
            except ValueError:
                data[col.name] = col.value

        else:
            data[col.name] = col.value

    return data


def sync_to_es(routing_key, event_type, row_data):
    """核心同步业务逻辑：将解析好的数据包塞入 ES9"""
    # info = es_client.info()
    # print(f"当前连接的 ES 集群名称: {info['cluster_name']}, 节点名称: {info['name']}")
    # 🔹 情况 A：若是新增(INSERT)或修改(UPDATE)事件，核心数据全部在 afterColumns 中
    if event_type in [EntryProtocol_pb2.EventType.INSERT, EntryProtocol_pb2.EventType.UPDATE]:
        data = parse_columns(row_data.afterColumns)
        article_id = data.get("article_id")

        if not article_id:
            return

        # 打印日志（Python 默认原生完美处理 UTF-8，控制台再无乱码烦恼）
        event_name = EntryProtocol_pb2.EventType.Name(event_type)
        logger.info(f"[{routing_key}] 🟢 捕获到 {event_name} 事件 | ID: {article_id} | 数据: {data}")

        # 增量/全量覆盖写入 ES9 索引（这里直接调用你成熟的 ES9 SDK，再无兼容性问题）
        es_client.index(
            index="articles",
            id=str(article_id),
            document=data
        )
        try:
            # 接收 ES9 的原生返回回执
            response = es_client.index(
                index="articles",
                id=str(article_id),
                document=data
            )
            logger.info(f"🎯 ES9 写入回执单: {response}")

        except Exception as e:
            logger.error(f"❌ 写入时发生致命错误: {e}")

    # 🔹 情况 B：若是删除(DELETE)事件，我们需要根据变更前的数据(beforeColumns)把 ES 里的文档干掉
    elif event_type == EntryProtocol_pb2.EventType.DELETE:
        data = parse_columns(row_data.beforeColumns)
        article_id = data.get("article_id")

        if article_id and es_client.exists(index="articles", id=str(article_id)):
            es_client.delete(index="articles", id=str(article_id))
            logger.info(f"[{routing_key}] 🔴 捕获到 DELETE 事件 | 已从 ES9 成功移除文章 ID: {article_id}")



def start_canal_worker():
    # 2. 连接你的 Canal-Server 容器
    client = Client()
    client.connect(host=settings.CANAL_HOST, port=settings.CANAL_PORT)
    client.check_valid()

    # 订阅具体的数据库和表（支持正则，这里精准订阅 fastapi 库下的 article 表）
    # 注意：在 Python 正则中，点号需要用双反斜杠转义
    client.subscribe(client_id="1001", destination="example", filter="fastapi\\.article")
    logger.info("🚀 Python Canal 监听服务已成功启动，正在死循环实时监听 Binlog 流...")

    try:
        while True:
            # 每次轮询尝试抓取最多 100 条变更消息
            message = client.get_without_ack(100)
            entries = message.get('entries', [])

            for entry in entries:
                # 过滤掉非数据变动的日志（如心跳数据 TRANSACTIONBEGIN/END 等，只看 ROWDATA）
                if entry.entryType == EntryProtocol_pb2.EntryType.ROWDATA:

                    # 反序列化出行变动核心对象
                    row_change = EntryProtocol_pb2.RowChange()
                    row_change.ParseFromString(entry.storeValue)

                    event_type = row_change.eventType
                    routing_key = f"{entry.header.schemaName}.{entry.header.tableName}"

                    # 遍历这一批次里受到影响的每一行数据（RowData）
                    for row_data in row_change.rowDatas:
                        try:
                            sync_to_es(routing_key, event_type, row_data)
                        except Exception as e:
                            logger.error(f"❌ 数据同步至 ES9 失败: {e}")

            # 💡 核心：确认消费成功！通知 Canal-Server，Binlog 游标向前推进
            if message.get('id'):
                client.ack(message['id'])

            time.sleep(0.2)  # 适当轻微平摊 CPU 轮询压力

    except KeyboardInterrupt:
        print("\n👋 收到终止信号，正在安全断开与 Canal-Server 的连接...")
    finally:
        client.disconnect()


if __name__ == "__main__":
    start_canal_worker()