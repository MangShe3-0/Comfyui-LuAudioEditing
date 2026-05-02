from .nodes.folder_loader import LuAudioDirectoryLoader
from .nodes.concat_audio import LuAudioConcat
from .nodes.convert_audio_single import LuAudioConvertSingle
from .nodes.convert_audio_batch import LuAudioConvertBatch
from .nodes.mix_audio import LuAudioMix
from .nodes.save_audio import LuAudioSave

NODE_CLASS_MAPPINGS = {
    "LuAudioDirectoryLoader": LuAudioDirectoryLoader,
    "LuAudioConcat": LuAudioConcat,
    "LuAudioConvertSingle": LuAudioConvertSingle,
    "LuAudioConvertBatch": LuAudioConvertBatch,
    "LuAudioMix": LuAudioMix,
    "LuAudioSave": LuAudioSave,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LuAudioDirectoryLoader": "Lu 音频目录读取",
    "LuAudioConcat": "Lu 批量拼合音频",
    "LuAudioConvertSingle": "Lu 单个音频格式转换",
    "LuAudioConvertBatch": "Lu 批量音频格式转换",
    "LuAudioMix": "Lu 双轨混音",
    "LuAudioSave": "Lu 保存音频",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
