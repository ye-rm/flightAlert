import json
import os
import time
import logging
from typing import Dict
import sys

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('flight_alert.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 常量定义
BASE_URL = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
PUSHPLUS_URL = "https://www.pushplus.plus/send"
RETRY_DELAY = 30  # 重试等待时间（秒）
REQUEST_TIMEOUT = 10  # 请求超时时间（秒）

# Cookie 失效告警相关
COOKIE_432_THRESHOLD = 3            # 连续出现该次数的 432 即视为 cookie 失效
COOKIE_ALERT_INTERVAL = 12 * 3600   # cookie 失效提醒的推送间隔（秒，≈每天 2 次）
ALERT_MODE_POLL_INTERVAL = 30 * 60  # 告警模式下，唤醒检查的间隔（秒）

# 浏览器请求头：携程接口会对没有 UA/Referer/Cookie 的请求返回 432
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://flights.ctrip.com/",
    "Origin": "https://flights.ctrip.com",
    "Connection": "keep-alive",
}

# 机场代码到城市名称的映射
AIRPORT_CITY_MAP = {
    'BJS': '北京', 'SHA': '上海', 'CAN': '广州', 'SZX': '深圳', 'CTU': '成都', 'HGH': '杭州',
    'WUH': '武汉', 'SIA': '西安', 'CKG': '重庆', 'TAO': '青岛', 'CSX': '长沙', 'NKG': '南京',
    'XMN': '厦门', 'KMG': '昆明', 'DLC': '大连', 'TSN': '天津', 'CGO': '郑州', 'SYX': '三亚',
    'TNA': '济南', 'FOC': '福州', 'AAT': '阿勒泰', 'AKU': '阿克苏', 'AOG': '鞍山', 'AQG': '安庆',
    'AVA': '安顺', 'AXF': '阿拉善左旗', 'MFM': '中国澳门', 'NGQ': '阿里', 'RHT': '阿拉善右旗',
    'YIE': '阿尔山', 'BZX': '巴中', 'AEB': '百色', 'BAV': '包头', 'BFJ': '毕节', 'BHY': '北海',
    'PKX': '北京(大兴国际机场)', 'PEK': '北京(首都国际机场)', 'BPL': '博乐', 'BSD': '保山',
    'DBC': '白城', 'KJI': '布尔津', 'NBS': '白山', 'RLK': '巴彦淖尔', 'BPX': '昌都', 'CDE': '承德',
    'CGD': '常德', 'CGQ': '长春', 'CHG': '朝阳', 'CIF': '赤峰', 'CIH': '长治', 'CWJ': '沧源',
    'CZX': '常州', 'JUH': '池州', 'DAT': '大同', 'DAX': '达州', 'DCY': '稻城', 'DDG': '丹东',
    'DIG': '迪庆', 'DLU': '大理', 'DNH': '敦煌', 'DOY': '东营', 'DQA': '大庆', 'HXD': '德令哈',
    'DSN': '鄂尔多斯', 'EJN': '额济纳旗', 'ENH': '恩施', 'ERL': '二连浩特', 'FUG': '阜阳',
    'FYJ': '抚远', 'FYN': '富蕴', 'GMQ': '果洛', 'GOQ': '格尔木', 'GYS': '广元', 'GYU': '固原',
    'KHH': '中国高雄', 'KOW': '赣州', 'KWE': '贵阳', 'KWL': '桂林', 'AHJ': '红原', 'HAK': '海口',
    'HCJ': '河池', 'HDG': '邯郸', 'HEK': '黑河', 'HET': '呼和浩特', 'HFE': '合肥', 'HIA': '淮安',
    'HJJ': '怀化', 'HLD': '海拉尔', 'HMI': '哈密', 'HNY': '衡阳', 'HRB': '哈尔滨', 'HTN': '和田',
    'HTT': '花土沟', 'HUN': '中国花莲', 'HUO': '霍林郭勒', 'HUZ': '惠州', 'HZG': '汉中',
    'TXN': '黄山', 'XRQ': '呼伦贝尔', 'CYI': '中国嘉义', 'JDZ': '景德镇', 'JGD': '加格达奇',
    'JGN': '嘉峪关', 'JGS': '井冈山', 'JIC': '金昌', 'JIU': '九江', 'JM1': '荆门', 'JMU': '佳木斯',
    'JNG': '济宁', 'JNZ': '锦州', 'JSJ': '建三江', 'JXA': '鸡西', 'JZH': '九寨沟', 'KNH': '中国金门',
    'SWA': '揭阳', 'KCA': '库车', 'KGT': '康定', 'KHG': '喀什', 'KJH': '凯里', 'KRL': '库尔勒',
    'KRY': '克拉玛依', 'HZH': '黎平', 'JMJ': '澜沧', 'LCX': '龙岩', 'LFQ': '临汾', 'LHW': '兰州',
    'LJG': '丽江', 'LLB': '荔波', 'LLV': '吕梁', 'LNJ': '临沧', 'LNL': '陇南', 'LPF': '六盘水',
    'LXA': '拉萨', 'LYA': '洛阳', 'LYG': '连云港', 'LYI': '临沂', 'LZH': '柳州', 'LZO': '泸州',
    'LZY': '林芝', 'LUM': '芒市', 'MDG': '牡丹江', 'MFK': '中国马祖', 'MIG': '绵阳', 'MXZ': '梅州',
    'MZG': '中国马公', 'NZH': '满洲里', 'OHE': '漠河', 'KHN': '南昌', 'LZN': '中国南竿',
    'NAO': '南充', 'NGB': '宁波', 'NLH': '宁蒗', 'NNG': '南宁', 'NNY': '南阳', 'NTG': '南通',
    'PZI': '攀枝花', 'SYM': '普洱', 'BAR': '琼海', 'BPE': '秦皇岛', 'HBQ': '祁连', 'IQM': '且末',
    'IQN': '庆阳', 'JIQ': '黔江', 'JJN': '泉州', 'JUZ': '衢州', 'NDG': '齐齐哈尔', 'RIZ': '日照',
    'RKZ': '日喀则', 'RQA': '若羌', 'HPG': '神农架', 'QSZ': '莎车', 'SHE': '沈阳', 'SHF': '石河子',
    'SJW': '石家庄', 'SQD': '上饶', 'SQJ': '三明', 'WDS': '十堰', 'WGN': '邵阳', 'YSQ': '松原',
    'HYN': '台州', 'RMQ': '中国台中', 'TCG': '塔城', 'TCZ': '腾冲', 'TEN': '铜仁', 'TGO': '通辽',
    'THQ': '天水', 'TLQ': '吐鲁番', 'TNH': '通化', 'TNN': '中国台南', 'TPE': '中国台北',
    'TTT': '中国台东', 'TVS': '唐山', 'TYN': '太原', 'DTU': '五大连池', 'HLH': '乌兰浩特',
    'UCB': '乌兰察布', 'URC': '乌鲁木齐', 'WEF': '潍坊', 'WEH': '威海', 'WNH': '文山',
    'WNZ': '温州', 'WUA': '乌海', 'WUS': '武夷山', 'WUX': '无锡', 'WUZ': '梧州', 'WXN': '万州',
    'WZQ': '乌拉特中旗', 'WSK': '巫山', 'ACX': '兴义', 'GXH': '夏河', 'HKG': '中国香港',
    'JHG': '西双版纳', 'NLT': '新源', 'WUT': '忻州', 'XAI': '信阳', 'XFN': '襄阳', 'XIC': '西昌',
    'XIL': '锡林浩特', 'XNN': '西宁', 'XUZ': '徐州', 'ENY': '延安', 'INC': '银川', 'LDS': '伊春',
    'LLF': '永州', 'UYN': '榆林', 'YBP': '宜宾', 'YCU': '运城', 'YIC': '宜春', 'YIH': '宜昌',
    'YIN': '伊宁', 'YIW': '义乌', 'YKH': '营口', 'YNJ': '延吉', 'YNT': '烟台', 'YNZ': '盐城',
    'YTY': '扬州', 'YUS': '玉树', 'YYA': '岳阳', 'DYG': '张家界', 'HSN': '舟山', 'NZL': '扎兰屯',
    'YZY': '张掖', 'ZAT': '昭通', 'ZHA': '湛江', 'ZHY': '中卫', 'ZQZ': '张家口', 'ZUH': '珠海',
    'ZYI': '遵义'
}

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(current_dir, 'config.json')


def get_readable_location(airport_code: str) -> str:
    """将机场代码转换为可读的城市名称

    Args:
        airport_code: 机场代码（如 'KMG'）

    Returns:
        str: 城市名称，如果不在映射表中则返回原机场代码
    """
    return AIRPORT_CITY_MAP.get(airport_code, airport_code)


def push_message(message: str, token: str) -> bool:
    """发送推送消息到微信

    使用 pushplus 官方文档（https://www.pushplus.plus/doc/guide/api.html）推荐的
    POST + JSON 方式；pushplus 即便在参数错误时也会返回 HTTP 200，但响应体中的
    ``code`` 字段为非 200，因此除了检查 HTTP 状态外，还要校验 ``code`` 字段。

    Args:
        message: 消息内容
        token: PushPlus token

    Returns:
        bool: 发送是否成功
    """
    if not token:
        logger.warning("未配置PushPlus token，跳过消息推送")
        return False

    payload = {
        "token": token,
        "title": "航班价格提醒",
        "content": message,
        "template": "markdown",
    }
    try:
        response = requests.post(
            PUSHPLUS_URL,
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        # pushplus 业务层错误也通过 HTTP 200 返回，必须再检查 code 字段
        try:
            data = response.json()
        except ValueError:
            logger.error(
                "消息推送失败: 响应不是合法 JSON, body=%r", response.text[:200])
            return False

        if data.get("code") != 200:
            logger.error(
                "消息推送失败: code=%s, msg=%s, data=%s",
                data.get("code"), data.get("msg"), data.get("data"))
            return False

        logger.info("消息推送成功: %s", message)
        return True
    except requests.exceptions.RequestException as e:
        logger.error("消息推送失败: %s", e)
        return False


# 携程接口返回 432 几乎总是 cookie/会话失效；用连续计数 + 告警模式来兜底
_cookie_alert_state = {
    "consecutive_432": 0,    # 连续 432 计数
    "alert_mode": False,     # True 时停止调用携程 API，只推送 cookie 失效告警
    "last_alert_ts": 0.0,    # 上次推送 cookie 告警的时间戳（time.time()）
}


def _record_api_success() -> None:
    """API 调用成功时调用：清空 432 计数并退出告警模式。"""
    state = _cookie_alert_state
    if state["alert_mode"] or state["consecutive_432"]:
        logger.info("携程接口调用恢复正常，退出 cookie 告警模式")
    state["consecutive_432"] = 0
    state["alert_mode"] = False


def _record_432_error() -> None:
    """API 返回 432 时调用：累计计数；首次达到阈值时进入告警模式。"""
    state = _cookie_alert_state
    state["consecutive_432"] += 1
    if not state["alert_mode"] and state["consecutive_432"] >= COOKIE_432_THRESHOLD:
        state["alert_mode"] = True
        # 强制让首次告警立刻发出，不受 COOKIE_ALERT_INTERVAL 节流
        state["last_alert_ts"] = 0.0
        logger.warning(
            "已连续 %d 次请求返回 432，疑似 cookie 失效，"
            "进入告警模式（暂停调用携程 API，仅推送告警）",
            state["consecutive_432"],
        )


def _try_send_cookie_alert(config: dict) -> None:
    """在告警模式下按 COOKIE_ALERT_INTERVAL 节流推送 cookie 失效提醒。"""
    state = _cookie_alert_state
    if not state["alert_mode"]:
        return
    now = time.time()
    if state["last_alert_ts"] and (now - state["last_alert_ts"]) < COOKIE_ALERT_INTERVAL:
        return
    msg = (
        f"【航班监控告警】携程接口已连续 {state['consecutive_432']} 次返回 432，"
        "Cookie 可能已失效，请尽快更新 config.json 中的 cookie 字段。"
        "在 cookie 修复前，监控已暂停调用携程 API，仅保留此告警推送。"
    )
    if push_message(msg, config.get("SCKEY", "")):
        state["last_alert_ts"] = now
        logger.info("Cookie 失效告警已推送")
    else:
        logger.error("Cookie 失效告警推送失败")


def load_config() -> dict:
    """加载配置文件

    Returns:
        dict: 配置信息

    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 验证必要的配置项
        required_fields = [
            'dateToGo', 'placeFrom', 'placeTo', 'flightWay',
            'sleepTime', 'priceStep']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"配置文件缺少必要字段: {field}")

        # 验证日期列表不为空
        if not config['dateToGo'] or not isinstance(
                config['dateToGo'], list):
            raise ValueError("dateToGo 必须是一个非空列表")

        # 验证日期格式和有效性
        from datetime import datetime
        for date in config['dateToGo']:
            if not isinstance(date, str) or len(date) != 8 or not date.isdigit():
                raise ValueError(f"日期格式错误: {date}，应为8位数字 (YYYYMMDD)")
            try:
                datetime.strptime(date, '%Y%m%d')
            except ValueError:
                raise ValueError(f"无效日期: {date}")

        # 验证数值类型
        if not isinstance(
                config['sleepTime'], int) or config['sleepTime'] <= 0:
            raise ValueError("sleepTime 必须是正整数")
        if not isinstance(
                config['priceStep'], int) or config['priceStep'] <= 0:
            raise ValueError("priceStep 必须是正整数")

        logger.info(f"配置加载成功: {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {config_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"配置文件JSON格式错误: {e}")
        raise ValueError(f"配置文件格式错误: {e}")


def fetch_flight_prices(config: dict, direct: bool = True) -> dict:
    """获取航班价格信息

    Args:
        config: 配置信息
        direct: 是否只查询直飞航班

    Returns:
        dict: 航班价格数据

    Raises:
        requests.exceptions.RequestException: 网络请求失败
    """
    params = {
        'flightWay': config['flightWay'],
        'dcity': config['placeFrom'],
        'acity': config['placeTo'],
        'army': 'false'
    }

    if direct:
        params['direct'] = 'true'

    # 合并默认请求头与 config 中可选的自定义请求头/cookie
    headers = dict(DEFAULT_HEADERS)
    custom_headers = config.get('headers') or {}
    if isinstance(custom_headers, dict):
        headers.update({k: v for k, v in custom_headers.items() if v})
    cookie = config.get('cookie') or config.get('Cookie')
    if cookie:
        headers['Cookie'] = cookie

    try:
        response = requests.get(
            BASE_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 2:
            raise ValueError(f"API返回错误状态: {data.get('msg', '未知错误')}")

        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"获取{'直飞' if direct else '非直飞'}航班价格失败: {e}")
        raise


def process_price_changes(
        date: str, direct_price: int, non_direct_price: int,
        target_prices: Dict[str, int], no_target_prices: Dict[str, int],
        config: dict) -> None:
    """处理价格变化并发送通知

    Args:
        date: 日期
        direct_price: 直飞价格
        non_direct_price: 非直飞价格
        target_prices: 直飞目标价格字典
        no_target_prices: 非直飞目标价格字典
        config: 配置信息
    """
    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    logger.info(
        f'{formatted_date} - 直飞: ¥{direct_price}, 非直飞: ¥{non_direct_price}')

    if target_prices[date] == 0:
        # 第一次获取价格
        logger.info(f'首次获取 {formatted_date} 的票价')
        push_message(
            f'首次提醒: {formatted_date} 的直飞价格 ¥{direct_price}, 非直飞价格 ¥{non_direct_price}',
            config.get("SCKEY", "")
        )
        target_prices[date] = direct_price
        no_target_prices[date] = non_direct_price
    else:
        # 检查直飞价格变化
        direct_change = direct_price - target_prices[date]
        if abs(direct_change) >= config["priceStep"]:
            change_text = "上涨" if direct_change > 0 else "下降"
            logger.info(
                f'{formatted_date} 直飞价格{change_text} ¥{abs(direct_change)} '
                f'(¥{target_prices[date]} → ¥{direct_price})')
            push_message(
                f'{formatted_date} 直飞价格{change_text} ¥{abs(direct_change)}, '
                f'当前价格: ¥{direct_price}',
                config.get("SCKEY", "")
            )
            target_prices[date] = direct_price

        # 检查非直飞价格变化
        non_direct_change = non_direct_price - no_target_prices[date]
        if abs(non_direct_change) >= config["priceStep"]:
            change_text = "上涨" if non_direct_change > 0 else "下降"
            logger.info(
                f'{formatted_date} 非直飞价格{change_text} ¥{abs(non_direct_change)} '
                f'(¥{no_target_prices[date]} → ¥{non_direct_price})')
            push_message(
                f'{formatted_date} 非直飞价格{change_text} ¥{abs(non_direct_change)}, '
                f'当前价格: ¥{non_direct_price}',
                config.get("SCKEY", "")
            )
            no_target_prices[date] = non_direct_price


if __name__ == "__main__":
    try:
        # 读取配置文件
        config = load_config()
        logger.info("航班价格监控程序启动")
        
        # 显示监控路线，使用可读的城市名称
        place_from = config['placeFrom']
        place_to = config['placeTo']
        from_display = get_readable_location(place_from)
        to_display = get_readable_location(place_to)
        logger.info(f"监控路线: {from_display}({place_from}) → {to_display}({place_to})")
        logger.info(f"监控日期: {', '.join(config['dateToGo'])}")

        # 初始化目标价格字典
        target_prices: Dict[str, int] = {
            date: 0 for date in config["dateToGo"]}
        no_target_prices: Dict[str, int] = {
            date: 0 for date in config["dateToGo"]}

        while True:
            # 告警模式：暂停调用携程 API，仅按节奏推送 cookie 失效告警
            if _cookie_alert_state["alert_mode"]:
                _try_send_cookie_alert(config)
                logger.info(
                    "处于 cookie 告警模式，%d 分钟后再次检查",
                    ALERT_MODE_POLL_INTERVAL // 60,
                )
                time.sleep(ALERT_MODE_POLL_INTERVAL)
                continue

            try:
                # 获取直飞和非直飞的机票信息
                direct_data = fetch_flight_prices(config, direct=True)
                non_direct_data = fetch_flight_prices(config, direct=False)

                # 两个调用都成功才算恢复正常
                _record_api_success()

                # 解析返回的数据
                direct_results = direct_data["data"]["oneWayPrice"][0]
                non_direct_results = non_direct_data["data"]["oneWayPrice"][0]

                # 处理每个日期的价格
                for date in config["dateToGo"]:
                    if date not in direct_results or date not in non_direct_results:
                        logger.warning(
                            f"未找到日期 {date} 的价格信息，请检查日期是否有效")
                        continue

                    direct_price = direct_results[date]
                    non_direct_price = non_direct_results[date]

                    process_price_changes(
                        date, direct_price, non_direct_price,
                        target_prices, no_target_prices, config
                    )

                # 等待下次查询
                logger.info(f'本轮查询完毕，等待 {config["sleepTime"]} 秒后继续')
                time.sleep(config["sleepTime"])

            except requests.exceptions.HTTPError as e:
                # 432：疑似 cookie 失效，进入累计 / 告警逻辑
                if e.response is not None and e.response.status_code == 432:
                    _record_432_error()
                    # 达到阈值时 _record_432_error 会立即触发首次告警
                    _try_send_cookie_alert(config)
                else:
                    # 其他 HTTP 错误（如 5xx）不算 cookie 问题，重置计数
                    _record_api_success()
                logger.error(f"查询过程中出错: {e}")
                logger.info(f"等待 {RETRY_DELAY} 秒后重试")
                time.sleep(RETRY_DELAY)
            except (requests.exceptions.RequestException,
                    ValueError, KeyError) as e:
                # 网络层异常 / 解析异常：不重置 432 计数（cookie 可能仍有问题）
                logger.error(f"查询过程中出错: {e}")
                logger.info(f"等待 {RETRY_DELAY} 秒后重试")
                time.sleep(RETRY_DELAY)

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        sys.exit(1)

