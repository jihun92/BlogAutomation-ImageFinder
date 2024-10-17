rm -rf build dist main.spec
pyinstaller --onefile --windowed --icon="img/icon-windowed.icns" src/main.py
