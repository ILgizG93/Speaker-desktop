import sys
import asyncio

from PySide6.QtWidgets import QApplication

from settings import SpeakerSetting
from UI.MainWindow import SpeakerApplication
from WinAPI.Device import AudioInterface

def main():

    app = QApplication(sys.argv)
    settings = SpeakerSetting()
    interface = AudioInterface(settings)
    speaker = SpeakerApplication(settings, interface)
    # speaker.showMaximized()
    speaker.show()

    asyncio.run(speaker.get_schedule_data_from_API())

    sys.exit(app.exec())

def test():

    import av
    from math import ceil

    audio = av.open('C:/PythonProjects/airport/modules/speaker/audio_files/18415750_2_RUS.wav').streams.audio[0]
    audio_data = {
        'duration': ceil(audio.container.duration / 1_000_000),
        'format': audio.container.format.name,
        'channels': audio.codec_context.channels,
        'codec_name': audio.codec_context.format.container_name,
        'codec_name_full': audio.codec_context.name,
        'samplerate': audio.codec_context.sample_rate
    }

    import soundfile as sf
    DATA_TYPE = "float32"
    audio = sf.read('C:/PythonProjects/airport/modules/speaker/audio_files/18415750_2_RUS.wav', dtype=DATA_TYPE)

    pass

if __name__ == "__main__":
    # test()
    
    main()
