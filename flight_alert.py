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

# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(current_dir, 'config.json')


def push_message(message: str, token: str) -> bool:
    """发送推送消息到微信

    Args:
        message: 消息内容
        token: PushPlus token

    Returns:
        bool: 发送是否成功
    """
    if not token:
        logger.warning("未配置PushPlus token，跳过消息推送")
        return False

    try:
        params = {
            'token': token,
            'title': '航班价格提醒',
            'content': message
        }
        response = requests.get(
            PUSHPLUS_URL, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logger.info(f"消息推送成功: {message}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"消息推送失败: {e}")
        return False


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

    try:
        response = requests.get(
            BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
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
        logger.info(f"监控路线: {config['placeFrom']} → {config['placeTo']}")
        logger.info(f"监控日期: {', '.join(config['dateToGo'])}")

        # 初始化目标价格字典
        target_prices: Dict[str, int] = {
            date: 0 for date in config["dateToGo"]}
        no_target_prices: Dict[str, int] = {
            date: 0 for date in config["dateToGo"]}

        while True:
            try:
                # 获取直飞和非直飞的机票信息
                direct_data = fetch_flight_prices(config, direct=True)
                non_direct_data = fetch_flight_prices(config, direct=False)

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

            except (requests.exceptions.RequestException,
                    ValueError, KeyError) as e:
                logger.error(f"查询过程中出错: {e}")
                logger.info(f"等待 {RETRY_DELAY} 秒后重试")
                time.sleep(RETRY_DELAY)

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序运行出错: {e}", exc_info=True)
        sys.exit(1)

