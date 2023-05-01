from aiogram.utils.callback_data import CallbackData

accept_task_with_comment_cb_data = CallbackData('Acc+comm', 'receiver_id')
accept_task_cb_data = CallbackData('Acc', 'receiver_id')
decline_task_with_comment_cb_data = CallbackData('Dec+comm', 'receiver_id')
decline_task_cb_data = CallbackData('Dec', 'receiver_id')

send_task_cb_data = CallbackData('Task', 'task_number')

    