import numpy as np
from PySide6.QtCore import QThread, Signal
import sounddevice as sd
import subprocess
import json

from numpy import ndarray
from sounddevice import RawOutputStream
from soundfile import read as read_soundfile
from threading import Thread

DATA_TYPE = "int16"

class SoundData:
    def __init__(self, path: str):
        self.music = self._load_sound_file_into_memory(path)

    def _load_sound_file_into_memory(self, path: str) -> ndarray:
        audio_data, _ = read_soundfile(path, dtype=DATA_TYPE)
        return audio_data

class StreamData:
    def __init__(self, indx: str) -> None:
        self.outstream = self._create_running_output_stream(indx)

    def _create_running_output_stream(self, indx: str) -> RawOutputStream: 
        output = RawOutputStream(
            device = indx,
            dtype = DATA_TYPE
        )
        return output

class SoundThread(Thread):
    def __init__(self, stream_indx: str, sound_file: SoundData) -> None:
        Thread.__init__(self)
        self.stream_indx = stream_indx
        self.sound_file = sound_file

    def run(self) -> None:
        stream[self.stream_indx].outstream.write(self.sound_file.music)

class AudioTrigger(QThread):
    position_changed = Signal(int)

    # def __init__(self, position_callback, playback_speed=1.0):
    def __init__(self, playback_speed=0.5):
        super().__init__()
        self.audio_data = None
        self.adjusted_audio_data = None
        self.position = 0
        self.samplerate = 44100
        self.channels = 2
        self.codec = 'f32le'
        self.codec_name = 'pcm_f32le'
        # self.position_callback = position_callback
        self.playing = False
        self.file_path = None
        self.playback_speed = playback_speed
        self.buffer_size = 1024 * 10

    def set_audio_file(self, file_path):
        if self.playing:
            self.stop()
        self.file_path = file_path

        # Получение информации о аудиофайле
        probe = subprocess.run(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_streams', file_path], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        probe_output = json.loads(probe.stdout.decode('utf-8'))
        audio_stream = next((stream for stream in probe_output['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_stream is None:
            raise ValueError("File doesn't contain audio streams")

        
        self.samplerate = int(audio_stream['sample_rate'])
        self.channels = (int(audio_stream['channels']), 2)[int(audio_stream['channels']) == 1]

        command = ['ffmpeg', '-v', 'quiet', '-i', file_path, '-f', self.codec, '-acodec', self.codec_name, '-ac', '2', '-ar', str(self.samplerate), '-']
        self.input_stream = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)

        self.audio_data = self.read_audio_blocks()

        self.position = 0
        self.adjusted_audio_data = self.audio_data

    def read_audio_blocks(self):
        audio_blocks = []
        while True:
            audio_bytes = self.input_stream.stdout.read(self.buffer_size * self.channels * 4)  # 4 bytes per float32
            if not audio_bytes:
                break
            audio_array = np.frombuffer(audio_bytes, np.float32)
            audio_blocks.append(np.reshape(audio_array, (-1, self.channels)))
        return np.concatenate(audio_blocks)
    
    def set_devices(self, settings):
        self.devices = tuple(map(lambda dev: dev[1].get('device_index'), list(filter(lambda item: item[1].get('is_active') == 1, settings.device.get('outputs').items()))))

    def run(self):
        self.playing = True
        block_size = 1024

        self.position_changed.emit(self.position)

        with sd.OutputStream(samplerate=self.samplerate * self.playback_speed, device=self.devices, channels=self.channels, dtype='float32', blocksize=block_size, callback=self.callback, latency='low'):
            print(f"Stream opened: samplerate={self.samplerate}, channels={self.channels}")

            while self.position < len(self.audio_data) and self.playing:
                self.msleep(10)

        self.playing = False
        print("Stream closed")

    def set_playback_speed(self, speed):
        self.playback_speed = speed

    def callback(self, outdata, frames, time, status):
        if self.position < len(self.audio_data):
            remaining = len(self.audio_data) - self.position
            current_block = min(remaining, frames)

            outdata[:current_block, :] = self.adjusted_audio_data[self.position:self.position + current_block, :]
            self.position += current_block

            # if callable(self.position_callback):
            #     self.position_callback(self.calculate_slider_position())
        else:
            outdata[:frames, :] = 0

    def stop(self):
        if self.playing:
            self.playing = False
            self.position = 0
            # if callable(self.position_callback):
            #     self.position_callback(0)

    def set_audio_position(self, position):
        self.position = int(position * len(self.audio_data))
        # if callable(self.position_callback):
        #     self.position_callback(position)

    def is_playing(self):
        return self.playing

    def set_volume(self, volume):
        if self.audio_data is not None:
            self.adjusted_audio_data = self.audio_data * volume

    def calculate_slider_position(self):
        return int(self.position / len(self.audio_data) * 100.0)
