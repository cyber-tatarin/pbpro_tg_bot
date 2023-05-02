async def send_and_copy_message(bot, receiver_id, message, extra_message, reply_markup=None):
    await bot.send_message(receiver_id, extra_message)
    await bot.copy_message(chat_id=receiver_id, from_chat_id=message.chat.id,
                           message_id=message.message_id,
                           reply_markup=reply_markup)
    await bot.send_message(receiver_id, '------------------------------------')
