import disnake
from disnake.ext import commands
from config import settings
import sqlite3
import datetime

bot = commands.Bot(command_prefix=settings['PREFIX'], intents=disnake.Intents.all(), allowed_mentions = disnake.AllowedMentions.all())
bot.remove_command('help')

DATABASE = "voice_time.db"
conn = sqlite3.connect('voice_time.db')
c = conn.cursor()

@bot.event
async def on_ready():
    c.execute("""CREATE TABLE IF NOT EXISTS voice_time (
        user_id TEXT PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        total_time INTEGER DEFAULT 0,
        start_time REAL)""")
    conn.commit()

    print(f'{bot.user.name} воркает так жоско будто мужики на фабрике')
    await bot.change_presence(status=disnake.Status.online)

@bot.event
async def on_voice_state_update(member, before, after):
    user_id = str(member.id)
    c = conn.cursor()

    if before.channel is None and after.channel is not None:
        c.execute('''
            INSERT INTO voice_time (user_id, start_time)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET start_time = excluded.start_time''', (user_id, datetime.datetime.now().timestamp()))
        conn.commit()

    elif before.channel is not None and after.channel is None:
        c.execute('SELECT start_time FROM voice_time WHERE user_id=?', (user_id,))
        row = c.fetchone()
        if row and row[0] is not None:
            start_time = row[0]
            end_time = datetime.datetime.now().timestamp()
            time_spent = end_time - start_time
            c.execute('''
                UPDATE voice_time
                SET total_time = total_time + ?,
                start_time = NULL
                WHERE user_id = ?
            ''', (time_spent, user_id))
            conn.commit()
            number = int(time_spent)
            repeat_count = number // 30
            
            for _ in range(repeat_count):
                c.execute("""UPDATE voice_time SET xp = xp + 1 WHERE user_id = ?""", (user_id, ))
                conn.commit()

@bot.command()
async def profile(ctx, member: disnake.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    c.execute('SELECT total_time FROM voice_time WHERE user_id=?',(user_id, ))
    row = c.fetchone()
    if row:
        total_time_seconds = row[0]
        hours, remainder = divmod(total_time_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        embed = disnake.Embed(
                title=f"Профіль **{member.name}**",
                description="",
                color=0x008fff)
        embed.add_field(name="", value=f"""Час - `{int(hours)}ч. {int(minutes)}х. {int(seconds)}с.`""", inline=True)
        embed.add_field(name="", value=f"""Пінг - {member.mention}""" , inline=False)
        embed.set_thumbnail(url=member.avatar)
        await ctx.send(embed=embed)
    else:
        embed = disnake.Embed(
                title=f"Профіль **{member.name}**",
                description="",
                color=0x008fff)
        embed.add_field(name="", value=f"""Час - `0ч. 0х. 0с.`""", inline=True)
        embed.add_field(name="", value=f"""Пінг - {member.mention}""" , inline=False)
        embed.set_thumbnail(url=member.avatar)
        await ctx.send(embed=embed)

bot.run(settings['TOKEN'])


