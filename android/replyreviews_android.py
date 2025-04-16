import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

### Configuring Play Console and GenAI
credentials = service_account.Credentials.from_service_account_file('/your/path/to/service-account-credentials.json', scopes=['https://www.googleapis.com/auth/androidpublisher'])
service = build('androidpublisher', 'v3', credentials=credentials)
package_name = 'your package name' # Ex: com.android.one

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

generation_config = {"temperature": 1.0, "top_p": 0.95, "response_mime_type": "text/plain", "top_k": 64, "max_output_tokens": 8192} 
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest", generation_config=generation_config)

### Get Reviews from Play Console
reviews = service.reviews().list(packageName=package_name).execute()
ist_time = timedelta(hours=5, minutes=30)
df = []
for review in reviews["reviews"]:
    author_name = review['authorName']
    review_id = review['reviewId']
    comments  = review["comments"]
    rating = comments[0]['userComment']['starRating']
    user_review = comments[0]['userComment']['text']
    review_secs = int(comments[0]['userComment']['lastModified']['seconds'])
    #review_nanos = int(comments[0]['userComment']['lastModified']['nanos'])
    review_time_utc = datetime.fromtimestamp(review_secs, timezone.utc) + timedelta(microseconds=review_nanos / 1000)
    review_time_ist = review_time_utc + ist_time
    for item in comments:
        if 'developerComment' in item:
            developer_reply = item["developerComment"]['text']
            replied_secs = int(item["developerComment"]['lastModified']['seconds'])
            #replied_nanos = int(item["developerComment"]['lastModified']['nanos'])
            replied_time_utc = datetime.fromtimestamp(replied_secs, timezone.utc) + timedelta(microseconds=replied_nanos / 1000)
            replied_time_ist = replied_time_utc + ist_time

        else :
            developer_reply = None
            replied_secs = None
            replied_nanos = None
            replied_time_utc = None
            replied_time_ist = None
    df.append([review_id, author_name, rating, user_review, review_time_ist, developer_reply, replied_time_ist])

#Creating a Dataframe
columns = ["Review ID", "Author Name", "Rating", "User Review", "Review Time", "Developer Reply", "Developer Reply Time"]
df_review = pd.DataFrame(df, columns = columns)
df_noreply = df_review[df_review['Developer Reply'].isna()].dropna(axis=1, how='all')
df_noreply = df_noreply.iloc[:10]
df_noreply

### Generate Replies
for index, row in df_noreply.iterrows():
    review = row["User Review"]
    prompt = f"""I want you to reply to user reviews that are received for my android application in google play store. Please understand the context of the review and reply as concise as possible in maximum of 2 lines by avoiding aggressive words and emoji symbols.
    
If the review contains any query or question or if your are not able to answer then ask the user to write an email to "Your Support email here" with additional details of the issue, but don’t confirm we will follow up or any such sentences.

Also, follow below rules:
* If review contains both negative and positive words: Express sorry (e.g., "We're sorry to hear").
* For positive reviews: Express thanks (e.g., "Thank you for the feedback!")

Please respond to this user review of an Android app:
"{review}" """
    reply = model.generate_content(prompt)
    df_noreply.loc[index, 'genai_reply'] = reply.text
df_final = df_noreply
df_final['API_Response'] = ''

### Reply to reviews using API
for index, review in df_final.iterrows():
    replytext =f'Hello {review["Author Name"]}, {review["genai_reply"]}'
    reply = service.reviews().reply(packageName=package_name, reviewId=review['Review ID'], body={'replyText': replytext}).execute()
    print(reply['result'])
    df_final.at[index, 'genai_reply'] = replytext
    df_final.at[index, 'API_Response'] = reply['result']
df_final
