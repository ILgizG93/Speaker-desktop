from sounddevice import query_hostapis, query_devices
from comtypes import CLSCTX_ALL, CoCreateInstance, CLSCTX_INPROC_SERVER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, IMMDeviceEnumerator, EDataFlow, ERole
from pycaw.constants import CLSID_MMDeviceEnumerator
from ctypes import cast, POINTER


class AudioInterface(AudioUtilities):
    def __init__(self, settings):
        super().__init__()
        device_index = list(*(host.get('devices') for host in query_hostapis() if host.get('name') == settings.device.get('hostapi')))
        self.system_device = dict((dev.get('name'), dev.get('index')) for dev in query_devices() if dev.get('name').startswith(settings.device.get('name')) and dev.get('index') in device_index)

    # Переопределяем метод, чтобы можно было выбирать устройство по ID. По умолчанию выбирает только все устройства.
    @staticmethod
    def GetSpeaker(id=None):
        device_enumerator = CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX_INPROC_SERVER)
        if id is not None:
            return device_enumerator.GetDevice(id)
        else:
            return device_enumerator.GetDefaultAudioEndpoint(EDataFlow.eRender.value, ERole.eMultimedia.value)

    def set_device_volume(self, device_id: str, volume: int) -> None:
        speaker = self.GetSpeaker(device_id)
        interface = speaker.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
        if volume_interface == 0:
            volume.GetMute()
        else:
            volume_interface.SetMasterVolumeLevel(volume / 100 * 45 - 45, None)
