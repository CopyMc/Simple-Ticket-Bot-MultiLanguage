import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Select
import json
import asyncio
import datetime
import aiohttp
import os
from typing import Dict, Any, Optional


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Ticket Bot Creator And Developer : ItzLilCopy Enjoy !
def load_languages():
    languages = {
        "en": {
            "ticket_title": "Ticket",
            "ticket_create": "Create Ticket",
            "ticket_close": "Close Ticket",
            "ticket_transcript": "Transcript",
            "ticket_claim": "Claim Ticket",
            "ticket_created": "Ticket created successfully!",
            "ticket_already_exists": "You already have an open ticket!",
            "ticket_no_permission": "You don't have permission to do this!",
            "ticket_closed": "Ticket closed by {closer}",
            "ticket_claimed": "Ticket claimed by {claimer}",
            "ticket_category_select": "Select a category",
            "ticket_category_support": "Support",
            "ticket_category_billing": "Billing",
            "ticket_category_other": "Other",
            "setup_success": "Setup completed successfully!",
            "premium_active": "Premium features are active on this server!",
            "premium_inactive": "This server doesn't have premium features.",
            "help_title": "Help - Ticket Bot Commands",
            "help_admin": "Admin Commands:",
            "help_setup": "`{prefix}setup` - Setup ticket system",
            "help_config": "`{prefix}config` - Configure bot settings",
            "help_add_premium": "`{prefix}addpremium` - Add premium to server",
            "help_remove_premium": "`{prefix}removepremium` - Remove premium from server",
            "help_user": "User Commands:",
            "help_new": "`{prefix}new` - Create a new ticket",
            "help_close": "`{prefix}close` - Close your ticket",
            "language_set": "Language set to English"
        },
        "fa": {
            "ticket_title": "تیکت",
            "ticket_create": "ایجاد تیکت",
            "ticket_close": "بستن تیکت",
            "ticket_transcript": "متن تیکت",
            "ticket_claim": " تیکت",
            "ticket_created": "تیکت با موفقیت ایجاد شد!",
            "ticket_already_exists": "شما در حال حاضر یک تیکت باز دارید!",
            "ticket_no_permission": "شما مجوز انجام این کار را ندارید!",
            "ticket_closed": "تیکت توسط {closer} بسته شد",
            "ticket_claimed": "تیکت توسط {claimer} ادعا شد",
            "ticket_category_select": "یک دسته انتخاب کنید",
            "ticket_category_support": "پشتیبانی",
            "ticket_category_billing": "صورتحساب",
            "ticket_category_other": "دیگر",
            "setup_success": "راه اندازی با موفقیت انجام شد!",
            "premium_active": "ویژگی های پریمیوم در این سرور فعال است!",
            "premium_inactive": "این سرور ویژگی های پریمیوم را ندارد.",
            "help_title": "راهنما - دستورات ربات تیکت",
            "help_admin": "دستورات ادمین:",
            "help_setup": "`{prefix}setup` - راه اندازی سیستم تیکت",
            "help_config": "`{prefix}config` - تنظیمات ربات",
            "help_add_premium": "`{prefix}addpremium` - افزودن پریمیوم به سرور",
            "help_remove_premium": "`{prefix}removepremium` - حذف پریمیوم از سرور",
            "help_user": "دستورات کاربر:",
            "help_new": "`{prefix}new` - ایجاد یک تیکت جدید",
            "help_close": "`{prefix}close` - بستن تیکت شما",
            "language_set": "زبان به فارسی تنظیم شد"
        }
    }
    return languages

languages = load_languages()

# Database functions
def get_guild_data(guild_id: int) -> Dict[str, Any]:
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    
    if str(guild_id) not in data:
        data[str(guild_id)] = {
            "ticket_counter": 0,
            "tickets": {},
            "premium": False,
            "language": "en",
            "support_roles": [],
            "log_channel": None,
            "ticket_category": None
        }
    
    return data[str(guild_id)]

def save_guild_data(guild_id: int, guild_data: Dict[str, Any]):
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    
    data[str(guild_id)] = guild_data
    
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)

def get_premium_servers():
    try:
        with open('premium.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_premium_servers(servers):
    with open('premium.json', 'w') as f:
        json.dump(servers, f, indent=4)


async def get_prefix(bot, message):
    if not message.guild:
        return "!"
    
    guild_data = get_guild_data(message.guild.id)
    return guild_data.get("prefix", "!")


class TicketCategorySelect(Select):
    def __init__(self, lang: str):
        options = [
            discord.SelectOption(
                label=languages[lang]["ticket_category_support"],
                value="support",
                emoji="🛠️"
            ),
            discord.SelectOption(
                label=languages[lang]["ticket_category_billing"],
                value="billing",
                emoji="💳"
            ),
            discord.SelectOption(
                label=languages[lang]["ticket_category_other"],
                value="other",
                emoji="❓"
            )
        ]
        
        super().__init__(
            placeholder=languages[lang]["ticket_category_select"],
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        guild_data = get_guild_data(interaction.guild.id)
        lang = guild_data.get("language", "en")
        

        ticket_id = guild_data["ticket_counter"] + 1
        guild_data["ticket_counter"] = ticket_id
        save_guild_data(interaction.guild.id, guild_data)
        
        category = discord.utils.get(interaction.guild.categories, id=guild_data.get("ticket_category"))
        if not category:
            category = discord.utils.get(interaction.guild.categories, name="Tickets") or await interaction.guild.create_category("Tickets")
            guild_data["ticket_category"] = category.id
            save_guild_data(interaction.guild.id, guild_data)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, manage_channels=True)
        }
        

        for role_id in guild_data.get("support_roles", []):
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)
        
        ticket_channel = await category.create_text_channel(
            f"{self.values[0]}-{ticket_id}",
            overwrites=overwrites
        )
        

        guild_data["tickets"][str(ticket_channel.id)] = {
            "user_id": interaction.user.id,
            "created_at": datetime.datetime.now().isoformat(),
            "category": self.values[0],
            "claimed_by": None,
            "closed": False
        }
        save_guild_data(interaction.guild.id, guild_data)
        

        embed = discord.Embed(
            title=languages[lang]["ticket_title"],
            description=languages[lang]["ticket_created"],
            color=discord.Color.green()
        )
        embed.set_footer(text=f"{languages[lang]['ticket_title']} ID: {ticket_id}")
        
        view = TicketView(lang, ticket_channel.id)
        await ticket_channel.send(embed=embed, view=view)
        await ticket_channel.send(f"{interaction.user.mention} Welcome! Please describe your issue.")
        
        # Send confirmation
        await interaction.response.send_message(
            f"{languages[lang]['ticket_created']} {ticket_channel.mention}",
            ephemeral=True
        )

class TicketView(View):
    def __init__(self, lang: str, channel_id: int):
        super().__init__(timeout=None)
        self.lang = lang
        self.channel_id = channel_id
        
        self.add_item(Button(
            label=languages[lang]["ticket_close"],
            style=discord.ButtonStyle.danger,
            custom_id=f"close_ticket_{channel_id}"
        ))
        self.add_item(Button(
            label=languages[lang]["ticket_claim"],
            style=discord.ButtonStyle.primary,
            custom_id=f"claim_ticket_{channel_id}"
        ))
        self.add_item(Button(
            label=languages[lang]["ticket_transcript"],
            style=discord.ButtonStyle.secondary,
            custom_id=f"transcript_ticket_{channel_id}"
        ))

class CreateTicketView(View):
    def __init__(self, lang: str):
        super().__init__(timeout=None)
        self.lang = lang
        self.add_item(TicketCategorySelect(lang))


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Ticket By Copy"))
    

    bot.add_view(CreateTicketView("en"))
    bot.add_view(CreateTicketView("fa"))

@bot.event
async def on_guild_join(guild):

    get_guild_data(guild.id)
    print(f"Joined guild: {guild.name}")

@bot.event
async def on_guild_remove(guild):

    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
        
        if str(guild.id) in data:
            del data[str(guild.id)]
            
        with open('data.json', 'w') as f:
            json.dump(data, f, indent=4)
    except:
        pass
    
    print(f"Left guild: {guild.name}")


@bot.event
async def on_interaction(interaction):
    if not interaction.data.get("custom_id"):
        return
    
    custom_id = interaction.data["custom_id"]
    
    if custom_id.startswith("create_ticket"):
        guild_data = get_guild_data(interaction.guild.id)
        lang = guild_data.get("language", "en")
        

        for ticket_id, ticket_data in guild_data["tickets"].items():
            if ticket_data["user_id"] == interaction.user.id and not ticket_data["closed"]:
                await interaction.response.send_message(
                    languages[lang]["ticket_already_exists"],
                    ephemeral=True
                )
                return
        
        view = CreateTicketView(lang)
        await interaction.response.send_message(
            languages[lang]["ticket_category_select"],
            view=view,
            ephemeral=True
        )
    
    elif custom_id.startswith("close_ticket_"):
        channel_id = int(custom_id.split("_")[2])
        channel = bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("Channel not found!", ephemeral=True)
            return
        
        guild_data = get_guild_data(interaction.guild.id)
        lang = guild_data.get("language", "en")
        
        ticket_data = guild_data["tickets"].get(str(channel_id))
        if not ticket_data:
            await interaction.response.send_message("Ticket not found!", ephemeral=True)
            return
        

        is_author = ticket_data["user_id"] == interaction.user.id
        is_support = any(role.id in guild_data.get("support_roles", []) for role in interaction.user.roles)
        is_admin = interaction.user.guild_permissions.manage_channels
        
        if not (is_author or is_support or is_admin):
            await interaction.response.send_message(
                languages[lang]["ticket_no_permission"],
                ephemeral=True
            )
            return
        

        ticket_data["closed"] = True
        ticket_data["closed_by"] = interaction.user.id
        ticket_data["closed_at"] = datetime.datetime.now().isoformat()
        save_guild_data(interaction.guild.id, guild_data)
        

        embed = discord.Embed(
            title=languages[lang]["ticket_title"],
            description=languages[lang]["ticket_closed"].format(closer=interaction.user.mention),
            color=discord.Color.red()
        )
        await channel.send(embed=embed)
        

        await asyncio.sleep(5)
        await channel.delete()
        
        await interaction.response.send_message("Ticket closed!", ephemeral=True)
    
    elif custom_id.startswith("claim_ticket_"):
        channel_id = int(custom_id.split("_")[2])
        channel = bot.get_channel(channel_id)
        
        if not channel:
            await interaction.response.send_message("Channel not found!", ephemeral=True)
            return
        
        guild_data = get_guild_data(interaction.guild.id)
        lang = guild_data.get("language", "en")
        

        has_support_role = any(role.id in guild_data.get("support_roles", []) for role in interaction.user.roles)
        is_admin = interaction.user.guild_permissions.manage_channels
        
        if not (has_support_role or is_admin):
            await interaction.response.send_message(
                languages[lang]["ticket_no_permission"],
                ephemeral=True
            )
            return
        

        ticket_data = guild_data["tickets"].get(str(channel_id))
        if ticket_data:
            ticket_data["claimed_by"] = interaction.user.id
            save_guild_data(interaction.guild.id, guild_data)
            
            # Send claim message
            embed = discord.Embed(
                title=languages[lang]["ticket_title"],
                description=languages[lang]["ticket_claimed"].format(claimer=interaction.user.mention),
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
        
        await interaction.response.send_message("Ticket claimed!", ephemeral=True)
    
    elif custom_id.startswith("transcript_ticket_"):
        await interaction.response.send_message("Transcript feature coming soon!", ephemeral=True)


@bot.command(name="setup")
@commands.has_permissions(manage_guild=True)
async def setup_ticket_system(ctx):
    guild_data = get_guild_data(ctx.guild.id)
    lang = guild_data.get("language", "en")
    
    embed = discord.Embed(
        title=languages[lang]["ticket_title"],
        description=languages[lang]["ticket_create"],
        color=discord.Color.blue()
    )
    
    view = View()
    view.add_item(Button(
        label=languages[lang]["ticket_create"],
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket"
    ))
    
    await ctx.send(embed=embed, view=view)
    await ctx.send(languages[lang]["setup_success"])

@bot.command(name="config")
@commands.has_permissions(manage_guild=True)
async def config_bot(ctx, setting: str = None, value: str = None):
    guild_data = get_guild_data(ctx.guild.id)
    lang = guild_data.get("language", "en")
    
    if not setting or not value:
  
        embed = discord.Embed(
            title="Bot Configuration",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Language",
            value=guild_data.get("language", "en"),
            inline=True
        )
        
        embed.add_field(
            name="Premium",
            value="Yes" if guild_data.get("premium", False) else "No",
            inline=True
        )
        
        support_roles = []
        for role_id in guild_data.get("support_roles", []):
            role = ctx.guild.get_role(role_id)
            if role:
                support_roles.append(role.mention)
        
        embed.add_field(
            name="Support Roles",
            value=", ".join(support_roles) if support_roles else "None",
            inline=False
        )
        
        log_channel = ctx.guild.get_channel(guild_data.get("log_channel", 0))
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "None",
            inline=True
        )
        
        await ctx.send(embed=embed)
        return
    
    if setting == "language":
        if value.lower() in ["en", "english"]:
            guild_data["language"] = "en"
            await ctx.send(languages["en"]["language_set"])
        elif value.lower() in ["fa", "persian", "farsi"]:
            guild_data["language"] = "fa"
            await ctx.send(languages["fa"]["language_set"])
        else:
            await ctx.send("Invalid language. Use 'en' or 'fa'.")
    
    elif setting == "supportrole":
        role = None
        
        if value.startswith("<@&") and value.endswith(">"):
            role_id = int(value[3:-1])
            role = ctx.guild.get_role(role_id)
        else:
            role = discord.utils.get(ctx.guild.roles, name=value)
        
        if not role:
            await ctx.send("Role not found!")
            return
        
        if "support_roles" not in guild_data:
            guild_data["support_roles"] = []
        
        if role.id not in guild_data["support_roles"]:
            guild_data["support_roles"].append(role.id)
            await ctx.send(f"Added {role.mention} as support role")
        else:
            guild_data["support_roles"].remove(role.id)
            await ctx.send(f"Removed {role.mention} from support roles")
    
    elif setting == "logchannel":
        channel = None
        
        if value.startswith("<#") and value.endswith(">"):
            channel_id = int(value[2:-1])
            channel = ctx.guild.get_channel(channel_id)
        else:
            channel = discord.utils.get(ctx.guild.channels, name=value)
        
        if not channel:
            await ctx.send("Channel not found!")
            return
        
        guild_data["log_channel"] = channel.id
        await ctx.send(f"Set log channel to {channel.mention}")
    
    save_guild_data(ctx.guild.id, guild_data)


@bot.command(name="addpremium")
@commands.is_owner()
async def add_premium(ctx, guild_id: int = None):
    if not guild_id:
        guild_id = ctx.guild.id
    
    premium_servers = get_premium_servers()
    
    if guild_id not in premium_servers:
        premium_servers.append(guild_id)
        save_premium_servers(premium_servers)
        
        guild_data = get_guild_data(guild_id)
        guild_data["premium"] = True
        save_guild_data(guild_id, guild_data)
        
        await ctx.send(f"Added premium to guild {guild_id}")
    else:
        await ctx.send("This guild already has premium!")

@bot.command(name="removepremium")
@commands.is_owner()
async def remove_premium(ctx, guild_id: int = None):
    if not guild_id:
        guild_id = ctx.guild.id
    
    premium_servers = get_premium_servers()
    
    if guild_id in premium_servers:
        premium_servers.remove(guild_id)
        save_premium_servers(premium_servers)
        
        guild_data = get_guild_data(guild_id)
        guild_data["premium"] = False
        save_guild_data(guild_id, guild_data)
        
        await ctx.send(f"Removed premium from guild {guild_id}")
    else:
        await ctx.send("This guild doesn't have premium!")

@bot.command(name="premiumservers")
@commands.is_owner()
async def list_premium_servers(ctx):
    premium_servers = get_premium_servers()
    
    if not premium_servers:
        await ctx.send("No premium servers!")
        return
    
    embed = discord.Embed(
        title="Premium Servers",
        color=discord.Color.gold()
    )
    
    for guild_id in premium_servers:
        guild = bot.get_guild(guild_id)
        if guild:
            embed.add_field(
                name=guild.name,
                value=f"ID: {guild.id}",
                inline=False
            )
    
    await ctx.send(embed=embed)


@bot.command(name="new")
async def create_ticket(ctx, *, reason: str = None):
    guild_data = get_guild_data(ctx.guild.id)
    lang = guild_data.get("language", "en")
    

    for ticket_id, ticket_data in guild_data["tickets"].items():
        if ticket_data["user_id"] == ctx.author.id and not ticket_data["closed"]:
            await ctx.send(languages[lang]["ticket_already_exists"])
            return
    

    ticket_id = guild_data["ticket_counter"] + 1
    guild_data["ticket_counter"] = ticket_id
    
    category = discord.utils.get(ctx.guild.categories, id=guild_data.get("ticket_category"))
    if not category:
        category = discord.utils.get(ctx.guild.categories, name="Tickets") or await ctx.guild.create_category("Tickets")
        guild_data["ticket_category"] = category.id
    
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
        ctx.author: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True),
        ctx.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, manage_channels=True)
    }
    

    for role_id in guild_data.get("support_roles", []):
        role = ctx.guild.get_role(role_id)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True)
    
    ticket_channel = await category.create_text_channel(
        f"ticket-{ticket_id}",
        overwrites=overwrites
    )
    

    guild_data["tickets"][str(ticket_channel.id)] = {
        "user_id": ctx.author.id,
        "created_at": datetime.datetime.now().isoformat(),
        "category": "general",
        "claimed_by": None,
        "closed": False
    }
    save_guild_data(ctx.guild.id, guild_data)
    
 
    embed = discord.Embed(
        title=languages[lang]["ticket_title"],
        description=languages[lang]["ticket_created"],
        color=discord.Color.green()
    )
    
    if reason:
        embed.add_field(name="Reason", value=reason, inline=False)
    
    embed.set_footer(text=f"{languages[lang]['ticket_title']} ID: {ticket_id}")
    
    view = TicketView(lang, ticket_channel.id)
    await ticket_channel.send(embed=embed, view=view)
    await ticket_channel.send(f"{ctx.author.mention} Welcome! Please describe your issue.")
    
    await ctx.send(f"{languages[lang]['ticket_created']} {ticket_channel.mention}")

@bot.command(name="close")
async def close_ticket(ctx):
    if not isinstance(ctx.channel, discord.TextChannel):
        await ctx.send("This command can only be used in a ticket channel!")
        return
    
    guild_data = get_guild_data(ctx.guild.id)
    lang = guild_data.get("language", "en")
    
    ticket_data = guild_data["tickets"].get(str(ctx.channel.id))
    if not ticket_data:
        await ctx.send("This is not a ticket channel!")
        return
    

    is_author = ticket_data["user_id"] == ctx.author.id
    is_support = any(role.id in guild_data.get("support_roles", []) for role in ctx.author.roles)
    is_admin = ctx.author.guild_permissions.manage_channels
    
    if not (is_author or is_support or is_admin):
        await ctx.send(languages[lang]["ticket_no_permission"])
        return
    

    ticket_data["closed"] = True
    ticket_data["closed_by"] = ctx.author.id
    ticket_data["closed_at"] = datetime.datetime.now().isoformat()
    save_guild_data(ctx.guild.id, guild_data)
    

    embed = discord.Embed(
        title=languages[lang]["ticket_title"],
        description=languages[lang]["ticket_closed"].format(closer=ctx.author.mention),
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    

    await asyncio.sleep(5)
    await ctx.channel.delete()

@bot.command(name="help")
async def help_command(ctx):
    guild_data = get_guild_data(ctx.guild.id)
    lang = guild_data.get("language", "en")
    prefix = guild_data.get("prefix", "!")
    
    embed = discord.Embed(
        title=languages[lang]["help_title"],
        color=discord.Color.blue()
    )
    
    if ctx.author.guild_permissions.manage_guild or await bot.is_owner(ctx.author):
        embed.add_field(
            name=languages[lang]["help_admin"],
            value="\n".join([
                languages[lang]["help_setup"].format(prefix=prefix),
                languages[lang]["help_config"].format(prefix=prefix),
                languages[lang]["help_add_premium"].format(prefix=prefix),
                languages[lang]["help_remove_premium"].format(prefix=prefix)
            ]),
            inline=False
        )
    
    embed.add_field(
        name=languages[lang]["help_user"],
        value="\n".join([
            languages[lang]["help_new"].format(prefix=prefix),
            languages[lang]["help_close"].format(prefix=prefix)
        ]),
        inline=False
    )
    
    if guild_data.get("premium", False):
        embed.set_footer(text=languages[lang]["premium_active"])
    else:
        embed.set_footer(text=languages[lang]["premium_inactive"])
    
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.NotOwner):
        await ctx.send("Only the bot owner can use this command!")
    else:
        print(f"Error: {error}")

if __name__ == "__main__":
    bot.run("YOUR_TOKEN_HERE")