import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import random

# Load environment variables from .env file
load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

class Player:
    def __init__(self, user):
        self.user = user
        self.cards = []
        self.turn = False
        self.withdrawn = False

class UnoGame:
    def __init__(self):
        self.players = []
        self.current_player_index = 0
        self.current_card = None
        self.playing = False
        self.withdrawn_players = []

    def start_game(self):
        self.deal_cards()
        self.playing = True
        self.current_card = self.draw_card()
        self.notify_current_player()

    def deal_cards(self):
        for player in self.players:
            player.cards = [self.draw_card() for _ in range(10)]

    def draw_card(self):
        if random.random() < 0.8:
            return f"{random.choice(colors)} {random.randint(1, 9)}"
        else:
            return f"{random.choice(colors)} {random.choice(special_cards)}"

    def notify_current_player(self):
        current_player = self.players[self.current_player_index]
        bot.loop.create_task(current_player.user.send(f"It's your turn! Current card: {self.current_card}\nYour cards: {', '.join(current_player.cards)}"))

    def next_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.notify_current_player()

    async def block_player(self, ctx):
        next_player_index = (self.current_player_index + 1) % len(self.players)
        await ctx.send(f"{self.players[next_player_index].user.name} has been blocked!")

    async def reverse_direction(self, ctx):
        # Your logic for reversing direction
        pass

game = UnoGame()

# Remove existing help command if needed
bot.remove_command('help')

@bot.command()
async def start(ctx):
    if len(game.players) > 1:
        game.start_game()
        await ctx.send("Game started!")
    else:
        await ctx.send("You need two or more players to start the game.")

@bot.command()
async def join(ctx):
    if not game.playing:
        game.players.append(Player(ctx.author))
        await ctx.send(f"{ctx.author} joined the game!")
    else:
        await ctx.send("The game is already in progress. Wait for the next round.")

@bot.command()
async def play(ctx, *, card):
    if not game.playing:
        await ctx.send("The game has not started yet. Please wait.")
        return

    current_player = game.players[game.current_player_index]
    if ctx.author != current_player.user:
        await ctx.send("It's not your turn!")
        return

    if card not in current_player.cards:
        await ctx.send("Invalid card. Choose another card or use !draw.")
        return

    current_player.cards.remove(card)
    await ctx.send(f"{ctx.author} played {card}")
    game.current_card = card

    if "Change_Color" in card:
        await ctx.send("Choose a color: Red, Yellow, Blue, Green")
    elif "Skip" in card:
        await game.block_player(ctx)
    elif "Reverse" in card:
        await game.reverse_direction(ctx)
    else:
        game.next_turn()

    if len(current_player.cards) == 0:
        await ctx.send(f"{ctx.author} wins!")
        game.playing = False

@bot.command()
async def draw(ctx):
    if not game.playing:
        await ctx.send("The game has not started yet.")
        return

    current_player = game.players[game.current_player_index]
    if ctx.author != current_player.user:
        await ctx.send("It's not your turn!")
        return

    new_card = game.draw_card()
    current_player.cards.append(new_card)
    await ctx.author.send(f"The card you drew is: {new_card}")

    game.next_turn()

@bot.command()
async def uno(ctx):
    if not game.playing:
        await ctx.send("The game has not started yet.")
        return

    current_player = game.players[game.current_player_index]
    if len(current_player.cards) != 1:
        await ctx.send("You can only use this command when you have one card left.")
        return

    await ctx.send("UNO!")

@bot.command()
async def withdraw(ctx):
    if not game.playing:
        await ctx.send("The game has not started yet.")
        return

    current_player = game.players[game.current_player_index]
    current_player.withdrawn = True
    game.withdrawn_players.append(current_player)
    await ctx.send(f"{current_player.user.name} has withdrawn from the game.")

    if len(game.withdrawn_players) == len(game.players) - 1:
        remaining_player = [player for player in game.players if not player.withdrawn][0]
        await ctx.send(f"{remaining_player.user.name} wins after everyone else has withdrawn!")

@bot.command()
async def help(ctx):
    help_message = """
    Commands:
    !start - Start a new game (requires at least 2 players)
    !join - Join the game
    !play [card] - Play a card
    !draw - Draw a card
    !uno - Declare 'UNO!'
    !withdraw - Withdraw from the game
    For more information, visit: https://shorturl.at/UJxg4
    """
    await ctx.send(help_message)

@bot.event
async def on_ready():
    activity = discord.Game(name="Uno Game")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Logged in as {bot.user}')

# Run the bot with the token from environment variable
bot.run(os.getenv('DISCORD_TOKEN'))
