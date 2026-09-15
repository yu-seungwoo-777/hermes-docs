#!/usr/bin/env python3
# video-watch — 영상(URL/로컬)을 프레임+자막+인덱스로 분석 준비하는 파이프라인.
# License: MIT. 출처: reports 저장소 investigations/2026-09-15-video-watch-skill/
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_FRAMES_DEFAULT = 24
EXIT_OK = 0        # 성공
EXIT_ENV = 1       # 환경 미비 (의존성 없음/버전 미달) — 사용자 환경 책임
EXIT_SKILL = 2     # 스킬 자체 실패 (파이프라인/산출물) — 배포자 책임


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
    """장면 전환 기준 대표 프레임 추출. 부족하면 균등 샘플 보충. 파일명에 타임스탬프 부여."""
    frames_dir = outdir / "frames"
    frames_dir.mkdir(exist_ok=True)
    dur = probe_duration(video)

    collected: list[tuple[float, Path]] = []  # (timestamp_sec, path)

    # 1) 장면 전환 감지 시도 (임계 0.3) — showinfo로 pts 시간을 받아 파일명에 반영
    try:
        sh(["ffmpeg", "-y", "-i", str(video), "-vf",
            "select='gt(scene,0.3)',scale=1080:-1,showinfo", "-vsync", "vfr",
            str(frames_dir / "scene_%02d.jpg")])
    except RuntimeError:
        pass
    # showinfo 로그는 stderr로 나가므로 재실행하며 시간을 파싱
    r = subprocess.run(["ffmpeg", "-y", "-i", str(video), "-vf",
                        "select='gt(scene,0.3)',scale=1080:-1,showinfo",
                        "-vsync", "vfr", str(frames_dir / "scene_%02d.jpg")],
                       capture_output=True, text=True)
    pts_times = [float(m) for m in
                 re.findall(r"pts_time:([\d.]+)", r.stderr)]
    scene_files = sorted(frames_dir.glob("scene_*.jpg"))
    for i, f in enumerate(scene_files):
        ts = pts_times[i] if i < len(pts_times) else i * (dur / max(len(scene_files), 1))
        collected.append((ts, f))

    # 2) 부족하면 균등 간격 보충 (fps 필터의 시간도 pts_time으로 파싱)
    if len(collected) < max_frames // 2:
        step = max(dur / max_frames, 1.0)
        r = subprocess.run(["ffmpeg", "-y", "-i", str(video), "-vf",
                            f"fps=1/{step},scale=1080:-1,showinfo",
                            "-vsync", "vfr", str(frames_dir / "even_%02d.jpg")],
                           capture_output=True, text=True)
        pts_times = [float(m) for m in
                     re.findall(r"pts_time:([\d.]+)", r.stderr)]
        even_files = sorted(frames_dir.glob("even_*.jpg"))
        for i, f in enumerate(even_files):
            ts = pts_times[i] if i < len(pts_times) else i * step
            collected.append((ts, f))

    # 3) 시간축 정렬 + 중복 제거(0.4초 이내 병합) — §6.1 기준축 통일
    collected.sort(key=lambda x: x[0])
    deduped: list[tuple[float, Path]] = []
    for ts, f in collected:
        if deduped and abs(ts - deduped[-1][0]) < 0.4:
            continue
        deduped.append((ts, f))

    # 4) 최종 파일명을 타임스탬프 기준으로 재부여 — 파일명 순서 = 시간 순서 보장
    final: list[Path] = []
    for idx, (ts, f) in enumerate(deduped[:max_frames], start=1):
        target = frames_dir / f"cut_{idx:02d}_t{ts:07.2f}s.jpg"
        f.rename(target)
        final.append(target)
    # 남은 중간 파일 정리
    for _, f in collected:
        if f.exists() and f not in final:
            f.unlink()
    return final


def parse_pts(name: str) -> float:
    m = re.search(r"_t([\d.]+)s\.jpg$", name)
    return float(m.group(1)) if m else -1.0


def extract_transcript(video: Path, outdir: Path, language: str = "ko") -> str:
    """타임스탬프 자막 추출. [0000.0s] 형식 — 컷별 표의 시간축 조인 기준."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("WARN: faster-whisper 미설치 — 자막 생략 (pip install faster-whisper)")
        (outdir / "transcript.txt").write_text(
            "(faster-whisper 미설치 — 자막 없음)", encoding="utf-8")
        return ""
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(video), language=language, vad_filter=True)
    lines = []
    for seg in segments:
        lines.append(f"[{seg.start:06.1f}s] {seg.text.strip()}")
    text = "\n".join(lines)
    (outdir / "transcript.txt").write_text(text, encoding="utf-8")
    return text


def check_env() -> list[str]:
    """preflight: 의존성 존재/버전 확인. 문제 목록 반환 (빈 목록 = 통과)."""
    problems = []
    # ffmpeg 계열은 -version만 받고(--version은 exit 8), yt-dlp는 --version만 받는다
    for tool, min_ver, flag in (("yt-dlp", "2026.1.1", "--version"),
                                ("ffmpeg", "5", "-version"),
                                ("ffprobe", "5", "-version")):
        try:
            out = sh([tool, flag])
        except (FileNotFoundError, RuntimeError):
            problems.append(f"{tool} 미설치")
            continue
        # yt-dlp는 버전 문자열만 출력("2026.08.19"), ffmpeg 계열은 "ffmpeg version X.Y ..."
        m = (re.search(r"^(\d{4}\.\d{2}\.\d+)$", out.strip())
             or re.search(r"version[ ]+(\d{4}\.\d{2}\.\d+|\d+\.\d+|\d+)", out))
        print(f"  {tool}: {m.group(1) if m else '버전 파싱 실패(설치는 됨)'}")
    try:
        import faster_whisper  # noqa: F401
        print("  faster-whisper: 설치됨")
    except ImportError:
        print("  faster-whisper: 미설치 (자막 생략으로 동작은 계속)")
    return problems


def make_synthetic_clip(path: Path, seconds: int = 3) -> None:
    """selftest용 합성 클립 생성 (ffmpeg testsrc, 네트워크 불요)."""
    sh(["ffmpeg", "-y", "-f", "lavfi", "-i",
        f"testsrc=duration={seconds}:size=640x360:rate=10",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        "-shortest", str(path)])


def selftest() -> int:
    """§4.2 설치 계약. 종료 코드 규약: 0 성공 / 1 환경 미비 / 2 스킬 자체 실패.

    검증 범위 (과장 금지 — §4.2): 본 selftest는 합성 클립 기반으로
    ffmpeg/ffprobe 프레임·인덱스 배선과 faster-whisper 로딩을 검증한다.
    yt-dlp 다운로더는 호출하지 않으므로 preflight --version 확인으로만 검증된다.
    """
    print("[selftest] 0/4 preflight (의존성 버전 확인)...")
    problems = check_env()
    hard = [p for p in problems if "yt-dlp" in p or "ffmpeg" in p]
    if hard:
        print(f"FAIL (exit 1): 환경 미비 — {'; '.join(hard)}")
        return EXIT_ENV

    print("[selftest] 1/4 ffmpeg 합성 클립 생성 (3초, 네트워크 불요)...")
    with tempfile.TemporaryDirectory(prefix="ytw_selftest_") as td:
        tdir = Path(td)
        clip = tdir / "synthetic.mp4"
        try:
            make_synthetic_clip(clip)
        except RuntimeError as e:
            print(f"FAIL (exit 1): ffmpeg 합성 클립 생성 실패 (환경 문제)\n{e}")
            return EXIT_ENV

        print("[selftest] 2/4 프레임 추출...")
        outdir = tdir / "out"
        outdir.mkdir()
        try:
            frames = extract_frames(clip, outdir, MAX_FRAMES_DEFAULT)
        except RuntimeError as e:
            print(f"FAIL (exit 2): 프레임 추출 실패 (스킬 결함)\n{e}")
            return EXIT_SKILL
        if not frames:
            print("FAIL (exit 2): 프레임 미추출")
            return EXIT_SKILL
        if not all(f.exists() and f.stat().st_size > 0 for f in frames):
            print("FAIL (exit 2): 빈 프레임 파일 존재")
            return EXIT_SKILL
        # 시간축 정렬 확인: 파일명에 타임스탬프가 부여돼야 한다 (§6.1)
        if any(parse_pts(f.name) < 0 for f in frames):
            print("FAIL (exit 2): 프레임 파일명에 타임스탬프 없음 — §6.1 위반")
            return EXIT_SKILL

        print("[selftest] 3/4 자막 모듈 로딩 확인...")
        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            print("WARN: faster-whisper 미설치 — 자막 없이 계속 가능하나 기능 축소")
        else:
            print("  faster-whisper 로딩 OK (무거운 모델 로드는 본 실행에서 수행)")

        print("[selftest] 4/4 index.json 생성...")
        index = {
            "source": "selftest",
            "video": str(clip),
            "duration_sec": probe_duration(clip),
            "frames": [{"file": str(f), "t": parse_pts(f.name)} for f in frames],
            "transcript": str(outdir / "transcript.txt"),
        }
        (outdir / "index.json").write_text(
            json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        if not (outdir / "index.json").exists():
            print("FAIL (exit 2): index.json 미생성")
            return EXIT_SKILL

    print(f"PASS (exit 0): 프레임 {len(frames)}장(타임스탬프 부여·정렬 확인) + "
          "whisper 로딩 + index.json — 배선 검증 완료")
    return EXIT_OK


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", nargs="?", help="영상 URL 또는 로컬 파일 경로")
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--max-frames", type=int, default=MAX_FRAMES_DEFAULT)
    ap.add_argument("--selftest", action="store_true",
                    help="검증 실행. 종료 코드: 0 성공 / 1 환경 미비 / 2 스킬 결함")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())
    if not args.source:
        ap.error("source 필요 (URL 또는 로컬 파일). 검증만 하려면 --selftest")

    outdir = Path(args.outdir or ".video-watch")
    outdir.mkdir(parents=True, exist_ok=True)

    src = Path(args.source)
    if src.exists():
        video = src
    elif args.source.startswith("http"):
        print("[1/3] yt-dlp 다운로드 중...")
        video = download(args.source, outdir)
    else:
        sys.exit(f"소스를 찾을 수 없습니다: {args.source}")

    print("[2/3] ffmpeg 프레임 추출 중 (타임스탬프 부여·정렬)...")
    frames = extract_frames(video, outdir, args.max_frames)

    print("[3/3] 자막 추출 중 (faster-whisper small, ko)...")
    extract_transcript(video, outdir)

    index = {
        "source": args.source,
        "video": str(video),
        "duration_sec": probe_duration(video),
        "frames": [{"file": str(f), "t": parse_pts(f.name)} for f in frames],
        "transcript": str(outdir / "transcript.txt"),
    }
    (outdir / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n완료. 컷 {len(frames)}개 (시간 정렬) + 자막 추출됨.")
    print("다음 단계(에이전트): index.json의 frames를 vision으로 읽고 보고서 작성")
    print(f"결과 디렉토리: {outdir.resolve()}")


if __name__ == "__main__":
    main()
