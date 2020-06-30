import sys
import asyncio
import discord
import datetime
import traceback





async def bg_tasks(bot):
    tasks = [
        
    ]
    while True:

        for task in tasks:
            try:
                await task()
            except Exception as e:
                raise e
        await asyncio.sleep(1)