import os
import shutil
import subprocess
import tempfile


class LuAudioConcat:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio_paths": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "concat_audio"
    CATEGORY = "Comfyui-LuAudioEditing"

    def concat_audio(self, audio_paths, **kwargs):
        if not shutil.which("ffmpeg"):
            raise RuntimeError("没有找到 ffmpeg。请确认 ffmpeg 已安装，并且已经加入系统 PATH。")

        paths = []
        for line in audio_paths.split("\n"):
            line = line.strip().strip("'\"")
            if line:
                paths.append(line)
        if not paths:
            raise RuntimeError("audio_paths 不能为空。请提供至少一个音频路径。")

        for p in paths:
            if not os.path.exists(p):
                raise RuntimeError(f"音频文件不存在：{p}")

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_wav = os.path.join(tmp_dir, "temp_concat.wav")

            n = len(paths)
            inputs = []
            for p in paths:
                inputs.extend(["-i", p])

            resample_parts = []
            concat_labels = []
            for i in range(n):
                resample_parts.append(
                    f"[{i}:a]aresample=44100,aformat=sample_fmts=s16:channel_layouts=stereo[a{i}]"
                )
                concat_labels.append(f"[a{i}]")

            filter_str = (
                ";".join(resample_parts)
                + ";"
                + "".join(concat_labels)
                + f"concat=n={n}:v=0:a=1[outa]"
            )

            cmd = [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filter_str,
                "-map", "[outa]",
                "-ac", "2",
                "-c:a", "pcm_s16le",
                output_wav,
            ]

            try:
                subprocess.run(cmd, capture_output=True, text=True, check=True,
                               encoding="utf-8", errors="replace")
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"FFmpeg 音频拼接失败。\n\n"
                    f"错误信息：\n{e.stderr}"
                )

            if not os.path.exists(output_wav):
                raise RuntimeError("FFmpeg 音频拼接失败，未生成输出文件。")

            import wave
            import numpy as np
            import torch

            with wave.open(output_wav, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                frames = wf.readframes(wf.getnframes())

            audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            audio_np = audio_np.reshape(-1, channels).T
            waveform = torch.from_numpy(audio_np).unsqueeze(0)
            audio = {"waveform": waveform, "sample_rate": sample_rate}

        return (audio,)
