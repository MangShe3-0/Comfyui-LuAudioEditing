import os
import shutil
import subprocess
import tempfile

import numpy as np
import torch
import wave


class LuAudioMix:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio1": ("AUDIO",),
                "audio2": ("AUDIO",),
                "duration_mode": (["longest", "shortest", "first"], {"default": "longest"}),
                "audio1_volume": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.05,
                }),
                "audio2_volume": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 5.0,
                    "step": 0.05,
                }),
            }
        }

    RETURN_TYPES = ("AUDIO",)
    RETURN_NAMES = ("audio",)
    FUNCTION = "mix_audio"
    CATEGORY = "Comfyui-LuAudioEditing"

    def _write_audio_to_wav(self, audio, wav_path):
        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])

        if waveform.ndim == 3:
            waveform = waveform[0]

        wf = waveform.detach().cpu().float().clamp(-1.0, 1.0)
        audio_np = wf.transpose(0, 1).numpy()
        audio_i16 = (audio_np * 32767.0).astype(np.int16)

        with wave.open(wav_path, "wb") as wh:
            wh.setnchannels(audio_i16.shape[1])
            wh.setsampwidth(2)
            wh.setframerate(sample_rate)
            wh.writeframes(audio_i16.tobytes())

    def mix_audio(self, audio1, audio2, duration_mode, audio1_volume, audio2_volume, **kwargs):
        if audio1_volume is None:
            audio1_volume = 1.0
        audio1_volume = float(audio1_volume)

        if audio2_volume is None:
            audio2_volume = 1.0
        audio2_volume = float(audio2_volume)

        if not shutil.which("ffmpeg"):
            raise RuntimeError("没有找到 ffmpeg。请确认 ffmpeg 已安装，并且已经加入系统 PATH。")

        with tempfile.TemporaryDirectory() as tmp_dir:
            wav1 = os.path.join(tmp_dir, "audio1.wav")
            wav2 = os.path.join(tmp_dir, "audio2.wav")
            mixed_wav = os.path.join(tmp_dir, "mixed.wav")

            try:
                self._write_audio_to_wav(audio1, wav1)
                self._write_audio_to_wav(audio2, wav2)
            except Exception as e:
                raise RuntimeError(f"[Comfyui-LuAudioEditing] 写入临时音频失败：{e}")

            filter_complex = (
                f"[0:a]volume={audio1_volume},"
                f"aresample=44100,"
                f"aformat=sample_fmts=flt:channel_layouts=stereo[a0];"
                f"[1:a]volume={audio2_volume},"
                f"aresample=44100,"
                f"aformat=sample_fmts=flt:channel_layouts=stereo[a1];"
                f"[a0][a1]amix=inputs=2:duration={duration_mode}:normalize=1[outa]"
            )

            cmd = [
                "ffmpeg", "-y",
                "-i", wav1,
                "-i", wav2,
                "-filter_complex", filter_complex,
                "-map", "[outa]",
                "-ac", "2",
                "-ar", "44100",
                "-c:a", "pcm_s16le",
                mixed_wav,
            ]

            try:
                subprocess.run(
                    cmd, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", check=True,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    f"[Comfyui-LuAudioEditing] 多轨混音失败。\n"
                    f"FFmpeg 错误信息：\n{e.stderr}"
                )

            try:
                with wave.open(mixed_wav, "rb") as wf:
                    channels = wf.getnchannels()
                    sample_rate = wf.getframerate()
                    frames = wf.readframes(wf.getnframes())

                audio_np = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                audio_np = audio_np.reshape(-1, channels).T
                waveform = torch.from_numpy(audio_np).unsqueeze(0)
            except Exception as e:
                raise RuntimeError(f"[Comfyui-LuAudioEditing] 读取混音结果失败：{e}")

        print(
            f"[Comfyui-LuAudioEditing] mix audio: "
            f"vol1={audio1_volume}, vol2={audio2_volume}, "
            f"duration={duration_mode}"
        )
        return ({"waveform": waveform, "sample_rate": sample_rate},)
