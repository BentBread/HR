import discord
import os
from discord.ext import commands
from flask import Flask, request, jsonify

TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # Ensure you have set this environment variable
CHANNEL_ID = 1123403508239052891  # replace with your channel ID

# Initialize the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Flask app to listen for purchase events
app = Flask(__name__)

@app.route('/notify_purchase', methods=['POST'])
def notify_purchase():
    data = request.json
    item_name = data['item_name']
    amount = data['amount']
    price = data['price']
    buyer = data['buyer']
    seller = data['seller']
    timestamp = data['timestamp']
    instant_text = data.get('instant_text', '')

    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        embed = discord.Embed(title="New Purchase Notification", color=0x00ff00)
        embed.add_field(name="Item", value=item_name, inline=False)
        embed.add_field(name="Amount", value=amount, inline=False)
        embed.add_field(name="Price", value=price, inline=False)
        embed.add_field(name="Buyer", value=buyer, inline=False)
        embed.add_field(name="Seller", value=seller, inline=False)
        embed.add_field(name="Timestamp", value=timestamp, inline=False)
        if instant_text:
            embed.add_field(name="Instant Text", value=instant_text, inline=False)

        bot.loop.create_task(channel.send(embed=embed))
    return jsonify({"status": "success"}), 200

# Run the Flask app in a separate thread
def run_flask():
    app.run(port=5001)

# Start the bot
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    import threading
    threading.Thread(target=run_flask).start()

bot.run(TOKEN)
