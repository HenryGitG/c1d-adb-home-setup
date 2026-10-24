# 借助系统远程协助开启网络 ADB

这份文档记录目标 C1D 上实际验证过的启动链路。决定性步骤不是单纯打开一个“USB 调试”页面，而是借助设备所有者主动开启的系统远程协助会话，调用设备端已有的系统命令代理，启动已经配置为 TCP 5555 的 `adbd`，完成本机 RSA 公钥授权后，再由电脑上的标准 `adb` 接管。

## 先区分四个组件

1. **系统远程协助 App**：C1D 固件预装的厂商组件，由设备所有者在投影仪上主动开启。
2. **厂商转发通道**：远程协助 App 与厂商服务之间的临时命令/回传通道。
3. **设备端命令代理**：接收当前设备的远程协助命令，并以 Android `system` 用户执行。
4. **标准 ADB**：电脑最终使用的 Android Platform Tools；连接建立后，不再依赖远程协助传输普通维护命令。

在目标设备上的实际数据流是：

```text
设备所有者在投影仪上开启远程协助
  -> 设备端远程协助服务连接厂商转发通道
  -> 已授权的支持端向当前设备发送一条 shell 命令
  -> 设备以 system 身份执行并返回输出
  -> 远程命令启动 adbd / 完成首次 ADB 公钥授权
  -> Mac 使用 adb connect <projector-ip>:5555
```

## 为什么仓库没有发布厂商转发客户端

本次验证中，支持端使用设备当前上报的远程调试路由和设备序列号，创建一次性客户端 ID，经厂商转发通道向该设备发送文本命令，并等待设备返回“已接收”和“执行结束”。

这段客户端一旦连同真实服务器地址、设备路由或序列号公开，本质上就是一个远程系统 Shell 客户端，可能被用于未授权设备。因此仓库只公开：

- 用户授权和身份核对流程；
- 在官方支持端或你自己的私有、当前会话客户端中执行的设备命令；
- ADB 公钥授权原则；
- 标准 ADB 接管和关闭流程。

仓库不公开厂商私有服务器地址、消息寻址细节、个人设备路由、设备序列号或可直接复用的转发客户端。复现这一段需要厂商提供的支持端控制台，或者仅限你自己设备、与当前已授权会话绑定的私有客户端。

## 1. 由设备所有者开启远程协助

1. 在 C1D 系统中打开自带的远程协助功能。
2. 由设备所有者在投影仪屏幕前确认当前会话。
3. 保持投影仪处于可观察状态，不要在无人看管时启动调试。
4. 支持端先执行只读身份检查，不要直接启动 ADB。

在已授权的远程命令控制台中执行：

```sh
id
getprop ro.serialno
getprop ro.product.model
getprop ro.product.name
```

目标 C1D 的远程命令代理应显示为 `uid=1000(system)`。把返回的型号、产品名和投影仪界面与当前设备核对；序列号只在本地核对，不要复制到 Issue、聊天截图或公开日志。

## 2. 检查 C1D 当前的 ADB 状态

在远程命令控制台中执行：

```sh
printf 'adb_enabled='; settings get global adb_enabled
printf 'persist_tcp_port='; getprop persist.adb.tcp.port
printf 'service_tcp_port='; getprop service.adb.tcp.port
printf 'adbd_state='; getprop init.svc.adbd
```

本次目标机的真实状态是：

- ADB 已标记为启用；
- `persist.adb.tcp.port` 和 `service.adb.tcp.port` 已经是 `5555`；
- 但 `init.svc.adbd` 没有显示为 `running`。

所以这台机不需要再次写入端口属性。问题只是固件已经准备好网络 ADB，却没有启动 `adbd` 服务。

## 3. 通过远程协助启动网络 ADB

确认上一步的端口确实是 `5555` 后，在远程命令控制台执行：

```sh
setprop ctl.start adbd
sleep 1
getprop init.svc.adbd
getprop service.adb.tcp.port
```

预期结果：

```text
running
5555
```

可以再用只读命令检查监听端口：

```sh
netstat -lnt 2>/dev/null | grep ':5555'
```

如果 `service.adb.tcp.port` 原本不是 `5555`，不要盲目照抄其他设备的 `setprop`。先确认固件是否提供“网络调试”开关；本仓库记录的是已验证 C1D 的状态，不把修改持久化端口当作通用步骤。

## 4. 完成电脑的 RSA 授权

网络端口打开并不代表电脑已经被授权。ADB 使用电脑的：

```text
~/.android/adbkey       私钥，只能留在电脑上
~/.android/adbkey.pub   公钥，可以授权给你自己的设备
```

优先方式是在投影仪屏幕出现“允许 USB 调试”提示时，核对 RSA 指纹并由设备所有者确认。

目标 C1D 当时没有出现可操作的授权提示，因此在已经由所有者授权、身份核对无误的远程 `system` 会话中完成了以下工作：

1. 对 `/data/misc/adb/adb_keys` 做保留权限的备份。
2. 检查文件末尾换行和已有内容。
3. 只追加当前 Mac 的 `~/.android/adbkey.pub`，没有传输私钥。
4. 保持原文件所有者和权限。
5. 重启 `adbd`，让授权列表重新加载。

对应的设备端操作顺序如下。`<MAC_ADB_PUBLIC_KEY>` 必须替换为当前 Mac 上 `adbkey.pub` 的完整单行内容：

```sh
cp -p /data/misc/adb/adb_keys /data/misc/adb/adb_keys.before-c1d-home
grep -Fqx '<MAC_ADB_PUBLIC_KEY>' /data/misc/adb/adb_keys || \
  printf '%s\n' '<MAC_ADB_PUBLIC_KEY>' >> /data/misc/adb/adb_keys
chown system:shell /data/misc/adb/adb_keys
chmod 0640 /data/misc/adb/adb_keys
setprop ctl.restart adbd
sleep 2
getprop init.svc.adbd
```

注意：

- 不要把 `adbkey` 私钥传到投影仪、厂商服务器或 GitHub。
- 不要覆盖整个 `adb_keys`，否则可能删除已有的合法授权。
- 修改前必须备份；如果电脑仍无法连接，恢复备份并停止操作。
- 这一步只适用于你拥有或获明确授权管理的设备。

## 5. Mac 使用标准 ADB 接管

从路由器租约或投影仪网络页面确认当前局域网地址。不要使用脚本里的历史地址，因为 DHCP 重新连接后 IP 可能变化。

在 Mac 上执行：

```bash
adb connect <projector-ip>:5555
adb devices -l
adb -s <projector-ip>:5555 shell id
adb -s <projector-ip>:5555 shell getprop ro.product.model
adb -s <projector-ip>:5555 shell getprop ro.product.name
```

只有 `adb devices -l` 显示 `device`，并且型号、产品名符合预期，才算从远程协助成功切换到标准 ADB。`offline` 或 `unauthorized` 都不算完成。

随后即可按 [替换 HOME](replace-home.md) 安装 APK、设置默认 HOME，并回读 `resolve-activity` 验证。

## 6. 远程协助和 ADB 的退出顺序

完成安装后先断开电脑：

```bash
adb disconnect <projector-ip>:5555
```

如果只想临时停止本次网络 ADB，在仍受控的设备端执行：

```sh
setprop ctl.stop adbd
getprop init.svc.adbd
```

然后：

1. 在投影仪中关闭 USB/网络调试或撤销不再需要的调试授权。
2. 结束系统远程协助会话。
3. 从另一台局域网设备确认 5555 已无法连接。
4. 不要在路由器中映射 5555，也不要把它暴露到公网。

只执行 `ctl.stop adbd` 不一定能跨重启持久关闭；固件若仍保留 ADB enable/持久端口设置，重启后可能再次启动。因此最终应通过投影仪设置关闭调试并实际复查端口。

## 设置助手在这条链路中的作用

`android/adb-settings-helper/` 是备用的本机入口工具：它能打开 TV/Android 开发者选项，以及 C1D 厂商画面缩放页面。目标固件的画面缩放组件中存在设备专用调试动作：在该页面快速按左键 20 次会调用厂商的 `enableAdb(true)`。

但它不能替代远程命令代理，也不会自行执行 `setprop`、写入 ADB 授权或连接厂商服务器。实际验证中，使 5555 开始监听的决定性动作仍是远程协助会话中的：

```sh
setprop ctl.start adbd
```

## 构建设置助手

```bash
cd android/adb-settings-helper
bash build.sh
```

需要 JDK 17、Android SDK 36 和 Build Tools 36.0.0。输出位于 `dist/C1D-ADB-Settings-Helper.apk`。
