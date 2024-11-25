import logging

import docker
import pymongo
import yaml


class Client:
    def __init__(self):
        with open("conf/config.yaml", 'r') as file:
            self.config = yaml.safe_load(file)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logging = logging.getLogger(__name__)
        self.uvicorn_log = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    "use_colors": False,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    # 这里日志格式加了时间显示
                },
            }
        }

    def docker_client(self):
        return docker.DockerClient(base_url=self.config['docker']['base_url'])

    def mongo_client(self):
        return pymongo.MongoClient(self.config['mongo']['url'])["docker"]

    def log_client(self):
        return self.logging

    def uvicorn_client(self):
        return self.uvicorn_log
