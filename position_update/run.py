#!/usr/bin/env python
# -*- coding: utf-8 -*-

from position_update.config import logger
from position_update.tasks import update_all_character_positions

def main():
    """主函数：运行脚本时执行一次位置更新"""
    try:
        # 执行一次位置更新
        logger.info("正在执行角色位置初始更新...")
        success = update_all_character_positions()
        
        if success:
            logger.info("初始位置更新完成，Celery将处理后续定时更新")
        else:
            logger.warning("初始位置更新未能完全成功")
            
        logger.info("提示：请确保已启动 Celery Worker 和 Beat 服务")
        logger.info("启动 Celery Worker: celery -A position_update.tasks worker --loglevel=info")
        logger.info("启动 Celery Beat: celery -A position_update.tasks beat --loglevel=info")
        logger.info("或者一起启动: celery -A position_update.tasks worker -B --loglevel=info")
    except Exception as e:
        logger.error(f"初始位置更新失败: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务运行出错: {str(e)}") 