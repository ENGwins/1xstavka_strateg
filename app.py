import asyncio

from aiogram import executor

from database import create_db1
from loader import dp

#from menu_handlers import set_default_commands
from parsing_v2 import parsing_football


async def on_startup(dispatcher):
   # await set_default_commands(dispatcher)
    await create_db1()
    print('Бот запущен!')



async def scheduled(wait_for):

    while True:

        #await parsing_volleyball2()
        #await parsing_volleyball()
        await parsing_football()
        await asyncio.sleep(wait_for)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled(40))
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
