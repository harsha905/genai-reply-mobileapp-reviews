import google.auth
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
import sqlalchemy
import urllib
import config

credentials = service_account.Credentials.from_service_account_file(r"/path/to/your/service-account-credentials.json", scopes=['https://www.googleapis.com/auth/androidpublisher'])
service = build('androidpublisher', 'v3', credentials=credentials)
package_name = 'com.shriram.one'

ist_time = timedelta(hours=5, minutes=30)
yesterday = datetime.now() - timedelta(days=1)
start_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 0, 0, 0)  # 12:00 AM
end_of_yesterday = datetime(yesterday.year, yesterday.month, yesterday.day, 23, 59, 59)  # 11:59:59 PM

df = []
next_page_token = None

while True:
    # Make the API request with pagination token (if available)
    if next_page_token:
        reviews = service.reviews().list(packageName=package_name, token=next_page_token).execute()
    else:
        reviews = service.reviews().list(packageName=package_name).execute()

    # Process the reviews
    for review in reviews["reviews"]:
        author_name = review['authorName']
        review_id = review['reviewId']
        comments = review["comments"]
        
        rating = comments[0]['userComment']['starRating']
        user_review = comments[0]['userComment']['text']
        
        # Convert last modified time to IST
        review_secs = int(comments[0]['userComment']['lastModified']['seconds'])
        review_time_utc = datetime.fromtimestamp(review_secs, timezone.utc)
        review_time_ist = review_time_utc + ist_time
        review_time_str = review_time_ist.strftime('%Y-%m-%d %H:%M:%S')
        
        # Other information
        review_lang = comments[0]['userComment']['reviewerLanguage']
        device = comments[0]['userComment'].get('device', None)
        android_version = comments[0]['userComment'].get('androidOsVersion', None)
        app_version = comments[0]['userComment'].get('appVersionCode', None)
        app_version_name = comments[0]['userComment'].get('appVersionName', None)
        
        # Append the review data to the list
        df.append([review_id, author_name, rating, user_review, review_time_str, review_lang, device, android_version, app_version, app_version_name])

    # Check if there's a next page of reviews
    next_page_token = reviews.get('tokenPagination', {}).get('nextPageToken', None)

    # If there is no next page token, we've fetched all the reviews
    if not next_page_token:
        break

#Creating a Dataframe
columns = ["Review ID", "Author Name", "Rating", "User Review", "Review Time", "Review Language", "Device", "Android Os Version", "App Version", "App Version Name"]
df_review = pd.DataFrame(df, columns = columns)

df_review['Review Time'] = pd.to_datetime(df_review['Review Time'], format='%Y-%m-%d %H:%M:%S')  # Ensure it's in datetime format

# filter yesterday reviews
df_reviews_yest = df_review[(df_review['Review Time'] >= start_of_yesterday) & (df_review['Review Time'] <= end_of_yesterday)]

# Loding to SQL Server
params = urllib.parse.quote_plus(f"DRIVER={config.DRIVER};"
                                     f"SERVER={config.SERVER};"
                                     f"DATABASE={config.DATABASE};"
                                     f"UID={config.UID};"
                                     f"PWD={config.PWD}")
engine = sqlalchemy.create_engine("mssql+pyodbc:///?odbc_connect={}".format(params), echo=False)

df_reviews_yest.to_sql(con=engine, name="android_reviews", if_exists='append', index=False)

print(yesterday,'-',df_reviews_yest.shape, 'Transfer Completed')

# Close Connection
engine.dispose()
