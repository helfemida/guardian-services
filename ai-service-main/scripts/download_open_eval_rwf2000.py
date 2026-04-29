import argparse
from pathlib import Path

import cv2
from huggingface_hub import hf_hub_download, list_repo_files


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download small open external eval set from RWF-2000 and extract JPEG frames."
    )
    parser.add_argument("--output-root", type=str, default="external_eval/rwf2000")
    parser.add_argument("--per-class", type=int, default=30, help="How many videos per class to sample.")
    parser.add_argument("--frame-pos", type=float, default=0.5, help="Frame position in [0,1], e.g. 0.5=middle.")
    parser.add_argument("--repo-id", type=str, default="valiantlynxz/godseye-violence-detection-dataset")
    return parser.parse_args()


def classify_path(path_str: str):
    s = path_str.lower()
    if any(tag in s for tag in ("/fight/", "\\fight/", "/violence/", "\\violence/")):
        return "violence"
    if any(
        tag in s for tag in ("/nonfight/", "\\nonfight/", "/non-fight/", "\\non-fight/", "/non_violence/", "\\non_violence/")
    ):
        return "non_violence"
    return None


def extract_frame(video_path: Path, out_path: Path, frame_pos: float) -> bool:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    target_idx = 0 if frame_count <= 1 else int(max(0.0, min(1.0, frame_pos)) * (frame_count - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_idx)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        return False
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return bool(cv2.imwrite(str(out_path), frame))


def safe_download(repo_id: str, repo_path: str, retries: int = 2) -> Path | None:
    for attempt in range(retries + 1):
        try:
            # Retry with force_download when cache checksum mismatch happens.
            local_path = hf_hub_download(
                repo_id=repo_id,
                repo_type="dataset",
                filename=repo_path,
                force_download=(attempt > 0),
            )
            return Path(local_path)
        except OSError as exc:
            if attempt >= retries:
                print(f"download_failed: {repo_path} ({exc})")
                return None
            print(f"retry_download[{attempt + 1}/{retries}]: {repo_path}")
    return None


def main():
    args = parse_args()
    output_root = Path(args.output_root)
    files = list_repo_files(repo_id=args.repo_id, repo_type="dataset")
    video_files = [f for f in files if f.lower().endswith((".avi", ".mp4", ".mov", ".mkv"))]
    # Keep original clips only to avoid duplicated "_processed" variants.
    video_files = [f for f in video_files if "_processed." not in f.lower()]
    violence_files = [f for f in video_files if classify_path(f) == "violence"][: args.per_class]
    non_violence_files = [f for f in video_files if classify_path(f) == "non_violence"][: args.per_class]

    if not violence_files or not non_violence_files:
        raise RuntimeError(
            "Could not detect both class folders in dataset repository structure. "
            "Inspect repository file tree and update classify_path()."
        )

    selected = [("violence", p) for p in violence_files] + [("non_violence", p) for p in non_violence_files]
    print(f"Selected videos: violence={len(violence_files)}, non_violence={len(non_violence_files)}")

    saved = 0
    failed_downloads = 0
    for label, repo_path in selected:
        local_video = safe_download(args.repo_id, repo_path, retries=2)
        if local_video is None:
            failed_downloads += 1
            continue
        stem = Path(repo_path).stem
        out_jpg = output_root / label / f"{stem}.jpg"
        ok = extract_frame(local_video, out_jpg, args.frame_pos)
        if ok:
            saved += 1
            print(f"saved: {out_jpg}")
        else:
            print(f"failed: {repo_path}")

    print(
        f"Done. Saved {saved}/{len(selected)} frames to {output_root}. "
        f"Failed downloads: {failed_downloads}"
    )


if __name__ == "__main__":
    main()
