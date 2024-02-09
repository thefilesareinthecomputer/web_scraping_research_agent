'''straightforward command line chat interface for google gemini-pro'''
'''requires a .env file with a GOOGLE_GEMINI_API_KEY variable'''

from dotenv import load_dotenv
import certifi
import google.generativeai as genai
import os
import ssl

# bring in the environment variables from the .env file
load_dotenv()

google_gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')

genai.configure(api_key=google_gemini_api_key)
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])
prompt = """### <SYSTEM MESSAGE> <START> ### 
    You are a helpful chatbot that helps people solve problems. 
    You will intently understand the user's messages and respond to the user in a direct, sincere, and insightful way. 
    Think through all of your responses step by step before you finish generating them. 
    Please make sure to avoid any critical errors or bias. 
    The user is a Python developer working on software develppment projects and will be asking for your help as a pair programmer and programming mentor. 
    Here are some question / andwer pairs to help calibrate your responses:
    User: "How do I do ___ in Python?" 
    Gemini: "You can do ___ in Python by ___. Many of the resources recommend ___ but that is outdated. I recommend ___ instead."
    User: "What is the best way to ___ in Python?" 
    Gemini: "There is a reliable ready-made solution for this issue with the ___ Python library. Here are the steps to implement it: ___." 
    User: "I'm trying to ___ but I don't know the best way to do it." 
    Gemini: "Interesting problem. I'm not aware of any libraries to abstract this, but here's how you can implement it in Python yourself: ___."
    ### <SYSTEM MESSAGE> <END> ###"""
primer = chat.send_message(f'{prompt}', stream=True)
primer.resolve()
primer_response = primer.text
print(primer_response)
exit_words = ['exit', 'quit', 'stop', 'end', 'bye', 'goodbye', 'done', 'break']
    
while True:
        user_input = input('User: ')
        if not user_input:
            continue

        query = user_input.lower().split()
        if not query:
            continue

        if query[0] in exit_words:
            print('Ending chat.')
            break

        else:
            response = chat.send_message(f'{user_input}', stream=True)
            if response:
                for chunk in response:
                    if hasattr(chunk, 'parts'):
                        # Concatenate the text from each part
                        full_text = ''.join(part.text for part in chunk.parts)
                        print(full_text)
                    else:
                        # If it's a simple response, just speak and print the text
                        print(chunk.text)
            if not response:
                attempt_count = 1  # Initialize re-try attempt count
                while attempt_count < 5:
                    response = chat.send_message(f'{user_input}', stream=True)
                    attempt_count += 1  # Increment attempt count
                    if response:
                        for chunk in response:
                            if hasattr(chunk, 'parts'):
                                # Concatenate the text from each part
                                full_text = ''.join(part.text for part in chunk.parts)
                                print(full_text)
                            else:
                                # If it's a simple response, just speak and print the text
                                print(chunk.text)
                    else:
                        print('Chat failed.')