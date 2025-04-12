import streamlit as st
import speech_recognition as sr
import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import serial
import pywhatkit
import pyautogui
from dotenv import load_dotenv
from ultralytics import YOLO
import cv2

# Lấy lệnh giọng nói
def get_voice_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎤 Nói lệnh điều khiển:")
        st.write("Bạn muốn làm gì?")
        audio = r.listen(source, timeout=10, phrase_time_limit=15)
    try:
        command = r.recognize_google(audio, language="vi-VN")
        st.write(f"🗣️ Bạn nói: {command}")
        return command.lower()
    except sr.UnknownValueError:
        st.write("Không hiểu bạn nói gì.")
        st.write("Mình không nghe rõ, bạn nói lại nhé.")
        return None

# Điều khiển nhạc (Spotify)
def control_music(sp, command):
    device_id = get_device_id(sp)
    if "dừng" in command or "tạm dừng" in command:
        sp.pause_playback(device_id=device_id)
        st.write("Đã dừng nhạc.")
    elif "tiếp tục" in command or "phát tiếp" in command:
        sp.start_playback(device_id=device_id)
        st.write("Tiếp tục phát nhạc.")
    elif "bài tiếp" in command or "tiếp theo" in command:
        sp.next_track(device_id=device_id)
        st.write("Chuyển bài tiếp.")
    elif "bài trước" in command:
        sp.previous_track(device_id=device_id)
        st.write("Quay lại bài trước.")
    elif "tăng âm lượng" in command:
        volume = sp.current_playback()['device']['volume_percent']
        new_volume = min(volume + 10, 100)
        sp.volume(new_volume, device_id=device_id)
        st.write("Đã tăng âm lượng.")
    elif "giảm âm lượng" in command:
        volume = sp.current_playback()['device']['volume_percent']
        new_volume = max(volume - 10, 0)
        sp.volume(new_volume, device_id=device_id)
        st.write("Đã giảm âm lượng.")
    else:
        play_song(sp, command)  # Nếu không phải lệnh điều khiển, coi là tên bài hát

# Phát bài hát trên Spotify
def play_song(sp, song_name):
    results = sp.search(q=song_name, type='track', limit=1)
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        uri = track['uri']
        st.write(f"🎵 Đang bật: {track['name']} - {track['artists'][0]['name']}")
        device_id = get_device_id(sp)
        if device_id:
            sp.start_playback(device_id=device_id, uris=[uri])
        else:
            st.write("Không tìm thấy thiết bị phát.")
    else:
        st.write("Không tìm thấy bài hát.")

# Kết nối Spotify
def connect_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-private"
    ))

# Tìm thiết bị đang hoạt động trên Spotify
def get_device_id(sp):
    devices = sp.devices()
    for device in devices['devices']:
        if device['is_active']:
            return device['id']
    if devices['devices']:
        return devices['devices'][0]['id']
    return None

# Kết nối với Arduino và điều khiển đèn
def control_light(command):
    ser = serial.Serial('COM8', 9600, timeout=1)  # Cổng Serial (đổi lại nếu cần)
    time.sleep(2)  # Đợi Arduino reset
    if "bật đèn" in command:
        ser.write(b'1')
        st.write("🔆 Đã bật đèn!")
    elif "tắt đèn" in command:
        ser.write(b'0')
        st.write("🌑 Đã tắt đèn!")
    else:
        st.write("❓ Lệnh không hiểu, hãy nói 'bật đèn' hoặc 'tắt đèn'.")

# Điều khiển YouTube
def control_youtube(command):
    if "bật" in command or "phát" in command:
        query = command.replace("bật", "").replace("phát", "").strip()
        st.write(f"🔍 Đang tìm: {query}")
        pywhatkit.playonyt(query)
        time.sleep(8)  # Chờ YouTube load
    elif "dừng" in command:
        pyautogui.hotkey("ctrl", "w")  # Đóng tab YouTube
        st.write("❌ Đã dừng phát.")
    else:
        st.write("Lệnh chưa được hỗ trợ.")

# Giao diện người dùng Streamlit với 3 chức năng
st.title("Ứng dụng Điều khiển Thiết bị Thông minh")

# Điều khiển đèn
if st.button("Bắt đầu điều khiển đèn"):
    st.write("🎤 Đang lắng nghe lệnh điều khiển đèn...")
    command = get_voice_command()
    if command:
        control_light(command)

# Điều khiển nhạc
if st.button("Bắt đầu điều khiển nhạc"):
    st.write("🎤 Đang lắng nghe lệnh điều khiển nhạc...")
    command = get_voice_command()
    if command:
        sp = connect_spotify()
        control_music(sp, command)

# Điều khiển YouTube
if st.button("Bắt đầu điều khiển YouTube"):
    st.write("🎤 Đang lắng nghe lệnh điều khiển YouTube...")
    command = get_voice_command()
    if command:
        control_youtube(command)
