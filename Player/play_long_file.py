from __future__ import division, print_function
import queue
import sys
import threading
import sounddevice as sd
import soundfile as sf


class Player:
    filename = f'C:/PythonProjects/airport/assets/Kamado Tanjiro No Uta.mp3'
    blocksize = 2048
    buffersize = 20
    q = queue.Queue(maxsize=buffersize)
    event = threading.Event()

    def callback(self, outdata, frames, time, status):
        assert frames == self.blocksize
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        assert not status
        try:
            data = self.q.get_nowait()
        except queue.Empty:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):] = b'\x00' * (len(outdata) - len(data))
            raise sd.CallbackStop
        else:
            outdata[:] = data


    def play(self):
        with sf.SoundFile(self.filename) as f:
            for _ in range(self.buffersize):
                data = f.buffer_read(self.blocksize, dtype='float32')
                if not data:
                    break
                self.q.put_nowait(data)

            # stream = sd.RawOutputStream(samplerate=f.samplerate, blocksize=blocksize, device=args.device, channels=f.channels, dtype='float32', callback=callback, finished_callback=event.set)
            stream = sd.RawOutputStream(samplerate=f.samplerate, blocksize=self.blocksize, channels=f.channels, dtype='float32', callback=self.callback, finished_callback=self.event.set)
            with stream:
                timeout = self.blocksize * self.buffersize / f.samplerate
                while data:
                    data = f.buffer_read(self.blocksize, dtype='float32')
                    self.q.put(data, timeout=timeout)
                self.event.wait()
