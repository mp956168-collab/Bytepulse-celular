[app]
title = BytePulse
package.name = bytepulse
package.domain = com.bytepulse.finance
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,kivymd,plyer,tzdata,pillow
icon.filename = %(source.dir)s/bytepulse-logo.png
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.enable_androidx = True
android.archs = armeabi-v7a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1