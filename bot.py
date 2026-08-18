import discord
from discord.ext import commands
import asyncio
import random
import sqlite3
import datetime
import os 
from dotenv import load_dotenv


def draw_card():
    valeurs = ['2','3','4','5','6','7','8','9','10','Valet','Dame','Roi','As']
    return random.choice(valeurs)

def value(card):
    if card in ['Valet','Dame','Roi']:
        return 10
    if card == 'As':
        return 11
    return int(card)

active_games = {} # Sert à empêcher de lancer deux parties en même temps

def hand_total(hand):
    total = sum(value(c) for c in hand)
    aces = hand.count('As')
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


# === CONFIGURATION ===
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
print("sincore.exe...")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)
bot.remove_command('help')

# === BASE DE DONNÉES ===
DB_PATH = 'gta_data.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coins INTEGER DEFAULT 0,
        job TEXT DEFAULT 'Aucun',
        job_level INTEGER DEFAULT 0,
        last_daily TEXT,
        last_roll TEXT,
        last_luckyroll TEXT,
        last_vol TEXT,
        last_deal TEXT,
        last_keep TEXT,
        last_fuck TEXT,
        last_kill TEXT,
        last_accept TEXT,
        last_hack TEXT,
        last_sell TEXT,
        last_corrupt TEXT,
        last_sell_info TEXT,
        last_getwhore TEXT,
        last_collect TEXT,
        last_rituel TEXT,
        last_babyoil TEXT,
        last_bj TEXT,
        last_roulette TEXT,
        last_pfc TEXT,
        last_give TEXT,
        last_collect_mafia TEXT,
        last_buy TEXT,
        free_roll_claimed INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        command TEXT,
        timestamp TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS nourice (
        user_id INTEGER PRIMARY KEY,
        kg REAL DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS hitman_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        target TEXT,
        reward INTEGER,
        risk INTEGER,
        accepted INTEGER DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS mafia (
        user_id INTEGER PRIMARY KEY,
        nourices INTEGER DEFAULT 0,
        dealeurs INTEGER DEFAULT 0,
        cocaine REAL DEFAULT 0,
        extasy REAL DEFAULT 0,
        heroine REAL DEFAULT 0,
        canabis REAL DEFAULT 0,
        bedo REAL DEFAULT 0,
        ketamine REAL DEFAULT 0
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS proxenete (
        user_id INTEGER,
        whore_type TEXT,
        date_recruited TEXT,
        PRIMARY KEY (user_id, whore_type)
    )''')

    # Migration des colonnes manquantes
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'free_roll_claimed' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN free_roll_claimed INTEGER DEFAULT 0")
    if 'last_luckyroll' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN last_luckyroll TEXT")
        
    conn.commit()
    conn.close()

init_db()


# === NOUVELLES FONCTIONS POUR LIMITE 5/H ET ROLL GRATUIT ===
def get_usage_count(user_id, command):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT timestamp FROM usage_log 
                 WHERE user_id = ? AND command = ? 
                 AND timestamp >= datetime('now', '-1 hour')''', (user_id, command))
    results = c.fetchall()
    conn.close()
    return results

def add_usage(user_id, command):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO usage_log (user_id, command, timestamp) VALUES (?, ?, ?)', (user_id, command, now))
    conn.commit()
    conn.close()

def get_free_roll_status(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT free_roll_claimed FROM users WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    conn.close()
    if res:
        return res[0]
    return 0

def claim_free_roll(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT free_roll_claimed, job FROM users WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    if res and res[0] == 0 and res[1] == 'Aucun':
        new_job = random.choice(JOBS_LEVEL1)
        set_job(user_id, new_job, 1)
        c.execute('UPDATE users SET free_roll_claimed = 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        return True, new_job
    conn.close()
    return False, None


# === FONCTIONS UTILITAIRES ===
def get_coins(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT coins FROM users WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    if res:
        conn.close()
        return res[0]
    else:
        c.execute('INSERT INTO users (user_id, coins) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        conn.close()
        return 0

def update_coins(user_id, amount):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET coins = coins + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def set_job(user_id, job, level):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET job = ?, job_level = ? WHERE user_id = ?', (job, level, user_id))
    conn.commit()
    conn.close()

def get_job(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT job, job_level FROM users WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    conn.close()
    if res:
        return res[0], res[1]
    return 'Aucun', 0

def get_last_use(user_id, command):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'SELECT {command} FROM users WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    conn.close()
    if res and res[0]:
        return datetime.datetime.fromisoformat(res[0])
    return None

def set_last_use(user_id, command):
    now = datetime.datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'UPDATE users SET {command} = ? WHERE user_id = ?', (now, user_id))
    conn.commit()
    conn.close()

def cooldown_ok(user_id, command, cooldown_hours):
    last = get_last_use(user_id, command)
    if last is None:
        return True
    delta = datetime.datetime.now() - last
    return delta.total_seconds() >= cooldown_hours * 3600

# === MÉTIERS ===
JOBS_LEVEL1 = ['Voleur', 'Dealeur', 'Nourice', 'Prostituée']
JOBS_LEVEL2 = ['Hitman', 'Hacker', 'Enquêteur']
JOBS_LEVEL3 = ['Mafia Boss', 'Proxenete']
JOBS_LEVEL4 = ['Franc-Maçon']




# === COMMANDES GÉNÉRALES ===

## BLACKJACK BUTTONS
class BlackjackView(discord.ui.View):
    def __init__(self, ctx, bet):
        super().__init__(timeout=30) # 30 secondes pour agir
        self.ctx = ctx
        self.bet = bet
        self.player_hand = [draw_card(), draw_card()]
        self.dealer_hand = [draw_card(), draw_card()]
        self.player_total = hand_total(self.player_hand)
        self.dealer_total = hand_total(self.dealer_hand)
        self.user_id = ctx.author.id
        self.msg = None
        self.is_game_over = False

    def update_embed(self, reveal_dealer=False):
        embed = discord.Embed(title="🃏 Blackjack", color=0x00ccff)
        embed.add_field(name="💪 Votre main", value=f"{self.player_hand} (total: {self.player_total})", inline=False)
        if reveal_dealer:
            embed.add_field(name="🎩 Croupier", value=f"{self.dealer_hand} (total: {self.dealer_total})", inline=False)
        else:
            embed.add_field(name="🎩 Croupier", value=f"[?, {self.dealer_hand[1]}]", inline=False)
        embed.add_field(name="💰 Mise", value=f"{self.bet} coins", inline=False)
        return embed

    @discord.ui.button(label="Tirer (Hit)", style=discord.ButtonStyle.success)
    async def hit_button(self, interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("⛔ Ce n'est pas ta partie !", ephemeral=True)
        if self.is_game_over:
            return await interaction.response.edit_message(view=self)

        self.player_hand.append(draw_card())
        self.player_total = hand_total(self.player_hand)

        if self.player_total > 21:
            await self.finish_game(interaction, "BUST")
        else:
            if self.player_total == 21:
                button.disabled = True
            await interaction.response.edit_message(embed=self.update_embed(), view=self)

    @discord.ui.button(label="Rester (Stand)", style=discord.ButtonStyle.danger)
    async def stand_button(self, interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("⛔ Ce n'est pas ta partie !", ephemeral=True)
        if self.is_game_over:
            return await interaction.response.edit_message(view=self)

        await self.finish_game(interaction, "STAND")

    @discord.ui.button(label="Doubler (Double)", style=discord.ButtonStyle.primary)
    async def double_button(self, interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("⛔ Ce n'est pas ta partie !", ephemeral=True)
        if self.is_game_over:
            return await interaction.response.edit_message(view=self)
        
        if len(self.player_hand) != 2:
            return await interaction.response.send_message("❌ Tu ne peux doubler qu'avec tes 2 premières cartes.", ephemeral=True)

        coins = get_coins(self.user_id)
        if coins < self.bet * 2:
            return await interaction.response.send_message("❌ T'as pas assez de thune pour doubler.", ephemeral=True)

        update_coins(self.user_id, -self.bet)
        self.bet *= 2 

        self.player_hand.append(draw_card())
        self.player_total = hand_total(self.player_hand)

        if self.player_total > 21:
            await self.finish_game(interaction, "BUST")
        else:
            await self.finish_game(interaction, "DOUBLE_STAND")

    async def finish_game(self, interaction, action):
        self.is_game_over = True
        for child in self.children:
            child.disabled = True
        
        if action == "STAND" or action == "DOUBLE_STAND":
            while self.dealer_total < 17:
                self.dealer_hand.append(draw_card())
                self.dealer_total = hand_total(self.dealer_hand)

        result_msg = ""
        if self.player_total > 21:
            result_msg = f"**💥 BUST !** Vous dépassez 21. Vous perdez **{self.bet}** coins."
            update_coins(self.user_id, -self.bet)
        elif self.dealer_total > 21:
            gain = self.bet * 2
            result_msg = f"**🎉 Vous gagnez !** Le croupier a dépassé 21. Vous remportez **{gain}** coins."
            update_coins(self.user_id, gain)
        elif self.player_total > self.dealer_total:
            gain = self.bet * 2
            result_msg = f"**🎉 Vous gagnez !** Croupier a {self.dealer_total}. Vous remportez **{gain}** coins."
            update_coins(self.user_id, gain)
        elif self.player_total == self.dealer_total:
            result_msg = f"**🤝 Égalité** (push). Vous récupérez votre mise."
        else:
            result_msg = f"**😔 Vous perdez.** Croupier a {self.dealer_total}. Vous perdez **{self.bet}** coins."
            update_coins(self.user_id, -self.bet)

        set_last_use(self.user_id, 'last_bj')
        add_usage(self.user_id, 'bj')
        final_embed = self.update_embed(reveal_dealer=True)
        final_embed.description = result_msg

        if (self.user_id, self.ctx.channel.id) in active_games:
            del active_games[(self.user_id, self.ctx.channel.id)]

        await interaction.response.edit_message(embed=final_embed, view=self)

    async def on_timeout(self):
        if self.is_game_over:
            return
        self.is_game_over = True
        for child in self.children:
            child.disabled = True

        while self.dealer_total < 17:
            self.dealer_hand.append(draw_card())
            self.dealer_total = hand_total(self.dealer_hand)

        result_msg = ""
        if self.player_total > 21:
            result_msg = f"⏱️ **Timeout - BUST !** Vous perdez **{self.bet}** coins."
            update_coins(self.user_id, -self.bet)
        elif self.dealer_total > 21:
            gain = self.bet * 2
            result_msg = f"⏱️ **Timeout - Gagné !** Croupier a dépassé 21. Vous remportez **{gain}** coins."
            update_coins(self.user_id, gain)
        elif self.player_total > self.dealer_total:
            gain = self.bet * 2
            result_msg = f"⏱️ **Timeout - Gagné !** Croupier a {self.dealer_total}. Vous remportez **{gain}** coins."
            update_coins(self.user_id, gain)
        elif self.player_total == self.dealer_total:
            result_msg = f"⏱️ **Timeout - Égalité** (push)."
        else:
            result_msg = f"⏱️ **Timeout - Perdu.** Croupier a {self.dealer_total}. Vous perdez **{self.bet}** coins."
            update_coins(self.user_id, -self.bet)

        set_last_use(self.user_id, 'last_bj')
        final_embed = self.update_embed(reveal_dealer=True)
        final_embed.description = result_msg

        if (self.user_id, self.ctx.channel.id) in active_games:
            del active_games[(self.user_id, self.ctx.channel.id)]

        try:
            await self.ctx.send(f"{self.ctx.author.mention} ⏱️ **Temps écoulé !**")
        except:
            pass

@bot.command(name='start', aliases=['debut', 'begin'])
async def start(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    success, job_given = claim_free_roll(user_id)
    if success:
        await ctx.send(f"🎉 **Bienvenue à toi, {ctx.author.mention} !** \nTon premier métier est offert. Tu es maintenant **{job_given} (Niveau 1)** ! Tape `.help` pour voir ce que tu peux faire.")
    else:
        await ctx.send("❌ Tu as déjà réclamé ton métier gratuit, ou tu en as déjà un ! Tape `.roll` si tu veux en changer (payant 500k).")

@bot.command(name='daily')
async def daily(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    if not cooldown_ok(user_id, 'last_daily', 24):
        last = get_last_use(user_id, 'last_daily')
        remaining = 24 - (datetime.datetime.now() - last).total_seconds() / 3600
        await ctx.send(f"T'as déjà pris ton daily, connard. Reviens dans {remaining:.1f} heures.")
        return
    amount = random.randint(25000, 50000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_daily')
    await ctx.send(f"T'as chopé {amount} coins. Dépense-les bien, sale riche.")

@bot.command(name='roll')
async def roll(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    
    # Vérification si c'est son premier roll gratuit
    success, job_given = claim_free_roll(user_id)
    if success:
        await ctx.send(f"🎉 **Bienvenue dans le jeu !** Comme c'est ta première fois, ton premier métier t'est offert. Tu es maintenant **{job_given}** (Niveau 1) !")
        return

    # Si pas gratuit, on continue normalement (Cooldown passé de 168h à 24h)
    coins = get_coins(user_id)
    if coins < 500000:
        await ctx.send(f"T'as que {coins} coins, t'es trop pauvre pour te payer un métier. Va bosser.")
        return
    if not cooldown_ok(user_id, 'last_roll', 24):  # 24 heures
        last = get_last_use(user_id, 'last_roll')
        remaining = 24 - (datetime.datetime.now() - last).total_seconds() / 3600
        await ctx.send(f"T'as déjà roulé aujourd'hui, bouffon. Reviens dans {remaining:.1f} heures.")
        return

    update_coins(user_id, -500000)
    set_last_use(user_id, 'last_roll')

    embed = discord.Embed(title="🎲 Roll en cours...", description="Tirage des métiers", color=0xffaa00)
    msg = await ctx.send(embed=embed)

    jobs_list = []
    for _ in range(60):
        jobs_list.extend(JOBS_LEVEL1)
    for _ in range(30):
        jobs_list.extend(JOBS_LEVEL2)
    for _ in range(9):
        jobs_list.extend(JOBS_LEVEL3)
    for _ in range(1):
        jobs_list.extend(JOBS_LEVEL4)

    for _ in range(15):
        fake_job = random.choice(jobs_list)
        embed = discord.Embed(title="🎲 Roll en cours...", description=f"**{fake_job}**", color=0xffaa00)
        await msg.edit(embed=embed)
        await asyncio.sleep(0.4)

    chosen = random.choice(jobs_list)
    if chosen in JOBS_LEVEL1:
        level = 1
    elif chosen in JOBS_LEVEL2:
        level = 2
    elif chosen in JOBS_LEVEL3:
        level = 3
    else:
        level = 4

    set_job(user_id, chosen, level)
    embed = discord.Embed(title="🎉 Métier obtenu !", description=f"Tu es maintenant **{chosen}** (niveau {level})", color=0x00ff00)
    await msg.edit(embed=embed)

@bot.command(name='luckyroll')
async def luckyroll(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    
    # Vérification si c'est son premier roll gratuit
    success, job_given = claim_free_roll(user_id)
    if success:
        await ctx.send(f"🎉 **Bienvenue dans le jeu !** Comme c'est ta première fois, ton premier métier t'est offert. Tu es maintenant **{job_given}** (Niveau 1) !")
        return

    # Cooldown de 168 heures (1 semaine)
    if not cooldown_ok(user_id, 'last_luckyroll', 168):
        last = get_last_use(user_id, 'last_luckyroll')
        remaining = 168 - (datetime.datetime.now() - last).total_seconds() / 3600
        await ctx.send(f"🍀 Ton Lucky Roll est en recharge. Reviens dans {remaining:.1f} heures ({remaining/24:.1f} jours).")
        return

    # Animation du Lucky Roll
    embed = discord.Embed(title="🍀 Lucky Roll en cours...", description="Tirage du métier de la chance", color=0xffd700)
    msg = await ctx.send(embed=embed)

    # 60% N2, 35% N3, 5% N4
    lucky_pool = []
    for _ in range(60):
        lucky_pool.extend(JOBS_LEVEL2)
    for _ in range(35):
        lucky_pool.extend(JOBS_LEVEL3)
    for _ in range(5):
        lucky_pool.extend(JOBS_LEVEL4)

    fake_pool = JOBS_LEVEL1 + JOBS_LEVEL2 + JOBS_LEVEL3 + JOBS_LEVEL4
    for _ in range(15):
        fake_job = random.choice(fake_pool)
        embed = discord.Embed(title="🍀 Lucky Roll en cours...", description=f"**{fake_job}**", color=0xffd700)
        await msg.edit(embed=embed)
        await asyncio.sleep(0.4)

    chosen = random.choice(lucky_pool)
    if chosen in JOBS_LEVEL2:
        level = 2
    elif chosen in JOBS_LEVEL3:
        level = 3
    else:
        level = 4

    set_job(user_id, chosen, level)
    set_last_use(user_id, 'last_luckyroll')
    embed = discord.Embed(title="🎉 Lucky Roll réussi !", description=f"Tu as décroché le métier **{chosen}** (niveau {level}) !", color=0x00ff00)
    await msg.edit(embed=embed)

# === LISTE DES MÉTIERS ===
@bot.command(name='job', aliases=['jobs', 'metiers'])
async def jobs(ctx):
    embed = discord.Embed(title="📋 Liste des métiers disponibles", color=0x3498db)
    
    level1 = ", ".join(JOBS_LEVEL1)
    level2 = ", ".join(JOBS_LEVEL2)
    level3 = ", ".join(JOBS_LEVEL3)
    level4 = ", ".join(JOBS_LEVEL4)
    
    embed.add_field(name="**Niveau 1**", value=level1, inline=False)
    embed.add_field(name="**Niveau 2**", value=level2, inline=False)
    embed.add_field(name="**Niveau 3**", value=level3, inline=False)
    embed.add_field(name="**Niveau 4 (Légendaire)**", value=level4, inline=False)
    embed.set_footer(text="Utilise .roll (1x/jour) ou .luckyroll (1x/semaine)")
    await ctx.send(embed=embed)


@bot.command(name='balance', aliases=['bal'])
async def balance(ctx):
    user_id = ctx.author.id
    coins = get_coins(user_id)
    job, level = get_job(user_id)
    await ctx.send(f"{ctx.author.mention}, t'as **{coins}** coins dans ton compte. Métier : {job} (niveau {level})")

@bot.command(name='give')
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("Faut donner un montant positif, abruti.")
        return
    user_id = ctx.author.id
    target_id = member.id
    if user_id == target_id:
        await ctx.send("Tu peux pas te donner à toi-même, crétin.")
        return
    get_coins(user_id)
    get_coins(target_id)
    coins = get_coins(user_id)
    if coins < amount:
        await ctx.send(f"T'as que {coins} coins, t'es trop pauvre pour donner {amount}.")
        return
    if not cooldown_ok(user_id, 'last_give', 1):
        await ctx.send("T'as déjà donné récemment, attends un peu.")
        return
    update_coins(user_id, -amount)
    update_coins(target_id, amount)
    set_last_use(user_id, 'last_give')
    await ctx.send(f"{ctx.author.mention} a donné **{amount}** coins à {member.mention}.")

# === BLACKJACK ===
@bot.command(name='bj', aliases=['blackjack'])
async def bj(ctx, mise: int):
    user_id = ctx.author.id
    get_coins(user_id)
    coins = get_coins(user_id)
    if mise <= 0 or mise > coins:
        await ctx.send(f"T'as que {coins} coins, tu peux pas miser {mise}.")
        return

    usages = get_usage_count(user_id, 'bj')
    if len(usages) >= 5:
        oldest = datetime.datetime.strptime(usages[0][0], '%Y-%m-%d %H:%M:%S')
        delta = datetime.datetime.now() - oldest
        remaining_seconds = 3600 - delta.total_seconds()
        await ctx.send(f"⏳ **Limite atteinte (5 par heure).** Attends encore **{remaining_seconds:.1f} secondes** avant de rejouer.")
        return

    if (ctx.author.id, ctx.channel.id) in active_games:
        await ctx.send("🚨 Tu as déjà une partie de Blackjack en cours dans ce salon ! Finis-la d'abord.")
        return

    view = BlackjackView(ctx, mise)
    embed = view.update_embed(reveal_dealer=False)
    embed.set_footer(text="⏱️ Tu as 30 secondes pour jouer !")

    active_games[(ctx.author.id, ctx.channel.id)] = view
    msg = await ctx.send(embed=embed, view=view)
    view.msg = msg

# === ROULETTE ===
@bot.command(name='roulette')
async def roulette(ctx, mise: int, choix: str):
    user_id = ctx.author.id
    get_coins(user_id)
    coins = get_coins(user_id)
    if mise <= 0 or mise > coins:
        await ctx.send(f"T'as que {coins} coins, tu peux pas miser {mise}.")
        return

    usages = get_usage_count(user_id, 'roulette')
    if len(usages) >= 5:
        oldest = datetime.datetime.strptime(usages[0][0], '%Y-%m-%d %H:%M:%S')
        delta = datetime.datetime.now() - oldest
        remaining_seconds = 3600 - delta.total_seconds()
        await ctx.send(f"⏳ **Limite atteinte (5 par heure).** Attends encore **{remaining_seconds:.1f} secondes** avant de rejouer.")
        return

    numero = random.randint(0, 36)
    couleur = 'rouge' if numero in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else 'noir' if numero != 0 else 'vert'
    if 1 <= numero <= 12:
        plage = '1-12'
    elif 13 <= numero <= 24:
        plage = '13-24'
    else:
        plage = '25-36'

    gain = 0
    win = False
    choix_lower = choix.lower()
    if choix_lower in ['rouge', 'noir']:
        if choix_lower == couleur:
            gain = mise * 2
            win = True
    elif choix_lower.isdigit() and int(choix_lower) == numero:
        gain = mise * 36
        win = True
    elif choix_lower in ['1-12', '13-24', '25-36']:
        if choix_lower == plage:
            gain = mise * 3
            win = True
    else:
        await ctx.send("Choix invalide. Utilise rouge, noir, un nombre, ou 1-12/13-24/25-36.")
        return

    if win:
        update_coins(user_id, gain)
        set_last_use(user_id, 'last_roulette')
        add_usage(user_id, 'roulette')
        await ctx.send(f"**Gagné !** Le numéro est {numero} ({couleur}, {plage}). Vous remportez {gain} coins.")
    else:
        update_coins(user_id, -mise)
        set_last_use(user_id, 'last_roulette')
        add_usage(user_id, 'roulette')
        await ctx.send(f"**Perdu.** Le numéro est {numero} ({couleur}, {plage}). Vous perdez {mise} coins.")

# === PFC ===
@bot.command(name='pfc')
async def pfc(ctx, mise: int, choix: str):
    user_id = ctx.author.id
    get_coins(user_id)
    coins = get_coins(user_id)
    if mise <= 0 or mise > coins:
        await ctx.send(f"T'as que {coins} coins, tu peux pas miser {mise}.")
        return

    usages = get_usage_count(user_id, 'pfc')
    if len(usages) >= 5:
        oldest = datetime.datetime.strptime(usages[0][0], '%Y-%m-%d %H:%M:%S')
        delta = datetime.datetime.now() - oldest
        remaining_seconds = 3600 - delta.total_seconds()
        await ctx.send(f"⏳ **Limite atteinte (5 par heure).** Attends encore **{remaining_seconds:.1f} secondes** avant de rejouer.")
        return

    choix = choix.lower()
    valides = ['pierre', 'feuille', 'ciseaux']
    if choix not in valides:
        await ctx.send("Choix invalide. Choisis pierre, feuille ou ciseaux.")
        return

    bot_choix = random.choice(valides)
    if choix == bot_choix:
        gain = mise
        msg = f"Égalité ! Vous jouez {choix}, le bot joue {bot_choix}. Vous récupérez votre mise."
    elif (choix == 'pierre' and bot_choix == 'ciseaux') or \
         (choix == 'feuille' and bot_choix == 'pierre') or \
         (choix == 'ciseaux' and bot_choix == 'feuille'):
        gain = mise * 2
        msg = f"**Vous gagnez !** Vous jouez {choix}, le bot joue {bot_choix}. Vous remportez {gain} coins."
    else:
        gain = -mise
        msg = f"**Vous perdez.** Vous jouez {choix}, le bot joue {bot_choix}. Vous perdez {mise} coins."

    update_coins(user_id, gain)
    set_last_use(user_id, 'last_pfc')
    add_usage(user_id, 'pfc')
    await ctx.send(msg)

# === TOP ===
@bot.command(name='top')
async def top(ctx):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, coins FROM users ORDER BY coins DESC LIMIT 10')
    results = c.fetchall()
    conn.close()
    if not results:
        await ctx.send("Personne n'a de coins, c'est triste.")
        return
    embed = discord.Embed(title="🏆 Top 10 des plus riches", color=0xffd700)
    for i, (user_id, coins) in enumerate(results, 1):
        user = await bot.fetch_user(user_id)
        name = user.name if user else f"ID {user_id}"
        embed.add_field(name=f"{i}. {name}", value=f"{coins} coins", inline=False)
    await ctx.send(embed=embed)

# === TIMER (EN EMBED) ===
@bot.command(name='timer')
async def timer(ctx):
    user_id = ctx.author.id
    job, _ = get_job(user_id)
    now = datetime.datetime.now()
    general = ['last_daily', 'last_roll', 'last_luckyroll']
    job_commands = {
        'Voleur': ['last_vol'],
        'Dealeur': ['last_deal'],
        'Nourice': ['last_keep'],
        'Prostituée': ['last_fuck'],
        'Hitman': ['last_kill', 'last_accept'],
        'Hacker': ['last_hack', 'last_sell'],
        'Enquêteur': ['last_corrupt', 'last_sell_info'],
        'Mafia Boss': ['last_collect_mafia', 'last_buy'],
        'Proxenete': ['last_getwhore', 'last_collect'],
        'Franc-Maçon': ['last_rituel', 'last_babyoil']
    }
    games = ['last_bj', 'last_roulette', 'last_pfc', 'last_give']

    all_cmds = general + games
    if job in job_commands:
        all_cmds.extend(job_commands[job])

    msg = ""
    found = False
    for cmd in all_cmds:
        if cmd in ['last_bj', 'last_roulette', 'last_pfc']:
            base_cmd = cmd.replace('last_', '')
            usages = get_usage_count(user_id, base_cmd)
            count = len(usages)
            if count >= 5:
                oldest = datetime.datetime.strptime(usages[0][0], '%Y-%m-%d %H:%M:%S')
                delta = datetime.datetime.now() - oldest
                rem_seconds = 3600 - delta.total_seconds()
                msg += f"**{base_cmd}**: {count}/5 utilisations. Recharge dans **{rem_seconds:.0f} sec**\n"
            else:
                msg += f"**{base_cmd}**: {count}/5 utilisations autorisées cette heure\n"
            found = True
            continue

        last = get_last_use(user_id, cmd)
        if last:
            delta = datetime.datetime.now() - last
            cooldown = 0
            if cmd == 'last_daily':
                cooldown = 24
            elif cmd == 'last_roll':
                cooldown = 24 # 1 jour
            elif cmd == 'last_luckyroll':
                cooldown = 168 # 1 semaine
            elif cmd == 'last_give':
                cooldown = 0.1
            elif cmd in ['last_vol', 'last_deal', 'last_keep', 'last_fuck']:
                cooldown = 2 # 2 heures
            elif cmd in ['last_kill', 'last_accept', 'last_hack', 'last_sell', 'last_corrupt', 'last_sell_info']:
                cooldown = 24
            elif cmd == 'last_collect_mafia' or cmd == 'last_buy':
                cooldown = 24
            elif cmd == 'last_getwhore' or cmd == 'last_collect':
                cooldown = 24
            elif cmd == 'last_rituel':
                cooldown = 72
            elif cmd == 'last_babyoil':
                cooldown = 24
            else:
                cooldown = 24

            remaining = cooldown - delta.total_seconds() / 3600
            if remaining > 0:
                found = True
                display = cmd.replace('last_', '')
                msg += f"**{display}**: {remaining:.1f}h\n"
                
    if not found:
        msg = "Aucun cooldown actif, tu peux tout utiliser."

    embed = discord.Embed(
        title="⏳ Temps restants avant prochaine utilisation :", 
        description=msg.strip(), 
        color=0x3498db
    )
    embed.set_footer(text="sincore.exe")
    await ctx.send(embed=embed)

# === HELP ===
@bot.command(name='help')
async def help_cmd(ctx, job: str = None):
    if job is None:
        embed = discord.Embed(title="📋 Commandes globales", color=0x00ff00)
        embed.add_field(name=".daily", value="Gagne 25k-50k coins (1x/jour)", inline=False)
        embed.add_field(name=".job / .jobs", value="Affiche la liste des métiers disponibles", inline=False)
        embed.add_field(name=".start", value="Offre un métier niveau 1 gratuit aux nouveaux joueurs", inline=False)
        embed.add_field(name=".roll", value="Roll un métier (coûte 500k, 1x/jour)", inline=False)
        embed.add_field(name=".luckyroll", value="Roll un métier de niveau 2 à 4 (Gratuit, 1x/semaine)", inline=False)
        embed.add_field(name=".balance / .bal", value="Affiche ton compte et métier", inline=False)
        embed.add_field(name=".give <@membre> <montant>", value="Donne des coins", inline=False)
        embed.add_field(name=".bj <mise>", value="Joue au blackjack", inline=False)
        embed.add_field(name=".roulette <mise> <choix>", value="Joue à la roulette", inline=False)
        embed.add_field(name=".pfc <mise> <choix>", value="Pierre-feuille-ciseaux", inline=False)
        embed.add_field(name=".top", value="Affiche le top des plus riches", inline=False)
        embed.add_field(name=".timer", value="Affiche les cooldowns", inline=False)
        embed.add_field(name=".help <métier>", value="Affiche les commandes spécifiques à un métier", inline=False)
        await ctx.send(embed=embed)
    else:
        job_lower = job.lower()
        if job_lower == 'voleur':
            embed = discord.Embed(title="🔪 Voleur (niveau 1)", color=0xff0000)
            embed.add_field(name=".vol", value="Voler un PNJ (10k-25k)", inline=False)
            embed.add_field(name=".vol @user", value="Voler un membre (risque)", inline=False)
        elif job_lower == 'dealeur':
            embed = discord.Embed(title="💊 Dealeur (niveau 1)", color=0xff8800)
            embed.add_field(name=".deal", value="Vendre de la drogue (10k-25k)", inline=False)
        elif job_lower == 'nourice':
            embed = discord.Embed(title="🏠 Nourice (niveau 1)", color=0x00aaff)
            embed.add_field(name=".keep", value="Garder de la drogue (stock max 15kg, gain quotidien)", inline=False)
        elif job_lower == 'prostituée':
            embed = discord.Embed(title="💋 Prostituée (niveau 1)", color=0xff66cc)
            embed.add_field(name=".fuck", value="Coucher et gagner (10k-25k)", inline=False)
        elif job_lower == 'hitman':
            embed = discord.Embed(title="🔫 Hitman (niveau 2)", color=0xcc0000)
            embed.add_field(name=".kill", value="Affiche les offres disponibles", inline=False)
            embed.add_field(name=".accept <id>", value="Accepte une offre", inline=False)
        elif job_lower == 'hacker':
            embed = discord.Embed(title="💻 Hacker (niveau 2)", color=0x00ccff)
            embed.add_field(name=".hack", value="Hacker une entreprise (gagne 100k-750k)", inline=False)
            embed.add_field(name=".sell", value="Vendre des infos (gagne 100k-750k)", inline=False)
        elif job_lower == 'enquêteur':
            embed = discord.Embed(title="🕵️ Enquêteur (niveau 2)", color=0x6600cc)
            embed.add_field(name=".corrupt", value="Fermer les yeux sur un traffic (200k-400k)", inline=False)
            embed.add_field(name=".sell", value="Vendre des infos d'enquête (200k-400k)", inline=False)
        elif job_lower == 'mafia boss':
            embed = discord.Embed(title="👑 Mafia Boss (niveau 3)", color=0x990000)
            embed.add_field(name=".mafia", value="Affiche l'état de ton empire", inline=False)
            embed.add_field(name=".buy <type> <qté>", value="Achète de la drogue (cocaine, extasy, heroine, canabis, bedo, ketamine)", inline=False)
            embed.add_field(name=".hire <type>", value="Embauche un nourice ou un dealer (150k nourice, 10k/jour dealer)", inline=False)
            embed.add_field(name=".collect", value="Récupère les gains quotidiens", inline=False)
        elif job_lower == 'proxenete':
            embed = discord.Embed(title="🍑 Proxénète (niveau 3)", color=0xff3399)
            embed.add_field(name=".getwhore", value="Recrute une pute (50% de chance)", inline=False)
            embed.add_field(name=".collect", value="Récupère les gains des putes", inline=False)
        elif job_lower == 'franc-maçon':
            embed = discord.Embed(title="🎩 Franc-Maçon (niveau 4)", color=0xcccccc)
            embed.add_field(name=".rituel", value="Rituel sombre (1x/3j, 100M)", inline=False)
            embed.add_field(name=".babyoil", value="Soirée spéciale (1x/j, 50M)", inline=False)
        else:
            await ctx.send("Métier inconnu, connard.")
            return
        await ctx.send(embed=embed)

# === COMMANDES DES MÉTIERS ===

# --- Voleur ---
@bot.command(name='vol')
async def vol(ctx, member: discord.Member = None):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Voleur':
        await ctx.send("T'es pas voleur, dégage.")
        return
    if not cooldown_ok(user_id, 'last_vol', 2):
        remaining = 2 - (datetime.datetime.now() - get_last_use(user_id, 'last_vol')).total_seconds() / 3600
        await ctx.send(f"T'as déjà volé, renoi. Reviens dans {remaining:.1f}h.")
        return

    if member is None:
        amount = random.randint(10000, 25000)
        update_coins(user_id, amount)
        set_last_use(user_id, 'last_vol')
        await ctx.send(f"Tu as volé un pauvre type dans la rue, tu as gagné {amount} coins.")
    else:
        target_id = member.id
        if target_id == user_id:
            await ctx.send("Tu peux pas te voler toi-même, idiot.")
            return
        get_coins(target_id)
        target_coins = get_coins(target_id)
        vol_amount = random.randint(10000, 25000)
        if target_coins < vol_amount:
            await ctx.send(f"{member.mention} est trop pauvre, il n'a que {target_coins} coins.")
            return
        if random.random() < 0.5:
            await ctx.send(f"Tu t'es fait gauler en volant {member.mention}, tu perds {vol_amount} coins en amende.")
            update_coins(user_id, -vol_amount)
        else:
            update_coins(target_id, -vol_amount)
            update_coins(user_id, vol_amount)
            await ctx.send(f"Tu as réussi à voler {member.mention} de {vol_amount} coins.")
        set_last_use(user_id, 'last_vol')

# --- Dealeur ---
@bot.command(name='deal')
async def deal(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Dealeur':
        await ctx.send("T'es pas dealeur, barre-toi.")
        return
    if not cooldown_ok(user_id, 'last_deal', 2):
        remaining = 2 - (datetime.datetime.now() - get_last_use(user_id, 'last_deal')).total_seconds() / 3600
        await ctx.send(f"T'as déjà deal aujourd'hui, reviens dans {remaining:.1f}h.")
        return
    amount = random.randint(10000, 25000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_deal')
    await ctx.send(f"Tu as vendu de la coke, t'as gagné {amount} coins.")

# --- Nourice ---
@bot.command(name='keep')
async def keep(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Nourice':
        await ctx.send("T'es pas nourice, casse-toi.")
        return
    if not cooldown_ok(user_id, 'last_keep', 2):
        remaining = 2 - (datetime.datetime.now() - get_last_use(user_id, 'last_keep')).total_seconds() / 3600
        await ctx.send(f"T'as déjà gardé de la drogue, reviens dans {remaining:.1f}h.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT kg FROM nourice WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    if res:
        kg = res[0]
    else:
        kg = 0
    added = random.randint(1, 5)
    kg = min(kg + added, 15.0)
    c.execute('REPLACE INTO nourice (user_id, kg) VALUES (?, ?)', (user_id, kg))
    conn.commit()
    conn.close()
    set_last_use(user_id, 'last_keep')
    gain = int((kg / 15) * 25000)
    update_coins(user_id, gain)
    await ctx.send(f"Tu as gardé {added} kg de drogue, ton stock est maintenant de {kg} kg. Tu as gagné {gain} coins.")

# --- Prostituée ---
@bot.command(name='fuck')
async def fuck(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Prostituée':
        await ctx.send("T'es pas pute, va te faire foutre.")
        return
    if not cooldown_ok(user_id, 'last_fuck', 2):
        remaining = 2 - (datetime.datetime.now() - get_last_use(user_id, 'last_fuck')).total_seconds() / 3600
        await ctx.send(f"T'as déjà baisé, t'es une salope. Reviens dans {remaining:.1f}h.")
        return
    amount = random.randint(10000, 25000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_fuck')
    await ctx.send(f"T'as couché avec un client, t'as gagné {amount} coins. Sale pute.")

# --- Hitman ---
@bot.command(name='kill')
async def kill(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Hitman':
        await ctx.send("T'es pas hitman, tu peux pas tuer.")
        return
    if not cooldown_ok(user_id, 'last_kill', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_kill')).total_seconds() / 3600
        await ctx.send(f"T'as déjà checké les offres aujourd'hui, reviens dans {remaining:.1f}h.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM hitman_offers WHERE user_id = ?', (user_id,))
    for _ in range(3):
        reward = random.randint(50000, 250000)
        risk = random.randint(1, 100)
        target = f"Cible-{random.randint(1000,9999)}"
        c.execute('INSERT INTO hitman_offers (user_id, target, reward, risk) VALUES (?, ?, ?, ?)',
                  (user_id, target, reward, risk))
    conn.commit()
    conn.close()
    set_last_use(user_id, 'last_kill')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, target, reward, risk FROM hitman_offers WHERE user_id = ? AND accepted = 0', (user_id,))
    offres = c.fetchall()
    conn.close()
    if not offres:
        await ctx.send("Aucune offre disponible, reviens plus tard.")
        return
    embed = discord.Embed(title="🔪 Offres de contrat", color=0xcc0000)
    for off in offres:
        embed.add_field(name=f"ID {off[0]}", value=f"Cible: {off[1]}\nRécompense: {off[2]} coins\nRisque: {off[3]}%", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='accept')
async def accept(ctx, offre_id: int):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Hitman':
        await ctx.send("T'es pas hitman, tu peux pas accepter.")
        return
    if not cooldown_ok(user_id, 'last_accept', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_accept')).total_seconds() / 3600
        await ctx.send(f"T'as déjà accepté une offre aujourd'hui, reviens dans {remaining:.1f}h.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT reward, risk, target FROM hitman_offers WHERE id = ? AND user_id = ? AND accepted = 0', (offre_id, user_id))
    res = c.fetchone()
    if not res:
        await ctx.send("Offre introuvable ou déjà acceptée.")
        conn.close()
        return
    reward, risk, target = res
    success_chance = 100 - risk + (level * 5)
    success = random.randint(1, 100) <= success_chance
    if success:
        update_coins(user_id, reward)
        await ctx.send(f"Mission accomplie ! Tu as tué {target} et gagné {reward} coins.")
    else:
        penalty = random.randint(10000, 50000)
        update_coins(user_id, -penalty)
        await ctx.send(f"Mission ratée ! Tu as échoué à tuer {target}, tu paies une amende de {penalty} coins.")
    c.execute('UPDATE hitman_offers SET accepted = 1 WHERE id = ?', (offre_id,))
    conn.commit()
    conn.close()
    set_last_use(user_id, 'last_accept')

# --- Hacker ---
@bot.command(name='hack')
async def hack(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Hacker':
        await ctx.send("T'es pas hacker, va te faire voir.")
        return
    if not cooldown_ok(user_id, 'last_hack', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_hack')).total_seconds() / 3600
        await ctx.send(f"T'as déjà hacké aujourd'hui, reviens dans {remaining:.1f}h.")
        return
    amount = random.randint(100000, 750000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_hack')
    await ctx.send(f"Tu as piraté une grosse entreprise, tu as récupéré {amount} coins en données.")

@bot.command(name='sell')
async def sell_hack(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Hacker':
        await ctx.send("T'es pas hacker, dégage.")
        return
    if not cooldown_ok(user_id, 'last_sell', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_sell')).total_seconds() / 3600
        await ctx.send(f"T'as déjà vendu des infos aujourd'hui, reviens dans {remaining:.1f}h.")
        return
    amount = random.randint(100000, 750000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_sell')
    await ctx.send(f"Tu as vendu des infos sur le darkweb, tu as gagné {amount} coins.")

# --- Enquêteur ---
@bot.command(name='corrupt')
async def corrupt(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Enquêteur':
        await ctx.send("T'es pas enquêteur, casse-toi.")
        return
    if not cooldown_ok(user_id, 'last_corrupt', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_corrupt')).total_seconds() / 3600
        await ctx.send(f"T'as déjà corrompu aujourd'hui, reviens dans {remaining:.1f}h.")
        return
    traffics = ['trafic d\'organes', 'trafic humain', 'trafic de drogue']
    traffic = random.choice(traffics)
    amount = random.randint(200000, 400000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_corrupt')
    await ctx.send(f"Tu as fermé les yeux sur un {traffic}. Merci pour ta corruption, voici {amount} coins.")

@bot.command(name='sellinfo')
async def sell_info(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Enquêteur':
        await ctx.send("T'es pas enquêteur, dégage.")
        return
    if not cooldown_ok(user_id, 'last_sell_info', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_sell_info')).total_seconds() / 3600
        await ctx.send(f"T'as déjà vendu des infos aujourd'hui, reviens dans {remaining:.1f}h.")
        return
    amount = random.randint(200000, 400000)
    update_coins(user_id, amount)
    set_last_use(user_id, 'last_sell_info')
    await ctx.send(f"Tu as vendu des informations d'enquête à des réseaux, tu as gagné {amount} coins. Merci pour ta collaboration.")

# --- Mafia Boss ---
@bot.command(name='mafia')
async def mafia(ctx):
    user_id = ctx.author.id
    job, level = get_job(user_id)
    if job != 'Mafia Boss':
        await ctx.send("T'es pas un boss de la mafia, retourne dans ta cave.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT nourices, dealeurs, cocaine, extasy, heroine, canabis, bedo, ketamine FROM mafia WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    if not res:
        c.execute('INSERT INTO mafia (user_id, nourices, dealeurs) VALUES (?, 0, 0)', (user_id,))
        conn.commit()
        res = (0, 0, 0, 0, 0, 0, 0, 0)
    nourices, dealeurs, cocaine, extasy, heroine, canabis, bedo, ketamine = res
    conn.close()
    embed = discord.Embed(title="👑 Empire Mafieux", color=0x990000)
    embed.add_field(name="Nourices", value=nourices, inline=True)
    embed.add_field(name="Dealeurs", value=dealeurs, inline=True)
    embed.add_field(name="Cocaine", value=f"{cocaine} kg", inline=True)
    embed.add_field(name="Extasy", value=f"{extasy} kg", inline=True)
    embed.add_field(name="Heroine", value=f"{heroine} kg", inline=True)
    embed.add_field(name="Canabis", value=f"{canabis} kg", inline=True)
    embed.add_field(name="Bedo", value=f"{bedo} kg", inline=True)
    embed.add_field(name="Ketamine", value=f"{ketamine} kg", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='buy')
async def buy(ctx, drug: str, quantity: float = 1.0):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Mafia Boss':
        await ctx.send("T'es pas un mafia boss, tu peux pas acheter.")
        return
    if not cooldown_ok(user_id, 'last_buy', 0.1):
        await ctx.send("Attends un peu avant d'acheter.")
        return
    drug = drug.lower()
    allowed = ['cocaine', 'extasy', 'heroine', 'canabis', 'bedo', 'ketamine']
    if drug not in allowed:
        await ctx.send("Type de drogue invalide. Choisis parmi: cocaine, extasy, heroine, canabis, bedo, ketamine.")
        return
    prix = {'cocaine': 15000, 'extasy': 10000, 'heroine': 20000, 'canabis': 8000, 'bedo': 12000, 'ketamine': 18000}
    cost = int(quantity * prix[drug])
    coins = get_coins(user_id)
    if coins < cost:
        await ctx.send(f"T'as pas assez de thune, il te faut {cost} coins.")
        return
    update_coins(user_id, -cost)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(f'UPDATE mafia SET {drug} = {drug} + ? WHERE user_id = ?', (quantity, user_id))
    conn.commit()
    conn.close()
    set_last_use(user_id, 'last_buy')
    await ctx.send(f"Tu as acheté {quantity} kg de {drug} pour {cost} coins.")

@bot.command(name='hire')
async def hire(ctx, type_emp: str):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Mafia Boss':
        await ctx.send("T'es pas un mafia boss, tu peux pas embaucher.")
        return
    type_emp = type_emp.lower()
    if type_emp == 'nourice':
        cost = 150000
        coins = get_coins(user_id)
        if coins < cost:
            await ctx.send(f"T'as pas assez, il faut {cost} coins.")
            return
        update_coins(user_id, -cost)
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE mafia SET nourices = nourices + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        await ctx.send(f"Tu as embauché un nourice pour {cost} coins.")
    elif type_emp == 'dealer':
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('UPDATE mafia SET dealeurs = dealeurs + 1 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        await ctx.send(f"Tu as embauché un dealer. Il te coûtera 10k par jour.")
    else:
        await ctx.send("Type invalide. Utilise 'nourice' ou 'dealer'.")

@bot.command(name='collect')
async def collect_mafia(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Mafia Boss':
        await ctx.send("T'es pas un mafia boss, tu peux pas collecter.")
        return
    if not cooldown_ok(user_id, 'last_collect_mafia', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_collect_mafia')).total_seconds() / 3600
        await ctx.send(f"T'as déjà collecté aujourd'hui, reviens dans {remaining:.1f}h.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT nourices, dealeurs, cocaine, extasy, heroine, canabis, bedo, ketamine FROM mafia WHERE user_id = ?', (user_id,))
    res = c.fetchone()
    if not res:
        await ctx.send("Tu n'as pas d'empire.")
        conn.close()
        return
    nourices, dealeurs, cocaine, extasy, heroine, canabis, bedo, ketamine = res

    lost_dealers = 0
    lost_nourices = 0
    for _ in range(dealeurs):
        if random.random() < 0.1:
            lost_dealers += 1
    for _ in range(nourices):
        if random.random() < 0.1:
            lost_nourices += 1

    if lost_dealers > 0 or lost_nourices > 0:
        c.execute('UPDATE mafia SET dealeurs = dealeurs - ? WHERE user_id = ?', (lost_dealers, user_id))
        c.execute('UPDATE mafia SET nourices = nourices - ? WHERE user_id = ?', (lost_nourices, user_id))
        await ctx.send(f"Certains de tes employés se sont fait péter ! Tu as perdu {lost_dealers} dealers et {lost_nourices} nourices.")

    total_drug = cocaine + extasy + heroine + canabis + bedo + ketamine
    base_gain = total_drug * 1000
    dealer_mult = dealeurs * 5000
    nourice_mult = nourices * 3000
    gain = base_gain + dealer_mult + nourice_mult
    cost = dealeurs * 10000
    net_gain = gain - cost
    if net_gain < 0:
        net_gain = 0
    update_coins(user_id, net_gain)
    set_last_use(user_id, 'last_collect_mafia')
    conn.commit()
    conn.close()
    await ctx.send(f"Tu as collecté {net_gain} coins aujourd'hui. (Base: {gain}, coûts: {cost})")

# --- Proxenete ---
@bot.command(name='getwhore')
async def getwhore(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Proxenete':
        await ctx.send("T'es pas proxénète, dégage.")
        return
    if not cooldown_ok(user_id, 'last_getwhore', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_getwhore')).total_seconds() / 3600
        await ctx.send(f"T'as déjà recruté aujourd'hui, reviens dans {remaining:.1f}h.")
        return

    if random.random() < 0.5:
        rand = random.random()
        if rand < 0.50:
            whore_type = 'Prostituée'
        elif rand < 0.85:
            whore_type = 'Modèle OF'
        elif rand < 0.95:
            whore_type = 'Star du Porno'
        else:
            whore_type = random.choice(['Sophie Rain', 'Bonnie Blue', 'Mia Khalifa'])
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM proxenete WHERE user_id = ? AND whore_type IN (?, ?, ?)',
                  (user_id, 'Sophie Rain', 'Bonnie Blue', 'Mia Khalifa'))
        count_top = c.fetchone()[0]
        if whore_type in ['Sophie Rain', 'Bonnie Blue', 'Mia Khalifa'] and count_top >= 3:
            await ctx.send("Tu as déjà 3 putes de la catégorie elite, tu peux pas en recruter plus.")
            conn.close()
            set_last_use(user_id, 'last_getwhore')
            return
        now = datetime.datetime.now().isoformat()
        c.execute('INSERT INTO proxenete (user_id, whore_type, date_recruited) VALUES (?, ?, ?)',
                  (user_id, whore_type, now))
        conn.commit()
        conn.close()
        set_last_use(user_id, 'last_getwhore')
        await ctx.send(f"Tu as recruté une {whore_type} !")
    else:
        set_last_use(user_id, 'last_getwhore')
        await ctx.send("Aucune pute trouvée aujourd'hui.")

@bot.command(name='collectp')
async def collect_prox(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Proxenete':
        await ctx.send("T'es pas proxénète, tu peux pas collecter.")
        return
    if not cooldown_ok(user_id, 'last_collect', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_collect')).total_seconds() / 3600
        await ctx.send(f"T'as déjà collecté aujourd'hui, reviens dans {remaining:.1f}h.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT whore_type, date_recruited FROM proxenete WHERE user_id = ?', (user_id,))
    whores = c.fetchall()
    conn.close()

    if not whores:
        await ctx.send("Tu n'as pas de putes.")
        return

    gains = {
        'Prostituée': 25000,
        'Modèle OF': 150000,
        'Star du Porno': 300000,
        'Sophie Rain': random.randint(750000, 1500000),
        'Bonnie Blue': random.randint(750000, 1500000),
        'Mia Khalifa': random.randint(750000, 1500000)
    }

    total_gain = 0
    lost = []
    for whore in whores:
        if random.random() < 0.05:
            lost.append(whore)
        else:
            total_gain += gains.get(whore[0], 0)

    if lost:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for whore in lost:
            c.execute('DELETE FROM proxenete WHERE user_id = ? AND whore_type = ? AND date_recruited = ?',
                      (user_id, whore[0], whore[1]))
        conn.commit()
        conn.close()
        await ctx.send(f"Certaines de tes putes se sont repenties : {', '.join([w[0] for w in lost])}.")

    update_coins(user_id, total_gain)
    set_last_use(user_id, 'last_collect')
    await ctx.send(f"Tu as collecté {total_gain} coins auprès de tes putes.")

# --- Franc-Maçon ---
@bot.command(name='rituel')
async def rituel(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Franc-Maçon':
        await ctx.send("T'es pas un franc-maçon, t'as pas le droit.")
        return
    if not cooldown_ok(user_id, 'last_rituel', 72):
        remaining = 72 - (datetime.datetime.now() - get_last_use(user_id, 'last_rituel')).total_seconds() / 3600
        await ctx.send(f"Le rituel est encore en recharge, reviens dans {remaining:.1f}h.")
        return
    update_coins(user_id, 100000000)
    set_last_use(user_id, 'last_rituel')
    await ctx.send("Tu as accompli le rituel sombre, tu gagnes 100 millions de coins.")

@bot.command(name='babyoil')
async def babyoil(ctx):
    user_id = ctx.author.id
    get_coins(user_id)
    job, level = get_job(user_id)
    if job != 'Franc-Maçon':
        await ctx.send("T'es pas un franc-maçon, dégage.")
        return
    if not cooldown_ok(user_id, 'last_babyoil', 24):
        remaining = 24 - (datetime.datetime.now() - get_last_use(user_id, 'last_babyoil')).total_seconds() / 3600
        await ctx.send(f"La soirée est en recharge, reviens dans {remaining:.1f}h.")
        return
    update_coins(user_id, 50000000)
    set_last_use(user_id, 'last_babyoil')
    await ctx.send("Tu as organisé une soirée baby-oil, tu gagnes 50 millions de coins.")

# === LANCEMENT ===
bot.run(token=token)