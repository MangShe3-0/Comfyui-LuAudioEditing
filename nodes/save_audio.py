import os
import shutil
import tempfile

import numpy as np
import wave


_CODEC_MAP = {
    "wav": "pcm_s16le",
    "mp3": "libmp3lame",
    "m4a": "aac",
    "aac": "aac",
    "flac": "flac",
    "ogg": "libvorbis",
}


class LuAudioSave:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "save_folder": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    OUTPUT_NODE = True
    FUNCTION = "save_audio"
    CATEGORY = "Comfyui-LuAudioEditing"

    def save_audio(self, audio, save_folder, **kwargs):
        import subprocess as sp

        save_folder = save_folder.strip().strip('"')
        if not save_folder:
            raise RuntimeError("save_folder 不能为空。")

        output_format = audio.get("output_format", "") or ""
        if not output_format:
            src_path = audio.get("source_path", "") or ""
            if src_path and isinstance(src_path, str):
                output_format = os.path.splitext(src_path)[1].lstrip(".")
            else:
                output_format = "wav"
        output_format = output_format.lower()

        stem = "saved_audio"
        fn = audio.get("filename", "") or ""
        if fn and isinstance(fn, str) and fn.strip():
            stem = fn.strip()
        else:
            src_path = audio.get("source_path", "") or ""
            if src_path and isinstance(src_path, str):
                base = os.path.splitext(os.path.basename(src_path))[0]
                if base:
                    stem = base

        os.makedirs(save_folder, exist_ok=True)

        final_path = os.path.join(save_folder, f"{stem}.{output_format}")
        counter = 1
        while os.path.exists(final_path):
            final_path = os.path.join(save_folder, f"{stem}_{counter}.{output_format}")
            counter += 1

        waveform = audio["waveform"]
        sample_rate = int(audio["sample_rate"])

        if waveform.ndim == 3:
            waveform = waveform[0]

        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_wav = os.path.join(tmp_dir, "temp.wav")

            try:
                wf = waveform.detach().cpu().float().clamp(-1.0, 1.0)
                audio_np = wf.transpose(0, 1).numpy()
                audio_i16 = (audio_np * 32767.0).astype(np.int16)

                with wave.open(temp_wav, "wb") as wh:
                    wh.setnchannels(audio_i16.shape[1])
                    wh.setsampwidth(2)
                    wh.setframerate(sample_rate)
                    wh.writeframes(audio_i16.tobytes())

                if output_format == "wav":
                    shutil.copy2(temp_wav, final_path)
                else:
                    codec = _CODEC_MAP.get(output_format, "pcm_s16le")
                    cmd = [
                        "ffmpeg", "-y", "-i", temp_wav,
                        "-c:a", codec, final_path,
                    ]
                    sp.run(cmd, capture_output=True, text=True, check=True,
                           encoding="utf-8", errors="replace")
            except Exception as e:
                raise RuntimeError(
                    f"[Comfyui-LuAudioEditing] 音频保存失败。\n"
                    f"保存目录：{save_folder}\n"
                    f"目标文件：{final_path}\n"
                    f"错误信息：{e}"
                )

        print(f"[Comfyui-LuAudioEditing] save audio -> {final_path}")
        return ()
