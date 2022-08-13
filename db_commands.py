from database import Bet


async def add_bet(**kwargs) -> Bet:
    return await Bet(**kwargs).create()


async def update_state(game_id, state):
    order = await Bet.query.where(Bet.game_id == game_id).gino.first()
    await order.update(state=state).apply()
    return