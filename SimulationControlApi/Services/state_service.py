
from pathlib import Path
import json
from datetime import datetime

class StateService():
    def __init__(self, path_state=""):
        
        self.__path_state = path_state
        self.__states=["WAIT","RUNNING", "ERROR", "READY", "FINISHED", "TERMINATED"]
        

    def create_state(self):
        try:
            state ={}
            state["state"] = self.__states[0]
            state["init_timestamp"] = datetime.now().isoformat()
            state["end_timestamp"] = None
            state["errors"] = []
            with open(self.__path_state, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2) 
        except Exception as e:
            self.__logger.error(f"Error al crear archivo de estado: {e}")
            raise

    def read_state(self):
        try:
            with open(self.__path_state, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            return data
        except Exception as e:
            print(f"Error al leer archivo de estado: {e}")
            raise
    
    def set_state(self, state:int ,error_message=""):
        try:
            file_state = self.read_state()
            file_state["state"] = self.__states[state]
            if(file_state["state"]=="RUNNING"):
                file_state["init_timestamp"] = datetime.now().isoformat()
                file_state["end_timestamp"] = None
                file_state["errors"] = []

            elif(file_state["state"]=="ERROR" or file_state["state"]=="READY"):
                file_state["end_timestamp"] = datetime.now().isoformat()
                if(file_state["state"]=="ERROR" and error_message!=""):
                    file_state["errors"].append({"timestamp": datetime.now().isoformat(), "message": error_message})

            with open(self.__path_state, 'w', encoding='utf-8') as f:
                json.dump(file_state, f, indent=2) 

        except Exception as e:
            print(f"Error al actualizar archivo de estado a ERROR: {e}")
            raise

    def get_state(self):
        try:
            file_state = self.read_state()
            return file_state["state"]
        except Exception as e:
            print(f"Error al obtener estado: {e}")
            raise

    def set_path(self, path_state: Path):
        self.__path_state = path_state

    def get_path(self):
        return self.__path_state
    