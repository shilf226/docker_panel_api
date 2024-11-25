import threading
import asyncio
import os
from pprint import pprint
from time import sleep
from typing import List

from fastapi import APIRouter, File
import psutil
from pydantic import BaseModel
from starlette.websockets import WebSocket, WebSocketDisconnect

from tools.Client import Client

DockerRouter = APIRouter()
client = Client().docker_client()
db_docker = Client().mongo_client()['docker']


@DockerRouter.get("/get/basicinfo")
async def info():
    data = [
        {
            'label': 'docker版本',
            'value': client.version()['Version']
        },
        {
            'label': '操作系统名称',
            'value': os.sys.platform
        },
        {
            'label': '内存大小(BG)',
            'value': round(psutil.virtual_memory().total / 1024 / 1024 / 1024)
        },
        {
            'label': 'cpu核数',
            'value': psutil.cpu_count()
        },
        {
            'label': '磁盘空间(BG)',
            'value': round(psutil.disk_usage('/').total / 1024 / 1024 / 1024)
        },
    ]

    return data


@DockerRouter.get("/get/dashinfo")
async def info():
    old_netio = psutil.net_io_counters()
    sleep(1)
    new_netio = psutil.net_io_counters()

    data = {
        'cpu': str(psutil.cpu_percent(interval=1)) + "%",
        'mem': str(psutil.virtual_memory().percent) + "%",
        'disk': str(psutil.disk_usage('/').percent) + "%",
        'network': {
            'bytes_sent_speed': new_netio.bytes_sent - old_netio.bytes_sent,
            'bytes_recv_speed': new_netio.bytes_recv - old_netio.bytes_recv
        }
    }

    return data


@DockerRouter.get("/get/images")
async def get_image_list():
    data = []
    for i in client.images.list():
        data.append({
            'Id': i.attrs['Id'],
            'RepoTags': i.attrs['RepoTags'][0],
            'Created': i.attrs['Created'],
            'Size': str(round(i.attrs['Size'] / 1000 / 1000)) + 'M',
            'data': i.attrs
        })
    return data


@DockerRouter.get("/get/images")
async def get_image_list():
    data = []
    for i in client.images.list():
        data.append({
            'RepoTags': i.attrs['RepoTags'][0],
            'Created': i.attrs['Created'],
            'Size': str(round(i.attrs['Size'] / 1000 / 1000)) + 'M',
            'data': i.attrs
        })
    return data


@DockerRouter.get("/remove/images/{image_id}")
async def remove_image(image_id: str):
    try:
        client.images.remove(image_id)
        return True
    except Exception as e:
        print("删除镜像时出错:", e)


@DockerRouter.post("/load/images/")
async def load_image(file: bytes = File()):
    try:
        client.images.load(file)
        return True
    except Exception as e:
        print("导入镜像时出错:", e)


@DockerRouter.get("/get/container/{container_id}/start")
async def get_container_start(container_id: str):
    container = client.containers.get(container_id=container_id)
    container.start()


@DockerRouter.get("/get/containers")
async def get_container():
    client.containers.list()
    data = []
    for i in client.containers.list(all=True):
        data.append({
            'name': str(i.attrs['Name']).replace("/", ""),
            'status': i.attrs['State']['Status'],
            'id': i.attrs['Id'],
            'attrs': db_docker.find_one({"hostname": str(i.attrs['Name']).replace("/", "")}, {'_id': 0})
        })
    return data


@DockerRouter.get("/pull/images/{tag}")
async def load_image(tag: str):
    try:
        data = client.images.pull(tag)
        print(data)
        return True
    except Exception as e:
        print("拉取镜像时出错:", e)


@DockerRouter.get("/get/container/{container_id}/stop")
async def get_container_stop(container_id: str):
    container = client.containers.get(container_id=container_id)
    container.stop()


@DockerRouter.get("/get/container/{container_id}/restart")
async def get_container_restart(container_id: str):
    container = client.containers.get(container_id=container_id)
    container.restart()


@DockerRouter.get("/remove/container/{container_id}/{hostname}")
async def get_container_remove(container_id: str, hostname: str):
    try:
        container = client.containers.get(container_id=container_id)
        container.remove()
        db_docker.delete_one({"hostname": hostname})
    except Exception as e:
        return e


@DockerRouter.get("/get/volume")
async def get_volume():
    data = []
    for i in client.volumes.list():
        data.append({
            'id': i.id,
            'Name': i.attrs['Name'],
            'Driver': i.attrs['Driver'],
            'CreatedAt': i.attrs['CreatedAt'],
            'attrs': i.attrs,
        })
        print(dir(i))
    return data


@DockerRouter.get("/remove/volume/{volume_id}")
async def get_volume_remove(volume_id: str):
    volumes = client.volumes.get(volume_id)
    try:
        volumes.remove()
        return True
    except Exception as e:
        print("删除存储卷时出错:", e)


@DockerRouter.get("/create/volume/{volume_name}")
async def get_volume_remove(volume_name: str):
    try:
        volume = client.volumes.create(name=volume_name)
        print(volume)
        # nfs卷
        # volume = client.volumes.create(driver="nfs",
        #                                driver_opts={"type": "nfs",
        #                                             "o": "addr=192.168.1.100,rw,nolock",
        #                                             "device": ":/exported_nfs_folder"})
    except Exception as e:
        print("创建存储卷时出错:", e)


class Container_info(BaseModel):
    hostname: str = None
    restart: str = 'always'
    image: str = None
    command: str = None
    environment: list = None
    volumes: list = None
    ports: list = None
    extra_hosts: list = None
    privileged: bool = False


@DockerRouter.post("/create/container")
async def add_container(item: Container_info):
    environment = [f"{env['key']}={env['value']}" for env in item.environment] if item.environment else None
    volumes = {i['host_path']: {"bind": i['container_path'], "mode": "rw"} for i in
               item.volumes} if item.volumes else None
    ports = {f"{i['host_ports']}/tcp": int(i['container_ports']) for i in item.ports} if item.ports else None
    extra_hosts = {i['host']: i['ip'] for i in item.extra_hosts} if item.extra_hosts else None

    db_docker.insert_one(dict(item))
    try:
        client.containers.create(
            name=item.hostname,
            image=item.image,
            hostname=item.hostname,
            restart_policy={"Name": item.restart},
            environment=environment,
            ports=ports,
            volumes=volumes,
            extra_hosts=extra_hosts,
            privileged=item.privileged,
            command=item.command
        )

    except Exception as e:
        pprint(e)


# websocker
class ConnectionManager:
    def __init__(self):
        # 存放激活的ws连接对象
        self.active_connections: List[WebSocket] = []

    async def connect(self, ws: WebSocket):
        # 等待连接
        await ws.accept()
        # 存储ws连接对象
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        # 关闭时 移除ws对象
        self.active_connections.remove(ws)

    @staticmethod
    async def send_personal_message(message: str, ws: WebSocket):
        # 发送个人消息
        await ws.send_text(message)

    async def broadcast(self, message: str):
        # 广播消息
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@DockerRouter.websocket("/ws/container/{container_id}/logs")
async def websocket_endpoint(websocket: WebSocket, container_id):
    await manager.connect(websocket)
    ThreadStreamlog(websocket, container_id).start()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class ThreadStreamlog(threading.Thread):
    def __init__(self, websocket, container_id):
        threading.Thread.__init__(self)
        self.websocket = websocket
        self.w = watch.Watch()
        self.container = client.containers.get(container_id=container_id)

    def run(self):
        try:
            for e in self.container.logs(stream=True):
                asyncio.run(manager.send_personal_message(e.decode("utf-8"), self.websocket))
        except Exception as e:
            print("链接已断开:", e)


@DockerRouter.websocket("/ws/container/{container_id}/exec")
async def websocket_endpoint(websocket: WebSocket, container_id):
    await manager.connect(websocket)
    ThreadStreamexec(websocket, container_id).start()
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class ThreadStreamexec(threading.Thread):
    def __init__(self, websocket, container_id):
        threading.Thread.__init__(self)
        self.websocket = websocket
        self.w = watch.Watch()
        self.container = client.containers.get(container_id=container_id)

    def run(self):
        try:
            while True:
                for e in self.container.exec_run('bash', stream=True):
                    asyncio.run(manager.send_personal_message(e.decode("utf-8"), self.websocket))
        except Exception as e:
            print("链接已断开:", e)
