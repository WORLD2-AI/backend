#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from character_system.config import logger
from character_system.tasks import update_all_character_positions
from character_system.character_scheduler import send_character_tasks
from celery_tasks.path_generator import generate_all_paths
from character_system.character_position_workflow import run_position_workflow
from character_system.services import sync_character_data_to_redis, start_sync_service
from character_system.start_services import start_all_services
from character_system.utils import view_all_redis_keys, clear_redis_data, export_redis_data, import_redis_data

def print_help():
    """打印帮助信息"""
    print("使用方法:")
    print("  python -m character_system.run               # 执行完整初始化")
    print("  python -m character_system.run --paths       # 只执行路径生成")
    print("  python -m character_system.run --positions   # 只执行位置更新")
    print("  python -m character_system.run --workflow    # 执行完整位置更新工作流")
    print("  python -m character_system.run --sync        # 执行数据同步（一次性）")
    print("  python -m character_system.run --sync-service # 启动数据同步服务")
    print("  python -m character_system.run --services    # 启动所有服务（数据同步、Celery Worker、Celery Beat）")
    print("\n数据管理工具:")
    print("  python -m character_system.run --view-keys [pattern] # 查看Redis键")
    print("  python -m character_system.run --export [filename]   # 导出Redis数据")
    print("  python -m character_system.run --import [filename]   # 导入Redis数据")
    print("  python -m character_system.run --clear [pattern]     # 清除Redis数据")
    print("  python -m character_system.run --help        # 显示此帮助信息")

def main():
    """主函数：运行脚本时执行初始化"""
    try:
        # 解析命令行参数
        if len(sys.argv) > 1:
            command = sys.argv[1].lower()
            
            if command == '--help':
                print_help()
                return
                
            elif command == '--paths':
                # 只执行路径生成
                logger.info("开始生成角色路径...")
                paths_result = generate_all_paths()
                
                if paths_result:
                    logger.info("角色路径生成完成")
                else:
                    logger.warning("角色路径生成未能完全成功")
                
                return
                
            elif command == '--positions':
                # 只执行位置更新
                logger.info("开始更新角色位置...")
                position_result = update_all_character_positions()
                
                if position_result:
                    logger.info("角色位置更新完成")
                else:
                    logger.warning("角色位置更新未能完全成功")
                
                return
                
            elif command == '--workflow':
                # 执行完整位置更新工作流
                logger.info("开始执行角色位置更新工作流...")
                workflow_result = run_position_workflow(batch_mode=True)
                
                logger.info(f"工作流执行结果: {workflow_result['status']} - {workflow_result['message']}")
                if 'stats' in workflow_result:
                    stats = workflow_result['stats']
                    logger.info(f"统计信息: 总角色数 {stats['total_characters']}, "
                                f"生成路径 {stats['paths_generated']}, "
                                f"更新位置 {stats['positions_updated']}, "
                                f"错误 {stats['errors']}")
                
                return
                
            elif command == '--sync':
                # 执行数据同步（一次性）
                logger.info("开始执行角色数据同步...")
                sync_result = sync_character_data_to_redis()
                
                if sync_result:
                    logger.info("角色数据同步完成")
                else:
                    logger.warning("角色数据同步未能完全成功")
                
                return
                
            elif command == '--sync-service':
                # 启动数据同步服务
                logger.info("正在启动数据同步服务...")
                
                # 获取同步间隔参数
                interval = 30  # 默认30秒
                if len(sys.argv) > 2:
                    try:
                        interval = int(sys.argv[2])
                    except ValueError:
                        logger.warning(f"无效的同步间隔参数: {sys.argv[2]}，将使用默认值30秒")
                
                service_result = start_sync_service(interval)
                
                if service_result:
                    logger.info(f"数据同步服务已启动，同步间隔: {interval}秒")
                    
                    # 保持程序运行
                    import time
                    try:
                        while True:
                            time.sleep(1)
                    except KeyboardInterrupt:
                        logger.info("数据同步服务已手动停止")
                else:
                    logger.warning("数据同步服务启动失败")
                
                return
                
            elif command == '--services':
                # 启动所有服务
                logger.info("正在启动所有服务...")
                service_result = start_all_services()
                
                if service_result:
                    logger.info("所有服务已成功启动")
                else:
                    logger.error("启动服务失败")
                
                return
                
            # 添加数据管理工具
            elif command == '--view-keys':
                # 查看Redis键
                pattern = sys.argv[2] if len(sys.argv) > 2 else '*'
                view_all_redis_keys(pattern)
                return
                
            elif command == '--export':
                # 导出Redis数据
                filename = sys.argv[2] if len(sys.argv) > 2 else 'redis_backup.json'
                pattern = sys.argv[3] if len(sys.argv) > 3 else '*'
                export_redis_data(filename, pattern)
                return
                
            elif command == '--import':
                # 导入Redis数据
                filename = sys.argv[2] if len(sys.argv) > 2 else 'redis_backup.json'
                overwrite = True if len(sys.argv) > 3 and sys.argv[3].lower() == 'true' else False
                import_redis_data(filename, overwrite)
                return
                
            elif command == '--clear':
                # 清除Redis数据
                pattern = sys.argv[2] if len(sys.argv) > 2 else '*'
                clear_redis_data(pattern)
                return
        
        # 执行位置更新初始化
        logger.info("正在执行角色位置初始更新...")
        position_result = update_all_character_positions()
        
        if position_result:
            logger.info("初始位置更新完成")
        else:
            logger.warning("初始位置更新未能完全成功")
        
        # 执行角色调度初始化
        logger.info("正在执行角色调度初始化...")
        scheduler_result = send_character_tasks()
        
        if scheduler_result.get('status') == 'success':
            logger.info("初始角色调度完成")
        else:
            logger.warning(f"初始角色调度未能完全成功: {scheduler_result.get('message', '')}")
        
        # 执行路径生成初始化
        logger.info("正在执行角色路径初始生成...")
        paths_result = generate_all_paths()
        
        if paths_result:
            logger.info("初始路径生成完成")
        else:
            logger.warning("初始路径生成未能完全成功")
            
        # 执行数据同步初始化
        logger.info("正在执行数据同步初始化...")
        sync_result = sync_character_data_to_redis()
        
        if sync_result:
            logger.info("初始数据同步完成")
        else:
            logger.warning("初始数据同步未能完全成功")
            
        logger.info("初始化完成")
        logger.info("提示：使用 python -m character_system.run --services 启动所有服务")
    except Exception as e:
        logger.error(f"初始化失败: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务运行出错: {str(e)}") 