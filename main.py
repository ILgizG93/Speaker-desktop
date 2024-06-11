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

    asyncio.run(speaker.get_fake_schedule_data())

    sys.exit(app.exec())

def test():
    import av

    audio = av.open('18409601_2_RUS.wav').streams.audio[0]
    audio_data = {
        'format': audio.container.format.name,
        'channels': audio.codec_context.channels,
        'codec_name': audio.codec_context.format.container_name,
        'codec_name_full': audio.codec_context.name,
        'samplerate': audio.codec_context.sample_rate
    }
    pass


if __name__ == "__main__":
    main()
