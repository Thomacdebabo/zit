pyinstaller --onefile --name zit run_zit.py
pyinstaller --onefile --name zit-git run_zit_git.py
pyinstaller --onefile --name zit-fm run_zit_fm.py
pyinstaller --onefile --name zit-sys run_zit_sys.py

chmod +x dist/zit
chmod +x dist/zit-git
chmod +x dist/zit-fm
chmod +x dist/zit-sys


