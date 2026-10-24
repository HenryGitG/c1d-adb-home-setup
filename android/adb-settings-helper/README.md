# C1D ADB 设置助手

这是一个无特权、无网络权限的 Android TV 小工具。它只打开 C1D 固件中已有的设置页面：TV 开发者选项、Android 开发者选项、厂商画面缩放页面和系统信息。

它不能自行开启 ADB，也不会修改系统设置。开启调试仍需设备所有者在投影仪上完成明确的按键操作。完整流程见仓库根目录的 `docs/remote-assistance-and-adb.md`。

## 构建

需要 Android SDK 36、Build Tools 36.0.0 和 JDK 17：

```bash
bash build.sh
```

输出：`dist/C1D-ADB-Settings-Helper.apk`。构建脚本使用本机 Android debug keystore，仅适合侧载和个人设备测试。
