import os
class Config:
    def __init__(self):
        self.__storage_path = os.getenv("STORAGE_PATH", "./Storage/Jobs")
        self.__internal_controller_path = os.getenv("STORAGE_PATH", "./Storage/InternalController")
        self.__ttlConfig = {
            "completed_jobs_hours": 24 * 7,  # 7 días para jobs completados exitosamente
            "failed_jobs_hours": 24 * 1,     # 1 día para jobs fallidos
        }
        

    def get_storage_path(self):
        return self.__storage_path
    
    def get_internal_controller_path(self):
        return self.__internal_controller_path
    
    def set_storage_path(self, path):
        self.__storage_path = path
    
    def set_internal_controller_path(self, path):
        self.__internal_controller_path = path
    
    def get_ttl_config(self):
        return self.__ttlConfig
    