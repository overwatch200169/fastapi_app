from elasticsearch.dsl import async_connections

from app.core.config import settings

ES_HOSTS = [settings.ELASTICSEARCH_HOST]
# ES_HOSTS = ['https://localhost:9200']

def create_es_connection():
    """
    根据文档建议，使用 create_connection 创建默认的全局连接。
    文档指出，此方法会自动为您使用内置的 serializer 以确保正确的 JSON 序列化。
    """
    # 使用 'default' 作为连接的别名（alias），这是文档中示例的默认值。
    # 将 hosts 参数传递给底层的 AsyncElasticsearch 客户端。
    async_connections.create_connection(

        hosts=ES_HOSTS,
        basic_auth=(settings.ES_AUTH, settings.ES_PASSWORD),  # 请替换‘您的密码’为实际密码
        # 对于自签名证书，在开发环境可以关闭验证
        verify_certs=False,
        # 您可以在此添加其他传递给 AsyncElasticsearch.__init__ 的参数，例如 timeout, sniff_on_start 等。
        # 具体选项请参考 elasticsearch-py 的文档。
    )
    print("Elasticsearch 默认连接已创建。")

# 可选：获取连接的函数，便于在其他地方使用
async def get_es_connection():
    """
    根据别名获取配置好的连接。
    文档中提到，使用多个连接时，可以通过此别名进行引用。
    """
    return async_connections.get_connection()