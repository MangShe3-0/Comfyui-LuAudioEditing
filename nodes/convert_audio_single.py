import os
import shutil
import subprocess
import tempfile

import folder_paths
from .utils import (
    resolve_output_dir,
    unique_path,
    ensure_extension,
    get_audio_codec,
    build_audio_cmd,
    run_ffmpeg,
)


class LuAudioConvertSingle:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "output_format": (["wav", "mp3", "m4a", "aac", "flac", "ogg"], {"default": "wav"}),
                "output_name": ("STRING", {"default": "converted_audio"}),
                "output_folder": ("STRING", {"default": "ffmpeg_convert_audio_single"}),
                "audio_codec": (
                    ["auto", "pcm_s16le", "libmp3lame", "aac", "flac", "libvorbis"],
                    {"default": "auto"},
                ),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "convert_audio"
    CATEGORY = "Comfyui-LuAudioEditing"

    def convert_audio(self, audio, output_format="wav",
                      output_name="converted_audio",
                      output_folder="ffmpeg_convert_audio_single",
                      audio_codec="auto", **kwargs):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("没有找到 ffmpeg。请确认 ffmpeg 已安装，并且已经加入系统 PATH。")

        audio_codec = get_audio_codec(output_format, audio_codec)
        output_name = ensure_extension(output_name, output_format)
        output_dir = resolve_output_dir(output_folder)
        output_path = unique_path(output_dir, output_name)

        import torch
        import numpy as np
        import wave

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_input = os.path.join(tmp_dir, "input.wav")

            waveform = audio["waveform"]
            sample_rate = int(audio["sample_rate"])
            if waveform.ndim == 3:
                waveform = waveform[0]
            wf = waveform.detach().cpu().float().clamp(-1.0, 1.0)
            audio_np = wf.transpose(0, 1).numpy()
            audio_i16 = (audio_np * 32767.0).astype(np.int16)

            with wave.open(temp_input, "wb") as wh:
                wh.setnchannels(audio_i16.shape[1])
                wh.setsampwidth(2)
                wh.setframerate(sample_rate)
                wh.writeframes(audio_i16.tobytes())

            cmd = build_audio_cmd(temp_input, output_path, audio_codec,
                                  "keep", "keep", "192k", "-n", allow_copy=False)
            run_ffmpeg(cmd, "单个音频格式转换", input_path=temp_input, output_path=output_path)

        with tempfile.TemporaryDirectory() as load_tmp:
            load_wav = os.path.join(load_tmp, "load.wav")
            load_cmd = [
                "ffmpeg", "-y", "-i", output_path,
                "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le", load_wav,
            ]
            subprocess.run(load_cmd, capture_output=True, text=True, check=True,
                           encoding="utf-8", errors="replace")

            import wave
            import numpy as np

            with wave.open(load_wav, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())

            audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            audio_np = audio_np.reshape(-1, channels).T
            waveform = torch.from_numpy(audio_np).unsqueeze(0)
            result = {"waveform": waveform, "sample_rate": sample_rate}
            result["output_format"] = output_format
            result["audio_codec"] = audio_codec
            result["filename"] = os.path.splitext(output_name)[0]
            result["source_path"] = output_path

        print(f"[Comfyui-LuAudioEditing] convert audio single -> {output_path}")
        return (result,)
