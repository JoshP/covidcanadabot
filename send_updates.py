#!/usr/bin/env python

# TODO: use better persistent store like DB to keep track of which updates are sent

import logging
import requests
import os

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

province = "BC"

# Keeps track of dates we have processed and sent
dates_sent = {"2021-01-21", "2021-01-22"}

def get_covid_info(province):
    after = {'after': '2021-01-21'}
    url = 'https://api.covid19tracker.ca/reports/province/' + province
    response = requests.get(url, params=after)
    jsonResponse = response.json()
    return jsonResponse["data"]

def has_data_been_sent(date):
    return date in dates_sent
    
def check_new_updates(context: CallbackContext):
    province_data = get_covid_info(province)
    for date_data in province_data:
        # change_cases will be null if the API has no data for that date yet
        if (not has_data_been_sent(date_data["date"]) and date_data["change_cases"] != None):
            logger.info("Change cases updated: %s", date_data["change_cases"])
            send_update(context, date_data)

def send_update(context: CallbackContext, date_data):
    info = f"""{province} - {date_data["date"]} update:
{date_data["change_cases"]} new cases,
{date_data["change_fatalities"]} new fatalities,
{date_data["change_vaccinations"]} new vaccinations.
"""
    logger.info(info)
    context.bot.send_message(chat_id=os.getenv('CHANNEL_ID'), text=info)
    global dates_sent
    dates_sent.add(date_data["date"])

def main() -> None:
    token = os.getenv('TOKEN');
    updater = Updater(token, use_context=True)
    
    job_queue = updater.job_queue
    recurring_job = job_queue.run_repeating(check_new_updates, interval=60, first=10)
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()