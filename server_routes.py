# import socket
# import argparse
# import signal
# import pyaudio
# import sys
# from datetime import datetime
# import wave

# def handler(signum, frame):
#     global playStream, server_socket, connection, output_file
#     print("Exiting the program")
#     playStream.stop_stream()
#     playStream.close()
#     pyaudioObj.terminate()
#     if 'connection' in globals():
#         connection.close()
#     server_socket.close()
#     if output_file:
#         output_file.close()
#     sys.exit(0)

# signal.signal(signal.SIGINT, handler)

# parser = argparse.ArgumentParser(description="AudioStream server")
# parser.add_argument("--protocol", required=False, default='tcp', choices=['udp', 'tcp'])
# parser.add_argument("--port", required=False, default=12345, type=int)
# parser.add_argument("--size", required=False, default=10, type=int, choices=range(10, 151, 10))
# parser.add_argument("--save", required=False, help="Save audio to file (WAV format)")
# args = parser.parse_args()

# print(f"Starting server on port {args.port} using {args.protocol.upper()}")
# if args.save:
#     print(f"Audio will be saved to {args.save}")

# FORMAT = pyaudio.paInt16
# CHANNELS = 1
# RATE = 44100
# CHUNK = 441
# NUMCHUNKS = int(args.size / 10)

# pyaudioObj = pyaudio.PyAudio()

# try:
#     playStream = pyaudioObj.open(format=FORMAT,
#                                channels=CHANNELS,
#                                rate=RATE,
#                                output=True,
#                                frames_per_buffer=CHUNK * NUMCHUNKS)
# except Exception as e:
#     print(f"Error opening audio stream: {e}")
#     sys.exit(1)

# silence = 0
# silenceData = silence.to_bytes(2) * CHUNK * NUMCHUNKS

# if args.save:
#     try:
#         output_file = wave.open(args.save, 'wb')
#         output_file.setnchannels(CHANNELS)
#         output_file.setsampwidth(pyaudio.get_sample_size(FORMAT))
#         output_file.setframerate(RATE)
#     except Exception as e:
#         print(f"Error opening output file: {e}")
#         output_file = None

# if args.protocol == 'udp':
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     server_socket.bind(('0.0.0.0', args.port))
# else:
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.bind(('0.0.0.0', args.port))
#     server_socket.listen(1)
#     print("Waiting for connection...")
#     connection, source = server_socket.accept()
#     print(f"Connected to {source[0]}:{source[1]}")

# expectedSeqNum = 0

# def recvData():
#     global expectedSeqNum, connection, output_file
    
#     print(f"Expecting Sequence #{expectedSeqNum}")

#     try:
#         if args.protocol == 'udp':
#             data, address = server_socket.recvfrom(CHUNK * NUMCHUNKS * 2 + 2)
#         else:
#             data = connection.recv(CHUNK * NUMCHUNKS * 2 + 2)
#             while len(data) < CHUNK * NUMCHUNKS * 2 + 2:
#                 data += connection.recv(CHUNK * NUMCHUNKS * 2 + 2 - len(data))
#     except Exception as e:
#         print(f"Error receiving data: {e}")
#         handler(signal.SIGINT, None)
#         return

#     sequenceNumber = int.from_bytes(data[:2], byteorder="little", signed=False)
#     audioData = data[2:]

#     if expectedSeqNum == sequenceNumber:
#         print(f"Received Sequence #{sequenceNumber} ({len(data)} bytes)")
#         playStream.write(audioData)
#         if output_file:
#             output_file.writeframes(audioData)
#         expectedSeqNum = (expectedSeqNum + 1) % 65536
#     else:
#         print(f"Received Out of Sequence #{sequenceNumber} ({len(data)} bytes)")
#         playStream.write(silenceData)
#         if sequenceNumber > expectedSeqNum:
#             expectedSeqNum = sequenceNumber + 1

# while True:
#     recvData()

import socket
import time
import os
import wave

# Konfigurasi Server
HOST = '0.0.0.0'  # Artinya server akan menerima koneksi dari IP manapun di jaringan
PORT = 12345      # Port yang akan didengarkan oleh server

# Konfigurasi Audio (Harus sesuai dengan pengaturan di aplikasi Android)
CHANNELS = 1              # 1 untuk mono, 2 untuk stereo
SAMPLE_WIDTH = 2          # 2 bytes untuk 16-bit audio
FRAME_RATE = 44100        # Standard CD quality sample rate

# Tentukan nama folder dan buat jika belum ada
REKORDING_FOLDER = 'rekaman'
if not os.path.exists(REKORDING_FOLDER):
    os.makedirs(REKORDING_FOLDER)
    print(f"Folder '{REKORDING_FOLDER}' berhasil dibuat.")

def handle_client_connection(conn, addr):
    """
    Fungsi ini menangani seluruh komunikasi dengan satu klien yang terhubung.
    """
    print(f"Terhubung dengan klien dari alamat: {addr}")

    # Gunakan bytearray untuk mengumpulkan semua data audio yang masuk
    all_audio_data = bytearray()

    try:
        while True:
            # Terima header (8 byte: 4 byte untuk nomor urut, 4 byte untuk panjang data)
            header = conn.recv(8)
            if not header:
                print(f"Koneksi dengan {addr} ditutup oleh klien.")
                break

            # Ekstrak informasi dari header
            seq_num = int.from_bytes(header[:4], 'big')
            length = int.from_bytes(header[4:], 'big')

            # Terima data audio sesuai panjang dari header
            data_buffer = b''
            while len(data_buffer) < length:
                packet = conn.recv(length - len(data_buffer))
                if not packet:
                    raise ConnectionError("Koneksi terputus saat menerima data audio.")
                data_buffer += packet
            
            print(f"Menerima Sequence #{seq_num} ({len(data_buffer)} bytes)")
            
            # Tambahkan data yang baru diterima ke buffer utama
            all_audio_data.extend(data_buffer)

    except ConnectionResetError:
        print(f"Koneksi direset secara paksa oleh {addr}")
    except ConnectionError as e:
        print(f"Error Koneksi: {e}")
    except Exception as e:
        print(f"Terjadi error tak terduga: {e}")
    finally:
        # === LOGIKA BARU: TULIS FILE WAV SETELAH SEMUA DATA DITERIMA ===
        if all_audio_data:
            print(f"Total data audio yang diterima: {len(all_audio_data)} bytes.")
            # Buat nama file unik dan path lengkapnya
            nama_file = f"rekaman_{int(time.time())}.wav"
            path_lengkap = os.path.join(REKORDING_FOLDER, nama_file)

            try:
                # Gunakan modul 'wave' untuk membuat file .wav yang valid
                with wave.open(path_lengkap, 'wb') as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(SAMPLE_WIDTH)
                    wav_file.setframerate(FRAME_RATE)
                    wav_file.writeframes(all_audio_data)
                
                print(f"File rekaman berhasil disimpan dengan header yang valid di: {path_lengkap}")
            except Exception as e:
                print(f"Gagal saat menulis file .wav: {e}")

        else:
            print("Tidak ada data audio yang diterima dari klien.")
        
        print(f"Menutup koneksi dengan {addr}.")
        conn.close()

def start_server():
    """
    Fungsi utama untuk memulai server dan mendengarkan koneksi masuk.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server berhasil dimulai di port {PORT} menggunakan TCP")
    print(f"File rekaman akan disimpan di folder '{REKORDING_FOLDER}'")
    print("Menunggu koneksi dari klien...")

    while True:
        conn, addr = server_socket.accept()
        handle_client_connection(conn, addr)
        print("\nMenunggu koneksi dari klien berikutnya...")

# Titik masuk utama program
if __name__ == "__main__":
    start_server()
