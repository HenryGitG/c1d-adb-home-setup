# 系统远程协助与 ADB

## 先区分三个概念

1. **系统远程协助**：厂商提供、由设备所有者在投影仪上主动开启并授权的临时会话。
2. **“USB 调试”设置**：Android 沿用的设置名称；在这台 C1D 上，最终使用的是局域网 TCP ADB，而不是长期插着 USB 线。
3. **ADB 客户端**：Mac/PC 上 Android Platform Tools 提供的标准 `adb` 命令。

远程协助不是日常控制通道。它只在首次没有 ADB 的情况下，帮助所有者把设置助手安装到投影仪并打开固件已有的设置界面。仓库不包含远程协助服务器地址、设备路由、序列号或私有协议实现。

## 1. 由所有者开启远程协助

在投影仪系统中打开自带的远程协助功能，并在屏幕上确认当前会话。只把会话交给你信任的人，完成首次引导后立即结束会话。

通过该授权会话，把本仓库构建的 `C1D-ADB-Settings-Helper.apk` 安装并打开。助手没有网络权限，也没有系统特权；它只调用公开的 Android Intent/厂商广播打开现有设置页面。

## 2. 打开 C1D 固件的调试入口

优先尝试助手中的“TV 开发者选项”和“Android 开发者选项”。如果固件隐藏了普通入口：

1. 打开“画面缩放（C1D 调试入口）”。
2. 确认屏幕已经进入厂商画面缩放页面。
3. 在该页面用遥控器连续按左键 20 次，每次间隔不超过 1 秒。
4. 只在这个页面执行该动作；如果画面尺寸发生变化，稍后在投影设置中重置。

目标固件的厂商设置组件会在满足该设备专用动作后调用其特权 `enableAdb(true)`。普通第三方 APK 无权自行开启 ADB；设置助手只是把所有者带到正确页面。

## 3. 从电脑验证标准 ADB

先在路由器或投影仪网络页面确认当前局域网地址。不要把地址写死进脚本，因为 DHCP 重新分配后可能变化。

```bash
adb connect <projector-ip>:5555
adb devices -l
adb -s <projector-ip>:5555 shell getprop ro.product.model
adb -s <projector-ip>:5555 shell getprop ro.product.name
```

只在型号与产品信息符合预期后继续。若屏幕弹出 RSA 调试授权，请在投影仪上核对并确认；本项目不提供绕过授权或写入其他设备 ADB 密钥的方法。

## 4. 完成后收口

安装和配置完成后：

```bash
adb disconnect <projector-ip>:5555
```

随后在投影仪中关闭网络调试或撤销不再需要的调试授权，并结束远程协助会话。不要在路由器上给 5555 建立公网端口映射。

## 构建设置助手

```bash
cd android/adb-settings-helper
bash build.sh
```

需要 JDK 17、Android SDK 36 和 Build Tools 36.0.0。输出位于 `dist/C1D-ADB-Settings-Helper.apk`。
