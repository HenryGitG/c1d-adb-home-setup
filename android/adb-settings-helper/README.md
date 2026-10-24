# C1D ADB 设置助手

这是一个无特权、无网络权限的 Android TV 小工具。它打开 C1D 固件中已有的设置页面，并能在投影仪本机显示远程协助所需的 `ro.serialno` 与 `persist.obe.REMOTE_DEBUG_URL`。

它不会把这些信息发送到网络，不能自行开启 ADB，也不会修改系统设置。设备序列号和远程路由应只抄入本机忽略提交的 `private/remote-route.json`。完整流程见 [借助系统远程协助开启网络 ADB](../../docs/remote-assistance-and-adb.md)。

## 构建

需要 Android SDK 36、Build Tools 36.0.0 和 JDK 17：

```bash
bash build.sh
```

输出：`dist/C1D-ADB-Settings-Helper.apk`。构建脚本使用本机 Android debug keystore，仅适合侧载和个人设备测试。
