import os
import json
import qdarktheme

SETTINGS_FILE_NAME = 'settings.json'
DEFAULT_SETTINGS_FILE_NAME = 'settings-default.json'
ROOT_DIR = os.path.abspath(os.curdir)

class SpeakerSetting():
    def __init__(self):
        self.working_dir: str
        self.theme: str
        self.api_url: str
        self.schedule_update_time: int
        self.background_schedule_update_time: int
        self.old_audio_days: int
        self.old_audio_delete_time: int
        self.device: dict
        self.log_file_path: str
        self.file_name: str
        self.file_format: str
        
        if os.path.isfile(SETTINGS_FILE_NAME):
            self.load_from_json()
        else:
            with open(DEFAULT_SETTINGS_FILE_NAME, 'r', encoding='utf-8') as default_file:
                DEFAULT_SETTINGS = json.load(default_file)
            for setting in DEFAULT_SETTINGS:
                setattr(self, setting, DEFAULT_SETTINGS[setting])
            self.save_to_json()
        self.set_working_dir(os.path.join(os.getcwd(), self.working_dir))

    def load_from_json(self):
        with open(SETTINGS_FILE_NAME, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)
            for setting in json_data:
                setattr(self, setting, json_data[setting])

    def save_to_json(self):
        with open(f"{ROOT_DIR}/{SETTINGS_FILE_NAME}", 'w', encoding='utf-8') as json_file:
            data = {
                'working_dir': self.working_dir,
                'theme': self.theme,
                'schedule_update_time': self.schedule_update_time,
                'background_schedule_update_time': self.background_schedule_update_time,
                'old_audio_days': self.old_audio_days,
                'old_audio_delete_time': self.old_audio_delete_time,
                'device': self.device,
                'api_url': self.api_url,
                'log_file_path': self.log_file_path,
                'file_name': self.file_name,
                'file_format': self.file_format
            }
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    def set_working_dir(self, directory):
        try:  
            os.mkdir(directory)  
        except OSError as error:
            pass
        finally:
            os.chdir(directory)

    def apply_theme(self, theme=None):
        theme = (theme, self.theme)[theme is None]
        parameter = theme_parameters.get(self.theme)
        qdarktheme.setup_theme(theme=parameter.get('theme'), additional_qss=parameter.get('qss'), custom_colors=parameter.get('custom'))


theme_parameters = {
    'Dark Theme': {
        'theme': 'dark',
        'qss': "QWidget { background-color: #2f2f33; } QPushButton { border-width: 0px; }",
        'custom': { "primary": "#58B040" } 
    },
    'Light Theme': {
        'theme': 'light',
        'qss': "QPushButton { border-width: 0px; }",
        'custom': { "primary": "#58B040" } 
    },
}
