# 航班价格提醒

本项目 fork 自 [davidwushi1145/flightAlert](https://github.com/davidwushi1145/flightAlert)，保留命令行和服务器部署方式。核心逻辑同步至上游 6724841，使用携程 15380 日历接口查询人民币含税价格。

## 运行

需要 Python 3.10 或更高版本：

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python flight_alert.py
```

Windows 可执行文件的配置放在 exe 同目录。可使用 `--config 路径` 指定配置，`--once` 查询一轮后退出，`--no-notify` 临时禁止推送。日志写入配置文件所在目录。

## 配置

修改 `config.json`，将日期改为未来日期：

```json
{
  "dateToGo": ["2027-01-05", "2027-01-06"],
  "placeFrom": "KMG",
  "placeTo": "TNA",
  "flightWay": "Oneway",
  "sleepTime": 3600,
  "priceStep": 50,
  "SCKEY": "",
  "searchType": 1,
  "grade": 1
}
```

- `dateToGo`：出发日期列表，支持 `YYYYMMDD` 或 `YYYY-MM-DD`。
- `placeFrom`、`placeTo`：城市代码。
- `flightWay`：`Oneway` 单程或 `Roundtrip` 往返。往返必须提供固定的 `returnDate`，且不早于任何出发日期。
- `sleepTime`：查询间隔（秒），默认 3600；`priceStep`：相对上次成功通知的价格变动阈值。
- `SCKEY`：[PushPlus](https://www.pushplus.plus/) token；留空只记录日志。
- `searchType`：1 国内、2 国际；`grade`：1 经济舱、2 超级经济舱、4 商务舱、8 头等舱，也支持组合 3 和 12。
- `passengerList` 可选，默认一名成人；国内日历仅支持一名成人。国际查询可指定 Adult、Child、Baby。

首次取得有效报价及价格达到阈值时，同一轮多个日期合并推送。推送失败时保留待发送状态，下轮重试；缺失报价不会作为零价。新接口返回含税日历最低价，不再区分直飞和中转，价格与实际预订页面可能不同。

网络错误和 5xx 会短暂重试；429 根据 Retry-After 或查询间隔等待。连续三次临时失败后暂停查询，并每 12 小时推送告警；检查问题后重启。业务错误或接口格式异常会停止程序并记录错误。`--once` 遇到失败直接返回非零状态。

## 服务器运行

可使用 systemd 托管，按实际路径和用户调整：

```ini
[Unit]
Description=FlightAlert price monitor
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/opt/flightAlert
ExecStart=/opt/flightAlert/.venv/bin/python /opt/flightAlert/flight_alert.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

保存为 `/etc/systemd/system/flightalert.service`，运行 `sudo systemctl daemon-reload` 和 `sudo systemctl enable --now flightalert`，通过 `journalctl -u flightalert -f` 查看日志。

运行测试：`python -m unittest discover`。

本工具仅供个人学习研究。
