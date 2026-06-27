
# 机票价格提醒工具（支持微信提醒）

本工具利用[携程 API](https://github.com/liangen1/-xiechengjipiao_aip)实时监控机票价格，并在价格变化超过设定值时，通过微信推送通知用户。该工具基于 `pushplus` 实现微信消息推送功能。

> **注意**：本工具仅供个人学习和研究使用，禁止用于商业用途。

## 功能特点

- 支持单程票和往返票的价格监控。
- 实时价格对比，价格变化时自动微信通知提醒。
- 配置简单，支持多日期、多城市监控。
- **Cookie 失效自检**：连续多次触发携程反爬（HTTP 432）时，自动停止调用 API 并按 ~2 次/天的频率推送提醒，避免无效请求和额度浪费。
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
  "sleepTime": 600,
  "priceStep": 50,
  "SCKEY": "你的 pushplus token",
  "cookie": "从浏览器复制的携程 Cookie"
}
```

字段含义：

- **`dateToGo`**：需要监控的出发日期列表（格式 `YYYYMMDD`，如 `"20251105"`）。可同时监控多个日期，每轮查询中所有日期的变化会合并为一条推送。
- **`placeFrom`**：出发城市的机场代码（见下方机场代码表）。
- **`placeTo`**：到达城市的机场代码（见下方机场代码表）。
- **`flightWay`**：机票类型，单程票用 `"Oneway"`，往返票用 `"Roundtrip"`。
- **`sleepTime`**：查询间隔时间，单位为秒，推荐 `600`（即十分钟查询一次）。
- **`priceStep`**：价格变化的触发阈值。**直飞**和**中转**价格任意一项的变化幅度（绝对值）超过该值时触发微信提醒。设为 `1` 表示任意变化都提醒。
- **`SCKEY`**：`pushplus` 的 token，详见 [pushplus 文档](https://www.pushplus.plus/doc/)。**留空时仍可监控价格，但不会发送微信通知**。
- **`cookie`**：携程的会话 Cookie，**必填**（详见下方 *关于携程 Cookie*）。

### 关于携程 Cookie

携程的航班价格接口对未携带会话信息的请求统一返回 HTTP **432**。本工具不会模拟登录获取 Cookie，而是要求你从浏览器复制一份当前有效的会话 Cookie 写入 `config.json`。

获取方式：

1. 在 Chrome / Edge 打开 `https://flights.ctrip.com/`，做一次正常的航班搜索（让页面拿到会话 Cookie）
2. 按 `F12` 打开 DevTools → 切到 **Network** 选项卡
3. 在网络列表中找到 `itinerary/api/12808/lowestPrice` 这条请求
4. 在 **Request Headers** 区域找到 `Cookie:`，**右键 → Copy value**
5. 把整段字符串粘到 `config.json` 的 `"cookie"` 字段（保留双引号）

> **注意**
> - Cookie 会过期，过期后会再次收到 432。当本工具检测到连续 3 次 432 时，会自动停止调用 API 并按约 12 小时一次的频率推送"Cookie 可能失效"提醒。修好 cookie 后重启程序即可恢复。
> - 不要把真实的 Cookie 提交到 git 仓库；建议 `config.json` 里始终留空，本地副本里填入。

## 推送消息示例

单次推送会把当轮所有变化日期合并为一条微信消息：

```
昆明 → 济南 航班价格提醒
2025-11-05: 直飞: ¥480, 中转: ¥700
2025-11-06: 直飞: ¥550, 中转: ¥760
```

当 Cookie 失效时，推送内容类似：

```
【航班监控告警】携程接口已连续 3 次返回 432，Cookie 可能已失效，
请尽快更新 config.json 中的 cookie 字段。
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

## 注意事项

- 建议监控的日期不要设置太长或已经过期的日期，以免无法获取机票信息。
- `pushplus` 微信推送功能需要在 `pushplus` 平台上注册并获取 `SCKEY`，未配置时脚本仍会持续运行并打印日志，只是不发微信。
- 本工具仅调用携程公开的查询接口，不会泄露你的携程账号密码，但 Cookie 等同于短期会话凭证，请妥善保管。

## 参考项目

- 本工具改进自 [flightAlert](https://github.com/omegatao/flightAlert)

## 版权声明

本程序仅供个人学习研究，禁止用于商业用途。请尊重版权，不得将本工具用于任何违反相关法律法规的行为。
