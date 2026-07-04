"""
QuickDraw Bot - AI Image Generator for Telegram
Deployed on Railway with GitHub integration
"""

import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from config import Config
from image_generator import ImageGenerator

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PROMPT = 1

# Initialize image generator
image_gen = ImageGenerator()

class QuickDrawBot:
    """Main bot class with all handlers"""
    
    def __init__(self):
        self.token = Config.BOT_TOKEN
        if not self.token:
            logger.error("BOT_TOKEN not found in environment variables")
            sys.exit(1)
        
        self.application = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        self.application = ApplicationBuilder().token(self.token).build()
        
        # Command handlers
        self.application.add_handler(CommandHandler('start', self.start_command))
        self.application.add_handler(CommandHandler('help', self.help_command))
        self.application.add_handler(CommandHandler('about', self.about_command))
        self.application.add_handler(CommandHandler('generate', self.generate_command))
        self.application.add_handler(CommandHandler('cancel', self.cancel_command))
        
        # Conversation handler for image generation
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('generate', self.generate_command)],
            states={
                WAITING_FOR_PROMPT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_prompt)
                ],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_command)],
        )
        self.application.add_handler(conv_handler)
        
        # Message handler for quick generation
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.quick_generate)
        )
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = (
            "🎨 *Welcome to QuickDraw Bot!*\n\n"
            "I'm an AI-powered image generator that creates stunning images from text descriptions.\n\n"
            "✨ *How to use:*\n"
            "• Send any text description\n"
            "• Use /generate for guided generation\n"
            "• Use /help for more commands\n\n"
            "💡 *Try it now:*\n"
            "Send me something like:\n"
            "`A cyberpunk city at night with neon lights`\n\n"
            "🚀 *Powered by Stable Diffusion AI*"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🆘 *QuickDraw Bot Help*\n\n"
            "📝 *Commands:*\n"
            "/start - Welcome message\n"
            "/help - Show this help\n"
            "/about - About the bot\n"
            "/generate - Start guided generation\n"
            "/cancel - Cancel generation\n\n"
            "🎯 *Tips for better images:*\n"
            "• Be descriptive and specific\n"
            "• Include style (e.g., watercolor, realistic, anime)\n"
            "• Add mood or lighting details\n"
            "• Mention colors and composition\n\n"
            "📸 *Examples:*\n"
            "• 'A majestic dragon flying over mountains at sunset'\n"
            "• 'A cozy cabin in a snowy forest, warm lighting'\n"
            "• 'Abstract art with vibrant colors and flowing shapes'\n"
            "• 'Portrait of a robot, cyberpunk style, neon blue'\n\n"
            "⚡ Images take 15-30 seconds to generate."
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_text = (
            "🤖 *QuickDraw Bot v2.0*\n\n"
            "An AI-powered Telegram bot that generates images from text prompts.\n\n"
            "🔧 *Powered by:*\n"
            "• Python 3.11\n"
            "• python-telegram-bot\n"
            "• Stable Diffusion 2.1\n"
            "• Hugging Face API\n\n"
            "🌐 *Hosted on:*\n"
            "• Railway\n"
            "• GitHub\n\n"
            "📚 *Open Source:*\n"
            "• MIT License\n"
            "• GitHub: [Your Repo Link]\n\n"
            "Made with ❤️ by @QuickDrawbBot"
        )
        await update.message.reply_text(about_text, parse_mode='Markdown')
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start guided image generation process"""
        await update.message.reply_text(
            "🎨 *Let's create something amazing!*\n\n"
            "Please describe the image you want to generate in detail.\n\n"
            "💡 *Example prompts:*\n"
            "• 'A beautiful landscape with mountains and a lake'\n"
            "• 'A futuristic city with flying cars'\n"
            "• 'A cat wearing a wizard hat'\n\n"
            "Send /cancel to stop the process.",
            parse_mode='Markdown'
        )
        return WAITING_FOR_PROMPT
    
    async def handle_prompt(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the prompt from /generate command"""
        prompt = update.message.text
        await self.process_image_generation(update, context, prompt)
        return ConversationHandler.END
    
    async def quick_generate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick generation from any message"""
        prompt = update.message.text
        await self.process_image_generation(update, context, prompt)
    
    async def process_image_generation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
        """Core image generation logic"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "User"
        
        # Truncate prompt for display
        display_prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        
        # Send processing message
        status_message = await update.message.reply_text(
            f"🔄 *Generating image...*\n\n"
            f"📝 *Prompt:* {display_prompt}\n\n"
            f"⏳ This may take 15-30 seconds...",
            parse_mode='Markdown'
        )
        
        try:
            # Generate image
            image_data = await image_gen.generate(prompt)
            
            if image_data:
                # Send the generated image
                await update.message.reply_photo(
                    photo=image_data,
                    caption=(
                        f"🎨 *Here's your image!*\n\n"
                        f"📝 *Prompt:* {prompt}\n"
                        f"👤 *Requested by:* @{username}\n"
                        f"⚡ *Model:* Stable Diffusion 2.1\n\n"
                        f"🔄 Generate more at @QuickDrawbBot"
                    ),
                    parse_mode='Markdown'
                )
                await status_message.delete()
            else:
                await status_message.edit_text(
                    "❌ *Failed to generate image*\n\n"
                    "The AI service might be temporarily unavailable.\n"
                    "Please try again in a few moments.\n\n"
                    "💡 *Tips:*\n"
                    "• Try a simpler prompt\n"
                    "• Check your internet connection\n"
                    "• Try again in a few minutes",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            await status_message.edit_text(
                f"❌ *An error occurred*\n\n"
                f"Error: {str(e)[:100]}\n\n"
                f"Please try again later or contact support.",
                parse_mode='Markdown'
            )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel current operation"""
        await update.message.reply_text(
            "❌ *Operation cancelled*\n\n"
            "You can start a new generation with /generate or send a prompt directly.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Global error handler"""
        logger.error(f"Update {update} caused error {context.error}")
        try:
            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "⚠️ *Something went wrong*\n\n"
                    "Please try again or use /help for assistance.",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")
    
    def run(self):
        """Start the bot"""
        if Config.USE_WEBHOOK:
            # Webhook mode (recommended for Railway)
            webhook_url = Config.WEBHOOK_URL
            if not webhook_url:
                logger.warning("WEBHOOK_URL not set, falling back to polling")
                self.application.run_polling()
            else:
                logger.info(f"Starting bot with webhook: {webhook_url}")
                self.application.run_webhook(
                    listen="0.0.0.0",
                    port=Config.PORT,
                    webhook_url=f"{webhook_url}/{self.token}"
                )
        else:
            # Polling mode (simpler but less efficient)
            logger.info("Starting bot with polling")
            self.application.run_polling()

def main():
    """Main entry point"""
    bot = QuickDrawBot()
    bot.run()

if __name__ == "__main__":
    main()
