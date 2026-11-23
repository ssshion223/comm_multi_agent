# # | # | 方法 | URL | 用途 |
# # | --- | --- | --- | --- |
# # | 1 | GET | /api/open/v1/topology | 网络拓扑查询 |
# # | 2 | GET | /api/open/v1/nodes | 节点列表 |
# # | 3 | GET | /api/open/v1/nodes/{nodeId} | 节点详情与状态查询 |
# # | 4 | GET | /api/open/v1/links | 链路列表（元素含参数） |
# # | 5 | GET | /api/open/v1/links/{linkId} | 链路状态查询 |
# # | 6 | GET | /api/open/v1/services | 业务列表 |
# # | 7 | GET | /api/open/v1/services/{serviceId} | 业务状态查询 |
# # | 8 | POST | /api/open/v1/services/{serviceId}/path | 业务路径设置 |
# # | 9 | GET | /api/open/v1/services/{serviceId}/path | 业务路径查询 |
# # | 10 | GET | /api/open/v1/events | 事件轮询 |
# # | 11 | GET | /api/open/v1/time | 服务器时间 |
# # | 12 | POST | /api/open/v1/simulation/start | 仿真运行启动 |

# host = "192.168.1.25"
# port = 10100
# token = "open-3e3b67617787ba3538fb87f4"
# agent_id = "THQF"

# # base_url = f"http://{host}:{port}/api/open/v1"
# # topo_url = f"http://{host}:{port}/api/open/v1/topology"
# # nodes_url = f"http://{host}:{port}/api/open/v1/nodes"
# # links_url = f"http://{host}:{port}/api/open/v1/links"
# # serv_url = f"http://{host}:{port}/api/open/v1/services"
# # event_url = f"http://{host}:{port}/api/open/v1/events"
# # time_url = f"http://{host}:{port}/api/open/v1/time"
# # start_url = f"http://{host}:{port}/api/open/v1/start"
