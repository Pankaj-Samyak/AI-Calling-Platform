import os
from datetime import datetime

class Log_class:
    def __init__(self, folder_path, file_name):
        self.folder_path = folder_path
        self.file_name = file_name
        os.makedirs(self.folder_path, exist_ok=True)

    def Info_Log(self, log_message):
        try:
            now = datetime.now()
            date = now.date()
            current_time = now.strftime("%H:%M:%S")
            with open(os.path.join(self.folder_path, self.file_name), 'a') as file:
                file.write(f"{date}\t{current_time}\t\tINFO\t\t{log_message}\n")
        except Exception as e:
            raise e

    def Error_Log(self, log_message):
        try:
            now = datetime.now()
            date = now.date()
            current_time = now.strftime("%H:%M:%S")
            with open(os.path.join(self.folder_path, self.file_name), 'a') as file:
                file.write(f"{date}\t{current_time}\t\tERROR\t\t{log_message}\n")
        except Exception as e:
            raise e