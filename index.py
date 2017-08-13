# AWS Lambda based skill

import urllib2
import json

global session_attributes
session_attributes = {
    'subreddit': None,
    'n_posts': None
    }


def lambda_handler(event, context):
    print("event.session.application.applicationId={}".format(
        event['session']['application']['applicationId']))

    if event['session']['new']:
        on_session_started(
            {'requestId': event['request']['requestId']}, event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedReqest":
        return on_session_ended(event['request'], event['session'])


# This will grab the posts from reddit
def get_posts():
    global session_attributes
    success = False
    while not success:
        try:
            page = urllib2.urlopen('https://reddit.com/r/{}/new/.json?'
                                   'limit={}'.format(
                                       session_attributes['subreddit'],
                                       session_attributes['n_posts']))
            success = True
        except:
            pass
    data = json.loads(page.read())
    posts = [str(child['data']['title']) for child in data['data']['children']]
    msg = "".join(["... {}".format(post) for post in posts])
    return msg


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    global session_attributes
    card_title = "Welcome!"
    speech_output = ("Welcome to the Reddit Posts skill."
                     " Please tell me how many posts to read from a specific"
                     " subreddit")
    # If the user either does not reply to the welcome message or
    # says something that is not understood,
    # they will be prompted again with this text.
    reprompt_text = ("I'm sorry, I didn't catch that. What subreddit "
                     "would you like to hear from and how many posts,"
                     " again?")
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_help():
    card_title = "Help: Format Response as... Read 5 posts from popular"
    speech_output = ("To have me read some new posts on a subreddit, just say,"
                     " read 5 posts from askreddit")
    reprompt_text = ("Sorry, I didn't get that. Again, to have me read some"
                     " new posts on a subreddit, just say, read 5 posts from"
                     " askreddit")
    should_end_session = False
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Have a nice day!"
    speech_output = "Have a nice day!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def create_subreddit_attribute(subreddit):
    global session_attributes
    session_attributes['subreddit'] = subreddit


def create_n_posts_attribute(n_posts):
    global session_attributes
    session_attributes['n_posts'] = n_posts


def on_session_started(session_started_request, session):
    # Called when a new session has been started
    print("on_session_started requestId={}, sessionId={}".format(
        session_started_request['requestId'], session['sessionId']))


def on_launch(launch_request, session):
    # Called when the user launches the skill without specifying what they want
    print("on_launch requestId={}, sessionId={}".format(
        launch_request['requestId'], session['sessionId']))
    return get_welcome_response()


def on_intent(intent_request, session):
    # Called when the user specifies an intent for this skill
    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    if intent_name == "SubredditIntent":
        return set_subreddit_in_session(intent, session)
    elif intent_name == "NumberIntent":
        return set_n_posts_in_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help()
    elif (intent_name == "AMAZON.CancelIntent" or
          intent_name == "AMAZON.StopIntent"):
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def set_subreddit_in_session(intent, session):
    # Sets the subreddit in the Session

    card_title = "New Reddit Posts"
    global session_attributes
    should_end_session = False

    if 'subreddit' in intent['slots']:
        global session_attributes
        subreddit = intent['slots']['subreddit']['value']
        create_subreddit_attribute(subreddit.replace(' ', '').replace('.', ''))
        print(intent['slots'])
        if 'value' in intent['slots']['number'].keys():
            create_n_posts_attribute(intent['slots']['number']['value'])
        if session_attributes['n_posts'] is not None:
            posts = get_posts()
            if len(posts) == 0:
                speech_output = ("I'm sorry, I could not find the"
                                 " subreddit you were looking for.")
                reprompt_text = None
            else:
                speech_output = ("The {} most recent posts from the {} "
                                 "subreddit are... {}".format(
                                  session_attributes['n_posts'],
                                  session_attributes['subreddit'], posts))
                reprompt_text = None
                should_end_session = True
        else:
            speech_output = ("How many posts would you like to hear"
                             " from {}?".format(
                              session_attributes['subreddit']))
            reprompt_text = ("I'm sorry, I didn't catch that, how many"
                             " posts would you like to hear from {}?"
                             "".format(
                              session_attributes['subreddit']))
    else:
        speech_output = ("I'm not sure what subreddit you are looking"
                         " for. Please try again.")
        reprompt_text = ("I'm not sure what subreddit you are looking"
                         " for. You can tell me which subreddit by saying read"
                         " posts from the soccer subreddit")
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def set_n_posts_in_session(intent, session):
    # sets the number of posts to read in th session

    card_title = "New Reddit Posts"
    global session_attribues
    should_end_session = False

    if 'value' in intent['slots']['number'].keys():
        n_posts = intent['slots']['number']['value']
        create_n_posts_attribute(n_posts)
        if session_attributes['subreddit'] is not None:
            posts = get_posts()
            if len(posts) == 0:
                speech_output = ("I'm sorry. I could not find the"
                                 "subreddit you were looking for")
                reprompt_text = None
            else:
                speech_output = ("The {} most recent posts from the {} "
                                 "subreddit are... {}".format(
                                  session_attributes['n_posts'],
                                  session_attributes['subreddit'], posts))
                reprompt_text = None
                should_end_session = True
        else:
            speech_output = ("What subreddit would you like to hear {}"
                             " posts from?".format(
                              session_attributes['n_posts']))
            reprompt_text = ("I'm sorry, I didn't catch that. What "
                             "subreddit would you like me to read?")
    else:
        speech_output = ("I'm not sure how many posts you would like"
                         " to hear")
        reprompt_text = ("I'm not sure how many posts you would like to"
                         " hear. You can tell me how many posts by saying read"
                         " 5 posts")
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId={}, sessionId={}".format(
        session_ended_request['requestId'], session['sessionId']))
    # add cleanup logic here
    # TODO?


# Amazon's own helper functions
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': "PlainText",
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': "PlainText",
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
