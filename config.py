import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

#BOT_TOKEN='5574885553:AAFlK1OuEZjkfuBvTpiUK-cCZSrqM8m7Y1U'      #@testing_elv_bot
BOT_TOKEN='5520673030:AAE_kaXiXlajkJ1FQEyCdekykaRiDHUlRMA'      #Слон
#BOT_TOKEN='5398224643:AAEWOrQQLhtYlWHsdGzT2T1dR27st8FfRlg'

admin=644812536


admins=[
    644812536
]
ip='193.187.173.232'
#PGPASSWD='4A0V8Gdf'
#PGUSER='gino2'
#DATABASE='gino_shop_game'

#ip='localhost'
PGPASSWD='4A0V8Gdf'
PGUSER='gino2_reserve'
DATABASE='gino2'
POSTGRES_URI=f'postgresql://{PGUSER}:{PGPASSWD}@{ip}/{DATABASE}'
#696800580