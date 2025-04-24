#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import time
import sys
import logging
import signal
import platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("服务启动器")

# 全局变量
MYSQL_PASSWORD = "020804"
CELERY_APP = "celery_tasks.app"
# MySQL可能的服务名列表
MYSQL_SERVICE_NAMES = ["mysql93", "MySQL", "MySQL80", "MySQL8.0", "MySQL57", "MySQL5.7", "MYSQL"]
SERVICES_STATUS = {
    "mysql": False,
    "celery": False
}
process_handlers = {}

def is_windows():
    """检查是否为Windows系统"""
    return platform.system().lower() == "windows"

def run_command(command, shell=True, background=True, env=None):
    """
    运行命令行命令
    
    Args:
        command: 要运行的命令
        shell: 是否在shell中运行
        background: 是否在后台运行
        env: 环境变量
        
    Returns:
        subprocess.Popen: 进程对象
    """
    try:
        logger.info(f"执行命令: {command}")
        
        if background:
            if is_windows():
                # Windows中使用CREATE_NEW_CONSOLE让进程在新窗口运行
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 1  # SW_SHOWNORMAL
                
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    env=env
                )
            else:
                # Linux/Mac中直接创建子进程
                process = subprocess.Popen(
                    command,
                    shell=shell,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=env
                )
        else:
            # 同步运行，等待命令完成
            process = subprocess.Popen(
                command,
                shell=shell,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                logger.error(f"命令执行失败: {stderr.decode('utf-8', errors='ignore')}")
                return None
            logger.info(f"命令执行成功: {stdout.decode('utf-8', errors='ignore')}")
            
        return process
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
        return None

def start_mysql():
    """启动MySQL服务"""
    global SERVICES_STATUS, process_handlers
    
    if SERVICES_STATUS["mysql"]:
        logger.info("MySQL服务已在运行中")
        return True
    
    try:
        if is_windows():
            # 检查所有可能的MySQL服务名
            mysql_service_running = False
            active_service_name = None
            
            # 检查是否有任何MySQL服务正在运行
            for service_name in MYSQL_SERVICE_NAMES:
                check_cmd = f"sc query {service_name}"
                check_process = subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = check_process.communicate()
                
                if "RUNNING" in stdout.decode('utf-8', errors='ignore'):
                    logger.info(f"MySQL服务({service_name})已在运行中")
                    SERVICES_STATUS["mysql"] = True
                    mysql_service_running = True
                    active_service_name = service_name
                    break
            
            # 如果有服务正在运行，则返回成功
            if mysql_service_running:
                return True
                
            # 如果没有服务运行，则尝试启动所有可能的服务名
            for service_name in MYSQL_SERVICE_NAMES:
                logger.info(f"尝试启动MySQL服务: {service_name}")
                # 启动MySQL服务
                start_cmd = f"net start {service_name}"
                process = run_command(start_cmd, background=False)
                
                if process is not None:  # 如果命令至少执行成功
                    # 再次检查服务是否启动
                    check_cmd = f"sc query {service_name}"
                    check_process = subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, _ = check_process.communicate()
                    
                    if "RUNNING" in stdout.decode('utf-8', errors='ignore'):
                        logger.info(f"MySQL服务({service_name})已成功启动")
                        SERVICES_STATUS["mysql"] = True
                        active_service_name = service_name
                        return True
            
            # 如果所有尝试都失败，则尝试以管理员身份启动
            logger.warning("所有MySQL服务启动尝试失败，尝试以管理员身份启动...")
            for service_name in MYSQL_SERVICE_NAMES:
                admin_cmd = f'powershell -Command "Start-Process cmd -Verb RunAs -ArgumentList \'/c net start {service_name}\'"'
                process = run_command(admin_cmd, background=False)
                time.sleep(3)  # 等待更长时间让管理员权限命令执行
                
                # 再次检查服务是否启动
                check_cmd = f"sc query {service_name}"
                check_process = subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, _ = check_process.communicate()
                
                if "RUNNING" in stdout.decode('utf-8', errors='ignore'):
                    logger.info(f"MySQL服务({service_name})已通过管理员权限成功启动")
                    SERVICES_STATUS["mysql"] = True
                    return True
            
            # 如果尝试管理员权限后仍然失败
            logger.error("所有MySQL服务启动尝试都失败")
            
            # 尝试使用mysqld命令直接启动MySQL
            logger.info("尝试使用mysqld命令直接启动MySQL...")
            mysqld_cmd = "mysqld --console"
            process = run_command(mysqld_cmd)
            
            if process:
                process_handlers["mysql"] = process
                time.sleep(5)  # 给mysqld足够的启动时间
                logger.info("已启动MySQL服务(使用mysqld命令)")
                SERVICES_STATUS["mysql"] = True
                return True
            
            return False
        else:
            # Linux/Mac启动MySQL服务
            process = run_command("service mysql start || systemctl start mysql", background=False)
            time.sleep(2)  # 等待服务启动
            
            # 验证服务是否成功启动
            check_process = subprocess.Popen(
                "systemctl status mysql || service mysql status", 
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            stdout, _ = check_process.communicate()
            
            if "running" in stdout.decode('utf-8', errors='ignore').lower():
                logger.info("MySQL服务已成功启动")
                SERVICES_STATUS["mysql"] = True
                return True
            else:
                logger.error("MySQL服务启动失败")
                return False
            
    except Exception as e:
        logger.error(f"启动MySQL服务时出错: {str(e)}")
        return False

def start_celery():
    """启动Celery服务"""
    global SERVICES_STATUS, process_handlers
    
    if SERVICES_STATUS["celery"]:
        logger.info("Celery服务已在运行中")
        return True
    
    try:
        # 检查celery命令是否可用
        check_celery_cmd = "celery --version"
        check_process = subprocess.Popen(check_celery_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = check_process.communicate()
        
        if check_process.returncode != 0:
            logger.error(f"Celery命令不可用: {stderr.decode('utf-8', errors='ignore')}")
            logger.info("请确保已安装Celery: pip install celery")
            return False
        
        # 找到项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)  # 假设register_char是项目的一个子目录
        
        # 设置环境变量
        env = os.environ.copy()
        
        # 添加必要的环境变量
        env["MYSQL_PASSWORD"] = MYSQL_PASSWORD
        env["CELERY_BROKER_URL"] = "memory://"  # 使用内存作为消息代理，不依赖Redis
        
        logger.info(f"项目根目录: {project_root}")
        logger.info(f"Celery应用: {CELERY_APP}")
        
        # 构建Celery命令
        if is_windows():
            celery_cmd = f"cd {project_root} && celery -A {CELERY_APP} worker --loglevel=info --pool=solo --without-gossip --without-mingle"
        else:
            celery_cmd = f"cd {project_root} && celery -A {CELERY_APP} worker --loglevel=info --without-gossip --without-mingle"
        
        # 尝试找到celery_config.py文件
        config_exists = os.path.exists(os.path.join(project_root, "celery_config.py"))
        if not config_exists:
            # 如果配置文件不存在，创建一个简单的配置文件
            logger.warning("未找到celery_config.py，创建一个基本配置文件...")
            config_content = """# 自动生成的Celery配置文件
broker_url = 'memory://'
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True
worker_concurrency = 1
"""
            try:
                with open(os.path.join(project_root, "celery_config.py"), "w") as f:
                    f.write(config_content)
                logger.info("已创建不依赖Redis的celery_config.py文件")
            except Exception as e:
                logger.error(f"创建celery_config.py文件失败: {str(e)}")
        else:
            # 如果配置文件存在，修改它以使用内存作为消息代理
            try:
                with open(os.path.join(project_root, "celery_config.py"), "r") as f:
                    config_content = f.read()
                
                # 替换Redis URL为内存模式
                config_content = config_content.replace("broker_url = 'redis://localhost:6379/0'", "broker_url = 'memory://'")
                config_content = config_content.replace("result_backend = 'redis://localhost:6379/0'", "# result_backend disabled")
                
                with open(os.path.join(project_root, "celery_config.py"), "w") as f:
                    f.write(config_content)
                logger.info("已修改celery_config.py文件以不依赖Redis")
            except Exception as e:
                logger.error(f"修改celery_config.py文件失败: {str(e)}")
        
        # 启动Celery
        logger.info(f"启动Celery: {celery_cmd}")
        process = run_command(celery_cmd, env=env)
        
        if process:
            process_handlers["celery"] = process
            logger.info("Celery服务已启动")
            
            # 等待一会儿，检查进程是否存活
            time.sleep(3)
            if process.poll() is None:  # 如果进程仍在运行
                SERVICES_STATUS["celery"] = True
                return True
            else:
                stdout, stderr = process.communicate()
                logger.error(f"Celery服务启动失败: {stderr.decode('utf-8', errors='ignore')}")
                return False
        else:
            logger.error("Celery服务启动失败")
            return False
            
    except Exception as e:
        logger.error(f"启动Celery服务时出错: {str(e)}")
        return False

def start_all_services():
    """启动所有服务"""
    status = {
        "mysql": False,
        "celery": False
    }
    
    # 启动MySQL
    logger.info("开始启动MySQL服务...")
    status["mysql"] = start_mysql()
    
    # 直接启动Celery，不依赖Redis
    logger.info("开始启动Celery服务...")
    status["celery"] = start_celery()
    
    return status

def stop_services():
    """停止所有服务"""
    global process_handlers, SERVICES_STATUS
    
    for service, process in process_handlers.items():
        try:
            if process.poll() is None:  # 检查进程是否仍在运行
                logger.info(f"停止{service}服务...")
                if is_windows():
                    # Windows下结束进程
                    process.terminate()
                else:
                    # Linux/Mac下发送SIGTERM信号
                    process.send_signal(signal.SIGTERM)
                
                # 等待一段时间后检查进程是否已终止
                time.sleep(2)
                if process.poll() is None:
                    logger.warning(f"{service}服务未响应终止请求，强制结束...")
                    process.kill()
                
                SERVICES_STATUS[service] = False
                logger.info(f"{service}服务已停止")
        except Exception as e:
            logger.error(f"停止{service}服务时出错: {str(e)}")
    
    # 清空进程处理器字典
    process_handlers = {}

def show_banner():
    """显示程序Banner"""
    banner = """
    =========================================================
                    服务启动脚本
    ---------------------------------------------------------
                      版本: 1.0.0
        支持服务: MySQL | Celery
    =========================================================
    """
    print(banner)

def main():
    """主函数"""
    show_banner()
    
    # 检查系统环境
    if is_windows():
        logger.info("检测到Windows操作系统")
    else:
        logger.info(f"检测到非Windows操作系统: {platform.system()}")
    
    # 检查服务可用性
    check_services_availability()
    
    try:
        # 启动所有服务
        status = start_all_services()
        
        # 显示服务状态
        print("\n服务启动状态:")
        print("---------------------------------------------------------")
        for service, running in status.items():
            status_text = "✓ 运行中" if running else "✗ 启动失败"
            print(f"{service.upper()}: {status_text}")
        print("---------------------------------------------------------\n")
        
        # 如果所有服务都启动成功
        if all(status.values()):
            logger.info("所有服务已成功启动")
            print("\n服务连接信息:")
            print("---------------------------------------------------------")
            print(f"MySQL: localhost:3306 (密码: {MYSQL_PASSWORD})")
            print(f"Celery: 应用 {CELERY_APP}")
            print("---------------------------------------------------------\n")
        else:
            logger.warning("部分服务启动失败，请检查日志获取详细信息")
            
            # 提供故障排除建议
            print("\n故障排除建议:")
            print("---------------------------------------------------------")
            if not status["mysql"]:
                print("MySQL启动失败可能原因:")
                print("- MySQL服务未正确安装")
                print("- MySQL服务名不是'mysql93'，请检查服务名并修改脚本")
                print("- 没有足够权限启动服务，请以管理员身份运行")
                print("- MySQL数据库可能已损坏或配置错误")
            
            if not status["celery"]:
                print("\nCelery启动失败可能原因:")
                print("- Celery未安装: pip install celery")
                print("- Celery应用名称配置不正确，当前为:", CELERY_APP)
                print("- celery_config.py文件不存在或配置错误")
                print("- Python环境问题，请确保所有依赖已安装")
            print("---------------------------------------------------------\n")
        
        # 保持脚本运行，直到用户中断
        print("按 Ctrl+C 停止所有服务并退出程序...")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n用户中断操作，正在停止服务...")
        stop_services()
        print("所有服务已停止，程序退出")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        stop_services()
        print("由于错误，程序已停止所有服务并退出")

def check_services_availability():
    """检查服务是否已安装/可用"""
    results = {
        "mysql": False,
        "celery": False
    }
    
    # 检查MySQL
    logger.info("检查MySQL是否已安装...")
    mysql_found = False
    for service_name in MYSQL_SERVICE_NAMES:
        check_cmd = f"sc query {service_name}"
        try:
            check_process = subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, _ = check_process.communicate()
            if "SERVICE_NAME" in stdout.decode('utf-8', errors='ignore'):
                logger.info(f"找到MySQL服务: {service_name}")
                mysql_found = True
                break
        except:
            pass
    
    if not mysql_found:
        logger.warning("未找到MySQL服务，请确保MySQL已正确安装")
    results["mysql"] = mysql_found
    
    # 检查Celery
    logger.info("检查Celery是否已安装...")
    try:
        check_cmd = "celery --version"
        check_process = subprocess.Popen(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = check_process.communicate()
        if check_process.returncode == 0:
            logger.info(f"Celery已安装: {stdout.decode('utf-8', errors='ignore').strip()}")
            results["celery"] = True
        else:
            logger.warning("未找到Celery，请使用pip安装: pip install celery")
    except:
        logger.warning("检查Celery安装失败")
    
    # 显示检测结果
    print("\n服务可用性检测结果:")
    print("---------------------------------------------------------")
    for service, available in results.items():
        status_text = "✓ 已安装" if available else "✗ 未找到"
        print(f"{service.upper()}: {status_text}")
    print("---------------------------------------------------------\n")
    
    return results

if __name__ == "__main__":
    main() 