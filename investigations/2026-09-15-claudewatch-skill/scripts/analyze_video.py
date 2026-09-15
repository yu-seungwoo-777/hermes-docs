#!/usr/bin/env python3
"""
claudewatch - 영상(릴스/유튜브/로컬 파일)을 프레임 단위로 분석할 준비를 하는 파이프라인.

역할 분담:
  - 이 스크립트: yt-dlp 다운로드 → ffmpeg 장면전환 기반 프레임 추출 → faster-whisper 자막 추출
  - 에이전트(모델): 추출된 프레임을 vision으로 직접 읽고 보고서 작성

사용법:
  python3 analyze_video.py <URL 또는 로컬 영상 파일> [--outdir 결과디렉토리] [--max-frames 24]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} 실패:\n{r.stderr[-2000:]}")
    return r.stdout


def download(url: str, outdir: Path) -> Path:
    out = outdir / "source.mp4"
    sh(["yt-dlp", "-o", str(out), "--recode-video", "mp4", "--no-playlist", url])
    return out


def probe_duration(video: Path) -> float:
    out = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
              "-of", "json", str(video)])
    return float(json.loads(out)["format"]["duration"])


def extract_frames(video: Path, outdir: Path, max_frames: int) -> list[Path]:
    """장면 전환 기준으로 대표 프레임 추출. 전환 프레임이 max_frames를 넘으면 균등 샘플로 대체."""
    frames_dir = outdir / "frames"
    frames_dir.mkdir(exist_ok=True)
    dur = probe_duration(video)

    # 1) 장면 전환 감지 시도 (임계 0.3)
    sh(["ffmpeg", "-y", "-i", str(video), "-vf",
        f"select='gt(scene,0.3)',scale=1080:-1", "-vsync", "vfr",
        str(frames_dir / "scene_%02d.jpg")])
    frames = sorted(frames_dir.glob("scene_*.jpg"))

    # 2) 부족하면 균등 간격 보충
    if len(frames) < max_frames // 2:
        step = max(dur / max_frames, 1.0)
        sh(["ffmpeg", "-y", "-i", str(video), "-vf",
            f"fps=1/{step},scale=1080:-1", "-vsync", "vfr",
            str(frames_dir / "even_%02d.jpg")])
        frames += sorted(frames_dir.glob("even_*.jpg"))

    return frames[:max_frames]


def extract_transcript(video: Path, outdir: Path) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "(faster-whisper 미설치 - 자막 생략. pip install faster-whisper)"
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(video), language="ko", vad_filter=True)
    lines = []
    for seg in segments:
        lines.append(f"[{seg.start:06.1f}s] {seg.text.strip()}")
    text = "\n".join(lines)
    (outdir / "transcript.txt").write_text(text, encoding="utf-8")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="영상 URL 또는 로컬 파일 경로")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--max-frames", type=int, default=24)
    args = ap.parse_args()

    outdir = Path(args.outdir or ".claudewatch")
    outdir.mkdir(parents=True, exist_ok=True)

    src = Path(args.source)
    if src.exists():
        video = src
    elif args.source.startswith("http"):
        print("[1/3] yt-dlp 다운로드 중...")
        video = download(args.source, outdir)
    else:
        sys.exit(f"소스를 찾을 수 없습니다: {args.source}")

    print("[2/3] ffmpeg 프레임 추출 중...")
    frames = extract_frames(video, outdir, args.max_frames)

    print("[3/3] 자막 추출 중 (faster-whisper small, ko)...")
    transcript = extract_transcript(video, outdir)

    index = {
        "source": args.source,
        "video": str(video),
        "duration_sec": probe_duration(video),
        "frames": [str(f) for f in frames],
        "transcript": str(outdir / "transcript.txt"),
    }
    (outdir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n완료. 프레임 {len(frames)}개 + 자막 추출됨.")
    print(f"다음 단계(에이전트): index.json의 frames를 vision으로 읽고 보고서 작성")
    print(f"결과 디렉토리: {outdir.resolve()}")


if __name__ == "__main__":
    main()
