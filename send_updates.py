#!/usr/bin/env python

import logging
import requests
import os
import psycopg2
import random

from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

province = "BC"
DATABASE_URL = os.environ['DATABASE_URL']
LIVE_MODE = False

def get_covid_info(province):
    # todo make this startDate dynamic to only look a month in the past
    after = {'after': '2021-10-01'}
    url = 'https://api.covid19tracker.ca/reports/province/' + province
    response = requests.get(url, params=after)
    jsonResponse = response.json()
    return jsonResponse["data"]

def has_data_been_sent(date):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("SELECT * FROM reports_sent WHERE date = %s;", (date,))
    row_exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return row_exists
    
def check_new_updates(context: CallbackContext):
    province_data = get_covid_info(province)
    for date_data in province_data:
        # change_cases will be null if the API has no data for that date yet
        if (not has_data_been_sent(date_data["date"]) and date_data["change_cases"] != None and date_data["change_cases"] != 0):
            logger.info("Change cases updated: %s", date_data["change_cases"])
            send_update(context, date_data)

def send_update(context: CallbackContext, date_data):
    user_list = ['Dave', 'Erik', 'Graham', 'Josh', 'Peter']
    user_of_the_day = random.choice(user_list)
    info = f"""{province} - {date_data["date"]} update:
{date_data["change_cases"]} new cases,
{date_data["change_fatalities"]} new fatalities,
{date_data["change_vaccinations"]} new vaccinations,
{date_data["change_boosters_1"]} new boosters,
{date_data["change_vaccinated"]} people newly vaccinated,
{date_data["total_vaccinated"]} total vaccinated, {round(date_data["total_vaccinated"]/4634349, 2)}% of eligible people.
User of the day is {user_of_the_day}.
"""
    logger.info(info)
    if (LIVE_MODE):
        context.bot.send_message(chat_id=os.getenv('CHANNEL_ID'), text=info)
    record_sent_update(date_data["date"])

def record_sent_update(date):
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cur = conn.cursor()
    cur.execute("INSERT INTO reports_sent (date) VALUES (%s);", (date,))
    conn.commit()
    cur.close()
    conn.close()

def main() -> None:
    token = os.getenv('TOKEN')
    updater = Updater(token, use_context=True)
    
    job_queue = updater.job_queue
    job_queue.run_repeating(check_new_updates, interval=60, first=10)
    
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()