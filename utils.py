import datetime
import discord
from discord import Embed

class UserDataManager:
    """用户数据管理器"""
    
    def __init__(self):
        self.user_search_results = {}
        self.conversation_histories = {}
        self.user_last_activity = {}
    
    def update_user_activity(self, user_id: int):
        """Update user activity time
        更新用户活动时间"""
        self.user_last_activity[user_id] = datetime.datetime.now()
    
    def cleanup_old_data(self):
        """cleanup old user data
        清理超过1小时不活动的用户数据"""
        current_time = datetime.datetime.now()
        expired_users = []
        
        for user_id, last_time in self.user_last_activity.items():
            if (current_time - last_time).total_seconds() > 3600:  # 1小时
                expired_users.append(user_id)
        
        for user_id in expired_users:
            if user_id in self.user_search_results:
                del self.user_search_results[user_id]
            if user_id in self.conversation_histories:
                del self.conversation_histories[user_id]
            if user_id in self.user_last_activity:
                del self.user_last_activity[user_id]
    
    def should_cleanup(self) -> bool:
        """Check if we should cleanup data (to prevent memory bloat)
        检查是否需要清理数据（防止内存占用过多）"""
        return len(self.user_last_activity) > 100

class EmbedHelper:
    
    
    @staticmethod
    def create_video_embed(video_data: dict, index: int = None) -> Embed:
        """Video data should contain: title, author, play_count, duration, pic, url (optional) --- IGNORE ---
        创建视频信息Embed"""
        title = video_data["title"]
        if len(title) > 100:
            title = title[:100] + "..."
        
        if index is not None:
            title = f"{index}. {title}"
        
        embed = Embed(
            title=title,
            description=f"👤 UP主：{video_data['author']}\n▶️ 播放：{video_data['play_count']} | ⏱️ 时长：{video_data['duration']}",
            url=video_data.get("url", None),
            color=0x00afff
        )
        embed.set_thumbnail(url=video_data["pic"])
        return embed
    
    @staticmethod
    def create_help_embed() -> Embed:
        """Help message
        信息Embed"""
        embed = Embed(
            title="",
            description="",
            color=0xFF69B4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="",
            value="",
            inline=False
        )
        
        embed.set_footer(text="")
        return embed
    
    @staticmethod
    def create_status_embed(active_users: int, active_conversations: int, active_searches: int, memory_usage: float) -> Embed:
        """Create status info Embed
        创建状态信息Embed"""
        embed = Embed(
            title="",
            color=0xFF69B4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="", value="", inline=False)
        
        return embed

class MessageHelper:
    
    @staticmethod
    async def send_long_message(channel, content: str, reply_to=None, mentions: list = None):
        
        # Set allowed mentions to enable user mentions
        # 设置允许提及
        allowed_mentions = discord.AllowedMentions(users=True)
        
        # Set allowed mentions to enable user mentions
        # 构建提及字符串
        mention_string = ""
        if mentions:
            mention_string = " ".join([f"<@{user_id}>" for user_id in mentions])
            full_content = f"{mention_string}\n\n{content}"
        else:
            full_content = content
        
        if len(full_content) > 2000:
            if mention_string:
                max_first_chunk_length = 2000 - len(mention_string) - 2
                
                if len(content) <= max_first_chunk_length:
                    if reply_to:
                        await reply_to.reply(full_content, allowed_mentions=allowed_mentions)
                    else:
                        await channel.send(full_content, allowed_mentions=allowed_mentions)
                else:
                    first_chunk_content = content[:max_first_chunk_length]
                    first_chunk = f"{mention_string}\n\n{first_chunk_content}"
                    
                    if reply_to:
                        await reply_to.reply(first_chunk, allowed_mentions=allowed_mentions)
                    else:
                        await channel.send(first_chunk, allowed_mentions=allowed_mentions)
                    
                    remaining_content = content[max_first_chunk_length:]
                    chunks = [remaining_content[i:i+2000] for i in range(0, len(remaining_content), 2000)]
                    for chunk in chunks:
                        await channel.send(chunk)
            else:
                chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
                for i, chunk in enumerate(chunks):
                    if i == 0 and reply_to:
                        await reply_to.reply(chunk, allowed_mentions=allowed_mentions)
                    else:
                        await channel.send(chunk, allowed_mentions=allowed_mentions)
        else:
            if reply_to:
                await reply_to.reply(full_content, allowed_mentions=allowed_mentions)
            else:
                await channel.send(full_content, allowed_mentions=allowed_mentions)

class MentionHelper:
    """提及功能助手"""
    
    @staticmethod
    def create_mention_guide_embed() -> Embed:
        """创建提及功能说明"""
        embed = Embed(
            title="Message",
            description="Message",
            color=0xFF69B4,
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="Message",
            value="Message",
            inline=False
        )
        
        return embed
    
    @staticmethod
    async def test_mention(channel, target_user: discord.Member):
        """Test"""
        if target_user.bot:
            await channel.send("Wrong")
            return
        
        test_message = f"Yes"
        # Use Discord format mention
        # 使用 Discord 格式的提及
        mention_string = f"<@{target_user.id}>"
        full_message = f"{mention_string} {test_message}"
        
        await channel.send(full_message, allowed_mentions=discord.AllowedMentions(users=True))