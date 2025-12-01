# -*- coding: utf-8 -*-
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from selenium.webdriver.chrome.service import Service # 导入 Service 类

#添加日志记录

logging.basicConfig(
    filename='shoudong.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # 关键：Windows 下写中文
)
def auto_fill_form(name, student_id, phone_number, day, time_slot, court):
    # 使用无头浏览器
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 使用无头模式来加快速度
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chromedriver_path = r"C:\Program Files\Google\Chrome\Application\chromedriver.exe"  # 将此路径替换为你的实际路径
    # driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
    service = Service(executable_path=chromedriver_path)  # Pass the path to Service
    driver = webdriver.Chrome(service=service, options=chrome_options)  # Use service argument
    # driver = webdriver.Chrome(options=chrome_options)

    logging.info("启动浏览器，准备自动填写表单")

    # 打开目标网页
    driver.get("http://koudaigou.net/web/formview/5f6eb43475a03c0cbfd2d74c")
    logging.info("打开网页成功")

    # 使用较短的等待时间加快速度
    wait = WebDriverWait(driver, 5)

    # 等待页面加载并填写信息
    wait.until(EC.presence_of_element_located((By.NAME, "F1")))
    driver.find_element(By.NAME, "F1").send_keys(name)
    driver.find_element(By.NAME, "F3").send_keys(student_id)
    driver.find_element(By.NAME, "F4").send_keys(phone_number)
    logging.info("填写基本信息成功")

    # 选择预约日期
    day_checkbox = wait.until(
        EC.element_to_be_clickable((By.XPATH, f"//label/span[contains(text(), '{day}')]"))
    )
    day_checkbox.click()
    logging.info(f"选择日期: {day}")

    # 选择时间段
    if day == "周五" and time_slot == "21:00-22:30":
        time_slot_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"(//label/span[contains(text(), '{time_slot}')])[2]"))
        )
    # elif day == "周五" and time_slot == "21:00-22:30":
    #     time_slot_element = wait.until(
    #         EC.element_to_be_clickable((By.XPATH, f"(//label/span[contains(text(), '{time_slot}')])[3]"))
    #     )
    # elif day == "周日" and time_slot == "18：00-20：00" :
    #     time_slot_element = wait.until(
    #         EC.element_to_be_clickable((By.XPATH, f"(//label/span[contains(text(), '{time_slot}')])[2]"))
    #     )
    else:
        time_slot_element = wait.until(
            EC.element_to_be_clickable((By.XPATH, f"//label/span[contains(text(), '{time_slot}')]"))
        )
    time_slot_element.click()
    logging.info(f"选择时间段: {time_slot}")

    # 场地选择映射代码
    available_court_dict = {
        ("周一", "18:30-21:00"): available_court_1_18_20,
        ("周一", "21:00-22:30"): available_court_1_20_22,
        ("周三", "18:30-20:30"): available_court_3_18_19,
        ("周三", "20:30-22:30"): available_court_3_19_20,
        # ("周四", "21:00-22:30"): available_court_4,
        ("周五", "21:00-22:30"): available_court_5,
        ("周六", "12-14"): available_court_6_12_14,
        ("周六", "14-16"): available_court_6_14_16,
        ("周六", "16-18"): available_court_6_16_18,
        ("周六", "18-20"): available_court_6_18_20,
        ("周六", "20-22:30"): available_court_6_20_22,
        ("周日", "18：00-20：00"): available_court_7_18_20,
        ("周日", "20：00-22：30"): available_court_7_20_22
    }

    # 选择场地（替换你原来的整段“# 选择场地 ... 提交表单成功”代码）
    court_dict = available_court_dict.get((day, time_slot), {})  # {int_field: label_for_attr}
    selected_court = None

    # 与上次前端规则保持一致（注意：键名与时间字符串须完全一致，包括全角冒号）
    ALLOWED_BY_RULE = {
        "周一": {
            "18:30-21:00": [1, 2, 3, 7, 8],
            "21:00-22:30": [1, 2, 3, 4, 6, 7, 8],
        },
        "周三": {
            # 周三任意时段仅 1/2/3/6/7/8
            "18:30-20:30": [1, 2, 3, 6, 7, 8],
            "20:30-22:30": [1, 2, 3, 6, 7, 8],
        },
        "周五": {
            "21:00-22:30": [1, 2, 3, 4, 6, 7, 8],
        },
        # 周六、周日未在规则中声明的时段默认 1-8 全开（见下方默认逻辑）
        # 周日时间保留全角冒号
        "周日": {
            "18：00-20：00": [1, 2, 3, 4, 5, 6, 7, 8],
            "20：00-22：30": [1, 2, 3, 4, 5, 6, 7, 8],
        },
    }

    # 默认优先&备选组（在“规则允许集合”内再做优先级）
    PRIORITY_FIELDS = [3, 4, 5, 8]
    BACKUP_FIELDS = [1, 2, 6, 7]

    def get_rule_allowed_fields(day_str: str, slot_str: str):
        """规则层允许的场地集合（若规则未定义该键，返回默认 1..8）"""
        if day_str in ALLOWED_BY_RULE and slot_str in ALLOWED_BY_RULE[day_str]:
            return set(ALLOWED_BY_RULE[day_str][slot_str])
        # 未声明的时段默认允许 1..8
        return set(range(1, 9))

    def select_court_from_list(court_list):
        """在给定列表顺序中找第一个可选的场地（页面剩余:1）"""
        nonlocal selected_court
        for field in court_list:
            label = court_dict.get(field)
            if not label:
                continue
            court_xpath = f"//label[@for='{label}']/following-sibling::label[@class='residue']"
            try:
                court_status = driver.find_element(By.XPATH, court_xpath).text
                # 如需兼容全角冒号，可用： if ("剩余:1" in court_status) or ("剩余：1" in court_status):
                if "剩余:1" in court_status:
                    selected_court = field
                    return True
                else:
                    logging.info(f"场地 {field} 已满")
            except Exception as _:
                logging.info(f"场地 {field} 查找失败")
        return False

    try:
        # 1) 规则允许集合 ∩ 页面存在集合
        rule_allowed = get_rule_allowed_fields(day, time_slot)  # 按业务规则允许
        page_available_fields = set(court_dict.keys())  # 页面上有对应 label 的场地
        effective_allowed = list(sorted(rule_allowed & page_available_fields))

        if not effective_allowed:
            logging.info("根据规则与页面可用性，当前时段无可预约场地")
        else:
            # 2) 先尝试“用户指定的场地”（若传入且在有效允许集合中）
            if court is not None:
                try:
                    court_int = int(court)
                except Exception:
                    court_int = None

                if court_int and court_int in effective_allowed:
                    label = court_dict.get(court_int)
                    if label:
                        court_xpath = f"//label[@for='{label}']/following-sibling::label[@class='residue']"
                        try:
                            court_status = driver.find_element(By.XPATH, court_xpath).text
                            if "剩余:1" in court_status:
                                selected_court = court_int
                            else:
                                logging.info(f"场地 {court_int} 已满，尝试优先/备选")
                        except Exception:
                            logging.info(f"场地 {court_int} 查找失败，尝试优先/备选")
                else:
                    logging.info("传入的场地不在本时段的有效允许集合内，跳过该场地")

            # 3) 若未选上，按优先→备选尝试（都在有效集合中再排序）
            if not selected_court:
                # 过滤优先、备选到有效允许集合内，并去掉已尝试的“用户指定场地”
                tried = set([int(court)]) if (court is not None and str(court).isdigit()) else set()
                priority_seq = [f for f in PRIORITY_FIELDS if f in effective_allowed and f not in tried]
                backup_seq = [f for f in BACKUP_FIELDS if f in effective_allowed and f not in tried]

                if not select_court_from_list(priority_seq):
                    logging.info("优先场地不可用或已满，尝试备选场地")
                    select_court_from_list(backup_seq)

            # 4) 点击选择或给出“全满”日志
            if not selected_court:
                logging.info("全部场地已满或不可用")
            else:
                label = court_dict[selected_court]
                court_choice = wait.until(EC.element_to_be_clickable((By.XPATH, f"//label[@for='{label}']")))
                court_choice.click()
                logging.info(f"选择场地: {selected_court}")

        # 提交
        submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
        submit_button.click()
        logging.info("提交表单成功")

    except TimeoutException:
        logging.error("操作超时，无法找到某些元素")
    except Exception as e:
        logging.error(f"填写表单时发生错误: {e}")
    finally:
        time.sleep(10)
        driver.quit()
        logging.info("关闭浏览器")


# 周一场地号对应标签
available_court_1_18_20 = {
    1: "r650c6c04fc918f4943f4d271",
    2: "r650c6c04fc918f4943f4d273",
    3: "r650c6c04fc918f4943f4d274",
    # 4: "r650c6c04fc918f4943f4d275",
    # 5: "r650c6c04fc918f4943f4d276",
    # 6: "r650c6c04fc918f4943f4d277",
    7: "r650c6c04fc918f4943f4d278",
    8: "r65f8f2bcfc918f57803051ed"
}

available_court_1_20_22 = {
    1: "r660bd230fc918f578077634f",
    2: "r660bd230fc918f5780776350",
    3: "r660bd230fc918f5780776351",
    4: "r660bd230fc918f5780776352",
    # 5: "r660bd230fc918f5780776353",
    6: "r6824114b75a03c036c8f7962",
    7: "r660bd230fc918f5780776355",
    8: "r660bd230fc918f5780776356"
}

# 周三场地号对应标签
available_court_3_18_19 = {
    1: "r6152870f75a03c68fe0252ba",
    2: "r6152870f75a03c68fe0252bb",
    3: "r631fea17fc918f28d9ea7976",
    # 4: "r631fea17fc918f28d9ea7977",
    # 5: "r631fea17fc918f28d9ea7978",
    6: "r6824114b75a03c036c8f7963",
    7: "r6152870f75a03c68fe0252bd",
    8: "r6152870f75a03c68fe0252be"
}

available_court_3_19_20 = {
    1: "r615287be75a03c68fe025d0c",
    2: "r615287be75a03c68fe025d0d",
    3: "r631fee6b75a03c4ff391a971",
    4: "r63f9771c75a03c4aa436f8c8",
    5: "r631fee6b75a03c4ff391a972",
    6: "r6824114b75a03c036c8f7964",
    7: "r615287be75a03c68fe025d0f",
    8: "r6420fcd475a03c35cf66f64f"
}
# 周四场地号对应标签
# available_court_4 = {
#     1: "r660bd262fc918f57807763db",
#     2: "r660bd262fc918f57807763dc",
#     3: "r660bd262fc918f57807763dd",
#     4: "r660bd262fc918f57807763de",
#     5: "r660bd262fc918f57807763df",
#     6: "r660bd262fc918f57807763e0",
#     7: "r660bd262fc918f57807763e1",
#     8: "r660bd262fc918f57807763e2"
# }

# 周五场地号对应标签
available_court_5 = {
    1: "r65112f5875a03c70bbc49e16",
    2: "r65112f5875a03c70bbc49e17",
    3: "r65112f5875a03c70bbc49e18",
    4: "r65112f5875a03c70bbc49e19",
    5: "r65112f5875a03c70bbc49e1a",
    6: "r6824114b75a03c036c8f7966",
    7: "r65112f5875a03c70bbc49e1c",
    8: "r65112f5875a03c70bbc49e1d"
}

# 周六场地号对应标签
available_court_6_12_14 = {
    1: "r5f6eb54f75a03c0cbfd2d862",
    2: "r5f6eb54f75a03c0cbfd2d863",
    3: "r5f6eb54f75a03c0cbfd2d865",
    4: "r5f6eb54f75a03c0cbfd2d866",
    5: "r5f6eb54f75a03c0cbfd2d867",
    6: "r6824114b75a03c036c8f7967",
    7: "r6420fd5075a03c35cf66fd30",
    8: "r65fd9436fc918f578042f2ee"
}

available_court_6_14_16 = {
    1: "r5f6eb54f75a03c0cbfd2d86b",
    2: "r5f6eb54f75a03c0cbfd2d86d",
    3: "r5f6eb54f75a03c0cbfd2d86e",
    4: "r5f6eb54f75a03c0cbfd2d86f",
    5: "r5f6eb54f75a03c0cbfd2d870",
    6: "r6824114b75a03c036c8f7968",
    7: "r5f6eb54f75a03c0cbfd2d872",
    8: "r65fd9436fc918f578042f2ef"
}

available_court_6_16_18 = {
    1: "r5f6eb54f75a03c0cbfd2d874",
    2: "r5f6eb54f75a03c0cbfd2d875",
    3: "r622602b0fc918f7b240a7c86",
    4: "r5f6eb54f75a03c0cbfd2d877",
    5: "r5f6eb54f75a03c0cbfd2d878",
    6: "r6824114b75a03c036c8f7969",
    7: "r5f6eb54f75a03c0cbfd2d87a",
    8: "r5f6eb54f75a03c0cbfd2d87b"
}

available_court_6_18_20 = {
    1: "r5f6eb54f75a03c0cbfd2d87d",
    2: "r5f6eb54f75a03c0cbfd2d87e",
    3: "r622602b6fc918f7b240a7c92",
    4: "r5f6eb54f75a03c0cbfd2d880",
    5: "r5f6eb54f75a03c0cbfd2d881",
    6: "r6824114b75a03c036c8f796a",
    7: "r5f6eb54f75a03c0cbfd2d883",
    8: "r5f6eb54f75a03c0cbfd2d884"
}

available_court_6_20_22 = {
    1: "r5f6eb54f75a03c0cbfd2d886",
    2: "r5f6eb54f75a03c0cbfd2d887",
    3: "r622602c0fc918f7b240a7cdb",
    4: "r5f6eb54f75a03c0cbfd2d889",
    5: "r5f6eb54f75a03c0cbfd2d88a",
    6: "r6824114b75a03c036c8f796b",
    7: "r5f6eb54f75a03c0cbfd2d88c",
    8: "r5f6eb54f75a03c0cbfd2d88d"
}

# 周日场地号对应标签
available_court_7_18_20 = {
    1: "r5fb6a2e3fc918f15180bb71c",
    2: "r5fb6a2e3fc918f15180bb71d",
    3: "r62260211fc918f7b240a7ab8",
    4: "r5fb6a2e3fc918f15180bb71e",
    5: "r5fb6a2e3fc918f15180bb71f",
    6: "r6824114b75a03c036c8f796e",
    7: "r5fb6a2e3fc918f15180bb721",
    8: "r5fb6a2e3fc918f15180bb722"
}

available_court_7_20_22 = {
    1: "r5f6eb54f75a03c0cbfd2d898",
    2: "r5f6eb54f75a03c0cbfd2d899",
    3: "r62260211fc918f7b240a7ab9",
    4: "r5f6eb54f75a03c0cbfd2d89b",
    5: "r5f6eb54f75a03c0cbfd2d89c",
    6: "r6824124075a03c036c8f8073",
    7: "r5f6eb54f75a03c0cbfd2d89e",
    8: "r5f6eb54f75a03c0cbfd2d89f"
}


auto_fill_form("张楠", "0221147015", 18180391342,"周三","18:30-20:30",8)

###使用定时任务管理程序
# 获取python路径：python -c "import sys; print(sys.executable)"
# 获取本文件路径：D:\001待处理\pythonProject1\web_link_badimitation\shoudong.py
# 设置时间

# # 创建调度器
# scheduler = BlockingScheduler()
#
# # 添加每天中午12点触发的任务
# scheduler.add_job(
#     auto_fill_form,
#     'cron',
#     hour=12,
#     minute=20,
#     args=["金渠成", "0221147033", 15180391342, "周三", "18:00-19:00", 8]
# )

# print("Scheduler started. Waiting for the next execution at 12:00...")
# # 启动调度器

# scheduler.start()
