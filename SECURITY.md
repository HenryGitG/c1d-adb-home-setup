# Security

本项目只适用于你拥有或明确获授权管理的设备。

- 不要把 ADB 5555 端口暴露到公网。
- 不要提交 ADB 私钥、设备序列号、远程协助路由、访问令牌或家庭网络地址。
- 完成安装后执行 `adb disconnect`，并在投影仪上关闭网络调试或撤销调试授权。
- 远程协助客户端只允许预定义动作，不提供任意 Shell 参数；修改动作要求再次确认完整设备序列号。
- 不要提交 `remoteDebugUrl`、`deviceSerial` 或 `private/remote-route.json`。这些值应被视为设备访问资料。

发现仓库自身的安全问题时，请通过 GitHub Security Advisory 私下报告，不要在公开 Issue 中粘贴设备信息或密钥。
