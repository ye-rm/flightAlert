import json
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from datetime import datetime
import sys
import logging
from typing import Dict
from PIL import Image, ImageTk

# 常量定义
BASE_URL = "https://flights.ctrip.com/itinerary/api/12808/lowestPrice?"
PUSHPLUS_URL = "https://www.pushplus.plus/send"
RETRY_DELAY = 30
REQUEST_TIMEOUT = 10
DEFAULT_SLEEP_TIME = 600
DEFAULT_PRICE_STEP = 50

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_readable_location(airport_code: str) -> str:
    """将机场代码转换为可读的城市名称

    Args:
        airport_code: 机场代码（如 'KMG'）

    Returns:
        str: 城市名称，如果不在映射表中则返回原机场代码
    """
    return AIRPORT_CITY_MAP.get(airport_code, airport_code)


class FlightAlertApp:
    def __init__(self, root):
        self.root = root
        self.root.title("航班价格监控")
        self.root.geometry("900x650")
        self.root.minsize(900, 650)
        
        # 设置自定义主题色
        self.bg_color = "#f5f5f5"
        self.accent_color = "#1E90FF"  # 蓝色
        self.text_color = "#333333"
        self.highlight_color = "#FFD700"  # 金色
        
        # 确保配置目录存在
        self.config_dir = self._get_config_dir()
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 配置样式
        self._setup_styles()
        
        # 变量初始化
        self.dates_var = tk.StringVar()
        self.place_from_var = tk.StringVar()
        self.place_to_var = tk.StringVar()
        self.flight_way_var = tk.StringVar(value="Oneway")
        self.sleep_time_var = tk.StringVar(value=str(DEFAULT_SLEEP_TIME))
        self.price_step_var = tk.StringVar(value=str(DEFAULT_PRICE_STEP))
        self.sckey_var = tk.StringVar()
        
        # 监控状态
        self.running = False
        self.monitor_thread = None
        self.target_prices = {}
        self.no_target_prices = {}
        
        # 创建UI
        self._create_ui()
        
        # 加载配置（如果存在）
        self._load_config()
    
    def _get_config_dir(self):
        """获取配置文件目录"""
        # 在Windows上，使用用户的应用数据目录
        if sys.platform.startswith('win'):
            app_data = os.environ.get('APPDATA', '')
            if app_data:
                return os.path.join(app_data, 'flightAlert')
        
        # 在其他系统或备选方案：使用当前可执行文件所在目录
        return os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    
    def _setup_styles(self):
        """设置自定义样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置主题色
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("微软雅黑", 10))
        style.configure("TButton", background=self.accent_color, foreground="white", font=("微软雅黑", 10))
        style.map("TButton", 
                 background=[("active", self.highlight_color), ("disabled", "#cccccc")],
                 foreground=[("active", self.text_color), ("disabled", "#666666")])
        
        # 标题样式
        style.configure("Title.TLabel", font=("微软雅黑", 16, "bold"), foreground=self.accent_color)
        
        # 子标题样式
        style.configure("Subtitle.TLabel", font=("微软雅黑", 12), foreground=self.text_color)
        
        # 标签框样式
        style.configure("TLabelframe", background=self.bg_color)
        style.configure("TLabelframe.Label", background=self.bg_color, foreground=self.accent_color, font=("微软雅黑", 11, "bold"))
        
        # 笔记本样式
        style.configure("TNotebook", background=self.bg_color, tabposition='n')
        style.configure("TNotebook.Tab", background="#e0e0e0", foreground=self.text_color, padding=[10, 5], font=("微软雅黑", 10))
        style.map("TNotebook.Tab", 
                 background=[("selected", self.accent_color)],
                 foreground=[("selected", "white")])
        
        # 输入框样式
        style.configure("TEntry", fieldbackground="white", foreground=self.text_color, font=("微软雅黑", 10))
        
        # 按钮样式
        style.configure("Primary.TButton", font=("微软雅黑", 10, "bold"))
        style.configure("Secondary.TButton", background="#f0f0f0", foreground=self.text_color)
        
        # 开始按钮
        style.configure("Start.TButton", background="#4CAF50", foreground="white", font=("微软雅黑", 10, "bold"))
        style.map("Start.TButton", background=[("active", "#66BB6A"), ("disabled", "#A5D6A7")])
        
        # 停止按钮
        style.configure("Stop.TButton", background="#F44336", foreground="white", font=("微软雅黑", 10, "bold"))
        style.map("Stop.TButton", background=[("active", "#EF5350"), ("disabled", "#FFCDD2")])
    
    def _create_ui(self):
        # 创建带标签的笔记本
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置标签页
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="配置设置")
        
        # 监控标签页
        monitor_frame = ttk.Frame(notebook)
        notebook.add(monitor_frame, text="价格监控")
        
        # 创建配置UI
        self._create_config_ui(config_frame)
        
        # 创建监控UI
        self._create_monitor_ui(monitor_frame)
    
    def _create_config_ui(self, parent):
        # 标题
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # 如果有图标，添加图标
        try:
            icon_path = resource_path("icon.png")
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path).resize((32, 32))
                icon_photo = ImageTk.PhotoImage(icon_img)
                icon_label = ttk.Label(
                    header_frame,
                    image=icon_photo,
                    background=self.bg_color)
                icon_label.image = icon_photo  # 保持引用
                icon_label.pack(side=tk.LEFT, padx=(0, 10))
        except (FileNotFoundError, OSError):
            pass
        
        ttk.Label(header_frame, text="航班价格监控配置", style="Title.TLabel").pack(side=tk.LEFT)
        
        # 分隔线
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # 创建表单
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.BOTH, padx=30, pady=10)
        
        # 创建两列布局
        form_frame.columnconfigure(0, weight=2)
        form_frame.columnconfigure(1, weight=3)
        
        # 日期
        ttk.Label(form_frame, text="监控日期 (格式YYYYMMDD，用逗号分隔):", style="Subtitle.TLabel").grid(row=0, column=0, sticky=tk.W, pady=(10, 5))
        date_entry = ttk.Entry(form_frame, textvariable=self.dates_var, width=50)
        date_entry.grid(row=0, column=1, sticky=tk.W, pady=(10, 5))
        
        # 出发地
        ttk.Label(form_frame, text="出发机场代码:", style="Subtitle.TLabel").grid(row=1, column=0, sticky=tk.W, pady=10)
        ttk.Entry(form_frame, textvariable=self.place_from_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=10)
        
        # 目的地
        ttk.Label(form_frame, text="到达机场代码:", style="Subtitle.TLabel").grid(row=2, column=0, sticky=tk.W, pady=10)
        ttk.Entry(form_frame, textvariable=self.place_to_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=10)
        
        # 航程类型
        ttk.Label(form_frame, text="航程类型:", style="Subtitle.TLabel").grid(row=3, column=0, sticky=tk.W, pady=10)
        flight_way_combo = ttk.Combobox(form_frame, textvariable=self.flight_way_var, values=["Oneway", "Roundtrip"], width=12, state="readonly")
        flight_way_combo.grid(row=3, column=1, sticky=tk.W, pady=10)
        flight_way_combo.current(0)
        
        # 刷新间隔
        ttk.Label(form_frame, text="检查间隔 (秒):", style="Subtitle.TLabel").grid(row=4, column=0, sticky=tk.W, pady=10)
        ttk.Entry(form_frame, textvariable=self.sleep_time_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=10)
        
        # 价格变动阈值
        ttk.Label(form_frame, text="价格变动阈值 (元):", style="Subtitle.TLabel").grid(row=5, column=0, sticky=tk.W, pady=10)
        ttk.Entry(form_frame, textvariable=self.price_step_var, width=10).grid(row=5, column=1, sticky=tk.W, pady=10)
        
        # PushPlus推送令牌
        ttk.Label(form_frame, text="PushPlus推送令牌:", style="Subtitle.TLabel").grid(row=6, column=0, sticky=tk.W, pady=10)
        ttk.Entry(form_frame, textvariable=self.sckey_var, width=50).grid(row=6, column=1, sticky=tk.W, pady=10)
        
        # 提示文本
        tip_frame = ttk.Frame(parent)
        tip_frame.pack(fill=tk.X, padx=30, pady=5)
        tip_text = "提示: PushPlus推送令牌用于发送价格变动通知到您的微信，可在 pushplus.plus 网站获取"
        ttk.Label(tip_frame, text=tip_text, foreground="#666666", font=("微软雅黑", 9)).pack(anchor=tk.W)
        
        # 配置保存位置提示
        config_path_frame = ttk.Frame(parent)
        config_path_frame.pack(fill=tk.X, padx=30, pady=5)
        config_path_text = f"配置文件保存位置: {self.config_dir}"
        ttk.Label(config_path_frame, text=config_path_text, foreground="#666666", font=("微软雅黑", 9)).pack(anchor=tk.W)
        
        # 按钮
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, padx=30, pady=20)
        
        ttk.Button(buttons_frame, text="保存配置", style="Primary.TButton", command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="加载配置", style="Secondary.TButton", command=self._load_config).pack(side=tk.LEFT, padx=5)
    
    def _create_monitor_ui(self, parent):
        # 控制按钮框架
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # 标题
        ttk.Label(controls_frame, text="航班价格监控", style="Title.TLabel").pack(side=tk.LEFT)
        
        # 按钮放在右边
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        self.start_button = ttk.Button(buttons_frame, text="开始监控", style="Start.TButton", command=self._start_monitoring, width=12)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(buttons_frame, text="停止监控", style="Stop.TButton", command=self._stop_monitoring, width=12, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 状态框架
        status_frame = ttk.LabelFrame(parent, text="当前状态")
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="准备就绪，等待开始监控", font=("微软雅黑", 10))
        self.status_label.pack(padx=15, pady=10, anchor=tk.W)
        
        # 价格框架
        prices_frame = ttk.LabelFrame(parent, text="当前价格")
        prices_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.prices_text = scrolledtext.ScrolledText(prices_frame, height=6, wrap=tk.WORD, font=("微软雅黑", 10))
        self.prices_text.pack(fill=tk.X, padx=10, pady=10)
        self.prices_text.config(state=tk.DISABLED)
        
        # 日志框架
        log_frame = ttk.LabelFrame(parent, text="活动日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=("微软雅黑", 10))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.config(state=tk.DISABLED)
        
        # 添加欢迎信息
        self._log("欢迎使用航班价格监控系统！")
        self._log("请在配置页面设置监控参数，然后点击开始监控按钮")
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            # 解析并验证日期
            dates = [date.strip()
                     for date in self.dates_var.get().split(",") if date.strip()]

            # 验证配置
            if not dates:
                raise ValueError("请至少输入一个日期")

            place_from = self.place_from_var.get().strip().upper()
            place_to = self.place_to_var.get().strip().upper()

            if not place_from:
                raise ValueError("请输入出发机场代码")
            if not place_to:
                raise ValueError("请输入到达机场代码")

            # 验证机场代码格式（应为3个字母）
            if len(place_from) != 3 or not place_from.isalpha():
                raise ValueError(
                    f"出发机场代码格式错误: {place_from}，应为3个字母的IATA代码")
            if len(place_to) != 3 or not place_to.isalpha():
                raise ValueError(
                    f"到达机场代码格式错误: {place_to}，应为3个字母的IATA代码")

            # 验证日期格式和有效性
            for date in dates:
                if len(date) != 8 or not date.isdigit():
                    raise ValueError(
                        f"日期格式错误: {date}，应为8位数字 (YYYYMMDD)")
                # 验证日期是否有效
                try:
                    datetime.strptime(date, '%Y%m%d')
                except ValueError:
                    raise ValueError(f"无效日期: {date}")

            # 验证数值
            try:
                sleep_time = int(self.sleep_time_var.get())
                if sleep_time <= 0:
                    raise ValueError("检查间隔必须大于0")
            except ValueError:
                raise ValueError("检查间隔必须是有效的正整数")

            try:
                price_step = int(self.price_step_var.get())
                if price_step <= 0:
                    raise ValueError("价格变动阈值必须大于0")
            except ValueError:
                raise ValueError("价格变动阈值必须是有效的正整数")

            config = {
                "dateToGo": dates,
                "placeFrom": place_from,
                "placeTo": place_to,
                "flightWay": self.flight_way_var.get(),
                "sleepTime": sleep_time,
                "priceStep": price_step,
                "SCKEY": self.sckey_var.get().strip()
            }

            # 获取配置路径
            config_path = os.path.join(self.config_dir, 'config.json')

            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._log(f"配置保存成功: {config_path}")
            messagebox.showinfo("成功", "配置保存成功")
        except ValueError as e:
            self._log(f"配置验证失败: {str(e)}")
            messagebox.showerror("错误", str(e))
        except Exception as e:
            self._log(f"保存配置出错: {str(e)}")
            messagebox.showerror("错误", f"保存配置失败: {str(e)}")
    
    def _load_config(self):
        try:
            config_path = os.path.join(self.config_dir, 'config.json')
            
            if not os.path.exists(config_path):
                self._log("未找到配置文件")
                return
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.dates_var.set(",".join(config.get("dateToGo", [])))
            self.place_from_var.set(config.get("placeFrom", ""))
            self.place_to_var.set(config.get("placeTo", ""))
            self.flight_way_var.set(config.get("flightWay", "Oneway"))
            self.sleep_time_var.set(str(config.get("sleepTime", 600)))
            self.price_step_var.set(str(config.get("priceStep", 50)))
            self.sckey_var.set(config.get("SCKEY", ""))
            
            self._log(f"配置加载成功: {config_path}")
        except Exception as e:
            self._log(f"加载配置出错: {str(e)}")
            messagebox.showerror("错误", f"加载配置失败: {str(e)}")
    
    def _start_monitoring(self):
        if self.running:
            return
        
        try:
            # 验证配置
            dates = [date.strip() for date in self.dates_var.get().split(",")]
            place_from = self.place_from_var.get()
            place_to = self.place_to_var.get()
            flight_way = self.flight_way_var.get()
            sleep_time = int(self.sleep_time_var.get())
            price_step = int(self.price_step_var.get())
            sckey = self.sckey_var.get()
            
            if not dates or "" in dates:
                raise ValueError("请至少输入一个日期")
            if not place_from:
                raise ValueError("请输入出发机场代码")
            if not place_to:
                raise ValueError("请输入到达机场代码")
            
            # 创建配置
            self.config = {
                "dateToGo": dates,
                "placeFrom": place_from,
                "placeTo": place_to,
                "flightWay": flight_way,
                "sleepTime": sleep_time,
                "priceStep": price_step,
                "SCKEY": sckey
            }
            
            # 初始化目标价格
            self.target_prices = {date: 0 for date in self.config["dateToGo"]}
            self.no_target_prices = {date: 0 for date in self.config["dateToGo"]}
            
            # 更新UI
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="价格监控进行中...")

            # 开始监控线程
            self.monitor_thread = threading.Thread(target=self._monitor_prices)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            # 显示监控路线，使用可读的城市名称
            from_display = get_readable_location(place_from)
            to_display = get_readable_location(place_to)
            self._log(f"价格监控已启动 - 路线: {from_display}({place_from}) → {to_display}({place_to})")
        except Exception as e:
            self._log(f"启动监控出错: {str(e)}")
            messagebox.showerror("错误", f"启动监控失败: {str(e)}")
    
    def _stop_monitoring(self):
        if not self.running:
            return
        
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_label.config(text="监控已停止")
        self._log("价格监控已停止")
    
    def _monitor_prices(self):
        """监控价格主循环"""
        while self.running:
            try:
                # 更新状态
                self._update_status(f"正在检查价格 ({datetime.now().strftime('%H:%M:%S')})")
                
                # 构建请求参数
                params_base = {
                    'flightWay': self.config["flightWay"],
                    'dcity': self.config["placeFrom"],
                    'acity': self.config["placeTo"],
                    'army': 'false'
                }
                
                # 获取直飞航班价格
                self._log("正在请求直飞航班数据...")
                params_direct = {**params_base, 'direct': 'true'}
                
                try:
                    direct_response = requests.get(BASE_URL, params=params_direct, timeout=REQUEST_TIMEOUT)
                    direct_response.raise_for_status()
                    direct_data = direct_response.json()
                    
                    if direct_data.get("status") == 2:
                        raise ValueError(f"API返回错误: {direct_data.get('msg', '未知错误')}")
                    
                except (requests.exceptions.RequestException, ValueError) as e:
                    self._log(f"获取直飞航班数据失败: {e}，将在{RETRY_DELAY}秒后重试")
                    self._update_prices_display("获取直飞航班数据失败")
                    self._wait_with_check(RETRY_DELAY)
                    continue
                
                # 获取非直飞航班价格
                self._log("正在请求非直飞航班数据...")
                
                try:
                    non_direct_response = requests.get(BASE_URL, params=params_base, timeout=REQUEST_TIMEOUT)
                    non_direct_response.raise_for_status()
                    non_direct_data = non_direct_response.json()
                    
                    if non_direct_data.get("status") == 2:
                        raise ValueError(f"API返回错误: {non_direct_data.get('msg', '未知错误')}")
                    
                except (requests.exceptions.RequestException, ValueError) as e:
                    self._log(f"获取非直飞航班数据失败: {e}，将在{RETRY_DELAY}秒后重试")
                    self._update_prices_display("获取非直飞航班数据失败")
                    self._wait_with_check(RETRY_DELAY)
                    continue
                
                # 解析响应
                direct_results = direct_data["data"]["oneWayPrice"][0]
                non_direct_results = non_direct_data["data"]["oneWayPrice"][0]
                
                # 更新价格显示
                prices_text = ""
                
                for date in self.config["dateToGo"]:
                    if date not in direct_results or date not in non_direct_results:
                        self._log(f"未找到日期 {date} 的数据")
                        prices_text += f"日期 {date}: 暂无数据\n"
                        continue
                    
                    direct_price = direct_results[date]
                    non_direct_price = non_direct_results[date]
                    
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    prices_text += f"日期 {formatted_date}: 直飞 ¥{direct_price}, 非直飞 ¥{non_direct_price}\n"
                    self._log(f"日期 {formatted_date}: 直飞 ¥{direct_price}, 非直飞 ¥{non_direct_price}")
                    
                    if self.target_prices[date] == 0:
                        # 首次获取价格
                        self._log(f"首次获取 {formatted_date} 的价格，正在发送通知")
                        self._push_message(
                            f'首次提醒: {formatted_date} 的直飞价格 ¥{direct_price}, 非直飞价格 ¥{non_direct_price}',
                            self.config["SCKEY"]
                        )
                        self.target_prices[date] = direct_price
                        self.no_target_prices[date] = non_direct_price
                    else:
                        # 检查直飞价格变化
                        direct_change = direct_price - self.target_prices[date]
                        if abs(direct_change) >= self.config["priceStep"]:
                            change_text = "上涨" if direct_change > 0 else "下降"
                            self._log(f"{formatted_date} 的直飞价格{change_text} ¥{abs(direct_change)} (从 ¥{self.target_prices[date]} 变为 ¥{direct_price})")
                            self._push_message(
                                f'{formatted_date} 的直飞价格{change_text} ¥{abs(direct_change)}，当前价格: ¥{direct_price}',
                                self.config["SCKEY"]
                            )
                            self.target_prices[date] = direct_price
                        
                        # 检查非直飞价格变化
                        non_direct_change = non_direct_price - self.no_target_prices[date]
                        if abs(non_direct_change) >= self.config["priceStep"]:
                            change_text = "上涨" if non_direct_change > 0 else "下降"
                            self._log(f"{formatted_date} 的非直飞价格{change_text} ¥{abs(non_direct_change)} (从 ¥{self.no_target_prices[date]} 变为 ¥{non_direct_price})")
                            self._push_message(
                                f'{formatted_date} 的非直飞价格{change_text} ¥{abs(non_direct_change)}，当前价格: ¥{non_direct_price}',
                                self.config["SCKEY"]
                            )
                            self.no_target_prices[date] = non_direct_price
                
                # 更新价格显示
                self._update_prices_display(prices_text)
                
                # 等待下次检查
                self._update_status(f"下次检查将在 {self.config['sleepTime']} 秒后进行")
                self._wait_with_check(self.config["sleepTime"])
                
            except Exception as e:
                self._log(f"监控过程中出错: {str(e)}")
                logger.exception("监控过程异常")
                self._update_status(f"错误: {str(e)}")
                self._wait_with_check(RETRY_DELAY)
    
    def _wait_with_check(self, seconds: int) -> None:
        """等待指定秒数，同时检查运行状态并显示倒计时

        Args:
            seconds: 等待秒数
        """
        for i in range(seconds):
            if not self.running:
                return
            remaining = seconds - i
            self._update_status(f"下次检查将在 {remaining} 秒后进行")
            time.sleep(1)
    
    def _push_message(self, message: str, token: str) -> bool:
        """发送推送消息
        
        Args:
            message: 消息内容
            token: PushPlus token
            
        Returns:
            bool: 是否成功发送
        """
        if not token:
            self._log("未提供PushPlus令牌，跳过通知")
            return False
        
        try:
            params = {
                'token': token,
                'title': '航班价格提醒',
                'content': message
            }
            response = requests.get(PUSHPLUS_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            if response.status_code == 200:
                self._log(f"通知已发送: {message}")
                return True
            else:
                self._log(f"发送通知失败，状态码: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self._log(f"发送通知出错: {str(e)}")
            return False
    
    def _log(self, message):
        """添加带时间戳的日志消息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.root.after(0, self._update_log, log_message)
    
    def _update_log(self, message):
        """更新日志文本框（线程安全）"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def _update_status(self, status):
        """更新状态标签（线程安全）"""
        self.root.after(0, lambda: self.status_label.config(text=status))
    
    def _update_prices_display(self, text):
        """更新价格文本框（线程安全）"""
        self.root.after(0, self._set_prices_text, text)
    
    def _set_prices_text(self, text):
        """设置价格文本框内容（从主线程调用）"""
        self.prices_text.config(state=tk.NORMAL)
        self.prices_text.delete(1.0, tk.END)
        self.prices_text.insert(tk.END, text)
        self.prices_text.config(state=tk.DISABLED)


def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和PyInstaller打包环境"""
    try:
        # PyInstaller创建临时文件夹并将路径存储在_MEIPASS中
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    root = tk.Tk()
    
    # 设置图标
    try:
        icon_path = resource_path("icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except (FileNotFoundError, OSError, tk.TclError):
        pass

    app = FlightAlertApp(root)
    root.mainloop()
