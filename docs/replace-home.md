# 安装与替换 HOME

配套仓库 `c1d-home-standby-ha` 提供公开版 C1D Home 源码。先按其 README 构建 APK，再在 ADB 已连接时安装：

```bash
adb -s <projector-ip>:5555 install -r /path/to/home-launcher.apk
```

## 切换到 C1D Home

在本仓库根目录执行：

```bash
python3 tools/switch-home.py <projector-ip> c1d
```

脚本会：

1. 连接 `<projector-ip>:5555`。
2. 显示设备型号与产品名并要求确认。
3. 启用公开版包 `com.gathin.tvhome`。
4. 使用 `cmd package set-home-activity` 设置 HOME。
5. 用 `resolve-activity` 回读并验证当前 HOME。

也可手动验证：

```bash
adb -s <projector-ip>:5555 shell cmd package resolve-activity --brief \
  -a android.intent.action.MAIN -c android.intent.category.HOME
```

预期包含：

```text
com.gathin.tvhome/com.gathin.tvhome.MainActivity
```

## 恢复原厂 HOME

在删除或停用第三方桌面之前先恢复原厂 HOME：

```bash
python3 tools/switch-home.py <projector-ip> factory
```

脚本会重新启用 C1D 当前固件使用的 `com.ktcp.launcher` 和 `com.ktcp.aiagent`，设置原厂 HOME，并回读验证。不同固件的原厂包名可能不同；此脚本只针对已验证的 C1D 固件。

确认原厂桌面可用后，才考虑卸载第三方 HOME。不要在没有可用回退桌面的情况下停用或删除系统 Launcher。
