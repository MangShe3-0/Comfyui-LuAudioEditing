import os
import re


def natural_sort_key(path):
    name = os.path.basename(path).lower()
    parts = re.split(r"(\d+)", name)
    return [int(part) if part.isdigit() else part for part in parts]


def _scan_folder(folder, recursive, sort_files, allowed_exts):
    exts = tuple(ext.strip().lower() for ext in allowed_exts.split(",") if ext.strip())

    files = []
    if recursive:
        for root, dirs, filenames in os.walk(folder):
            for f in filenames:
                if any(f.lower().endswith(ext) for ext in exts):
                    files.append(os.path.join(root, f))
    else:
        for f in os.listdir(folder):
            full_path = os.path.join(folder, f)
            if os.path.isfile(full_path) and any(f.lower().endswith(ext) for ext in exts):
                files.append(full_path)

    if sort_files:
        files.sort(key=natural_sort_key)

    return files


class LuAudioDirectoryLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_dir": ("STRING", {"default": ""}),
                "recursive": ("BOOLEAN", {"default": False}),
                "file_ext": (["all", "wav", "mp3", "m4a", "aac", "flac", "ogg"], {"default": "all"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("audio_paths",)
    FUNCTION = "load_audio_folder"
    CATEGORY = "Comfyui-LuAudioEditing"

    def load_audio_folder(self, audio_dir, recursive=False, file_ext="all"):
        audio_dir = audio_dir.strip().strip('"')

        if not audio_dir:
            raise RuntimeError("audio_dir 不能为空。")

        if not os.path.exists(audio_dir):
            raise RuntimeError(f"音频目录不存在：{audio_dir}")

        if not os.path.isdir(audio_dir):
            raise RuntimeError(f"路径不是目录：{audio_dir}")

        if file_ext == "all":
            exts = ".wav,.mp3,.m4a,.aac,.flac,.ogg"
        else:
            exts = f".{file_ext}"

        files = _scan_folder(audio_dir, recursive, True, exts)

        if not files:
            raise RuntimeError(
                f"在目录中未找到音频文件：{audio_dir}\n"
                f"允许的扩展名：{exts}"
            )

        return ("\n".join(files),)
