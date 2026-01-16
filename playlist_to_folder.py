import os
import re
import sys
import json
import shutil
import argparse
import unicodedata
from pathlib import Path

from mutagen import File as MutagenFile

# Optional fuzzy matching
try:
    from rapidfuzz import process as rf_process
    from rapidfuzz import fuzz as rf_fuzz
    HAS_RAPIDFUZZ = True
except Exception:
    import difflib
    HAS_RAPIDFUZZ = False


AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".alac", ".aiff"}


def norm_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = s.casefold()

    # Remove bracketed parts: (remaster), [live], etc.
    s = re.sub(r"[\(\[].*?[\)\]]", " ", s)

    # Drop "feat/ft/featuring ..." suffixes
    s = re.sub(r"\b(feat|ft|featuring)\b.*$", " ", s)

    # Keep latin/cyrillic/digits, replace the rest with spaces
    s = re.sub(r"[^0-9a-z\u0400-\u04FF]+", " ", s)

    s = re.sub(r"\s+", " ", s).strip()
    return s


def make_key(artist: str, title: str) -> str:
    a = norm_text(artist)
    t = norm_text(title)
    if a and t:
        return f"{a} - {t}"
    return t or a


def safe_copy_or_move(src: Path, dst_dir: Path, mode: str) -> Path:
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name

    # Avoid overwriting: add (1), (2), ...
    if dst.exists():
        stem, suf = src.stem, src.suffix
        i = 1
        while True:
            candidate = dst_dir / f"{stem} ({i}){suf}"
            if not candidate.exists():
                dst = candidate
                break
            i += 1

    if mode == "move":
        shutil.move(str(src), str(dst))
    else:
        shutil.copy2(str(src), str(dst))
    return dst


def read_audio_tags(path: Path) -> dict:
    """
    Tries to read common tags: title, artist, album.
    Returns dict with keys: title, artist, album.
    """
    info = {"title": "", "artist": "", "album": ""}
    try:
        audio = MutagenFile(path, easy=True)
        if not audio:
            return info

        def first(tagname: str) -> str:
            v = audio.get(tagname)
            if isinstance(v, list) and v:
                return str(v[0])
            if isinstance(v, str):
                return v
            return ""

        # Common easy tags
        info["title"] = first("title")
        info["artist"] = first("artist")
        info["album"] = first("album")

        # Some formats may use 'albumartist'
        if not info["artist"]:
            info["artist"] = first("albumartist")

    except Exception:
        pass
    return info


def build_local_index(library_dir: Path, album_filter: str | None = None) -> dict[str, list[Path]]:
    """
    Returns mapping: key -> [paths...]
    Key is based on tags (artist-title). If tags missing, fallback to filename.
    """
    index: dict[str, list[Path]] = {}
    album_filter_norm = norm_text(album_filter) if album_filter else ""

    for root, _, files in os.walk(library_dir):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() not in AUDIO_EXTS:
                continue

            tags = read_audio_tags(p)
            title = tags["title"] or p.stem
            artist = tags["artist"]  # may be empty
            album = tags["album"]

            # Album restriction (optional)
            if album_filter_norm:
                ok = False
                if album and norm_text(album) == album_filter_norm:
                    ok = True
                # fallback: folder name contains album words
                if not ok and album_filter_norm in norm_text(str(p.parent)):
                    ok = True
                if not ok:
                    continue

            key = make_key(artist, title)
            if not key:
                continue
            index.setdefault(key, []).append(p)

    return index


def best_match(query_key: str, choices: list[str], min_score: int) -> str | None:
    if not choices:
        return None

    if HAS_RAPIDFUZZ:
        result = rf_process.extractOne(
            query_key,
            choices,
            scorer=rf_fuzz.token_set_ratio
        )
        if not result:
            return None
        choice, score, _ = result
        return choice if score >= min_score else None

    # Fallback: difflib (rougher)
    best = difflib.get_close_matches(query_key, choices, n=1, cutoff=min_score / 100)
    return best[0] if best else None


def fetch_spotify_playlist_tracks(playlist_id_or_url: str) -> list[tuple[str, str]]:
    """
    Returns list of (artist, title)
    Requires env vars:
      SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
    """
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth

    # If url, extract id
    playlist_id = playlist_id_or_url
    m = re.search(r"open\.spotify\.com/playlist/([A-Za-z0-9]+)", playlist_id_or_url)
    if m:
        playlist_id = m.group(1)

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="playlist-read-private"))
    items = []
    offset = 0
    limit = 100

    while True:
        page = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        for it in page.get("items", []):
            tr = it.get("track") or {}
            name = tr.get("name") or ""
            artists = tr.get("artists") or []
            artist = (artists[0].get("name") if artists else "") or ""
            if name:
                items.append((artist, name))

        if page.get("next") is None:
            break
        offset += limit

    return items


def fetch_ytmusic_playlist_tracks(playlist_id: str, headers_path: Path) -> list[tuple[str, str]]:
    """
    Returns list of (artist, title)
    Uses ytmusicapi (unofficial); needs browser headers exported.
    """
    from ytmusicapi import YTMusic

    ytm = YTMusic(str(headers_path))
    data = ytm.get_playlist(playlist_id, limit=None)
    tracks = []
    for t in data.get("tracks", []):
        title = t.get("title") or ""
        artists = t.get("artists") or []
        artist = (artists[0].get("name") if artists else "") or ""
        if title:
            tracks.append((artist, title))
    return tracks


def main():
    ap = argparse.ArgumentParser(
        description="Copy/move local audio files that match a Spotify/YouTube Music playlist."
    )
    ap.add_argument("--source", choices=["spotify", "ytmusic"], required=True,
                    help="Where to read the playlist from.")
    ap.add_argument("--playlist", required=True,
                    help="Spotify playlist URL/ID OR YouTube Music playlistId.")
    ap.add_argument("--library", required=True, help="Path to your local music library folder.")
    ap.add_argument("--out", required=True, help="Destination folder for matched tracks.")
    ap.add_argument("--mode", choices=["copy", "move"], default="copy",
                    help="Copy or move matched files.")
    ap.add_argument("--album", default=None,
                    help="Optional: restrict local search to a specific album (by tag or folder name).")
    ap.add_argument("--min-score", type=int, default=92,
                    help="Fuzzy match threshold 0..100 (used if exact key not found).")
    ap.add_argument("--headers", default=None,
                    help="(ytmusic only) Path to ytmusicapi headers_auth.json")
    args = ap.parse_args()

    library_dir = Path(args.library).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()

    if not library_dir.exists():
        print(f"[ERR] Library folder not found: {library_dir}", file=sys.stderr)
        sys.exit(2)

    # Build local index
    print("[*] Indexing local library (reading tags)...")
    local_index = build_local_index(library_dir, album_filter=args.album)
    keys = list(local_index.keys())
    print(f"[*] Indexed {sum(len(v) for v in local_index.values())} files, {len(keys)} unique keys")

    # Fetch playlist tracks
    print(f"[*] Fetching playlist tracks from {args.source}...")
    if args.source == "spotify":
        tracks = fetch_spotify_playlist_tracks(args.playlist)
    else:
        if not args.headers:
            print("[ERR] --headers is required for ytmusic source", file=sys.stderr)
            sys.exit(2)
        headers_path = Path(args.headers).expanduser().resolve()
        if not headers_path.exists():
            print(f"[ERR] headers file not found: {headers_path}", file=sys.stderr)
            sys.exit(2)
        tracks = fetch_ytmusic_playlist_tracks(args.playlist, headers_path)

    print(f"[*] Playlist contains {len(tracks)} tracks")

    matched = 0
    missing = 0
    copied_paths: list[Path] = []

    for artist, title in tracks:
        qkey = make_key(artist, title)
        if not qkey:
            continue

        # 1) exact match
        candidates = local_index.get(qkey)

        # 2) fuzzy match
        if not candidates:
            best = best_match(qkey, keys, min_score=args.min_score)
            candidates = local_index.get(best, None) if best else None

        if not candidates:
            missing += 1
            print(f"[MISS] {artist} - {title}")
            continue

        # If multiple local files match same key, copy/move all (or choose first).
        for src in candidates:
            dst = safe_copy_or_move(src, out_dir, args.mode)
            copied_paths.append(dst)

        matched += 1
        print(f"[OK]   {artist} - {title}  -> {len(candidates)} file(s)")

    print("\n=== Done ===")
    print(f"Matched tracks: {matched}")
    print(f"Missing tracks: {missing}")
    print(f"Files written:  {len(copied_paths)}")
    print(f"Output folder:  {out_dir}")


if __name__ == "__main__":
    main()
