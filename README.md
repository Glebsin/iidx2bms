<div align="center">
  <h1>iidx2bms</h1>

  <img src="https://github.com/Glebsin/iidx2bms/blob/resources/iidx2bms_logo.svg?raw=true" width="200" alt="iidx2bms logo">

  <p>Tools for converting iidx 33 charts to bms charts</p>
</div>

# HOW TO USE (for 2026.221.0 pre-release)

1. Download [`iidx2bms.zip`](https://github.com/Glebsin/iidx2bms/releases/download/2026.221.0/iidx2bms.zip) from Releases
2. Launch iidx2bms.exe
3. Choose your `\contents\data\sound\` and `\contents\data\movie\` paths in **`Settings`** --> **`File paths`** 
4. Find charts that you want to convert in search bar
5. Select charts by double-clicking or pressing enter
6. Click `Start conversion` button
7. Solve problems if chart has non-standard symbols in chart name or genre
8. Get result in `Result` folder

**Tested on Windows 11, doesn't work with omnimix charts, doesn't work with charts that have more than one .2dx file, not counting _pre.2dx**

**Converted charts tested only in [**`LR2oraja Endless Dream`**](https://github.com/seraxis/lr2oraja-endlessdream) and probably working only there (or in common beatoraja too idk)**

python -m pip install --upgrade pip && python -m pip install PyQt6 ifstools pyinstaller

python -m PyInstaller --noconfirm --clean --windowed --onefile --name iidx2bms --icon icon\iidx2bms_logo.ico --hidden-import PyQt6.QtSvg --hidden-import ifstools.ifs --add-data "gui\assets;gui\assets" --add-data "icon;icon" --add-data "music_data;music_data" --add-data "stagefiles;stagefiles" --add-data "one2bme;one2bme" main.py


# HOW TO USE (for 2026.207.0 release)

1. Install requirements `python -m pip install requests beautifulsoup4`
2. Download [`iidx2bms.zip`](https://github.com/Glebsin/iidx2bms/releases/download/2025.207.0/iidx2bms.zip) from Releases
3. Put .1, .s3p and _pre.2dx or only .ifs files in folder "put .1, .s3p and _pre.2dx or only .ifs files here"
4. If you want put .png and .mp4 with any name in folder "put .png and .mp4 here"
5. Run "run.bat"
6. Follow instructions in console
7. Get result in "result" folder

**Tested on Windows 11, ffmpeg and Python 3.14.2 should be installed and added to PATH, 1 chart per script launch, doesn't work with omnimix charts.**

**Converted charts tested only in [**`LR2oraja Endless Dream`**](https://github.com/seraxis/lr2oraja-endlessdream) and probably working only there (or in common beatoraja too idk)**
