import discord
from discord.ext import commands
from config import Config
from bot_handlers import BotHandlers

class DiscordBot:
    def __init__(self):
        self.config = Config()
        self.bot = commands.Bot(
            command_prefix="", 
            intents=self._setup_intents()
        )
        self.handlers = BotHandlers(self.bot)
        self._setup_events()
        self._setup_commands()
        
    def _setup_intents(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.message_content = True
        return intents
    
    def _setup_events(self):
        @self.bot.event
        async def on_ready():
            await self.handlers.handle_ready_event()
        
        @self.bot.event
        async def on_message(message):
            await self.handlers.handle_message(message)
        
        @self.bot.event
        async def on_command_error(ctx, error):
            await self.handlers.handle_command_error(ctx, error)
    
    def _setup_commands(self):
        @self.bot.command()
        async def searchb(ctx, *, keyword: str):
            await self.handlers.handle_search_command(ctx, keyword)
        
        @self.bot.command()
        async def next(ctx):
            await self.handlers.handle_next_command(ctx)
        
        @self.bot.command()
        async def prev(ctx):
            await self.handlers.handle_prev_command(ctx)
        
        @self.bot.command()
        async def choose(ctx, index: int):
            await self.handlers.handle_choose_command(ctx, index)
        
        @self.bot.command()
        async def clear(ctx):
            await self.handlers.handle_clear_command(ctx)
        
        @self.bot.command()
        async def status(ctx):
            await self.handlers.handle_status_command(ctx)
        
        @self.bot.command()
        async def command(ctx):
            await self.handlers.handle_command_command(ctx)
        
        @self.bot.command()
        async def mention_test(ctx, target_user: discord.Member = None):
            await self.handlers.handle_mention_test_command(ctx, target_user)
    
        @self.bot.command()
        async def mention_demo(ctx):
            await self.handlers.handle_mention_demo_command(ctx)
        
        @self.bot.command()
        async def shutdown(ctx):
            await self.handlers.handle_shutdown_command(ctx)
    
    def run(self):
        """boost bot"""
        print("Bot boosting...")
        try:
            self.bot.run(self.config.DISCORD_TOKEN)
        except Exception as e:
            print(f"Bot lost: {e}")

if __name__ == "__main__":
    bot = DiscordBot()
    bot.run()