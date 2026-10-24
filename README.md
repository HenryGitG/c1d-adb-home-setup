# C1D ADB 与 HOME 设置

这个仓库记录 C1D 投影仪从“只能使用系统界面”到“借助系统远程协助启动网络 ADB，再通过标准 ADB 安装并切换第三方 HOME”的已验证流程。

核心链路：

```text
设备所有者开启系统远程协助
  -> 远程 system 命令代理核对设备与 ADB 属性
  -> setprop ctl.start adbd，使固件预设的 TCP 5555 开始监听
  -> 屏幕确认 RSA，或在授权会话中只追加电脑的 ADB 公钥
  -> Mac/PC 使用标准 adb connect 接管
  -> 安装 C1D Home
  -> 切换并验证默认 HOME
```

本仓库写明远程协助命令代理、`adbd` 启动和首次公钥授权的实际命令链，但不实现、仿制或公开厂商转发通道的私有客户端、服务器地址、设备路由或序列号。远程协助只承担首次引导；获得 ADB 后，后续操作全部使用 Android SDK 自带的 `adb`。

## 仓库内容

- `android/adb-settings-helper/`：无网络权限、无特权的设置页面快捷入口。
- `tools/switch-home.py`：切换 C1D Home 与原厂 HOME，并读取系统解析结果进行验证。
- `docs/remote-assistance-and-adb.md`：远程协助命令代理、启动 TCP ADB、公钥授权和标准 ADB 接管。
- `docs/replace-home.md`：安装、切换、验证和恢复 HOME。

桌面源码、网络待机及 Home Assistant 集成位于配套仓库：[c1d-home-standby-ha](https://github.com/HenryGitG/c1d-home-standby-ha)。

## 前提

- 只操作你拥有或获明确授权管理的 C1D。
- Mac/PC 已安装 Android Platform Tools，`adb version` 可正常运行。
- 电脑与投影仪位于可信的同一局域网。
- 不要把 5555 端口映射到公网。

先阅读 [远程协助与 ADB](docs/remote-assistance-and-adb.md)，再执行 [替换 HOME](docs/replace-home.md)。

## 验证状态

- C1D 固件的画面缩放入口和隐藏调试动作：已在目标机型流程中验证。
- 标准局域网 ADB、HOME 切换及原厂 HOME 恢复：已在目标设备验证。
- 不同固件版本可能删除或修改厂商入口；不要在其他品牌或未确认版本上照搬。

## License

MIT。见 [LICENSE](LICENSE)。
