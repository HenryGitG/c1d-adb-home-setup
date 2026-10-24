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

## 公开的转发客户端如何工作

仓库现在提供 `tools/remote_assistance_client.py`，实现了本次验证使用的连接协议，但不包含任何真实设备数据。客户端需要两个由你自己的 C1D 上报的值：

```json
{
  "remoteDebugUrl": "ws://<设备上显示的厂商转发地址>",
  "deviceSerial": "<你自己的设备序列号>"
}
```

可以使用设置助手的“显示远程协助连接信息”在投影仪本机读取：

- `deviceSerial`：来自 `ro.serialno`，为空时回退到 `ro.boot.serialno`。
- `remoteDebugUrl`：来自 `persist.obe.REMOTE_DEBUG_URL`。

这两个值应只保存在自己的电脑上：

```bash
mkdir -p private
cp examples/remote-route.example.json private/remote-route.json
```

编辑 `private/remote-route.json`，填入投影仪屏幕显示的真实值。`private/` 和 `remote-route.json` 已被 `.gitignore` 排除。

### 连接协议

客户端每次执行都会：

1. 生成随机的一次性客户端 ID，例如 `c1d-owner-<uuid>`。
2. 连接 `<remoteDebugUrl>/webSocket/<client-id>`。
3. 向 WebSocket 发送：

```json
{
  "from": "<client-id>",
  "to": "<deviceSerial>",
  "type": "chat",
  "text": "<预定义设备命令>"
}
```

4. 只接收 `from=deviceSerial` 且 `to=client-id` 的响应。
5. 收到以 `收到:` 开头的消息后标记设备已接受命令。
6. 收到以 `执行结束` 结尾的消息后标记命令完成并关闭连接。

实现没有提供任意 `--command` 参数，只开放身份探测、ADB 状态、启动/停止 `adbd` 和授权当前电脑公钥五个动作。修改设备的动作必须用 `--confirm-device-serial` 再次提交完整序列号。

### 安装客户端依赖

```bash
python3 -m pip install -r requirements.txt
```

如果希望避免修改全局 Python 环境，也可以使用 `uv`：

```bash
uv run --with 'websocket-client>=1.8,<2' \
  python tools/remote_assistance_client.py --help
```

仓库公开连接过程、消息格式与客户端源码，但不会提交真实转发地址、真实序列号或任何 ADB 私钥。

## 1. 由设备所有者开启远程协助

1. 在 C1D 系统中打开自带的远程协助功能。
2. 由设备所有者在投影仪屏幕前确认当前会话。
3. 保持投影仪处于可观察状态，不要在无人看管时启动调试。
4. 支持端先执行只读身份检查，不要直接启动 ADB。

使用公开客户端执行：

```bash
python3 tools/remote_assistance_client.py \
  --route private/remote-route.json probe
```

客户端在设备端执行的等价只读命令是：

```sh
id
getprop ro.serialno
getprop ro.product.model
getprop ro.product.name
```

目标 C1D 的远程命令代理应显示为 `uid=1000(system)`。把返回的型号、产品名和投影仪界面与当前设备核对；序列号只在本地核对，不要复制到 Issue、聊天截图或公开日志。

## 2. 检查 C1D 当前的 ADB 状态

使用公开客户端执行：

```bash
python3 tools/remote_assistance_client.py \
  --route private/remote-route.json adb-status
```

设备端等价命令是：

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

确认上一步的端口确实是 `5555` 后执行：

```bash
python3 tools/remote_assistance_client.py \
  --route private/remote-route.json \
  --confirm-device-serial '<deviceSerial>' \
  start-adbd
```

客户端在设备端执行：

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

公开客户端可以读取当前 Mac 的公钥并以 Base64 封装后发送，私钥不会被读取：

```bash
python3 tools/remote_assistance_client.py \
  --route private/remote-route.json \
  --confirm-device-serial '<deviceSerial>' \
  --adb-public-key ~/.android/adbkey.pub \
  authorize-key
```

客户端执行的设备端顺序等价于以下命令。`<MAC_ADB_PUBLIC_KEY>` 代表当前 Mac 上 `adbkey.pub` 的完整单行内容：

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

如果只想临时停止本次网络 ADB，可以通过同一远程协助会话执行：

```bash
python3 tools/remote_assistance_client.py \
  --route private/remote-route.json \
  --confirm-device-serial '<deviceSerial>' \
  stop-adbd
```

客户端在设备端执行：

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
