from slack_bolt import App
from flask import Flask, request
from slack_bolt.adapter.flask import SlackRequestHandler
import requests
import re
import attractions
import os

url = "https://api.wit.ai/message"


conversation_states = {}


app = App(
    token="",
    signing_secret="",
)

headers = {
    'Authorization':'Bearer '
}


# Step 1: Introduction and Greeting
@app.message(re.compile("@bot"))
def greet_and_get_names(body, say, logger):
    logger.info("Greetings")
    event = body.get('event')
    user_id = event.get('user')
    channel = event.get('channel')
    print("run")

    if channel not in conversation_states:
        conversation_states[channel] = {}
    
    if user_id not in conversation_states[channel]:
         conversation_states[channel][user_id] = {"step": 1, "introduced": False}
         response = f"Hello, <@{user_id}>! My name is bot, and I'm happy to assist you today. Please share your vacations Preferences"
         say(response)


@app.event("message")
def handle_message(payload, say):
    channel = payload["channel"]
    user_id = payload["user"]
    msg = payload['text']
    # check intent
    response = requests.get('https://api.wit.ai/message', params= {
        'q': msg
    }, headers = headers).json()
    intents = response['intents']
    entities = response['entities']
    print(intents, "\n")
    print(type(entities), "\n")
    sorted_intents = sorted(intents, key= lambda x: x['confidence'])
    if (len(sorted_intents) == 0):
        return say("Please rephrase, I could not understand")
    if (sorted_intents[len(sorted_intents) -1]['confidence'] > 0.8):
        intent = sorted_intents[len(sorted_intents) - 1]['name']
        if (intent == 'INTERST_INTENT'):
            return handle_interest(user_id, entities, sorted_intents, msg, channel, say)
        elif (intent == 'SUGGEST_INTENTS'):
            return handle_suggest(user_id, entities, sorted_intents, msg, channel, say)
        elif (intent == 'BUDGET_INTENT'):
            return handle_budget(user_id, entities, sorted_intents, msg, channel)
        


# Step 3: Interest and Preferences
def handle_interest(user, entities, sorted_intents, msg, channel, say):
    user_state = conversation_states.get(channel)
    # check if user has mentioned bot
    if (user_state and user_state[user]):
        if (user_state[user]['step'] == 1):
            # user mentiones interests for the first time
            say(f"Great! Now, let's talk about attractions based on your interests. <@{user}>")
            user_state[user]['step'] = 2
            user_state[user]['interest'] = "beach"
            # call a function that responds to interests 
            # remind other user to share their interests
            for u in user_state:
                if (user_state[u]['step'] == 1 and u != user):
                    say(f"What about you <@{u}>, Please share your interests")
                elif (user_state[user]['interest'] == user_state[u]['interest']):
                    say("Interesting, both of you got the same interest")
                elif (user_state[user]['interest'] == user_state[u]['interest']):
                    say("You have different interest")
        else:
            say(f"I have taken your interests earlier")
    

def handle_suggest(user, entities, sorted_intents, msg, channel, say):
    user_state = conversation_states.get(channel)

    if (user_state and user_state[user]):
        say(f"Sure, I would love to share some attractions. which emirate is do you want to visit please?")

def handle_budget(user, entities, sorted_intents, msg, channel, say):
    pass


@app.message(re.compile(r".*(dubai|abu dhabi| ajman|fujairah|sharjah|ras al khaimah| umm al quwain).*"))
def suggest_attraction_based_emirate(payload, say):
    channel = payload["channel"]
    user_id = payload["user"]
    user_state = conversation_states.get(channel)
    emirate = payload['text'].capitalize()

    attractions_list = attractions.uae_attractions[emirate]
    response = ""
    if (user_state and user_state[id]):
        say(f"Here are attractions in {emirate}")
        for i, (attraction, description) in enumerate(attractions_list.items(), start=1):
            response += f" {attraction}: {description} \n"
        say(response)


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
