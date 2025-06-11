#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import asyncio
import tempfile
from typing import List, Optional
from pathlib import Path

import qbittorrentapi
from telegram import Update, Document
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class QBTelegramBot:
    def __init__(self):
        # 从环境变量获取配置
        self.bot_token = os.getenv('TG_BOT_TOKEN')
        self.authorized_users = self._parse_authorized_users()
        
        # qBittorrent 配置
        self.qb_host = os.getenv('QB_HOST', 'localhost')
        self.qb_port = int(os.getenv('QB_PORT', '8080'))
        self.qb_username = os.getenv('QB_USERNAME', 'admin')
        self.qb_password = os.getenv('QB_PASSWORD', 'adminadmin')
        
        # 验证必需的配置
        if not self.bot_token:
            raise ValueError("TG_BOT_TOKEN is required")
        
        # 初始化 qBittorrent 客户端
        self.qb_client = None
        self._connect_qbittorrent()
        
        logger.info("QBTelegramBot initialized successfully")
    
    def _parse_authorized_users(self) -> Optional[List[int]]:
        """解析授权用户列表"""
        users_str = os.getenv('TG_AUTHORIZED_USERS')
        if not users_str:
            return None
        
        try:
            return [int(user_id.strip()) for user_id in users_str.split(',') if user_id.strip()]
        except ValueError as e:
            logger.error(f"Invalid authorized users format: {e}")
            return None
    
    def _connect_qbittorrent(self):
        """连接到 qBittorrent"""
        try:
            self.qb_client = qbittorrentapi.Client(
                host=self.qb_host,
                port=self.qb_port,
                username=self.qb_username,
                password=self.qb_password
            )
            self.qb_client.auth_log_in()
            
            # 创建标签
            try:
                self.qb_client.torrents_create_tags(tags="tg_qb_bot")
                logger.info("Created tag 'tg_qb_bot'")
            except Exception as e:
                logger.info(f"Tag 'tg_qb_bot' may already exist or creation failed: {e}")
            
            logger.info(f"Connected to qBittorrent at {self.qb_host}:{self.qb_port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to qBittorrent: {e}")
            raise
    
    def _is_authorized(self, user_id: int) -> bool:
        """检查用户是否有权限"""
        if self.authorized_users is None:
            return True  # 如果没有设置授权用户，允许所有用户
        return user_id in self.authorized_users
    
    def _is_magnet_link(self, text: str) -> bool:
        """检查是否为磁力链接"""
        magnet_pattern = r'magnet:\?xt=urn:btih:[a-fA-F0-9]{32,40}'
        return bool(re.search(magnet_pattern, text))
    
    def _extract_magnet_links(self, text: str) -> List[str]:
        """提取文本中的所有磁力链接"""
        magnet_pattern = r'magnet:\?xt=urn:btih:[a-fA-F0-9]{32,40}[^\s]*'
        return re.findall(magnet_pattern, text)
    
    async def _add_magnet_to_qb(self, magnet_link: str) -> bool:
        """添加磁力链接到 qBittorrent"""
        try:
            self.qb_client.torrents_add(
                urls=magnet_link,
                tags="tg_qb_bot"
            )
            logger.info(f"Successfully added magnet link to qBittorrent")
            return True
        except Exception as e:
            logger.error(f"Failed to add magnet link: {e}")
            return False
    
    async def _add_torrent_file_to_qb(self, file_path: str) -> bool:
        """添加种子文件到 qBittorrent"""
        try:
            with open(file_path, 'rb') as torrent_file:
                self.qb_client.torrents_add(
                    torrent_files=torrent_file,
                    tags="tg_qb_bot"
                )
            logger.info(f"Successfully added torrent file to qBittorrent")
            return True
        except Exception as e:
            logger.error(f"Failed to add torrent file: {e}")
            return False
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人")
            return
        
        welcome_text = """
🤖 欢迎使用 qBittorrent Telegram Bot！

📋 支持的功能：
• 发送磁力链接自动添加下载
• 发送 .torrent 文件自动添加下载
• 所有下载都会自动添加标签 "tg_qb_bot"

💡 使用方法：
• 直接发送包含磁力链接的消息
• 直接发送 .torrent 文件

🔧 命令列表：
/start - 显示帮助信息
/status - 查看机器人状态
        """
        
        await update.message.reply_text(welcome_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人")
            return
        
        try:
            # 获取 qBittorrent 状态
            transfer_info = self.qb_client.transfer_info()
            torrents = self.qb_client.torrents_info(tag="tg_qb_bot")
            
            status_text = f"""
📊 qBittorrent 状态

🌐 连接状态: ✅ 已连接
📡 服务器: {self.qb_host}:{self.qb_port}

📈 传输信息:
• 下载速度: {transfer_info.dl_info_speed / 1024 / 1024:.2f} MB/s
• 上传速度: {transfer_info.up_info_speed / 1024 / 1024:.2f} MB/s

🏷️ "tg_qb_bot" 标签:
• 种子数量: {len(torrents)}
            """
            
            await update.message.reply_text(status_text)
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文本消息（磁力链接）"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人")
            return
        
        message_text = update.message.text
        
        # 检查是否包含磁力链接
        if self._is_magnet_link(message_text):
            magnet_links = self._extract_magnet_links(message_text)
            
            await update.message.reply_text(f"🔍 发现 {len(magnet_links)} 个磁力链接，正在添加...")
            
            success_count = 0
            for magnet_link in magnet_links:
                if await self._add_magnet_to_qb(magnet_link):
                    success_count += 1
            
            if success_count == len(magnet_links):
                await update.message.reply_text(f"✅ 成功添加 {success_count} 个磁力链接到下载队列")
            else:
                await update.message.reply_text(f"⚠️ 添加完成：成功 {success_count}/{len(magnet_links)}")
        else:
            await update.message.reply_text("❓ 没有发现磁力链接，请检查消息内容")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理文档（种子文件）"""
        user_id = update.effective_user.id
        
        if not self._is_authorized(user_id):
            await update.message.reply_text("❌ 您没有权限使用此机器人")
            return
        
        document: Document = update.message.document
        
        # 检查文件类型
        if not document.file_name.lower().endswith('.torrent'):
            await update.message.reply_text("❌ 只支持 .torrent 文件")
            return
        
        try:
            await update.message.reply_text("📥 正在下载种子文件...")
            
            # 下载文件到临时目录
            file = await context.bot.get_file(document.file_id)
            
            with tempfile.NamedTemporaryFile(suffix='.torrent', delete=False) as temp_file:
                await file.download_to_drive(temp_file.name)
                temp_file_path = temp_file.name
            
            # 添加到 qBittorrent
            if await self._add_torrent_file_to_qb(temp_file_path):
                await update.message.reply_text(f"✅ 成功添加种子文件: {document.file_name}")
            else:
                await update.message.reply_text(f"❌ 添加种子文件失败: {document.file_name}")
            
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error handling torrent file: {e}")
            await update.message.reply_text(f"❌ 处理种子文件失败: {str(e)}")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """运行机器人"""
        try:
            # 创建应用
            application = Application.builder().token(self.bot_token).build()
            
            # 添加处理程序
            application.add_handler(CommandHandler("start", self.start_command))
            application.add_handler(CommandHandler("status", self.status_command))
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            application.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
            
            # 添加错误处理
            application.add_error_handler(self.error_handler)
            
            logger.info("Starting Telegram bot...")
            
            # 运行机器人
            application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

def main():
    """主函数"""
    try:
        bot = QBTelegramBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
