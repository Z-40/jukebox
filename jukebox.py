import os
import json
import discord
import asyncio
from discord.ext import commands


class JukeBox():
    global bot
    bot = commands.Bot(command_prefix="/")
    def __init__(self, bot_vars):
        with open(bot_vars, "r") as bot_vars:
            self.bot_vars = json.loads(bot_vars.read())

        self.token = self.bot_vars["TOKEN"]
        self.ffmpeg = self.bot_vars["FFMPEG_EXECUTABLE_PATH"]
        self.music = self.bot_vars["MUSIC_FOLDER_PATH"]
        self.name = self.bot_vars["BOT_NAME"]

        self.available_channels = []
        self.voice_channels = {}

    @bot.event
    async def on_ready(self):
        """Get available voice channels"""
        print(f"{bot.user} has connected to Discord!")
        all_channels = list(bot.get_all_channels())
        for channel in all_channels:
            if channel.__class__ == discord.channel.VoiceChannel:
                self.voice_channels[channel.name] = channel
        for channel in all_channels:
            self.available_channels.append(channel.name)

    @bot.command(name="songs")
    async def get_song_list(self, ctx):
        songs = list(list(os.walk(self.music)))[0]
        songs.remove(self.music)
        songs.remove([])
        songs = [s for s in songs[0]]
        songs = "\n".join(songs)
        await ctx.send(f"The available songs are as follows: \n{songs}")
        await ctx.send(f"To play use !play <file>")

    @bot.command(name="join")
    async def join(self, ctx, channel):
        if channel in self.available_channels:
            try:
                selected_channel = self.voice_channels[channel]
            except KeyError:
                await ctx.send("Can only join Voice Channels")
            else:
                try:
                    await selected_channel.connect()
                except discord.errors.ClientException:
                    if "music_bot" in [m.name for m in selected_channel.members]:
                        await ctx.send(f"All ready joined #{selected_channel}")
                    else:
                        if ctx.voice_client.is_playing():
                            ctx.voice_client.stop()
                        await ctx.voice_client.move_to(selected_channel)
                        await ctx.send(f"Moved to #{selected_channel}")
                else:
                    await ctx.send(f"Joined #{selected_channel}")
        else:
            await ctx.send(f"Cannot join #{channel} since it does not exist")

    @staticmethod
    @bot.command(name="quit")
    async def leave(ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.voice_client.disconnect()
        try:
            await ctx.voice_client.cleanup()
        except AttributeError:
            pass
        finally:
            await ctx.send("Quitting voice channel")

    @bot.command(name="play")
    async def play(self, ctx, file):
        songs = list(list(os.walk(self.music))[0])
        songs.remove(self.music)
        songs.remove([])
        songs = [s for s in songs[0]]
        songs = "\n".join(songs)

        src = f"{self.music}\\{file}"
        vc = ctx.voice_client

        if vc:
            if not vc.is_playing():
                if file in songs:
                    try:
                        vc.play(discord.FFmpegPCMAudio(executable=self.ffmpeg, source=src))
                    except discord.ClientException:
                        await ctx.send("ffmpeg executable not found")
                    else:
                        await ctx.send(f"Now playing: {file}")
                        while vc.is_playing():
                            await asyncio.sleep(0)
                else:
                    await ctx.send(f"Could not find {file}")
            else:
                await ctx.send("Something is all ready playing. Use !stop command")
        else:
            await ctx.send("Join a voice channel first")

    @staticmethod
    @bot.command(name="pause")
    async def pause(ctx):
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused")
        else:
            await ctx.send("Nothing playing")

    @bot.command(name="resume")
    async def resume(ctx):
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel")
        elif ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resumed")
        else:
            await ctx.send("All ready playing")

    @bot.command(name="stop")
    async def stop(ctx):
        if not ctx.voice_client:
            await ctx.send("Not connected to a voice channel")
        else:
            ctx.voice_client.stop()

    @staticmethod
    @commands.is_owner()
    @bot.command(name="shutdown")
    async def close(ctx):
        await ctx.send("Shutting Down...")
        await bot.close()

