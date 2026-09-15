from PyInstaller.utils.hooks import collect_data_files, collect_submodules


hidden_imports = collect_submodules('pycaw')
sounddevice_data = collect_data_files('_sounddevice_data')

a = Analysis(
	['main.py'],
	pathex=[],
	binaries=[],
	datas=sounddevice_data + [
		('FlooCastApp.gif', '.'),
		('FlooCastApp.ico', '.'),
		('FlooCastHeader.png', '.'),
		('offS.png', '.'),
		('onS.png', '.'),
		('locales', 'locales'),
	],
	hiddenimports=hidden_imports,
	hookspath=[],
	hooksconfig={},
	runtime_hooks=[],
	excludes=[],
	noarchive=False,
	optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
	pyz,
	a.scripts,
	a.binaries,
	a.datas,
	[],
	name='FlooCast-Audio-Switch-Test',
	debug=False,
	bootloader_ignore_signals=False,
	strip=False,
	upx=True,
	upx_exclude=[],
	runtime_tmpdir=None,
	console=True,
	disable_windowed_traceback=False,
	argv_emulation=False,
	target_arch=None,
	codesign_identity=None,
	entitlements_file=None,
	icon=['FlooCastApp.ico'],
)
