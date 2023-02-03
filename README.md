# grade-scraper

Check grades and notify on changes

## Usage on Windows
- Download the executable from [releases](https://github.com/JtheDroid/grade-scraper/releases)
- Run it
- Enter username and password, select an installed browser (Chrome/Firefox/Edge)
- Click **Start**

Grades will be checked every 15 minutes, a notification will be displayed on changes

## Setup

- Clone repo
- Install requirements
    - `pip install -r requirements.txt` or
    - `python3 -m pip install -r requirements.txt`
- Run Selenium WebDriver
    - Run docker container `selenium/standalone-chrome`
    - `docker-compose up -d` in directory `selenium_chrome`
- Run `python3 main.py` to create settings file `settings.json`
- Edit `settings.json`
    - **users**: **username** and **password**
    - **discord_webhook.url**: [Discord Webhook URL](#get-discord-webhook-id) (`https://discord.com/api/webhooks/...`)
    - **remote_webdriver_url**: URL for remote webdriver, default value works with the docker container running locally
    - Optional:
        - **users**: **discord_id**: Discord User ID to be mentioned, *everyone* or *here*
        - **discord_webhook**
            - **name**: Override name in Discord message
            - **avatar_url**: Override icon in Discord message

### Get Discord Webhook ID

- Select channel the messages should be sent to
- Click the gear icon (Edit channel)
- Go to Integrations > Webhooks
- Create a Webhook
    - Change name and avatar (will be used if not set in `settings.json`)
- Copy Webhook URL

## Run

Periodically run `python3 main.py`
