#!/usr/bin/env python3
"""
youtube-watch - 유튜브(및 yt-dlp 지원 사이트) 영상을 프레임+자막으로 분석 준비하는 파이프라인.

역할 분담:
  - 이 스크립트: yt-dlp 다운로드 → ffmpeg 장면전환 기반 프레임 추출 → faster-whisper 자막 추출
  - 에이전트(모델): 추출된 프레임을 vision으로 직접 읽고 보고서 작성 (§3 출력 계약)

사용법:
  python3 analyze_video.py <URL 또는 로컬 영상 파일> [--outdir 결과디렉토리] [--max-frames 24]
  python3 analyze_video.py --selftest          # 네트워크 불요 검증 (§2.4 검증 계약)
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_FRAMES_DEFAULT = 24


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
    """장면 전환 기준으로 대표 프레임 추출. 전환 프레임이 절반에 못 미치면 균등 샘플로 보충."""
    frames_dir = outdir / "frames"
    frames_dir.mkdir(exist_ok=True)
    dur = probe_duration(video)

    # 1) 장면 전환 감지 시도 (임계 0.3)
    sh(["ffmpeg", "-y", "-i", str(video), "-vf",
        "select='gt(scene,0.3)',scale=1080:-1", "-vsync", "vfr",
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


def extract_transcript(video: Path, outdir: Path, language: str = "ko") -> str:
    """타임스탬프 자막 추출. [0000.0s] 형식 — 컷별 표의 시간축 조인 기준."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return "(faster-whisper 미설치 - 자막 생략. pip install faster-whisper)"
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(video), language=language, vad_filter=True)
    lines = []
    for seg in segments:
        lines.append(f"[{seg.start:06.1f}s] {seg.text.strip()}")
    text = "\n".join(lines)
    (outdir / "transcript.txt").write_text(text, encoding="utf-8")
    return text


def make_synthetic_clip(path: Path, seconds: int = 3) -> None:
    """selftest용 합성 클립 생성 (ffmpeg testsrc, 네트워크 불요)."""
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i",
        f"testsrc=duration={seconds}:size=640x360:rate=10",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-shortest", str(path)])


def selftest() -> int:
    """§2.4 검증 계약: 합성 클립 → 파이프라인 전체 → 산출물 판정. 네트워크 불요."""
    print("[selftest] 1/4 ffmpeg 합성 클립 생성 (3초)...")
    with tempfile.TemporaryDirectory(prefix="ytw_selftest_") as td:
        tdir = Path(td)
        clip = tdir / "synthetic.mp4"
        try:
            make_synthetic_clip(clip)
        except RuntimeError as e:
            print(f"FAIL: ffmpeg 합성 클립 생성 실패\n{e}")
            return 1

        print("[selftest] 2/4 프레임 추출...")
        outdir = tdir / "out"
        outdir.mkdir()
        try:
            frames = extract_frames(clip, outdir, MAX_FRAMES_DEFAULT)
        except RuntimeError as e:
            print(f"FAIL: 프레임 추출 실패\n{e}")
            return 1
        if not frames:
            print("FAIL: 프레임이 하나도 추출되지 않음")
            return 1
        if not all(f.exists() and f.stat().st_size > 0 for f in frames):
            print("FAIL: 빈 프레임 파일 존재")
            return 1

        print("[selftest] 3/4 자막 추출 (faster-whisper)...")
        try:
            extract_transcript(clip, outdir, language="en")
        except Exception as e:  # whisper 로딩 오류 등
            print(f"FAIL: 자막 추출 실패\n{e}")
            return 1
        transcript = outdir / "transcript.txt"
        if not transcript.exists():
            print("FAIL: transcript.txt 미생성")
            return 1

        print("[selftest] 4/4 index.json 생성...")
        index = {
            "source": "selftest",
            "video": str(clip),
            "duration_sec": probe_duration(clip),
            "frames": [str(f) for f in frames],
            "transcript": str(transcript),
        }
        (outdir / "index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        if not (outdir / "index.json").exists():
            print("FAIL: index.json 미생성")
            return 1

    print(f"PASS: 프레임 {len(frames)}장 + transcript.txt + index.json 생성 확인 (exit 0)")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?", help="영상 URL 또는 로컬 파일 경로")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES_DEFAULT)
    ap.add_argument("--selftest", action="store_true",
                    help="네트워크 불요 검증 실행 (성공: exit 0)")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.source:
        ap.error("source 필요 (URL 또는 로컬 파일). 검증만 하려면 --selftest")

    outdir = Path(args.outdir or ".youtube-watch")
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
    extract_transcript(video, outdir)

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
    print("다음 단계(에이전트): index.json의 frames를 vision으로 읽고 보고서 작성")
    print(f"결과 디렉토리: {outdir.resolve()}")


if __name__ == "__main__":
    main()
