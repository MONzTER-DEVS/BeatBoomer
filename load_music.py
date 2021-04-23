
def load_music(path: str):
    import json
    import librosa
    import numpy as np

    music_name = path
    y, sr = librosa.load(music_name, dtype=float)        # y is waveform and sr is sampling rate, idk wut they do but still

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    print("tempo:", tempo)

    stft = (librosa.stft(y, hop_length=512, n_fft=1024))  # getting a matrix which contains amplitudes acc to freq and time
    spectrogram = librosa.amplitude_to_db(stft, ref=np.max)  # converting the matrix to decibel matrix ##

    spec = np.abs(librosa.core.stft(y, n_fft=1024, hop_length=512))
    duration = librosa.core.get_duration(filename=music_name)

    freqs = librosa.core.fft_frequencies(n_fft=1024)  # getting an array of freq ##
    # getting an array of time periodic
    times = librosa.core.frames_to_time(np.arange(spectrogram.shape[1]), sr=sr, hop_length=512, n_fft=1024)
    time_index_ratio = len(times)/times[len(times) - 1] ##
    frequencies_index_ratio = len(freqs)/freqs[len(freqs)-1] ##

    data = {
        "music_name": music_name,
        "beat_times": beat_times.tolist(),
        "tempo": tempo
    }

    with open("music_data.json", "w") as f:
        json.dump(data, f)
