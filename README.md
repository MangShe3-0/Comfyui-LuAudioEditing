# Comfyui-LuAudioEditing

ComfyUI 音频编辑节点包，基于 FFmpeg，实现音频读取、拼接、格式转换、双轨混音和保存。

## 功能列表

- **Lu 音频目录读取** — 扫描指定目录，批量读取音频文件路径
- **Lu 批量拼合音频** — 将多个音频按顺序拼接成一个音频，支持混合格式输入
- **Lu 单个音频格式转换** — 将 ComfyUI AUDIO 对象转换为指定格式并保存到文件
- **Lu 批量音频格式转换** — 批量转换多个音频文件到指定格式，自动保存到子文件夹
- **Lu 双轨混音** — 将两路音频同时叠加混合，支持独立音量控制
- **Lu 保存音频** — 将 AUDIO 对象保存为文件，自动继承格式和文件名信息

## 安装方法

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/你的用户名/Comfyui-LuAudioEditing.git
cd Comfyui-LuAudioEditing
pip install -r requirements.txt
```

然后重启 ComfyUI。

## FFmpeg 安装说明

本项目需要 FFmpeg 作为音频处理引擎，请确保 `ffmpeg` 命令可在终端调用。

### Windows

1. 下载 FFmpeg：https://ffmpeg.org/download.html
2. 将 `bin` 目录（包含 ffmpeg.exe）添加到系统 PATH
3. 在终端执行 `ffmpeg -version` 确认安装成功

### Linux

```bash
sudo apt install ffmpeg
```

### macOS

```bash
brew install ffmpeg
```

## 节点说明

### Lu 音频目录读取 (`LuAudioDirectoryLoader`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio_dir | STRING | 音频目录路径 |
| recursive | BOOLEAN | 是否递归扫描子目录 |
| file_ext | COMBO | 文件扩展名过滤（all/wav/mp3/m4a/aac/flac/ogg） |

输出：`audio_paths` (STRING, 多行文本)

### Lu 批量拼合音频 (`LuAudioConcat`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio_paths | STRING | 多个音频路径，每行一个 |

输出：`audio` (AUDIO)

### Lu 单个音频格式转换 (`LuAudioConvertSingle`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio | AUDIO | 输入音频 |
| output_format | COMBO | 输出格式 |
| output_name | STRING | 输出文件名 |
| output_folder | STRING | 输出目录 |
| audio_codec | COMBO | 音频编码器 |

输出：`audio` (AUDIO)

### Lu 批量音频格式转换 (`LuAudioConvertBatch`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio_paths | STRING | 多个音频路径，每行一个 |
| output_format | COMBO | 输出格式 |
| output_folder | STRING | 父级保存目录 |
| audio_codec | COMBO | 音频编码器 |

终点节点，无输出口。自动在 `output_folder` 下创建 `converted_audio` 子文件夹保存文件。

### Lu 双轨混音 (`LuAudioMix`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio1 | AUDIO | 第一轨音频 |
| audio2 | AUDIO | 第二轨音频 |
| duration_mode | COMBO | 混音时长模式（longest/shortest/first） |
| audio1_volume | FLOAT | 第一轨音量（0.0 - 5.0） |
| audio2_volume | FLOAT | 第二轨音量（0.0 - 5.0） |

输出：`audio` (AUDIO)

### Lu 保存音频 (`LuAudioSave`)

| 参数 | 类型 | 说明 |
|------|------|------|
| audio | AUDIO | 输入音频 |
| save_folder | STRING | 保存目录路径 |

终点节点，无输出口。自动从 audio 对象继承格式和文件名信息。

## 示例工作流

参考 `examples/workflow_examples.json` 导入示例工作流。

## 注意事项

- 所有音频节点均使用 Python 标准库 `wave` 读写 WAV，不依赖 `torchaudio`、`torchcodec`、`soundfile`
- FFmpeg 为系统依赖，必须预先安装
- 批量格式转换节点和保存节点为终点节点（OUTPUT_NODE = True），无数据输出口
- 文件名重复时自动追加 `_1`、`_2` 等后缀，不覆盖已有文件

## License

MIT
