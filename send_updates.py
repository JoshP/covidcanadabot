#!/usr/bin/env python

# TODO: use better persistent store like DB to keep track of which updates are sent
# TODO: switch to https://api.covid19tracker.ca/reports/province/bc?after=2021-01-15 so that we can get sat/sun updates instead of just monday

import logging
import requests
import os
import pytz

from uuid import uuid4
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

last_message_sent="2020-01-22"

def get_covid_info(province):
    url = 'https://api.covid19tracker.ca/summary/split'
    response = requests.get(url)
    jsonResponse = response.json()
    data = jsonResponse["data"]
    for province_data in data:
        if (province_data["province"] == province):
            return province_data

def has_data_been_sent(today):
    return (last_message_sent == today)
    
def check_new_updates(context: CallbackContext):
    province_data = get_covid_info("BC")
    today = datetime.now(pytz.timezone('US/Pacific')).strftime("%Y-%m-%d")
    if (province_data["date"] == today and province_data["change_cases"] != None):
        logger.info("Change cases updated: %s", province_data["change_cases"])
        sent_already = has_data_been_sent(today)
        if (not sent_already):
            send_update(context, province_data)

def send_update(context: CallbackContext, province_data):
    info = f"""{province_data["province"]} - {province_data["date"]} update:
{province_data["change_cases"]} new cases,
{province_data["change_fatalities"]} new fatalities,
{province_data["change_vaccinations"]} new vaccinations.
"""
    logger.info(info)
    context.bot.send_message(chat_id=os.getenv('CHANNEL_ID'), text=info)
    global last_message_sent
    last_message_sent=province_data["date"]

def main() -> None:
    token = os.getenv('TOKEN');
    updater = Updater(token, use_context=True)
    
    job_queue = updater.job_queue
    recurring_job = job_queue.run_repeating(check_new_updates, interval=60, first=10)
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()