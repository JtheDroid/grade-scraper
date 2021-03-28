# grade-scraper

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