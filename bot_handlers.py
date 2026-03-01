import discord
from discord.ext import commands
import datetime
import asyncio
import psutil
from deepseek_client import DeepSeekClient
from bilibili_service import BilibiliService
from utils import UserDataManager, EmbedHelper, MessageHelper, MentionHelper
from config import Config

class BotHandlers:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deepseek_client = DeepSeekClient()
        self.bilibili_service = BilibiliService()
        self.data_manager = UserDataManager()
        self.embed_helper = EmbedHelper()
        self.message_helper = MessageHelper()
    
    async def handle_message(self, message: discord.Message):
        # Ignore the robot's own messages 
        # 忽略机器人自己的消息
        if message.author == self.bot.user:
            return
        
        # Update the user's activity time 
        # 更新用户活动时间
        self.data_manager.update_user_activity(message.author.id)
        
        # Regularly clean up expired data 
        # 定期清理过期数据
        if self.data_manager.should_cleanup():
            self.data_manager.cleanup_old_data()
        
        # Check if you have @ed the robot 
        # 检查是否@了机器人
        if self.bot.user.mentioned_in(message):
            await self._handle_ai_message(message)
            return
        
        # If it's not @robot, handle other commands normally 
        # 如果不是@机器人，正常处理其他命令
        await self.bot.process_commands(message)
    
    async def _handle_ai_message(self, message: discord.Message):
        """处理AI聊天消息，支持提及功能
        "Handle AI chat messages and support mention function"""
        # Remove the @ mention to get plain text content
        # 移除@提及，获取纯文本内容
        clean_content = message.clean_content.replace(f'@{self.bot.user.name}', '').strip()
        
        # 如果只有@没有内容，发送帮助信息
        if not clean_content:
            help_msg = (
                "Message"
            )
            await message.reply(help_msg)
            return
        
        # Obtain the user information mentioned in the message (excluding the robot itself)
        # 获取消息中提及的用户信息（排除机器人自己）
        mentioned_users_info = await self._get_mentioned_users_info(message)
        
        async with message.channel.typing():
            user_id = message.author.id
            
            # Get the conversation history
            # 获取对话历史
            history = self.data_manager.conversation_histories.get(user_id, [])
            
            # Call the DeepSeek API to obtain responses and the users that need to be mentioned
            # 调用DeepSeek API，获取回复和需要提及的用户
            response, mentions_to_send = await self.deepseek_client.get_response_with_mentions(
                clean_content, user_id, history, mentioned_users_info
            )
            
            # update conversation history
            # 更新对话历史
            history.append({"role": "user", "content": clean_content})
            history.append({"role": "assistant", "content": response})
            
            # limit history length (last 10 rounds of conversation)
            # 限制历史长度（最近10轮对话）
            if len(history) > Config.MAX_HISTORY_LENGTH:
                history = history[-Config.MAX_HISTORY_LENGTH:]
            
            self.data_manager.conversation_histories[user_id] = history
            
            # send the reply, including actual mentions
            # 发送回复，包含实际提及
            await self._send_response_with_mentions(message, response, mentions_to_send)
    
    async def _send_response_with_mentions(self, original_message: discord.Message, response: str, user_ids_to_mention: list):
        """发送回复并实际提及用户"""
        # Use MessageHelper to send the message, passing the mention list
        # 使用 MessageHelper 发送消息，传递提及列表
        await self.message_helper.send_long_message(
            original_message.channel, 
            response, 
            original_message,
            mentions=user_ids_to_mention 
        )
    
    async def _get_mentioned_users_info(self, message: discord.Message) -> list:
        """获取消息中提及的用户信息（排除机器人自己）"""
        mentioned_users = []
        
        for user in message.mentions:
            if user.id != self.bot.user.id and not user.bot:
                mentioned_users.append({
                    'id': user.id,
                    'username': user.name,
                    'display_name': user.display_name
                })
        
        return mentioned_users
    
    async def handle_mention_test_command(self, ctx, target_user: discord.Member = None):
        """测试提及功能"""
        if target_user:
            await MentionHelper.test_mention(ctx.channel, target_user)
        else:
            embed = MentionHelper.create_mention_guide_embed()
            await ctx.send(embed=embed)
    
    async def handle_mention_demo_command(self, ctx):
        """演示提及功能的工作方式"""
        demo_text = (
            "Message"
        )
        await ctx.send(demo_text)
    
    async def handle_search_command(self, ctx, keyword: str):
        """处理搜索命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        await ctx.send(f"Search「{keyword}」...")
        videos = await self.bilibili_service.search_videos(keyword, page=1)
        if not videos:
            await ctx.send("❌ Not found")
            return

        self.data_manager.user_search_results[ctx.author.id] = {
            "keyword": keyword,
            "results": videos,
            "page": 1
        }

        header = f"Result 第1页（共{len(videos)}条）** - 关键词：{keyword}"
        await ctx.send(header)
        
        for i, video in enumerate(videos[:Config.SEARCH_RESULTS_PER_PAGE], 1):
            embed = self.embed_helper.create_video_embed(video, i)
            await ctx.send(embed=embed)

        await ctx.send("输入 `choose [编号]` 选择视频，或输入 `next` 查看下一页。")
    
    async def handle_next_command(self, ctx):
        """处理下一页命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        user_id = ctx.author.id
        if user_id not in self.data_manager.user_search_results:
            await ctx.send("❌ 请先使用 `searchb [关键词]`。")
            return

        data = self.data_manager.user_search_results[user_id]
        keyword = data["keyword"]
        page = data["page"] + 1

        videos = await self.bilibili_service.search_videos(keyword, page=page)
        if not videos:
            await ctx.send("🚫 没有更多结果。")
            return

        data["results"] = videos
        data["page"] = page

        header = f"📺 **搜索结果 第{page}页（共{len(videos)}条）** - 关键词：{keyword}"
        await ctx.send(header)
        
        for i, video in enumerate(videos[:Config.SEARCH_RESULTS_PER_PAGE], 1):
            embed = self.embed_helper.create_video_embed(video, i)
            await ctx.send(embed=embed)

        await ctx.send("输入 `choose [编号]` 选择视频，输入 `next` 查看下一页，或输入 `prev` 返回上一页。")
    
    async def handle_prev_command(self, ctx):
        """处理上一页命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        user_id = ctx.author.id
        if user_id not in self.data_manager.user_search_results:
            await ctx.send("❌ 请先使用 `searchb [关键词]`。")
            return

        data = self.data_manager.user_search_results[user_id]
        keyword = data["keyword"]
        page = max(1, data["page"] - 1)

        if page == data["page"]:
            await ctx.send("🚫 已经是第一页了。")
            return

        videos = await self.bilibili_service.search_videos(keyword, page=page)
        if not videos:
            await ctx.send("❌ 没有上一页结果。")
            return

        data["results"] = videos
        data["page"] = page

        header = f"📺 **搜索结果 第{page}页（共{len(videos)}条）** - 关键词：{keyword}"
        await ctx.send(header)
        
        for i, video in enumerate(videos[:Config.SEARCH_RESULTS_PER_PAGE], 1):
            embed = self.embed_helper.create_video_embed(video, i)
            await ctx.send(embed=embed)

        await ctx.send("输入 `choose [编号]` 选择视频，输入 `next` 查看下一页, 或输入 `prev` 返回上一页。")
    
    async def handle_choose_command(self, ctx, index: int):
        """处理选择视频命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        user_id = ctx.author.id
        if user_id not in self.data_manager.user_search_results:
            await ctx.send("❌ 请先使用 `searchb [搜索内容]`。")
            return

        results = self.data_manager.user_search_results[user_id]["results"]
        if index < 1 or index > len(results):
            await ctx.send("⚠️ 无效编号，请输入 1~20。")
            return

        video_data = results[index - 1]
        await self._send_video(ctx.channel, video_data["title"], video_data["url"])
    
    async def _send_video(self, channel, title: str, url: str):
        """发送视频到频道"""
        try:
            await channel.send(f"🎬 正在下载：**{title}**\n{url}")
            file_path = await self.bilibili_service.download_video(url)

            size_mb = self.bilibili_service.get_video_size(file_path)
            if size_mb > Config.MAX_VIDEO_SIZE_MB:
                await channel.send(f"⚠️ 视频太大（{size_mb:.2f} MB），Discord 无法上传。")
            else:
                embed = discord.Embed(
                    title=title,
                    description=f"[点击在B站观看]({url})",
                    color=0x00aeff,
                    timestamp=datetime.datetime.now()
                )
                await channel.send(embed=embed)
                await channel.send(file=discord.File(file_path))
                await channel.send("✅ 视频加载完成！")

        except Exception as e:
            await channel.send(f"❌ 视频加载失败：{e}，请点击链接观看")
        finally:
            self.bilibili_service.cleanup_temp_file(file_path)
    
    async def handle_clear_command(self, ctx):
        """处理清除历史命令"""
        user_id = ctx.author.id
        if user_id in self.data_manager.conversation_histories:
            del self.data_manager.conversation_histories[user_id]
            await ctx.send("✅ 对话历史已清除")
        else:
            await ctx.send("ℹ️ 没有找到对话历史")
    
    async def handle_status_command(self, ctx):
        """处理状态查询命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        # Get CPU usage
        # 获取内存使用情况
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        # Data statistics
        # 统计数据
        active_users = len(self.data_manager.user_last_activity)
        active_conversations = len(self.data_manager.conversation_histories)
        active_searches = len(self.data_manager.user_search_results)
        
        embed = self.embed_helper.create_status_embed(
            active_users, active_conversations, active_searches, memory_usage
        )
        
        await ctx.send(embed=embed)
    
    async def handle_command_command(self, ctx):
        """处理帮助命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        embed = self.embed_helper.create_help_embed()
        await ctx.send(embed=embed)
    
    async def handle_shutdown_command(self, ctx):
        """处理关闭命令"""
        self.data_manager.update_user_activity(ctx.author.id)
        
        if ctx.author.id not in Config.ALLOWED_USERS:
            await ctx.send("❌ 你没有权限关闭机器人。")
            return

        await ctx.send("🛑 机器人即将关闭……")
        await self.bot.close()
    
    async def handle_ready_event(self):
        """处理机器人就绪事件"""
        print(f"✅ 已登录为 {self.bot.user}")
        print(f"🆔 机器人ID: {self.bot.user.id}")
        print(f"👥 已加入 {len(self.bot.guilds)} 个服务器")
        
        channel = self.bot.get_channel(Config.CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="Bot active",
                description="Thanks for using the bot! Here are some new features and instructions to get you started:",
                color=0xFF69B4,
                timestamp=datetime.datetime.now()
            )
            
            embed.add_field(
                name="✨ 新功能",
                value="• AI智能聊天（@我即可）\n• B站视频搜索\n• 视频下载功能\n• 智能提及朋友",
                inline=False
            )
            
            embed.add_field(
                name="📝 使用说明",
                value="使用 `command` 查看完整命令列表\n使用 `mention_demo` 查看提及功能演示",
                inline=False
            )
            
            embed.set_footer(text="祝您拥有美好的一天！")
            
            await channel.send(embed=embed)
    
    async def handle_command_error(self, ctx, error):
        """处理命令错误"""
        if isinstance(error, commands.CommandNotFound):
            # ignore unknown command errors since our command prefix is empty
            # 忽略未知命令错误，因为我们的命令前缀是空字符串
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ 命令参数不完整，请检查使用方式。")
        else:
            print(f"命令错误: {error}")
            await ctx.send("❌ 执行命令时出现错误。")