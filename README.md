<div align="center">
  <img src="docs/assets/logo.png" width="360">
  <br>
  <strong style="font-size:32px">List2Folder</strong>
</div>

<p align="center">
  Turn Spotify / YouTube Music playlists into a local folder by matching tracks in your library.
</p>

<p align="center">
  <a href="https://github.com/Rincodev/List2Folder/releases/latest">
    <img alt="version" src="https://img.shields.io/github/v/release/Rincodev/List2Folder?label=version">
  </a>
  <a href="LICENSE">
    <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
  </a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB">
  <img alt="CLI" src="https://img.shields.io/badge/CLI-Tool-111">
  <img alt="platform" src="https://img.shields.io/badge/Windows%20%7C%20Linux%20%7C%20macOS-supported-informational">
  <a href="https://github.com/Rincodev/List2Folder/releases">
    <img alt="downloads" src="https://img.shields.io/github/downloads/Rincodev/List2Folder/total?label=downloads">
  </a>
</p>

<p align="center">
  <a href="https://github.com/Rincodev/List2Folder/releases/latest">
    <img src="https://img.shields.io/badge/Download-%F0%9F%93%A6-FF9800?style=for-the-badge" alt="Download">
  </a>
</p>

<p align="center">
  No downloading. Works with your existing files: match by tags (ID3/FLAC) + optional fuzzy matching, then copy/move into a new folder.
  This project is distributed as a standalone CLI executable for Windows.
  A Python script version is also available for advanced users.
</p>

---

<p align="center">
  <a href="https://www.linkedin.com/in/bohdan-yatsenko-880a4831b/" target="_blank">
    <img alt="LinkedIn" src="https://img.shields.io/badge/LinkedIn-follow-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white">
  </a>
  <a href="https://bohdan.nothix.eu/en/" target="_blank">
    <img alt="Portfolio" src="https://img.shields.io/badge/Portfolio-visit-111?style=for-the-badge&logo=globe&logoColor=white">
  </a>
</p>

---

## Features
- Read playlists from **Spotify** or **YouTube Music**.
- Scan your local library and match tracks using **audio tags** (title/artist/album).
- Optional **fuzzy matching** (handles small differences like “Remastered”, “feat.”, punctuation).
- **Copy** (default) or **move** matched files into an output folder.
- Safe file handling: avoids overwrites by auto-renaming duplicates.
- Generates a simple report: matched / missing.

---

## Quick start (Windows EXE)

### 1) Download
Download the latest release from the **Releases** page and unzip it anywhere (e.g. `D:\Tools\List2Folder\`).

### 2) Run
Open a terminal **in the folder** with `List2Folder.exe`:

```bat
List2Folder.exe --help
```

> **PowerShell note:** Don’t run `--headers ...` by itself (PowerShell treats `--` as an operator). `--headers` must be part of the full `List2Folder.exe ...` command.

---

## Quick start (Run from source)

### 1) Install
```bash
pip install -r requirements.txt
```

### 2) Run
```bash
python playlist_to_folder.py --help
```

---

## Authentication / Setup

### Spotify (OAuth)
Spotify requires an app in the Spotify Developer Dashboard.

You will need:
- `SPOTIPY_CLIENT_ID`
- `SPOTIPY_CLIENT_SECRET`
- `SPOTIPY_REDIRECT_URI` (recommended: `http://localhost:8888/callback`)

#### Create Spotify credentials
1. Open the Spotify Developer Dashboard.
2. Create an app.
3. Add Redirect URI: `http://localhost:8888/callback`
4. Copy **Client ID** and **Client Secret**.

#### Set variables (Windows PowerShell)
```powershell
$env:SPOTIPY_CLIENT_ID="..."
$env:SPOTIPY_CLIENT_SECRET="..."
$env:SPOTIPY_REDIRECT_URI="http://localhost:8888/callback"
```

> **Tip:** For the source version you can also use a local `.env` file (don’t commit it).

---

### YouTube Music (Browser headers via `ytmusicapi`)
This project uses `ytmusicapi` (unofficial). The most reliable method on Windows is **manual `browser.json`** built from browser request headers.

#### 1) Get the playlist ID
Open the playlist in YouTube Music. The URL looks like:

```
https://music.youtube.com/playlist?list=PLxxxxxxxxxxxx
```

The playlist id is the part after `list=`:
- `PLxxxxxxxxxxxx` (or sometimes `OLAK5uy...`)

#### 2) Create `browser.json` (recommended, reliable)
You must be logged in to `music.youtube.com` in your browser.

1. Open **https://music.youtube.com**
2. Press **F12** → **Network**
3. Refresh the page (**Ctrl+R**)
4. Filter for: `browse`
5. Open the **POST** request to `.../youtubei/v1/browse`
6. In **Request Headers**, copy the values for:
   - `authorization: SAPISIDHASH ...`  ✅ required
   - `cookie: ...` (very long string) ✅ required
   - `content-type: application/json`
   - `x-goog-authuser: 0`
   - `x-origin: https://music.youtube.com`

Now create a file named `browser.json` in the same folder as the EXE (or provide a full path) with this template:

```json
{
  "Accept": "*/*",
  "Authorization": "SAPISIDHASH ...",
  "Content-Type": "application/json",
  "X-Goog-AuthUser": "0",
  "x-origin": "https://music.youtube.com",
  "Cookie": "PASTE_FULL_COOKIE_HERE"
}
```

⚠️ **Security:** `browser.json` contains your cookies. **Never commit it** and never share it.

---

## Usage

### Windows (PowerShell)

#### Spotify
```powershell
.\List2Folder.exe `
  --source spotify `
  --playlist "https://open.spotify.com/playlist/XXXX" `
  --library "D:\Music" `
  --out "D:\Selected" `
  --mode copy
```

#### YouTube Music
```powershell
.\List2Folder.exe `
  --source ytmusic `
  --playlist "PLxxxxxxxxxxxx" `
  --headers ".\browser.json" `
  --library "D:\Music" `
  --out "D:\Selected" `
  --mode copy
```

### Windows (cmd.exe)

#### Spotify
```bat
List2Folder.exe ^
  --source spotify ^
  --playlist "https://open.spotify.com/playlist/XXXX" ^
  --library "D:\Music" ^
  --out "D:\Selected" ^
  --mode copy
```

#### YouTube Music
```bat
List2Folder.exe ^
  --source ytmusic ^
  --playlist "PLxxxxxxxxxxxx" ^
  --headers ".\browser.json" ^
  --library "D:\Music" ^
  --out "D:\Selected" ^
  --mode copy
```

### Run from source (any OS)

#### Spotify
```bash
python playlist_to_folder.py \
  --source spotify \
  --playlist "https://open.spotify.com/playlist/XXXX" \
  --library "/path/to/your/music" \
  --out "/path/to/output" \
  --mode copy
```

#### YouTube Music
```bash
python playlist_to_folder.py \
  --source ytmusic \
  --playlist "PLxxxxxxxxxxxx" \
  --headers "./browser.json" \
  --library "/path/to/your/music" \
  --out "/path/to/output" \
  --mode copy
```

### Useful options
```bash
--album "Album Name"      # restrict local search to a specific album
--min-score 92            # fuzzy threshold (0..100)
--mode copy|move          # default: copy
--dry-run                 # show what would happen without writing files
```

---

## How matching works
1) Prefer **tags** (artist + title).  
2) If tags are missing, fall back to **filename**.  
3) Normalize text (case, punctuation, “feat.”, brackets).  
4) If no exact match exists, use **fuzzy matching** (threshold via `--min-score`).

---

## Troubleshooting

### PowerShell: “Missing expression after unary operator '--'”
You ran an argument by itself. Always run the full command, e.g.:
```powershell
.\List2Folder.exe --source ytmusic --playlist "PL..." --headers ".\browser.json" --library "D:\Music" --out "D:\Out"
```

### Spotify: `No client_id`
Set `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET`, `SPOTIPY_REDIRECT_URI` in your environment (or `.env` for source).

### YouTube Music: `oauth_credentials` / “looks like OAuth credentials”
Your `browser.json` is missing required browser headers, most commonly:
- `Authorization: SAPISIDHASH ...`
- `x-origin: https://music.youtube.com`
- full `Cookie: ...` header

Re-create `browser.json` using the template above.

### YouTube Music: `KeyError: contents` / `logged_in: 0`
This usually means YouTube treated the request as logged out:
- regenerate `browser.json` (make sure Cookie is complete)
- ensure you are logged in to the browser profile you copied headers from
- if the playlist is **Private**, switch it to **Unlisted** or **Public** for testing

---

## Limitations / notes
- This tool does **not** download music. It only organizes files you already have.
- Playlist sources may change behavior over time (especially YouTube Music integrations).
- Best results when your library has correct metadata tags.

---

## Contributing
PRs and issues are welcome. If you add a provider or improve matching, please include a small test sample.

---

## License
MIT — see [LICENSE](LICENSE).
