import os
import subprocess

from pathlib import Path
global SaveEditorPath, ProfileNumber, SaveProfilePath


class SaveFileReader:
    def __init__(self, save_editor_path, profile_number):
        global SaveEditorPath, ProfileNumber, SaveProfilePath
        SaveEditorPath = save_editor_path
        ProfileNumber = profile_number
        SaveProfilePath = rf'C:\Program Files (x86)\Steam\userdata\71731729\262060\remote\profile_{profile_number}'
        self.SaveEditorPath = SaveEditorPath
        self.ProfileNumber = ProfileNumber
        self.SaveProfilePath = SaveProfilePath

    @staticmethod
    def save_editor_path():
        global SaveEditorPath
        return SaveEditorPath

    @staticmethod
    def save_profile_number():
        global ProfileNumber
        return ProfileNumber

    @staticmethod
    def save_profile_path():
        global SaveProfilePath
        return SaveProfilePath

    @staticmethod
    def decrypt_save_info(file):
        filepath = Path(f'{SaveEditorPath}/{file}')
        if os.path.exists(filepath):
            os.remove(filepath)
        subprocess.call(['java', '-jar', Path(f'{SaveEditorPath}/DDSaveEditor.jar'), 'decode',
                         '-o', filepath, Path(f'{SaveProfilePath}/{file}')])
        print(f'decrypted {file}!')
