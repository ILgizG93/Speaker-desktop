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

def play(sound: str, settings) -> None:
    global stream 
    thread = []
    
    devices = settings.device.get('outputs')
    stream = list(StreamData(value.get('device_index')) for value in devices.values() if value.get('is_active') and value.get('volume') > 0)
    for indx, s in enumerate(stream):
        thread.append(SoundThread(indx, SoundData(sound)))
        s.outstream.start()
        thread[indx].start()
