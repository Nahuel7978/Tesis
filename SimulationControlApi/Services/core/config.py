import os
class Config:
    def __init__(self):
        self.storage_path = os.getenv("STORAGE_PATH", "./Storage/Jobs")
        self.internal_controller_path = os.getenv("STORAGE_PATH", "./Storage/InternalController")

    def get_storage_path(self):
        return self.storage_path
    
    def get_internal_controller_path(self):
        return self.internal_controller_path
    
    def set_storage_path(self, path):
        self.storage_path = path
    
    def set_internal_controller_path(self, path):
        self.internal_controller_path = path
    
