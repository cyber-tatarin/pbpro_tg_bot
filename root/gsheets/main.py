import asyncio
import os.path

import pygsheets
from datetime import datetime, timezone
from pygsheets.custom_types import HorizontalAlignment, FormatType

from root.logger.log import get_logger

logger = get_logger()
key_json = os.path.abspath(os.path.join(os.path.pardir, 'gsheets', 'gsheets_key.json'))
# Authenticate using service account credentials
gc = pygsheets.authorize(service_file=key_json)

# Open the Google Sheet by name
sheet = gc.open('ProjectBox telegram bot overview')
# Select the first worksheet in the Google Sheet
worksheet = sheet[0]


def find_row_number(user_id):
    try:
        cells_list_of_lists = sheet.find(user_id)    # [[]]
        if cells_list_of_lists[0]:   # empty list object considered as false
            return cells_list_of_lists[0][0].row
        else:
            return None
    except Exception as x:
        logger.exception(x)


def got_link(user_id, user_full_name):
    try:
        now = datetime.now()
        current_time = now.strftime("%d-%m-%Y %H:%M")
        row_number = find_row_number(user_id)
        col_index = 3
        
        if row_number is None:
            id_user_time = [[user_id, user_full_name, current_time]]
            
            last_row = worksheet.get_col(1, include_empty=False)
            # get the index of the first empty row
            insert_index = len(last_row)
            worksheet.insert_rows(row=insert_index, values=id_user_time, inherit=True)
            
            cell_to_edit = worksheet.cell((row_number, col_index))
            cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            cell_to_edit.update()
            
        else:
            # Get the cell object for the specific column and edit its value
            cell_to_edit = worksheet.cell((row_number, col_index))
            cell_to_edit.value = current_time
            cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            cell_to_edit.update()
    except Exception as x:
        logger.exception(x)


def paid(user_id):
    try:
        now = datetime.now()
        current_time = now.strftime("%d-%m-%Y %H:%M")
        row_number = find_row_number(user_id)
        
        if row_number is not None:
            col_index = 4
            cell_to_edit = worksheet.cell((row_number, col_index))
            cell_to_edit.value = current_time
            cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            cell_to_edit.update()
    except Exception as x:
        logger.exception(x)
        
        
def on_task(user_id, task_number):
    try:
        now = datetime.now()
        current_time = now.strftime("%d-%m-%Y %H:%M")
        row_number = find_row_number(user_id)
        
        if row_number is not None:
            time_col_index = 6
            task_col_index = 5
            
            time_cell_to_edit = worksheet.cell((row_number, time_col_index))
            time_cell_to_edit.value = current_time
            time_cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            time_cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            
            task_cell_to_edit = worksheet.cell((row_number, task_col_index))
            task_cell_to_edit.value = task_number
            task_cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            
            worksheet.update_cells([task_cell_to_edit, time_cell_to_edit])
    except Exception as x:
        logger.exception(x)


async def async_got_link(user_id, user_full_name):
    try:
        loop = asyncio.get_running_loop()
    
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(None, got_link, user_id, user_full_name)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


async def async_on_task(user_id, task_number):
    try:
        loop = asyncio.get_running_loop()
    
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(None, on_task, user_id, task_number)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


async def async_paid(user_id):
    try:
        loop = asyncio.get_running_loop()
        
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(None, paid, user_id)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


if __name__ == '__main__':
    asyncio.run(async_got_link('uuuu', 'paka'))
    asyncio.run(async_paid('uuuu'))


