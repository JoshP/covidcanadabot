import logging
import os
import random
import datetime
from time import sleep

import psycopg2
import pytz
from telegram.ext import CallbackContext, Updater

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ['DATABASE_URL']
LIVE_MODE = True




def send_update(context: CallbackContext):
    user_list = ['Dave', 'Erik', 'Graham', 'Josh', 'Peter']
    user_of_the_day = random.choice(user_list)

    record_win(user_of_the_day)
    win_percentage = get_win_percentage(username=user_of_the_day)
    recent_winners = get_recent_winners()

    remaining_users = [user for user in user_list if user != user_of_the_day]
    loser_of_the_day = random.choice(remaining_users)

    loser_phrases = ['💩 The loser of the day is', '🤡 The clown of the day is',
                     '🧌 The troll of the day is', '🗞️ The old newz of the day is',
                     '🐽 The pig of the day is',
                     '🪳 The cockroach of the day is']
    loser_phrase = f"{random.choice(loser_phrases)} {loser_of_the_day}"

    info = f"""🏆 User of the day is {user_of_the_day}!
{user_of_the_day} currently has a win percentage of {win_percentage:.2f}%!
Recent champs: {recent_winners}
{loser_phrase}.
"""
    logger.info(info)
    if LIVE_MODE:
        context.bot.send_message(chat_id=os.getenv('CHANNEL_ID'), text=info)


def record_win(username):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("update user_wins set wins = wins + 1 where username = %s", (username,))
    today_pacific = datetime.date.today() - datetime.timedelta(days=1)
    cur.execute("insert into user_wins_by_date(win_date, username) values(%s, %s)",
                (today_pacific, username,))
    conn.commit()

    cur.close()
    conn.close()


def get_win_percentage(username):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("select sum(wins) from user_wins")
    total_wins = int(cur.fetchone()[0])
    cur.execute("select wins from user_wins where username = %s", (username,))
    user_wins = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    return user_wins * 100.0 / total_wins


def get_recent_winners() -> str:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("select count(*),username from user_wins_by_date "
                "where win_date >= current_date - interval '10' day group by username")
    tup = cur.fetchall()
    recent_winners = ', '.join([f"{t[1]} ({t[0]})" for t in tup])
    cur.close()
    conn.close()
    return recent_winners


def main() -> None:
    # wait a bit so previous instance has a chance to shut down, to avoid Telegram duplicate errors
    sleep(60)

    token = os.getenv('TOKEN')
    updater = Updater(token, use_context=True)

    job_queue = updater.job_queue

    job_queue.run_daily(send_update, datetime.time(hour=21, minute=0, tzinfo=pytz.timezone('US/Pacific')))
    # job_queue.run_repeating(send_update, first=10, interval=60)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
