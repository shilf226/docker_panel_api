import json
import os
import shutil
import zipfile
from fastapi import APIRouter, File, UploadFile
from tools.Client import Client

DockerStore = APIRouter()
client = Client().docker_client()
db_store = Client().mongo_client()['store']
log = Client().log_client()


@DockerStore.post("/upload/container")
async def upload_zip(file: UploadFile = File(...)):
    log.info("导入服务商店")
    # 保存上传的文件到临时路径
    temp_file_path = f"./temp_{file.filename}"
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file.file.close()  # 关闭文件，避免内存泄漏

    with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
        # 获取压缩包内所有文件的列表
        zip_info_list = zip_ref.infolist()
        for file in zip_info_list:
            if file.filename.lower().endswith('.tar') or file.filename.lower().endswith('.tgz'):
                log.info("导入镜像")
                client.images.load(zip_ref.read(file.filename))
            elif file.filename.lower().endswith('.json'):
                log.info("导入配置说明")
                data = zip_ref.read(file.filename).decode('utf-8')
                data = json.loads(data)
                # 导入
                if db_store.find_one({"hostname": data['hostname']}):
                    log.info("名称重复或数据已存在")
                else:
                    db_store.insert_one(data)
            else:
                return "检查包中的文件格式"

    # 清理临时文件
    os.remove(temp_file_path)

    return {"message": "文件上传并处理成功"}


@DockerStore.get("/get/storeall")
def get_store():
    db_data = db_store.find({}, {"_id": 0})
    data = []
    for i in db_data:
        data.append(i)
    return data


@DockerStore.get("/remove/{name}")
def get_store(name: str):
    try:
        db_store.delete_one({"hostname": name})
    except Exception as e:
        return e
