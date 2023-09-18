
SLACK_TOKEN = "xoxb-5817394942737-5790226507639-yR8GjqScVYXCVSq71AZHSiER"
SIGNING_SECRET = "b2d6813296153e31455aff7c555e3230"
url = "https://api.wit.ai/message"


conversation_states = {}

from slack_bolt import App
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
import requests
import re

app = App(
    token=SLACK_TOKEN,
    signing_secret=SIGNING_SECRET
)


# Step 1: Introduction and Greeting
@app.message(re.compile("@bot"))
def greet_and_get_names(body, say, logger):
    logger.info("Greetings")
    event = body.get('event')
    user_id = event.get('user')
    channel = event.get('channel')
    print("here")

    if channel not in conversation_states:
        conversation_states[channel] = {"users": [], "step": 1}

    if user_id not in conversation_states[channel]["users"]:
        conversation_states[channel]["users"].append(user_id)

        if len(conversation_states[channel]["users"]) == 1:
            response = f"Hello, <@{user_id}>! Please introduce yourself."
        else:
            response = f"Hello, <@{user_id}>! Please introduce yourself as well."

        app.client.chat_postMessage(channel=channel, text=response)


# Step 2: Initial Inquiry
@app.message(re.compile(".*name.*"))
def initial_inquiry(payload, say):
    channel = payload["channel"]
    user_id = payload["user"]
    user_state = conversation_states.get(channel)

    if user_state and user_id in user_state["users"] and user_state["step"] == 1:
        user_state["step"] = 2
        say("What do you need or expect from your trip to the UAE?")


# Step 3: Interest and Preferences
@app.message(re.compile(".*interest.*"))
def get_interests(payload, say):
    channel = payload["channel"]
    user_id = payload["user"]
    user_state = conversation_states.get(channel)

    if user_state and user_state["step"] == 3:
        if len(conversation_states[channel]) >= 2:
            # Both users have shared their interests
            user_state["step"] = 4
            say("Great! Now, let's talk about attractions based on your interests.")
        else:
            say("Thanks for sharing your interests. Please wait for the other user to share theirs.")

# @app.message(re.compile("@bot"))
# def bot_message(body, say, logger):
    # logger.info(body)
    # event = body.get('event')
    # user_id = event.get('user')
    # text = event.get('text')
    # response = (requests.get(url, headers={"Authorization": "Bearer " + "WHQMO3BTFYAYJCDSLLP77RPTP6VJGQBD"},params={"q": text})).json()
    # if (len(response['intents']) > 0 and response['intents'][0]['confidence'] > 0.7):
    #     say("Intent --> "+response['intents'][0]['name']+ "")
    # else:
    #     say("I'm not sure how to respond to that.")


@app.event("message")
def event_test(body, say, logger):
    logger.info(body)
    event = body.get('event')
    user_id = event.get('user')
    text = event.get('text')
    channel = event.get('channel')
    f = open(channel+".txt", "a")
    f.write(user_id + ", " + text +"\n")
    f.close()

@app.event("team_join")
def ask_for_introduction(event, say):
    welcome_channel_id = "C12345"
    user_id = event["user"]
    text = f"Welcome to the team, <@{user_id}>! 🎉 You can introduce yourself in this channel."
    say(text=text, channel=welcome_channel_id)


flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    flask_app.run(host='0.0.0.0', port='3000',debug=True)