import socket
import argparse
import signal
import pyaudio
import sys
import queue
from datetime import datetime

def handler(signum, frame):
    global recordStream, client_socket
    print("Exiting the program")
    recordStream.stop_stream()
    recordStream.close()
    pyaudioObj.terminate()
    client_socket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, handler)

parser = argparse.ArgumentParser(description="AudioStream client")
parser.add_argument("--protocol", required=False, default='tcp', choices=['udp', 'tcp'])
parser.add_argument("--host", required=True, help="Server IP address")
parser.add_argument("--port", required=False, default=12345, type=int)
parser.add_argument("--size", required=False, default=10, type=int, choices=range(10, 151, 10))
args = parser.parse_args()

print(f"Connecting to {args.host}:{args.port} using {args.protocol.upper()}")

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 441
NUMCHUNKS = int(args.size / 10)

sendQueue = queue.Queue()
silence = 0
silenceData = silence.to_bytes(2) * CHUNK * NUMCHUNKS
sequenceNumber = 0

def record(data, frame_count, time_info, status):
    global sendQueue
    sendQueue.put(data)
    return (silenceData, pyaudio.paContinue)

pyaudioObj = pyaudio.PyAudio()

try:
    recordStream = pyaudioObj.open(format=FORMAT,
                                  channels=CHANNELS,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=NUMCHUNKS * CHUNK,
                                  stream_callback=record)
except Exception as e:
    print(f"Error opening audio stream: {e}")
    sys.exit(1)

print("PyAudio Device Initialized")

try:
    if args.protocol == 'udp':
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    else:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((args.host, args.port))
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)

def sendAudio():
    global client_socket, sequenceNumber, sendQueue
    
    try:
        audioData = sendQueue.get()
        seqBytes = sequenceNumber.to_bytes(2, byteorder="little", signed=False)
        sendData = seqBytes + audioData

        print(f"Sending Sequence #{sequenceNumber} ({len(sendData)} bytes)")

        if args.protocol == 'udp':
            client_socket.sendto(sendData, (args.host, args.port))
        else:
            client_socket.sendall(sendData)

        sequenceNumber = (sequenceNumber + 1) % 65536
    except Exception as e:
        print(f"Error sending audio: {e}")
        handler(signal.SIGINT, None)

while True:
    sendAudio()