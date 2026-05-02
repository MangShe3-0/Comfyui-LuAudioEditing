import os
import re
import shutil

from .utils import (
    parse_path_lines,
    validate_files,
    _AUDIO_EXTS,
    resolve_output_dir,
    get_audio_codec,
    build_audio_cmd,
    run_ffmpeg,
)


class LuAudioConvertBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_paths": ("STRING", {"multiline": True, "default": ""}),
                "output_format": (["wav", "mp3", "m4a", "aac", "flac", "ogg"], {"default": "wav"}),
                "output_folder": ("STRING", {"default": "ffmpeg_convert_audio_batch"}),
                "audio_codec": (
                    ["auto", "pcm_s16le", "libmp3lame", "aac", "flac", "libvorbis", "copy"],
                    {"default": "auto"},
                ),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    OUTPUT_NODE = True
    FUNCTION = "convert_audio"
    CATEGORY = "Comfyui-LuAudioEditing"

    def convert_audio(self, audio_paths, output_format="wav",
                      output_folder="ffmpeg_convert_audio_batch",
                      audio_codec="auto", **kwargs):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("没有找到 ffmpeg。请确认 ffmpeg 已安装，并且已经加入系统 PATH。")

        paths = parse_path_lines(audio_paths)
        if not paths:
            raise RuntimeError("audio_paths 不能为空。请提供至少一个音频路径。")

        validate_files(paths, _AUDIO_EXTS, "音频")

        audio_codec = get_audio_codec(output_format, audio_codec)
        output_dir = resolve_output_dir(output_folder)

        sub_name = "converted_audio"
        sub_dir = os.path.join(output_dir, sub_name)
        counter = 1
        while os.path.exists(sub_dir):
            sub_dir = os.path.join(output_dir, f"{sub_name}_{counter}")
            counter += 1
        os.makedirs(sub_dir)

        converted_count = 0
        for input_path in paths:
            stem = os.path.splitext(os.path.basename(input_path))[0]
            stem = re.sub(r'[<>:"/\\|?*]', "", stem)
            output_name = f"{stem}.{output_format}"
            output_path = os.path.join(sub_dir, output_name)

            file_counter = 1
            while os.path.exists(output_path):
                output_path = os.path.join(sub_dir, f"{stem}_{file_counter}.{output_format}")
                file_counter += 1

            cmd = build_audio_cmd(input_path, output_path, audio_codec,
                                  "keep", "keep", "192k", "-n")
            run_ffmpeg(cmd, "批量音频格式转换", input_path=input_path, output_path=output_path)
            print(f"[Comfyui-LuAudioEditing] convert audio batch: {input_path} -> {output_path}")
            converted_count += 1

        print(f"[Comfyui-LuAudioEditing] batch convert audio -> {sub_dir}")
        print(f"[Comfyui-LuAudioEditing] converted count: {converted_count}")
        return ()
