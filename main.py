from contextlib import asynccontextmanager
from colorama import Fore, Style
from fastapi import FastAPI
import uvicorn
import yaml
from starlette.middleware.cors import CORSMiddleware
from controller.DockerConntroller import DockerRouter
from controller.DockerStore import DockerStore
from tools.log_tool import Logs

uvicorn_log = Logs()


def read_yaml_file():
    with open("conf/config.yaml", 'r') as file:
        return yaml.safe_load(file)


data = read_yaml_file()


@asynccontextmanager
async def lifespan(server: FastAPI):
    print(Fore.GREEN + '''

    ███████╗ █████╗ ███████╗████████╗ █████╗ ██████╗ ██╗
    ██╔════╝██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║
    █████╗  ███████║███████╗   ██║   ███████║██████╔╝██║
    ██╔══╝  ██╔══██║╚════██║   ██║   ██╔══██║██╔═══╝ ██║
    ██║     ██║  ██║███████║   ██║   ██║  ██║██║     ██║
    ╚═╝     ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝

    FastAPI Service Start OK \n    Host: '''
          + data['project']['host'],
          "\n    Port:",
          str(data['project']['port'])
          + '''
''' + Style.RESET_ALL)
    yield
    print("Kube service stop down")


app = FastAPI(lifespan=lifespan)

# 注册路由
app.include_router(DockerRouter, prefix="/api/docker")
app.include_router(DockerStore, prefix="/api/store")

app.add_middleware(
    CORSMiddleware,
    allow_origins=data['allow_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    uvicorn.run(
        app='main:app',
        host=data['project']['host'],
        port=data['project']['port'],
        reload=True,
        log_config=uvicorn_log.uvicorn_log
    )
