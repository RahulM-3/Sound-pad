import shutil
from pathlib import Path

AUDIO_DIR = Path("audio")


class ProfileManager:
    def __init__(self):
        AUDIO_DIR.mkdir(exist_ok=True)
        if not self.get_profile_names():
            self.create_profile("Default")

    def get_profile_names(self):
        """Return directories inside audio/, each representing a profile."""
        return sorted(d.name for d in AUDIO_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))

    def load_profile(self, name: str) -> dict:
        """Scan the profile directory and return all .wav files."""
        profile_dir = AUDIO_DIR / name
        sounds = []
        if profile_dir.exists() and profile_dir.is_dir():
            for f in sorted(profile_dir.glob("*.wav")):
                # Use the file's stem (name without extension) as the playback label
                sounds.append({"label": f.stem, "file": str(f)})
        return {"name": name, "sounds": sounds}

    def create_profile(self, name: str):
        """Create a new folder for the profile."""
        (AUDIO_DIR / name).mkdir(exist_ok=True)

    def delete_profile(self, name: str):
        """Delete the profile folder and all its audio files."""
        path = AUDIO_DIR / name
        if path.exists() and path.is_dir():
            shutil.rmtree(path)

    def add_sound(self, profile_name: str, label: str, src_path: str,
                  data=None, sr: int = None) -> str:
        """Convert any audio to WAV, save directly into the profile's directory."""
        profile_dir = AUDIO_DIR / profile_name
        profile_dir.mkdir(exist_ok=True)
        
        # Clean label so it can be used as a safe filename
        safe_label = "".join(c for c in label if c.isalnum() or c in " _-") or "sound"
        dest = profile_dir / f"{safe_label}.wav"
        
        # Avoid filename collisions
        counter = 1
        while dest.exists():
            dest = profile_dir / f"{safe_label}_{counter}.wav"
            counter += 1

        if data is not None and sr is not None:
            import soundfile as sf
            sf.write(str(dest), data, sr)
        else:
            src = Path(src_path)
            try:
                import soundfile as sf
                d, s = sf.read(str(src), dtype="float32", always_2d=True)
                sf.write(str(dest), d, s)
            except Exception:
                from pydub import AudioSegment
                AudioSegment.from_file(str(src)).export(str(dest), format="wav")

        return str(dest)

    def remove_sound(self, profile_name: str, file_path: str):
        """Delete the specific audio file from the filesystem."""
        f = Path(file_path)
        if f.exists() and f.is_file():
            f.unlink()
