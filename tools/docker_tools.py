import docker


class Docker:

    def __init__(self):
        self.client = docker.DockerClient(base_url='tcp://localhost:2375')

    def docker_client(self):
        return self.client