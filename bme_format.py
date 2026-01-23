from pathlib import Path

def ask_with_confirm(prompt):
    value = input(prompt).strip()
    if value != "":
        return value

    print("Your input are empty, are you sure ? Press Enter to leave it empty, or enter text/number:")
    value = input().strip()
    return value

def run(bme_dir: Path, song_id: str):
    remove_keys = {
        "#SUBARTIST",
        "#VOLWAV",
        "#MOVIEDELAY",
        "#PLAYTIME",
        "#PREVIEW",
        "#TOTALNOTES",
        "#REALNOTES",
        "#BACKBMP",
    }

    genre = ask_with_confirm("Write GENRE of song: ")
    title = ask_with_confirm("Write TITLE of song: ")
    artist = ask_with_confirm("Write ARTIST of song: ")

    stagefile = "1.png"
    bga = f"{song_id}.mp4"

    bme_files = list(bme_dir.glob("*.bme"))

    for bme in bme_files:
        lines = bme.read_text(encoding="shift_jis", errors="ignore").splitlines(True)
        out = []

        for line in lines:
            if any(line.startswith(k) for k in remove_keys):
                continue
            if line.startswith("#GENRE"):
                out.append(f"#GENRE {genre}\n")
            elif line.startswith("#TITLE"):
                out.append(f"#TITLE {title}\n")
            elif line.startswith("#ARTIST"):
                out.append(f"#ARTIST {artist}\n")
            elif line.startswith("#STAGEFILE"):
                out.append(f"#STAGEFILE {stagefile}\n")
            elif line.startswith("#BMP01"):
                out.append(f"#BMP01 {bga}\n")
            else:
                out.append(line)

        bme.write_text("".join(out), encoding="shift_jis", errors="ignore")

    for bme in bme_files:
        playlevel = ask_with_confirm(f"Write PLAYLEVEL of {bme.name} difficulty: ")

        lines = bme.read_text(encoding="shift_jis", errors="ignore").splitlines(True)
        out = []

        for line in lines:
            if line.startswith("#PLAYLEVEL"):
                out.append(f"#PLAYLEVEL {playlevel}\n")
            else:
                out.append(line)

        bme.write_text("".join(out), encoding="shift_jis", errors="ignore")

    return title
