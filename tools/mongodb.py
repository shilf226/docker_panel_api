import pymongo


class Mongo:

    def __init__(self):
        client = pymongo.MongoClient("mongodb://mongo:mongo@localhost:27017/")
        self.db_client = client["docker"]

    def mongo_docker(self):
        return self.db_client['docker']

    def mongo_store(self):
        return self.db_client['store']