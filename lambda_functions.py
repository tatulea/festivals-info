# -*- coding: utf-8 -*-
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_model.dialog import delegate_directive

import pycountry
import requests
import json


sb = SkillBuilder()


##
# AMAZON
##
@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    # Handler for Skill Launch
    speech_text = "Welcome to Festivals Info! Ask me about your next festival based on your desired country."

    return handler_input.response_builder \
            .speak(speech_text) \
            .set_should_end_session(False).response
    # return handler_input.response_builder.speak(speech_text).set_card(
        # SimpleCard("Hello World", speech_text)).set_should_end_session(
        # False).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    # Handler for Session End
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # Handler for Help Intent
    speech_text = "You can ask me about your next festival in your desired country"

    return handler_input.response_builder \
            .speak(speech_text)\
            .ask(speech_text).response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    # Single handler for Cancel and Stop Intent
    speech_text = "Goodbye!"

    return handler_input.response_builder \
            .speak(speech_text) \
            .set_should_end_session(True).response


# @sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
# def fallback_handler(handler_input):
#     # AMAZON.FallbackIntent is only available in en-US locale.
#     # This handler will not be triggered except in that locale,
#     # so it is safe to deploy on any locale
#     speech = (
#         "The Hello World skill can't help you with that.  "
#         "You can say hello!!")
#     reprompt = "You can say hello!!"
#     handler_input.response_builder.speak(speech).ask(reprompt)
#     return handler_input.response_builder.response


##
# EXCEPTION
##
@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Catch all exception handler, log exception and
    # respond with custom message
    print("Encountered following exception: {}".format(exception))

    speech = "Sorry, there was a problem. Please try again!"
    handler_input.response_builder.speak(speech).ask(speech)

    return handler_input.response_builder.response


##
# CUSTOM INTENTS
##
@sb.request_handler(can_handle_func=is_intent_name("NextFestival"))
def next_festival_intent_handler(handler_input):
    slots = handler_input.request_envelope.request.intent.slots

    country  = slots['country'].value

    if country is None:
        return handler_input.response_builder.add_directive(delegate_directive.DelegateDirective()).response

    try:
        country_code = pycountry.countries.get(name=country.title()).alpha_2
        url = 'https://www.festicket.com/festivals/api/?country=' + country_code
        r = requests.get(url, timeout=2)
        response = json.loads(r.content)['content']

        if response['areResultsFiltered'] == False:
            speech_text = "Oops, there is no festival for this country. Try another country."
        else:
            festivals = response['festivals']
            festivals_details = response['festivalData']

            first_festival = festivals[0]
            first_festival_details = festivals_details[str(first_festival['id'])]

            speech_text = "The next festival in {COUNTRY} is {NAME}. It takes place on {DATE} at {PLACE}.".format(
                    COUNTRY=country,
                    NAME=first_festival_details['name'],
                    DATE=first_festival_details['date_string'],
                    PLACE=first_festival_details['place_short'],
                )
    except KeyError:
        speech_text = "Oops, his country is not recognized. Please, try again."
    except requests.exceptions.ConnectTimeout:
        speech_text = "Oops, it looks like there was an error. Try again later."


    return handler_input.response_builder \
            .speak(speech_text) \
            .set_should_end_session(True).response


handler = sb.lambda_handler()