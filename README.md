
# 机票价格提醒工具（支持微信提醒）

本工具利用[携程 API](https://github.com/liangen1/-xiechengjipiao_aip)实时监控机票价格，并在价格变化超过设定值时，通过微信推送通知用户。该工具基于 `pushplus` 实现微信消息推送功能。

> **注意**：本工具仅供个人学习和研究使用，禁止用于商业用途。

## 本项目对原版做出的调整

本项目 fork 自 [davidwushi1145/flightAlert](https://github.com/davidwushi1145/flightAlert)，其上游为 [omegatao/flightAlert](https://github.com/omegatao/flightAlert)。在这个 fork 中相对上游主要做了以下调整：

- **去 GUI 化**：删除 `flight_alert_gui.py` 与 Pillow 等 GUI 依赖，仅保留 CLI 版本。
- **无需 Cookie**：携程的 `lowestPrice` 接口现已无需会话 Cookie 即可访问，请求头按浏览器实际抓包还原，开箱即用。
- **接口失败自检**：连续多次调用失败后自动停止调用 API，按约 12 小时一次的频率推送"接口调用失败"提醒，避免无效请求和额度浪费。
- **推送模板从 markdown 切到 html**：解决单 `\n` 不能换行的问题。
- **多日期合并 + 简洁格式**：同轮所有变化日期合并为一条微信消息，正文为 `日期: 直飞: ¥x, 中转: ¥y`，标题带路线 `出发地 → 到达地 航班价格提醒`。
- **文档重写**：使用流程、`config.json` 字段详解、推送消息示例都重新整理过。

## 功能特点

- 支持单程票和往返票的价格监控。
- 实时价格对比，价格变化时自动微信通知提醒。
- 配置简单，支持多日期、多城市监控。
- **接口失败自检**：连续多次调用携程接口失败时，自动停止调用 API 并按 ~2 次/天的频率推送提醒，避免无效请求和额度浪费。
- **多日期合并推送**：同一轮查询中所有日期的变化合并为一条微信消息，醒目不打扰。

## 使用方法

### 方法一：直接使用可执行文件（推荐）

1. 进入 [Releases 页面](https://github.com/ye-rm/flightAlert/releases) 下载最新的 `FlightAlert.exe`
2. 将 `FlightAlert.exe` 与 `config.json` 放在同一目录
3. 编辑 `config.json`（参考下方 *config.json 文件配置说明*）
4. 在终端（cmd / PowerShell）双击或运行：

   ```bash
   FlightAlert.exe
   ```

   程序会一直运行并按 `sleepTime` 间隔轮询，按 `Ctrl+C` 退出。

### 方法二：从源码运行

1. **环境要求**：
   本工具依赖 `Python 3.10` 及以上版本，推荐在 `Python 3.10` 上运行。

2. **下载代码**：
   克隆或下载本项目代码，并进入对应的目录：

   ```bash
   git clone https://github.com/ye-rm/flightAlert.git
   cd flightAlert
   ```

3. **创建虚拟环境**：
   使用如下命令创建并激活 Python 虚拟环境：

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux / macOS
   venv\Scripts\activate  # Windows
   ```

4. **安装依赖包**：
   运行以下命令安装所需依赖包：

   ```bash
   pip install -r requirements.txt
   ```

5. **运行程序**：
   编辑 `config.json` 后运行：

   ```bash
   python flight_alert.py
   ```

## `config.json` 文件配置说明

`config.json` 是程序读取的唯一配置文件，**所有字段均为必填**（除特别标注外）。

```json
{
  "dateToGo": ["20251105", "20251106"],
  "placeFrom": "KMG",
  "placeTo": "TNA",
  "flightWay": "Oneway",
  "sleepTime": 3600,
  "priceStep": 50,
  "SCKEY": "你的 pushplus token"
}
```

字段含义：

- **`dateToGo`**：需要监控的出发日期列表（格式 `YYYYMMDD`，如 `"20251105"`）。可同时监控多个日期，每轮查询中所有日期的变化会合并为一条推送。
- **`placeFrom`**：出发城市的机场代码（见下方机场代码表）。
- **`placeTo`**：到达城市的机场代码（见下方机场代码表）。
- **`flightWay`**：机票类型，单程票用 `"Oneway"`，往返票用 `"Roundtrip"`。
- **`sleepTime`**：查询间隔时间，单位为秒，推荐 `3600`（即一小时一次）。间隔太短容易触发携程反爬，1 小时是经验上比较稳的值。
- **`priceStep`**：价格变化的触发阈值。**直飞**和**中转**价格任意一项的变化幅度（绝对值）超过该值时触发微信提醒。设为 `1` 表示任意变化都提醒。
- **`SCKEY`**：`pushplus` 的 token，详见 [pushplus 文档](https://www.pushplus.plus/doc/)。**留空时仍可监控价格，但不会发送微信通知**。

> 本工具按浏览器实际抓包还原请求头调用携程公开的 `lowestPrice` 接口，无需配置 Cookie。若接口因反爬等原因连续多次调用失败，程序会自动停止调用并按约 12 小时一次的频率推送告警提醒，恢复后重启程序即可。

## 推送消息示例

单次推送会把当轮所有变化日期合并为一条微信消息：

```
昆明 → 济南 航班价格提醒
2025-11-05: 直飞: ¥480, 中转: ¥700
2025-11-06: 直飞: ¥550, 中转: ¥760
```

当接口连续多次调用失败时，推送内容类似：

```
【航班监控告警】携程接口已连续 3 次调用失败，
监控已暂停调用携程 API，仅保留此告警推送。
请检查网络或接口是否可用，恢复后重启程序即可。
```

## 机场代码对照表

以下是部分常用城市的机场代码：

| 城市   | 机场代码 | 城市   | 机场代码 |
| ------ | -------- | ------ | -------- |
| 北京   | BJS      | 上海   | SHA      |
| 广州   | CAN      | 深圳   | SZX      |
| 成都   | CTU      | 杭州   | HGH      |
| 武汉   | WUH      | 西安   | SIA      |
| 重庆   | CKG      | 青岛   | TAO      |
| 长沙   | CSX      | 南京   | NKG      |
| 厦门   | XMN      | 昆明   | KMG      |
| 济南   | TNA      | 福州   | FOC      |
| 南昌   | KHN      | 厦门   | XMN      |

更多城市机场代码请参见[完整列表](https://www.iata.org/en/publications/directories/code-search/).

## 部署到服务器持续运行

本项目是一个 `while True` 长进程，最适合用 **systemd**（几乎所有 Linux 发行版自带）托管：开机自启、崩溃自动重启、日志统一收口。

下面给一个最小可用的配置（Ubuntu / Debian 适用，其他发行版把 `apt` 换成对应包管理器即可）：

1. **把项目放到服务器**

   ```bash
   sudo mkdir -p /opt/flightAlert && sudo chown $USER:$USER /opt/flightAlert
   cd /opt/flightAlert
   git clone https://github.com/ye-rm/flightAlert.git .
   ```

2. **创建虚拟环境并安装依赖**

   ```bash
   cd /opt/flightAlert
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **编辑 `config.json`**：填好 `SCKEY`、监控日期等。本工具无需配置 Cookie，开箱即用。

4. **创建 systemd unit 文件** `/etc/systemd/system/flightalert.service`：

   ```ini
   [Unit]
   Description=FlightAlert price monitor
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/opt/flightAlert
   ExecStart=/opt/flightAlert/.venv/bin/python /opt/flightAlert/flight_alert.py
   Restart=always
   RestartSec=10
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

   > 把 `User=ubuntu` 换成你 SSH 登录用的用户名（`echo $USER` 查看）。

5. **启动并设为开机自启**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now flightalert
   sudo systemctl status flightalert      # 看到 active (running) 即成功
   ```

6. **日常运维**

   ```bash
   # 查看实时日志
   sudo journalctl -u flightalert -f

   # 停止 / 启动 / 重启
   sudo systemctl stop flightalert
   sudo systemctl start flightalert
   sudo systemctl restart flightalert

    # 接口失败告警来了之后：检查网络/接口 → 重启服务
   ```

这样脚本就会 7×24 持续运行，服务器重启后会自动拉起，崩溃后 10 秒内自动重启。日志在 journald 里，统一用 `journalctl` 查看与清理。

> 如果不想用 systemd，只是临时跑：把第 5 步换成 `tmux new -s flightalert 'python flight_alert.py'`，按 `Ctrl+B D` 退出但脚本继续。

## 注意事项

- 建议监控的日期不要设置太长或已经过期的日期，以免无法获取机票信息。
- `pushplus` 微信推送功能需要在 `pushplus` 平台上注册并获取 `SCKEY`，未配置时脚本仍会持续运行并打印日志，只是不发微信。
- 本工具仅调用携程公开的查询接口，不会泄露你的携程账号密码。

## 参考项目

- 上游：[omegatao/flightAlert](https://github.com/omegatao/flightAlert)
- 本项目 fork 自：[davidwushi1145/flightAlert](https://github.com/davidwushi1145/flightAlert)

## 版权声明

本程序仅供个人学习研究，禁止用于商业用途。请尊重版权，不得将本工具用于任何违反相关法律法规的行为。
