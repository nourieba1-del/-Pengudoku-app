[app]
title = Pengudoku AI
package.name = pengudoku
package.domain = org.pengudoku
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3==3.10.13,hostpython3==3.10.13,kivy==2.2.1,pillow,libjpeg,png
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.accept_sdk_license = True
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
p4a.branch = release-2024.01.21

[buildozer]
log_level = 2
warn_on_root = 0
