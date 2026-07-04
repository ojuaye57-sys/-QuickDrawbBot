"""
QuickDraw Bot - AI Image Generator for Telegram
Deployed on Railway with GitHub integration
"""

import os
import logging
import requests
import time
from io import BytesIO
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HUGGINGFACE_API_KEY = os.environ.get('HUGGINGFACE_API_KEY')
HUGGINGFACE_MODEL = os.environ.get('HUGGINGFACE_MODEL', 'stabilityai/stable-diffusion-2-1')

# Conversation states
WAITING_FOR_PROMPT = 1

# Check for required environment variables
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found in environment variables")
    raise ValueError("BOT_TOKEN is required")

if not HUGGINGFACE_API_KEY:
    logger.warning("HUGGINGFACE_API_KEY not found. Image generation will fail.")

# Global variables for rate limiting
last_request_time = 0
min_interval = 2  # Minimum 2 seconds between requests

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "• 'Abstract art with vibrant colors and flowing shapes'\n\n"
        "⚡ Images take 15-30 seconds to generate."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /about command"""
    about_text = (
        "🤖 *QuickDraw Bot v2.0*\n\n"
        "An AI-powered Telegram bot that generates images from text prompts.\n\n"
        "🔧 *Powered by:*\n"
        "• Python 3.10\n"
        "• python-telegram-bot\n"
        "• Stable Diffusion 2.1\n"
        "• Hugging Face API\n\n"
        "🌐 *Hosted on:*\n"
        "• Railway\n"
        "• GitHub\n\n"
        "Made with ❤️ by @QuickDrawbBot"
    )
    await update.message.reply_text(about_text, parse_mode='Markdown')

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the prompt from /generate command"""
    prompt = update.message.text
    await process_image_generation(update, context, prompt)
    return ConversationHandler.END

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    await update.message.reply_text(
        "❌ *Operation cancelled*\n\n"
        "You can start a new generation with /generate or send a prompt directly.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def quick_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Quick generation from any message"""
    prompt = update.message.text
    await process_image_generation(update, context, prompt)

async def process_image_generation(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str):
    """Core image generation logic"""
    global last_request_time
    
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
        # Check API key
        if not HUGGINGFACE_API_KEY:
            await status_message.edit_text(
                "❌ *Hugging Face API key not configured*\n\n"
                "Please set HUGGINGFACE_API_KEY in environment variables.",
                parse_mode='Markdown'
            )
            return
            
        # Rate limiting
        elapsed = time.time() - last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        last_request_time = time.time()
        
        # Generate image
        image_data = await generate_image(prompt)
        
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
            f"Please try again later.\n\n"
            f"Error: {str(e)[:100]}",
            parse_mode='Markdown'
        )

async def generate_image(prompt: str):
    """Generate an image from text prompt using Hugging Face API"""
    try:
        api_url = f"https://api-inference.huggingface.co/models/{HUGGINGFACE_MODEL}"
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "negative_prompt": "blurry, bad quality, distorted, deformed, low resolution, pixelated, ugly",
                "num_inference_steps": 25,
                "guidance_scale": 7.5
            }
        }
        
        logger.info(f"Generating image for prompt: {prompt[:50]}...")
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            logger.info("Image generated successfully")
            return response.content
        elif response.status_code == 503:
            # Model is loading, wait and retry
            try:
                data = response.json()
                wait_time = data.get("estimated_time", 20) + 5
                logger.info(f"Model loading, waiting {wait_time} seconds...")
                time.sleep(wait_time)
                
                # Retry
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                if response.status_code == 200:
                    logger.info("Image generated after model loading")
                    return response.content
            except:
                pass
            return None
        else:
            logger.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.Timeout:
        logger.error("Request timeout")
        return None
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return None

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def main():
    """Start the bot"""
    logger.info("Starting QuickDraw Bot...")
    
    # Create the Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('about', about_command))
    application.add_handler(CommandHandler('cancel', cancel_command))
    
    # Conversation handler for /generate
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('generate', generate_command)],
        states={
            WAITING_FOR_PROMPT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel_command)],
    )
    application.add_handler(conv_handler)
    
    # Message handler for quick generation
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, quick_generate)
    )
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Bot started! 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
