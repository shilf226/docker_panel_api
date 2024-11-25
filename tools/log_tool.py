import logging


class Logs:
    def __init__(self):
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

    # 信息
    def info(self, data):
        return self.logging.info(data)

    # 调试
    def debug(self, data):
        return self.logging.debug(data)

    # 警告
    def warning(self, data):
        return self.logging.warning(data)

    def uvicorn_log(self):
        return self.uvicorn_log
