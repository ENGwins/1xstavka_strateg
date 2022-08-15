import asyncio
import datetime
from typing import List

from gino import Gino
from gino.schema import GinoSchemaVisitor
from sqlalchemy import sql, TIMESTAMP, JSON, DateTime
import sqlalchemy as sa

from config import POSTGRES_URI

db = Gino()

class BaseModel(db.Model):
    __abstract__ = True

    def __str__(self):
        model = self.__class__.__name__
        table: sa.Table = sa.inspect(self.__class__)
        primary_key_columns: List[sa.Column] = table.primary_key_column
        values = {
            column.name: getattr(self, self._column_name_map[column.name])
            for column in primary_key_columns
        }
        values_str = " ".join(f"{name}={value!r}" for name, value in values.items())
        return f"<{model} {values_str}>"


class TimedBaseModel(BaseModel):
    __abstract__ = True

    today = datetime.datetime.now()
    created_at = db.Column(DateTime(True), server_default=db.func.now())
    update_at = db.Column(DateTime(True), default=datetime.datetime.utcnow().tzinfo,
                          onupdate=datetime.datetime.utcnow().tzinfo,
                          server_default=db.func.now())


class Bet(TimedBaseModel):
    __tablename__ = 'bets'
    query: sql.Select
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    strateg=db.Column(db.String(50))
    strateg_descr = db.Column(db.String(250))
    game_id = db.Column(db.Integer)
    comand_1=db.Column(db.String(250))
    comand_2 = db.Column(db.String(250))
    score=db.Column(db.String(250))
    coef = db.Column(db.String(50))
    state=db.Column(db.String(50))



class Admin(TimedBaseModel):
    __tablename__ = 'forAdmin_bets'
    query: sql.Select
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True)
    user_id = db.Column(db.BigInteger)  # id покупателя
    user_first_name = db.Column(db.String(50))
    user_last_name = db.Column(db.String(50))\
    # basket = db.Column(JSON)

    def __repr__(self):
        return f"""
ID: {self.user_id}
Имя: {self.user_first_name}
Фамилия: {self.user_last_name}
"""



async def create_db1():
    await db.set_bind(POSTGRES_URI)
    db.gino: GinoSchemaVisitor
    await db.gino.create_all()


asyncio.get_event_loop().run_until_complete(create_db1())
