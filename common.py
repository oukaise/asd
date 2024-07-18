from bot import bot
from aiogram.fsm.context import FSMContext



async def send_message_from_bot(message, user_id):
    await bot.send_message(user_id, message)

async def get_user_id(state: FSMContext):
    state_data = await state.get_data()
    user_id1 = state_data.get('userid')
    if user_id1 is None:
        print("user_id not found in state")
    else:
        print(f"user_id is {user_id1}")
    return user_id1