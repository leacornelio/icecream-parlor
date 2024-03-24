import os
import requests
import streamlit as st

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

BEARER_TOKEN = os.environ['BEARER_TOKEN']
client = OpenAI()

lambda_url = "https://ujs5smnta2icm5oinwcfjdg2hy0rxtsa.lambda-url.ap-southeast-1.on.aws"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BEARER_TOKEN}"
}
    
def process_request(query):
    prompt = """
        You are an advanced AI agent for an ice cream parlor. \
        Your capabilities include handling various tasks such as providing information about \
        the menu, taking orders, recording customer feedback, restocking inventory, and generating satisfaction reports. \
        You can also answer general queries related to the parlor's operations. \
        Your responses should be helpful, informative, and align with the specific request made.
    
        Identify the type of request from the user and output in JSON format:
        menu retrieval: {'request': 'menu_retrieval'}
        order placement: Extract the flavors and the quantity for each flavor. \
                         {'request': 'order_placement', 'payload': {"item": "vanilla", "quantity": 2}}
        inventory retrieval: {'request': 'inventory_retrieval'}
        restocking: Extract the flavors and the quantity for each flavor. \
                    {'request': 'restocking', 'payload': {"item": "vanilla", "quantity": 50}}
        customer feedback submission: Extract the comment and rating. Default value for comment is '' and 0 for rating. \
                    {'request': 'feedback_submission', 'payload': {"comment": "Great service!", "rating": 5}}
        customer feedback retrieval: {'request': 'feedback_retrieval'}
        employee satisfaction report submission: Extract the feedback and rating. Default value for feedback is '' and 0 for rating. \
                    {'request': 'report_submission', 'payload: {"feedback_summary": "Overall positive feedback", "average_rating": 4}}
        employee satisfaction report retrieval: {'request': 'report_retrieval'}
        general question: {'request': 'inquiry', 'payload': 'What are you selling?', 'answer': <answer to inquiry>}
    """
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0,
            max_tokens=500,
            response_format = {"type": "json_object"}
        ).choices[0].message.content

        request = eval(response.strip().replace("\n", ""))
        if request['request'] == 'menu_retrieval':
            results = requests.get(lambda_url+'/menu', headers=headers).json()
            output = "Here are our available flavors: " + ", ".join([flavor.title() for flavor in results['flavors']])
        elif request['request'] == 'inventory_retrieval':
            results = requests.get(lambda_url+'/inventory', headers=headers).json()
            output = "Inventory\n\n" + "  \n".join([f"{item['item'].title()}: {item['quantity']}" for item in results["items"]])
        elif request['request'] == 'order_placement':
            inventory = requests.get(lambda_url+'/inventory', headers=headers).json()['items']
            flavor = request['payload']['item']
            quantity = request['payload']['quantity']
            if any(item['item'] == flavor and item['quantity'] >= quantity for item in inventory):
                requests.post(lambda_url+'/order', json=request['payload'], headers=headers)
                output = f'Successfully placed order for {quantity} scoop/s of the {flavor.title()} flavor. Thank you!'
            else:
                output = f'Sorry. There is not enough stock for the {flavor.title()} flavor.'
        elif request['request'] == 'restocking':
            flavor = request['payload']['item']
            quantity = request['payload']['quantity']
            requests.post(lambda_url+'/restock', json=request['payload'], headers=headers).json()
            output = f'Successfully restocked the {flavor.title()} flavor of quantity {quantity}.'
        elif request['request'] == 'feedback_retrieval':
            results = requests.get(lambda_url+'/feedback', headers=headers).json()
            output = "Customer Feedbacks\n"
            for feedback in results['feedback']:
                output += "\nComment: '" + feedback['comment'] + "'  \n"
                output += "Rating: " + str(feedback['rating']) + "\n"
        elif request['request'] == 'feedback_submission':
            requests.post(lambda_url+'/feedback', json=request['payload'], headers=headers).json()
            output = 'Successfully submitted feedback. Thank you!'
        elif request['request'] == 'report_submission':
            output = requests.post(lambda_url+'/report', json=request['payload'], headers=headers).json()
            output = 'Successfully submitted report.'
        elif request['request'] == 'report_retrieval':
            results = requests.get(lambda_url+'/report', headers=headers).json()
            output = "Employee Satisfaction Reports\n"
            for report in results['report']:
                output += "\nFeedback Summary: '" + report['feedback_summary'] + "'  \n"
                output += "Average Rating: " + str(report['average_rating']) + "\n"
        elif request['request'] == 'inquiry':
            output = request['answer']
        else:
            output = "Sorry, your request cannot be processed at the moment. Please try another request."
    except Exception as e:
        print(e)
        output = "Something went wrong when processing your request. Please try again."
    return output

def main():
    st.set_page_config(page_title="The Menti Ice Cream Parlor", page_icon="🍦")
    st.title('🍦 The Menti Ice Cream Parlor')

    # User query
    query = st.text_input("Welcome! How may I help you today?")

    if query:
        output = process_request(query)

        # Display the output
        st.write(output)

if __name__ == "__main__":
    main()