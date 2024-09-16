# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['TFG.py'],
    pathex=[],
    binaries=[],
    datas=[('imágenes/diametros_comerciales.png', '.'), ('imágenes/gráfica_arrastre.PNG', '.'), ('imágenes/gráfica_flujoplato.JPG', '.'), ('imágenes/gráfico_k1.JPG', '.'), ('output_plate.png', '.'), ('Plato columna.STL', '.'), ('propiedades.xlsx', '.')],
    hiddenimports=[],
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
    name='TFG',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
