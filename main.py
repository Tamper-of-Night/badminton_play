# -*- coding: utf-8 -*-
import logging
import time
import json
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('booking_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class CourtBookingSystem:
    def __init__(self, config_file='config.json'):
        """初始化系统，加载配置"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 完整的场地映射表
        self.court_mappings = {
            ("周一", "18:30-21:00"): {
                1: "r650c6c04fc918f4943f4d271",
                2: "r650c6c04fc918f4943f4d273",
                3: "r650c6c04fc918f4943f4d274",
                7: "r650c6c04fc918f4943f4d278",
                8: "r65f8f2bcfc918f57803051ed"
            },
            ("周一", "21:00-22:30"): {
                1: "r660bd230fc918f578077634f",
                2: "r660bd230fc918f5780776350",
                3: "r660bd230fc918f5780776351",
                4: "r660bd230fc918f5780776352",
                6: "r6824114b75a03c036c8f7962",
                7: "r660bd230fc918f5780776355",
                8: "r660bd230fc918f5780776356"
            },
            ("周三", "18:30-20:30"): {
                1: "r6152870f75a03c68fe0252ba",
                2: "r6152870f75a03c68fe0252bb",
                3: "r631fea17fc918f28d9ea7976",
                6: "r6824114b75a03c036c8f7963",
                7: "r6152870f75a03c68fe0252bd",
                8: "r6152870f75a03c68fe0252be"
            },
            ("周三", "20:30-22:30"): {
                1: "r615287be75a03c68fe025d0c",
                2: "r615287be75a03c68fe025d0d",
                3: "r631fee6b75a03c4ff391a971",
                4: "r63f9771c75a03c4aa436f8c8",
                5: "r631fee6b75a03c4ff391a972",
                6: "r6824114b75a03c036c8f7964",
                7: "r615287be75a03c68fe025d0f",
                8: "r6420fcd475a03c35cf66f64f"
            },
            ("周五", "21:00-22:30"): {
                1: "r65112f5875a03c70bbc49e16",
                2: "r65112f5875a03c70bbc49e17",
                3: "r65112f5875a03c70bbc49e18",
                4: "r65112f5875a03c70bbc49e19",
                5: "r65112f5875a03c70bbc49e1a",
                6: "r6824114b75a03c036c8f7966",
                7: "r65112f5875a03c70bbc49e1c",
                8: "r65112f5875a03c70bbc49e1d"
            },
            ("周六", "12-14"): {
                1: "r5f6eb54f75a03c0cbfd2d862",
                2: "r5f6eb54f75a03c0cbfd2d863",
                3: "r5f6eb54f75a03c0cbfd2d865",
                4: "r5f6eb54f75a03c0cbfd2d866",
                5: "r5f6eb54f75a03c0cbfd2d867",
                6: "r6824114b75a03c036c8f7967",
                7: "r6420fd5075a03c35cf66fd30",
                8: "r65fd9436fc918f578042f2ee"
            },
            ("周六", "14-16"): {
                1: "r5f6eb54f75a03c0cbfd2d86b",
                2: "r5f6eb54f75a03c0cbfd2d86d",
                3: "r5f6eb54f75a03c0cbfd2d86e",
                4: "r5f6eb54f75a03c0cbfd2d86f",
                5: "r5f6eb54f75a03c0cbfd2d870",
                6: "r6824114b75a03c036c8f7968",
                7: "r5f6eb54f75a03c0cbfd2d872",
                8: "r65fd9436fc918f578042f2ef"
            },
            ("周六", "16-18"): {
                1: "r5f6eb54f75a03c0cbfd2d874",
                2: "r5f6eb54f75a03c0cbfd2d875",
                3: "r622602b0fc918f7b240a7c86",
                4: "r5f6eb54f75a03c0cbfd2d877",
                5: "r5f6eb54f75a03c0cbfd2d878",
                6: "r6824114b75a03c036c8f7969",
                7: "r5f6eb54f75a03c0cbfd2d87a",
                8: "r5f6eb54f75a03c0cbfd2d87b"
            },
            ("周六", "18-20"): {
                1: "r5f6eb54f75a03c0cbfd2d87d",
                2: "r5f6eb54f75a03c0cbfd2d87e",
                3: "r622602b6fc918f7b240a7c92",
                4: "r5f6eb54f75a03c0cbfd2d880",
                5: "r5f6eb54f75a03c0cbfd2d881",
                6: "r6824114b75a03c036c8f796a",
                7: "r5f6eb54f75a03c0cbfd2d883",
                8: "r5f6eb54f75a03c0cbfd2d884"
            },
            ("周六", "20-22:30"): {
                1: "r5f6eb54f75a03c0cbfd2d886",
                2: "r5f6eb54f75a03c0cbfd2d887",
                3: "r622602c0fc918f7b240a7cdb",
                4: "r5f6eb54f75a03c0cbfd2d889",
                5: "r5f6eb54f75a03c0cbfd2d88a",
                6: "r6824114b75a03c036c8f796b",
                7: "r5f6eb54f75a03c0cbfd2d88c",
                8: "r5f6eb54f75a03c0cbfd2d88d"
            },
            ("周日", "18：00-20：00"): {
                1: "r5fb6a2e3fc918f15180bb71c",
                2: "r5fb6a2e3fc918f15180bb71d",
                3: "r62260211fc918f7b240a7ab8",
                4: "r5fb6a2e3fc918f15180bb71e",
                5: "r5fb6a2e3fc918f15180bb71f",
                6: "r6824114b75a03c036c8f796e",
                7: "r5fb6a2e3fc918f15180bb721",
                8: "r5fb6a2e3fc918f15180bb722"
            },
            ("周日", "20：00-22：30"): {
                1: "r5f6eb54f75a03c0cbfd2d898",
                2: "r5f6eb54f75a03c0cbfd2d899",
                3: "r62260211fc918f7b240a7ab9",
                4: "r5f6eb54f75a03c0cbfd2d89b",
                5: "r5f6eb54f75a03c0cbfd2d89c",
                6: "r6824124075a03c036c8f8073",
                7: "r5f6eb54f75a03c0cbfd2d89e",
                8: "r5f6eb54f75a03c0cbfd2d89f"
            }
        }

    def get_tasks_for_execution_day(self, execution_day):
        """根据执行日获取需要执行的任务"""
        tasks_to_execute = []
        
        if execution_day in self.config['execution_schedule']:
            days_to_run = self.config['execution_schedule'][execution_day]
            
            for day in days_to_run:
                if day in self.config['tasks']:
                    task_config = self.config['tasks'][day]
                    tasks_to_execute.append((day, task_config))
        
        return tasks_to_execute

    def execute_task_for_day(self, day_name, task_config):
        """执行指定日期的任务"""
        logging.info(f"开始执行 {day_name} 的任务")
        
        # 处理有多个时间段的任务（周一、周三、周六）
        if day_name in ["周一", "周三", "周六", "周日"]:
            success_count = 0
            
            # 时间段1
            if 'time_slot_1' in task_config and task_config['users_slot_1']:
                time_slot = task_config['time_slot_1']
                court = task_config['court_1']
                for user in task_config['users_slot_1']:
                    if self.auto_fill_form(
                        name=user['name'],
                        student_id=user['student_id'],
                        phone_number=user['phone_number'],
                        day=day_name,
                        time_slot=time_slot,
                        court=court
                    ):
                        success_count += 1
                    time.sleep(3)  # 每个预约间隔3秒
            
            # 时间段2
            if 'time_slot_2' in task_config and task_config['users_slot_2']:
                time_slot = task_config['time_slot_2']
                court = task_config['court_2']
                for user in task_config['users_slot_2']:
                    if self.auto_fill_form(
                        name=user['name'],
                        student_id=user['student_id'],
                        phone_number=user['phone_number'],
                        day=day_name,
                        time_slot=time_slot,
                        court=court
                    ):
                        success_count += 1
                    time.sleep(3)  # 每个预约间隔3秒
            
            return success_count
        
        # 处理单个时间段的任务（周五）
        elif day_name == "周五" and 'users' in task_config:
            success_count = 0
            time_slot = task_config['time_slot']
            court = task_config['court']
            
            for user in task_config['users']:
                if self.auto_fill_form(
                    name=user['name'],
                    student_id=user['student_id'],
                    phone_number=user['phone_number'],
                    day=day_name,
                    time_slot=time_slot,
                    court=court
                ):
                    success_count += 1
                time.sleep(3)  # 每个预约间隔3秒
            
            return success_count
        
        return 0

    def auto_fill_form(self, name, student_id, phone_number, day, time_slot, court):
        """执行表单填写"""
        try:
            # 设置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # 设置用户代理
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            logging.info(f"为 {name} 启动浏览器，预约 {day} {time_slot} 场地{court}")
            
            # 在GitHub Actions中使用
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get("http://koudaigou.net/web/formview/5f6eb43475a03c0cbfd2d74c")
                logging.info(f"{name}: 打开网页成功")
                
                wait = WebDriverWait(driver, 15)
                
                # 填写基本信息
                wait.until(EC.presence_of_element_located((By.NAME, "F1")))
                driver.find_element(By.NAME, "F1").send_keys(name)
                driver.find_element(By.NAME, "F3").send_keys(student_id)
                driver.find_element(By.NAME, "F4").send_keys(str(phone_number))
                logging.info(f"{name}: 填写基本信息成功")
                
                # 选择日期
                day_xpath = f"//label/span[contains(text(), '{day}')]"
                day_checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, day_xpath)))
                day_checkbox.click()
                logging.info(f"{name}: 选择日期: {day}")
                
                # 选择时间段
                if day == "周五" and time_slot == "21:00-22:30":
                    time_xpath = f"(//label/span[contains(text(), '{time_slot}')])[2]"
                else:
                    time_xpath = f"//label/span[contains(text(), '{time_slot}')]"
                
                time_element = wait.until(EC.element_to_be_clickable((By.XPATH, time_xpath)))
                time_element.click()
                logging.info(f"{name}: 选择时间段: {time_slot}")
                
                # 选择场地
                court_dict = self.court_mappings.get((day, time_slot), {})
                if court in court_dict:
                    label = court_dict[court]
                    court_xpath = f"//label[@for='{label}']"
                    court_choice = wait.until(EC.element_to_be_clickable((By.XPATH, court_xpath)))
                    court_choice.click()
                    logging.info(f"{name}: 选择场地: {court}")
                else:
                    logging.warning(f"{name}: 场地{court}在{day} {time_slot}中不可用")
                    return False
                
                # 提交表单
                submit_button = wait.until(EC.element_to_be_clickable((By.ID, "btnSubmit")))
                submit_button.click()
                logging.info(f"{name}: 提交表单成功")
                
                # 等待提交完成
                time.sleep(5)
                
                # 截图保存
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_name = f"success_{name}_{day}_{timestamp}.png"
                driver.save_screenshot(screenshot_name)
                
                return True
                
            except TimeoutException:
                logging.error(f"{name}: 页面加载超时")
                # 错误截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                driver.save_screenshot(f"error_{name}_{timestamp}.png")
                return False
                
            except Exception as e:
                logging.error(f"{name}: 表单填写错误: {str(e)}")
                # 错误截图
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                driver.save_screenshot(f"error_{name}_{timestamp}.png")
                return False
                
            finally:
                driver.quit()
                logging.info(f"{name}: 关闭浏览器")
                
        except Exception as e:
            logging.error(f"{name}: 浏览器启动失败: {str(e)}")
            return False

def main():
    """主函数"""
    # 获取当前星期几
    weekday = datetime.now().weekday()
    day_map = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 
               4: "周五", 5: "周六", 6: "周日"}
    current_day = day_map.get(weekday)
    
    logging.info(f"今天是: {current_day}")
    
    # 只在一、三、五执行
    if current_day not in ["周一", "周三", "周五"]:
        logging.info(f"今天不是周一、周三或周五，不执行任务")
        return
    
    # 初始化系统
    system = CourtBookingSystem()
    
    # 获取需要执行的任务
    tasks = system.get_tasks_for_execution_day(current_day)
    
    if not tasks:
        logging.info(f"今天({current_day})没有配置任务")
        return
    
    total_success = 0
    total_tasks = 0
    
    for day_name, task_config in tasks:
        logging.info(f"准备执行 {day_name} 的任务")
        success = system.execute_task_for_day(day_name, task_config)
        total_success += success
        
        # 统计任务数量
        if day_name in ["周一", "周三", "周六", "周日"]:
            total_tasks += len(task_config.get('users_slot_1', []))
            total_tasks += len(task_config.get('users_slot_2', []))
        elif day_name == "周五":
            total_tasks += len(task_config.get('users', []))
        
        # 不同日期间隔5秒
        time.sleep(5)
    
    logging.info(f"任务执行完成: 成功 {total_success}/{total_tasks}")

if __name__ == "__main__":
    main()
