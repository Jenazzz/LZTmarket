import time
import discord
import json
import requests
import subprocess

from datetime import datetime
from LOLZTEAM import AutoUpdate, Constants, Utils
from LOLZTEAM.API import Market
from LOLZTEAM.Tweaks import DelaySync, Debug, SendAsAsync, CreateJob

#########################################################
# # # # # # # # # # Config loader # # # # # # # # # # # #
with open('config.json') as f:
    config = json.load(f)
# # # # # # # # # # # Config data # # # # # # # # # # # #
discord_webhook_url = config["discord_webhook_url"]
market = Market(token=config["api_token"], language="en")
lzt_market_url = config["market_url"]
#########################################################

# Sync bypass fuck skips
DelaySync(apis=[market])
Debug().enable()

# Создаем множество аккаунтов (чтобы убрать дубликаты)
minecraft_usernames = set()

while True:
    try:
        response = market.category.minecraft.get(
            search_params={'level_hypixel_min': 4},
            order_by=Constants.Market.ItemOrder.newest_upload
        )

        new_minecraft_accounts = []
        new_minecraft_accounts = response.json()
        if not isinstance(new_minecraft_accounts.get('items'), list):
            raise Exception(f"Ошибка при получении списка аккаунтов: ответ сервера не содержит списка аккаунтов. Ответ: {new_minecraft_accounts}")
        print(f"Подключились к маркету, получили список аккаунтов ({len(new_minecraft_accounts['items'])} аккаунтов)")

        new_usernames = [account['minecraft_nickname'] for account in new_minecraft_accounts['items']]
        print("Логины аккаунтов:")
        print(" ".join(new_usernames))

        for account in new_minecraft_accounts['items']:
            username = account['minecraft_nickname']
            Rank = account['minecraft_hypixel_rank']
            LevelHypixel = account['minecraft_hypixel_level']
            item_id = account['item_id']
            if username not in minecraft_usernames:
                print(f"Добавлен новый аккаунт: {username}")

                server_time = datetime.utcfromtimestamp(account["published_date"])

                minutes_ago = (datetime.now() - server_time).total_seconds() / 60 - 180
                
                embed = discord.Embed(title="Minecraft account", description=f"Price: ```{account['price']} rubles```\n{output_str}", color=0x00ff00)
                embed.add_field(name="Name", value=f"```{username}```", inline=True)
                if LevelHypixel not in (0, 1):
                    embed.add_field(name="Level", value=f"```{LevelHypixel}```", inline=True)
                if Rank:
                    embed.add_field(name="Rank", value=f"```{Rank}```", inline=True)
                    
                embed.add_field(name="Posted", value=f"**{minutes_ago:.1f} минут назад**", inline=False)
                embed.add_field(name="", value=f"**{lzt_market_url}/{item_id}/**", inline=False)

                try:
                    if LevelHypixel > 1:
                        response = requests.post(discord_webhook_url, json={"embeds": [embed.to_dict()]})
                        if response.status_code != 200:
                            print(f"Ошибка при отправке сообщения в Discord: код ошибки {response.status_code}")
                except Exception as e:
                    print(f"Ошибка при отправке сообщения в Discord: {e}")

                minecraft_usernames.add(username)
    except Exception as e:
        print(f"Ошибка: {e}")

    time.sleep(30)
