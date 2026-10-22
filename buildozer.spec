[app]
title = Dau Truong Anh Hung
package.name = daututruonganhhung
package.domain = org.moba
source.dir = .
source.include_exts = py,ttf
version = 1.0
requirements = python3,pygame
orientation = landscape
fullscreen = 1
android.permissions =
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
# Neu loi "recipe pygame": thu bo dau # o dong duoi
# p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0
