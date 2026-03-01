import os
import re
from openai import AsyncOpenAI
from config import Config

class DeepSeekClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
    
    async def get_response(self, message: str, user_id: int, conversation_history: list = None, mentioned_users: list = None) -> str:
        
        messages = []
        
       #build system prompt with mention info if available
        system_prompt = self._build_hutao_system_prompt(mentioned_users)
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the user's current message
        messages.append({"role": "user", "content": message})
        
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                max_tokens=8192,
                temperature=0.8,  # Increase temperature for more creativity in responses
                stream=False
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Wrong ({str(e)})"
    
    def _build_hutao_system_prompt(self, mentioned_users: list = None) -> str:
        """build system prompt for hutao with mention info"""
        
        base_prompt = """Custom requirements"""
        
        # 如果有被提及的用户，添加到系统提示中
        if mentioned_users and len(mentioned_users) > 0:
            mention_prompt = "\n\n## 提及功能说明：\n"
            mention_prompt += "自定义需求"
            mention_prompt += f"\n当前被提及的用户有：{', '.join(mentioned_users)}"
            
            base_prompt += mention_prompt
        
        return base_prompt
    
    async def get_response_with_mentions(self, message: str, user_id: int, conversation_history: list = None, mentioned_users_info: list = None) -> tuple:

        # Get the list of mentioned usernames for the system prompt
        mentioned_usernames = [user['username'] for user in mentioned_users_info] if mentioned_users_info else []
        
        # AI response with system prompt that includes mentioned usernames
        response = await self.get_response(message, user_id, conversation_history, mentioned_usernames)
        
        # Check if the response contains mentions of any of the mentioned users
        mentions_to_send = self._find_mentions_in_response(response, mentioned_users_info)
        
        return response, mentions_to_send
    
    def _find_mentions_in_response(self, response: str, mentioned_users_info: list) -> list:

        if not mentioned_users_info:
            return []
        
        mentions_found = []
        for user_info in mentioned_users_info:
            username = user_info['username']
            display_name = user_info.get('display_name', username)
            
            # Check if either the username or display name is mentioned in the response (case-insensitive)
            if (username.lower() in response.lower() or 
                display_name.lower() in response.lower()):
                mentions_found.append(user_info['id'])
        
        return mentions_found
    
    async def get_video_search_suggestions(self, user_request: str) -> str:
        """获取视频搜索建议"""
        prompt = f"""
        想要搜索视频，需求是：{user_request}
        
        Other requirements
        """
        
        return await self.get_response(prompt, 0)