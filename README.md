# Brick Recognition System for Qimeng Project (Phase 1)

## Architecture

```mermaid
graph LR;
O[[MES System]];
A(API Server);
B(Event Handler);
C(Camera Server);
D("Camera Client (Multi Process)");
E("Camera Client (RPC)");
C1(("Camera"));
C2(("Camera"));
F[("Database")];
X([Algorithm API]);

O -.HTTP Request.- A;
C<--RPC-->E
subgraph Server 
A <--> F;
A <--> B;
B <---> C;
C <--Share Memory--> D;
end
D==USB 3.0===C2;
subgraph Client
E
end
B<----->|RPC|X
subgraph Algorithm
X
end
E==USB 3.0===C1;

```

## Deploy

### Requirements

* Ubuntu 20.04
* Docker
* Docker compose

### Prepare setting file (`settings.json`)

```json
{
    "server_side_cameras": {
		"camera": "042121120356"
    },
    "camera_server_url": "tcp://192.168.0.120:33033",
    "camera_server_url_local": "tcp://camera-server:33033",
    "camera_server_port": 33033,
    "algorithm_rpc_url": "tcp://192.168.0.79:4242",
    "camera_config": "/share/qm.Config",
    "image_shape": [
        2348,
        3376,
        3
    ]
}
```

* `server_side_cameras`: name and SN number of the camera connected to the server machine
* `camera_server_url`: the URL for camera RPC server
* `camera_server_url_local`: the URL for camera RPC server in docker network
* `camera_server_port`: the port for camera RPC server
* `algorithm_rpc_url`: the URL for algorithm RPC
* `camera_config`: the absolute path to camera config
* `image_shape`: the shape of shotted image

### Deploy Server

To deploy service server and also camera server (`Server` part in the graph above):

```shell
docker compose up --scale worker=8    
```

### Deploy RPC Camera Client (Optional)

Put camera config `qm.Config` and setting `settings.json` in `/share`. Then run:

```shell
ADDR=192.168.0.120
PORT=55555
docker run -v /share:/share --rm -it --name camera -p $PORT:$PORT --privileged tb5zhh/qimeng-deploy:latest python -m camera.client --station_id $ADDR --port $PORT
```

### Deploy Algorithm

==TODO==

## API

### `GET apis/ping/	`

> 服务器连通测试

响应样例：

```
pong
```

### `GET apis/list/`

> 只用于调试。返回检测请求的状态可视化
>
> 返回格式：
>
> `[检测请求ID] | [时间戳] | [工站编号] | [检测状态] | [（可选）工单列表] | [（可选）搜索关键词] | [检测结果]`

响应样例：

```shell
5 | 2023-01-02 15:14:55.631298+00:00 | 192.168.2.61 | FINISHED | None | None | ['02.02.0202.01.45', 0.56524086]
['02.02.0202.01.59', 0.30756888]
['02.02.0202.01.54', 0.04166368]
['02.02.0202.01.51', 0.022670781]
['02.02.0202.01.29', 0.01490246]
['02.02.0202.04.54', 0.008121818]
['02.02.0202.04.59', 0.0044193882]
['02.02.0202.01.D9', 0.004251861]
['02.02.0202.01.43', 0.0035241335]
['02.02.0202.01.B6', 0.0015638525]
6 | 2023-01-02 15:17:10.800552+00:00 | 192.168.2.61 | FINISHED | None | None | ['02.01.0101.01.58', 0.8483082]
['02.01.0101.01.58', 0.110284604]
['02.01.0101.10.54', 0.011641412]
['02.01.0101.10.56', 0.0058405213]
['02.01.0101.01.G5', 0.0045391945]
['02.01.0101.01.58', 0.0039531877]
['02.01.0101.01.65', 0.002501456]
['02.01.0101.51.58', 0.0020376414]
['02.01.0101.01.38', 0.0012946441]
['02.01.0101.01.36', 0.0012279692]
```

### `POST apis/create/`

> 提交检测请求，返回JSON对象。需要以 `x-www-form-urlencoded` 格式提供以下参数：
>
> * `station_id`：工站编号；服务端使用这个编号来选择需要拍摄的相机，实际部署时会使用工站电脑的IP地址作为工站编号
> * `order_list`：（可选）JSON字符串格式的工单列表；用于缩减检测范围。
>   * JSON字符串为列表，每一个元素分别为形状ID和颜色ID的组合
>   * 举例：`["02.01.0101.01.58", "02.02.0202.01.D9"]` 
> * `search_key`：（可选）搜索关键字；用于缩减检测范围
>   * 举例：`2x4`
>   * 使用`search_key`需要使用[接口](#post-apisupdate_bricks)录入待检索的积木列表
>
> 如果检测请求创建成功，检测请求的ID将被返回

请求样例（Python 3）：

```python
import requests
url = "127.0.0.1:8000/apis/create/"
# x-www-form-urlencoded
payload='station_id=test&search_key=%E6%B5%8B%E8%AF%95&order_list=%5B%20%5B%2202.01.0601.45.75%22%2C%20%22%E9%BB%91%22%5D%5D'
headers = {
  'Content-Type': 'application/x-www-form-urlencoded'
}
response = requests.request("POST", url, headers=headers, data=payload)
print(response.text)
```

响应样例：

```json
{"detection_id": 237}
```

### `GET apis/query/<id>/`

> 查询检测请求的状态，返回JSON对象。
>
> 在响应JSON对象中：
>
> - `detection_id`: 检测请求的ID
> - `status`: 检测请求的状态
>   - `SUBMMITED`：已提交，正在排队
>   - `RUNNING`：正在检测
>   - `FINISHED`：检测完成
>   - `ERROR`：发生错误
> - `result`: 检测结果
>   - 未检测完时为`null`
>   - 检测完成后为JSON格式字符串，为预测结果的列表
>   - 预测结果格式为`[("形状id", "颜色id"), 置信度]`

请求样例（Python 3）：

```python
import requests
url = "127.0.0.1:8000/apis/query/237/"
payload = {}
headers = {}
response = requests.request("GET", url, headers=headers, data=payload)
```

响应样例：

```json
{
    "detection_id": 237,
    "status": "SUBMITTED",
    "result": null
}
```

```json
{
    "detection_id": 238,
    "status": "FINISHED",
    "result": [
        ["02.01.0101.01.58", 0.8483082],
        ["02.01.0101.01.52", 0.110284604],
        ["02.01.0101.10.51", 0.011641412],
        ["02.01.0101.10.58", 0.0058405213],
        ["02.01.0101.01.G5", 0.0045391945],
        ["02.01.0101.01.G2", 0.0039531877],
        ["02.01.0101.01.65", 0.002501456],
        ["02.01.0101.51.58", 0.0020376414],
        ["02.01.0101.01.38", 0.0012946441],
        ["02.01.0101.01.36", 0.0012279692]
}
```

### `POST apis/clear/`

> 删除服务器上的全部检测请求

请求样例（Python 3）：

```python
# Python 3
import requests
url = "127.0.0.1:8000/apis/clear/"
payload = {}
headers = {}
response = requests.request("POST", url, headers=headers, data=payload)
```

响应样例：

```shell
success
```

### `GET apis/list_bricks/`

> 返回待检索的积木列表。列表中每一项格式为`[名称] | [ID]`

响应样例：

```shell
2x2圆形黑色件 | 02.07.0202.10.45 
```

### `POST apis/update_bricks/`

> 清空现有的待检索积木列表，替换为请求中的列表。
>
> 请求体为JSON字符串，样例见下方：

请求样例:

```python
import requests
import json
url = "127.0.0.1:8000/apis/update_bricks/"
payload = json.dumps({
  "bricks": [
    [
      "2x2圆形黑色件",
      "02.07.0202.10.45"
    ]
  ]
})
headers = {
  'Content-Type': 'application/json'
}
response = requests.request("POST", url, headers=headers, data=payload)

```

响应样例:

```shell
success
```

### `POST report/<id>/`

> 反馈检测结果。
>
> URL中`id`为需要反馈结果的检测请求的ID。
>
> 请求体为JSON字符串，样例见下方：

请求样例：

```python
import requests
import json
url = "127.0.0.1:8000/apis/update_bricks/"
payload = json.dumps({
  "result": False,          # 算法输出结果（第一项）是否正确
  "id": "02.07.0202.10.45", # 正确的积木ID
})
headers = {
  'Content-Type': 'application/json'
}
response = requests.request("POST", url, headers=headers, data=payload)

```



