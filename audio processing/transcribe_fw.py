from faster_whisper import WhisperModel
from post_processing import AllMerged


audio_path = "../audios/chunks/chunk_10.wav"   # path to your audio

model = WhisperModel(
    "base",
    device="auto",
    compute_type="int8",
)

segments, info = model.transcribe(
    audio_path,
    # language="hi",

    # decoding
    beam_size=5,
    temperature=0.0,
    best_of=1,

    # 🔴 CRITICAL: stop repetition + punctuation collapse
    repetition_penalty=1.2,
    no_repeat_ngram_size=3,

    # 🔴 Hindi-safe thresholds
    compression_ratio_threshold=1.6,
    log_prob_threshold=-1.2,
    no_speech_threshold=0.7,

    # 🔴 break loops
    condition_on_previous_text=False,

    # 🔴 VAD (keep)
    vad_filter=True,
    vad_parameters={
        "min_silence_duration_ms": 700
    },

    # 🔴 DO NOT suppress tokens or blanks
    suppress_blank=False,
    suppress_tokens=None,
)

text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())









print(AllMerged(text))
