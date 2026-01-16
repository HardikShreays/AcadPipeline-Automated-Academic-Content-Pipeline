#!/usr/bin/env python3
"""
Process a single audio chunk: transcribe and post-process.
"""
import sys
import os
from faster_whisper import WhisperModel
from post_processing import AllMerged

# Initialize Whisper model (cache it globally for efficiency)
_model = None

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(
            "base",
            device="auto",
            compute_type="int8",
        )
    return _model

def transcribe_chunk(audio_path: str) -> str:
    """Transcribe a single audio chunk using Whisper."""
    model = get_model()
    
    segments, info = model.transcribe(
        audio_path,
        # decoding
        beam_size=5,
        temperature=0.0,
        best_of=1,
        
        # CRITICAL: stop repetition + punctuation collapse
        repetition_penalty=1.2,
        no_repeat_ngram_size=3,
        
        # Hindi-safe thresholds
        compression_ratio_threshold=1.6,
        log_prob_threshold=-1.2,
        no_speech_threshold=0.7,
        
        # break loops
        condition_on_previous_text=False,
        
        # VAD (keep)
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 700
        },
        
        # DO NOT suppress tokens or blanks
        suppress_blank=False,
        suppress_tokens=None,
    )
    
    text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
    return text

def process_chunk(audio_path: str) -> str:
    """
    Process a single chunk: transcribe and post-process.
    
    Args:
        audio_path: Path to the audio chunk file
        
    Returns:
        Processed text string
    """
    # Transcribe
    raw_text = transcribe_chunk(audio_path)
    
    if not raw_text.strip():
        return ""
    
    # Post-process
    processed_text = AllMerged(raw_text)
    
    return processed_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_chunk.py <audio_chunk_path>", file=sys.stderr)
        sys.exit(1)
    
    audio_path = sys.argv[1]
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = process_chunk(audio_path)
        print(result)
    except Exception as e:
        print(f"Error processing chunk: {e}", file=sys.stderr)
        sys.exit(1)
