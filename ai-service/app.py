# ai-service/app.py

import os
import json
import time
import numpy as np
import librosa
import tensorflow as tf
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from flask import Flask, request, jsonify

app = Flask(__name__)

MODELS_DIR = 'models'
CRNN_EXTRACTOR_PATH = os.path.join(MODELS_DIR, 'crnn_feature_extractor_final.h5')
XGB_MODEL_PATH = os.path.join(MODELS_DIR, 'hybrid_xgboost_model.joblib')
SCALER_PATH = os.path.join(MODELS_DIR, 'hybrid_feature_scaler.joblib')
LABEL_ENCODER_PATH = os.path.join(MODELS_DIR, 'hybrid_label_encoder.joblib')
GENRES_PATH = os.path.join(MODELS_DIR, 'genres.json')

SAMPLE_RATE = 22050
N_MELS = 128
HOP_LENGTH = 512
N_FFT = 2048
CHUNK_DURATION = 2.0
SAMPLES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_DURATION)

crnn_encoder = None
xgb_model = None
scaler = None
le = None
genres_list = []

class SpecAugment(tf.keras.layers.Layer):
    def __init__(self, freq_mask_param, time_mask_param, **kwargs):
        super(SpecAugment, self).__init__(**kwargs)
        self.freq_mask_param = freq_mask_param
        self.time_mask_param = time_mask_param
    def call(self, inputs, training=None):
        if not training: return inputs
        input_squeezed = tf.squeeze(inputs, axis=-1)
        input_shape = tf.shape(input_squeezed)
        batch_size, freq_max, time_max = input_shape[0], input_shape[1], input_shape[2]
        f = tf.random.uniform([], 0, self.freq_mask_param, dtype=tf.int32)
        f0 = tf.random.uniform([], 0, freq_max - f, dtype=tf.int32)
        freq_mask = tf.concat([tf.ones((f0, time_max)), tf.zeros((f, time_max)), tf.ones((freq_max - f0 - f, time_max))], axis=0)
        t = tf.random.uniform([], 0, self.time_mask_param, dtype=tf.int32)
        t0 = tf.random.uniform([], 0, time_max - t, dtype=tf.int32)
        time_mask = tf.concat([tf.ones((freq_max, t0)), tf.zeros((freq_max, t)), tf.ones((freq_max, time_max - t0 - t))], axis=1)
        mask = tf.expand_dims(freq_mask * time_mask, -1)
        return inputs * tf.cast(mask, dtype=inputs.dtype)

def load_models():
    global crnn_encoder, xgb_model, scaler, le, genres_list

    print(" * Loading models...")
    try:
        le = joblib.load(LABEL_ENCODER_PATH)
        genres_list = le.classes_.tolist()
        print(f" * LabelEncoder loaded. Genres: {genres_list}")
    except FileNotFoundError:
        print(f"!!! FILE {LABEL_ENCODER_PATH} NOT FOUND. USING GENRES FROM genres.json OR DEFAULTS !!!")
        try:
            with open(GENRES_PATH, "r") as f:
                genres_list = json.load(f)
            le = LabelEncoder()
            le.fit(genres_list)
            print(f" * Genres loaded from {GENRES_PATH}: {genres_list}")
        except FileNotFoundError:
            print("!!! genres.json FILE NOT FOUND. USING DEFAULT GENRES !!!")
            genres_list = [
                "Electronic", "Experimental", "Folk", "Hip-Hop",
                "Instrumental", "International", "Pop", "Rock"
            ]
            le = LabelEncoder()
            le.fit(genres_list)


    try:
        scaler = joblib.load(SCALER_PATH)
        print(f" * StandardScaler loaded from {SCALER_PATH}")
    except FileNotFoundError:
        print(f"!!! FILE {SCALER_PATH} NOT FOUND. PREDICTIONS MAY BE INCORRECT !!!")
        scaler = StandardScaler()

    try:
        crnn_full_model = tf.keras.models.load_model(
            CRNN_EXTRACTOR_PATH,
            custom_objects={'SpecAugment': SpecAugment}
        )
        encoder_output = crnn_full_model.get_layer("gru_embedding").output
        crnn_encoder = tf.keras.models.Model(inputs=crnn_full_model.input, outputs=encoder_output)
        del crnn_full_model
        tf.keras.backend.clear_session()
        print(f" * CRNN Feature Extractor loaded from {CRNN_EXTRACTOR_PATH}")
    except FileNotFoundError:
        print(f"!!! FILE {CRNN_EXTRACTOR_PATH} NOT FOUND. SERVICE WILL NOT FUNCTION !!!")
        crnn_encoder = None
    except Exception as e:
        print(f"!!! ERROR LOADING CRNN MODEL: {e} !!!")
        crnn_encoder = None

    try:
        xgb_model = joblib.load(XGB_MODEL_PATH)
        print(f" * XGBoost Model loaded from {XGB_MODEL_PATH}")
    except FileNotFoundError:
        print(f"!!! FILE {XGB_MODEL_PATH} NOT FOUND. SERVICE WILL NOT FUNCTION !!!")
        xgb_model = None
    except Exception as e:
        print(f"!!! ERROR LOADING XGBOOST MODEL: {e} !!!")
        xgb_model = None

    if not all([crnn_encoder, xgb_model, scaler, le]):
        print("!!! NOT ALL MODELS LOADED. SERVICE MAY FUNCTION INCORRECTLY OR THROW ERRORS !!!")
    print(" * Model loading complete.")


@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "Audio file not found in request"}), 400

    audio_file = request.files['file']
    if not audio_file.filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
        return jsonify({"error": "Unsupported file format. Please upload MP3, WAV, FLAC, or OGG."}), 400

    if not all([crnn_encoder, xgb_model, scaler, le]):
        return jsonify({"error": "Models not loaded or loaded incorrectly. Please check server logs."}), 500

    print(f" * Received prediction request for file: {audio_file.filename}")
    start_time = time.time()

    try:
        signal, sr = librosa.load(audio_file, sr=SAMPLE_RATE, mono=True)

        chunk_specs = []
        for i in range(0, len(signal), SAMPLES_PER_CHUNK):
            chunk = signal[i:i + SAMPLES_PER_CHUNK]
            if len(chunk) == SAMPLES_PER_CHUNK:
                mel_spec = librosa.feature.melspectrogram(y=chunk, sr=sr, n_mels=N_MELS, hop_length=HOP_LENGTH, n_fft=N_FFT)
                db_spec = librosa.power_to_db(mel_spec, ref=np.max)
                chunk_specs.append(db_spec)

        if not chunk_specs:
            return jsonify({"error": "Could not extract audio chunks from the file. The file might be too short (less than 2 seconds) or corrupted."}), 422

        chunks_np = np.array(chunk_specs)[..., np.newaxis]
        embeddings = crnn_encoder.predict(chunks_np, verbose=0, batch_size=64)

        track_embedding = np.mean(embeddings, axis=0)

        scaled_features = scaler.transform(track_embedding.reshape(1, -1))

        probabilities_array = xgb_model.predict_proba(scaled_features)[0]

        probabilities = {
            genre: float(prob) for genre, prob in zip(genres_list, probabilities_array)
        }

        top_genre_index = np.argmax(probabilities_array)
        top_genre = genres_list[top_genre_index]

        response_data = {
            "top_genre": top_genre,
            "genre_probabilities": probabilities
        }

        end_time = time.time()
        print(f" * Prediction completed in {end_time - start_time:.2f} seconds. Top genre: {top_genre}")

        return jsonify(response_data)

    except librosa.utils.exceptions.NoAudioFileError:
        return jsonify({"error": "Could not load audio file. It might be corrupted or have an unsupported format."}), 400
    except Exception as e:
        print(f"!!! ERROR PROCESSING REQUEST: {e} !!!")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


if __name__ == "__main__":
    load_models()
    app.run(host='0.0.0.0', port=5001, debug=True)