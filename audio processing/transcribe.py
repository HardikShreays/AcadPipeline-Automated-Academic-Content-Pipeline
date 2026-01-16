import sys
import whisper
import torch

torch.set_num_threads(1)

audio_path = sys.argv[1]

model = whisper.load_model("small")

# result = model.transcribe(
#     audio_path,
#     # language="hi",
#     fp16=False,
#     verbose=False,

#     # 🔒 CRITICAL STABILITY SETTINGS
#     temperature=0.0,
#     beam_size=5,
#     best_of=1,

#     # 🔇 HALLUCINATION CONTROL
#     no_speech_threshold=0.6,
#     logprob_threshold=-1.0,
#     compression_ratio_threshold=2.4
# )

result = model.transcribe(
    audio_path,
    language="hi",
    fp16=False,
    verbose=False,

    # Determinism
    temperature=0.0,
    beam_size=5,
    best_of=1,

    # Hallucination control
    no_speech_threshold=0.7,              # ↑ more aggressive
    logprob_threshold=-1.2,
    compression_ratio_threshold=1.6,      # ↓ stricter for Hindi

    # Repetition control
    condition_on_previous_text=False,

    # 🔴 CRITICAL: stop long junk segments
    patience=0.0,                         # stop early if unsure
    suppress_tokens=[-1],                 # disable filler tokens
)



print(result["text"])
