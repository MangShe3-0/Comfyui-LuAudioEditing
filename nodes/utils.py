import os
import re
import shutil
import subprocess

import folder_paths

_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}

_LOSSY_CODECS = {"libmp3lame", "aac", "libvorbis"}

_AUDIO_CODEC_MAP = {
    "wav": "pcm_s16le",
    "mp3": "libmp3lame",
    "m4a": "aac",
    "aac": "aac",
    "flac": "flac",
    "ogg": "libvorbis",
}


def parse_path_lines(text):
    paths = []
    for line in text.split("\n"):
        line = line.strip().strip("'\"")
        if line:
            paths.append(line)
    return paths


def validate_files(paths, allowed_exts, label):
    exts_str = ", ".join(sorted(allowed_exts))
    for p in paths:
        if not os.path.exists(p):
            raise RuntimeError(f"{label}文件不存在：{p}")
        ext = os.path.splitext(p)[1].lower()
        if ext not in allowed_exts:
            raise RuntimeError(f"不支持的{label}格式：{p}\n支持的格式：{exts_str}")


def ensure_output_dir(output_subfolder):
    output_dir = folder_paths.get_output_directory()
    if output_subfolder:
        output_dir = os.path.join(output_dir, output_subfolder)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def resolve_output_dir(folder):
    if os.path.isabs(folder):
        output_dir = folder
    else:
        output_dir = os.path.join(folder_paths.get_output_directory(), folder)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def unique_path(output_dir, output_name):
    base, ext = os.path.splitext(output_name)
    candidate = os.path.join(output_dir, output_name)
    if not os.path.exists(candidate):
        return candidate
    counter = 1
    while True:
        candidate = os.path.join(output_dir, f"{base}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', "", name)


def ensure_extension(filename, output_format):
    filename = filename.strip()
    expected_ext = f".{output_format}"
    base, ext = os.path.splitext(filename)
    if ext.lower() != expected_ext:
        filename = f"{base}{expected_ext}"
    return filename


def get_audio_codec(output_format, codec):
    if codec == "auto":
        return _AUDIO_CODEC_MAP[output_format]
    return codec


def build_audio_cmd(input_path, output_path, audio_codec, sample_rate, channels,
                    bitrate, overwrite_flag, allow_copy=True):
    cmd = ["ffmpeg", overwrite_flag, "-i", input_path, "-vn"]
    if audio_codec == "copy" and allow_copy:
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", audio_codec]
        if audio_codec in _LOSSY_CODECS:
            cmd += ["-b:a", bitrate]
    if sample_rate != "keep":
        cmd += ["-ar", sample_rate]
    if channels == "mono":
        cmd += ["-ac", "1"]
    elif channels == "stereo":
        cmd += ["-ac", "2"]
    cmd.append(output_path)
    return cmd


def run_ffmpeg(cmd, task_name, index=None, input_path=None, output_path=None):
    try:
        subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as e:
        lines = [f"FFmpeg {task_name} 失败"]
        if index is not None:
            lines[0] += f"（序号 {index}）"
        lines.append("")
        if input_path:
            lines.append(f"输入：{input_path}")
        if output_path:
            lines.append(f"输出：{output_path}")
        lines.append("")
        lines.append(f"执行命令：\n{' '.join(cmd)}")
        lines.append("")
        lines.append(f"错误信息：\n{e.stderr}")
        raise RuntimeError("\n".join(lines))
