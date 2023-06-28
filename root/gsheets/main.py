import asyncio
import os.path
from concurrent.futures import ThreadPoolExecutor

import pygsheets
from datetime import datetime, timezone
from pygsheets.custom_types import HorizontalAlignment, FormatType

from root.logger.log import logger

logger = logger
key_json = os.path.abspath(os.path.join('root', 'gsheets', 'gsheets_key.json'))


def find_row_number(user_id):
    try:
        # Authenticate using service account credentials
        gc = pygsheets.authorize(service_file=key_json)
    
        # Open the Google Sheet by name
        sheet = gc.open('ProjectBox telegram bot overview')

        cells_list_of_lists = sheet.find(str(user_id), matchEntireCell=True)    # [[]]
        if cells_list_of_lists[0]:   # empty list object considered as false
            return cells_list_of_lists[0][0].row
        else:
            return None
    except Exception as x:
        logger.exception(x)


def got_link(user_id, user_full_name, username):
    try:
        # Authenticate using service account credentials
        gc = pygsheets.authorize(service_file=key_json)
    
        # Open the Google Sheet by name
        sheet = gc.open('ProjectBox telegram bot overview')
        # Select the first worksheet in the Google Sheet
        worksheet = sheet[0]
        
        # current_time = datetime.now()
        # current_time = now.strftime("%d-%m-%Y %H:%M")
        
        now = datetime.now()
        epoch = datetime(1899, 12, 30)
        delta = now - epoch
        current_time = delta.days + (delta.seconds / 86400)
        
        row_number = find_row_number(user_id)
        col_index = 4
        
        if row_number is None:
            id_user_time = [[user_id, user_full_name, username, current_time]]
            
            last_row = worksheet.get_col(1, include_empty=False)
            # get the index of the first empty row
            insert_index = len(last_row)
            worksheet.insert_rows(row=insert_index, values=id_user_time, inherit=True)
            
            # cell_to_edit = worksheet.cell((insert_index, col_index))
            # cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            # cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            # cell_to_edit.update()
            
        else:
            # Get the cell object for the specific column and edit its value
            worksheet.update_value((row_number, col_index), current_time)
            
            # cell_to_edit = worksheet.cell((row_number, col_index))
            # cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            # cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            # cell_to_edit.update()
            
    except Exception as x:
        logger.exception(x)


def paid(user_id):
    try:
        # Authenticate using service account credentials
        gc = pygsheets.authorize(service_file=key_json)
    
        # Open the Google Sheet by name
        sheet = gc.open('ProjectBox telegram bot overview')
        # Select the first worksheet in the Google Sheet
        worksheet = sheet[0]
        
        # current_time = datetime.now()
        # current_time = now.strftime("%d-%m-%Y %H:%M")
        
        now = datetime.now()
        epoch = datetime(1899, 12, 30)
        delta = now - epoch
        current_time = delta.days + (delta.seconds / 86400)
        
        row_number = find_row_number(user_id)
        
        if row_number is not None:
            col_index = 5
            worksheet.update_value((row_number, col_index), current_time)
            
            # cell_to_edit = worksheet.cell((row_number, col_index))
            # cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            # cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            # cell_to_edit.update()
            
    except Exception as x:
        logger.exception(x)
        
        
def on_task(user_id, task_number):
    try:
        # Authenticate using service account credentials
        gc = pygsheets.authorize(service_file=key_json)
    
        # Open the Google Sheet by name
        sheet = gc.open('ProjectBox telegram bot overview')
        # Select the first worksheet in the Google Sheet
        worksheet = sheet[0]
        
        # current_time = datetime.now()
        # current_time = now.strftime("%d-%m-%Y %H:%M")
        
        now = datetime.now()
        epoch = datetime(1899, 12, 30)
        delta = now - epoch
        current_time = delta.days + (delta.seconds / 86400)
        
        row_number = find_row_number(user_id)
        
        if row_number is not None:
            time_col_index = 7
            task_col_index = 6
            
            worksheet.update_value((row_number, time_col_index), current_time)
            
            # time_cell_to_edit = worksheet.cell((row_number, time_col_index))
            # time_cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            # time_cell_to_edit.set_number_format(FormatType.DATE_TIME, pattern="DD-MM-YYYY HH:MM")
            # time_cell_to_edit.update()
            
            task_cell_to_edit = worksheet.cell((row_number, task_col_index))
            task_cell_to_edit.value = task_number
            task_cell_to_edit.set_horizontal_alignment(HorizontalAlignment.CENTER)
            task_cell_to_edit.update()

    except Exception as x:
        logger.exception(x)


async def async_got_link(user_id, user_full_name, username):
    try:
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=10)
    
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(executor, got_link, user_id, user_full_name, username)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


async def async_on_task(user_id, task_number):
    try:
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=10)
    
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(executor, on_task, user_id, task_number)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


async def async_paid(user_id):
    try:
        loop = asyncio.get_running_loop()
        executor = ThreadPoolExecutor(max_workers=10)
        
        # run the blocking sync operation in a separate thread
        await loop.run_in_executor(executor, paid, user_id)
    
        # do some other async operations
        await asyncio.sleep(1)
        return
    except Exception as x:
        logger.exception(x)


if __name__ == '__main__':
    asyncio.run(async_got_link('p', 'paka', 'pp'))
    asyncio.run(async_paid('p'))
    asyncio.run(async_on_task('p', 1))


