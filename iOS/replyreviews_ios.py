import os
import jwt
import time
import requests
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timedelta

load_dotenv()

private_key_path = '/path/to/your/appstore_authkey.p8.p8'  # Path to your .p8 file
key_id = os.environ["key_id"]  # Your Key ID
issuer_id = os.environ["issuer_id"]  # Your Issuer ID
app_id = os.environ["ios_app_id"] # IOS app ID

# Calculate date for 1 month
last_month = datetime.now() - timedelta(days=25)
last_month_str = last_month.strftime('%Y-%m-%dT%H:%M:%S%Z')

                                    ### Generating JWT

with open(private_key_path, 'r') as f:     
    private_key = f.read() 

# Create the JWT payload
payload = {
    'iss': issuer_id,
    'iat': int(time.time()),
    'exp': int(time.time()) + 20 * 60,
    'aud': 'appstoreconnect-v1'
}

# Encode the JWT with ES256 algorithm
token = jwt.encode(payload, private_key, algorithm='ES256', headers={'kid': key_id})

                                    ### Get Reviews

# Set the API endpoint
url = f'https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews'

reviews_list = []

# Make the GET request
while url:
    response = requests.get(url, headers={'Authorization': f'Bearer {token}'})

    # Check the response
    if response.status_code == 200:
        # Successfully fetched the reviews
        reviews = response.json()
        #print("Reviews:", reviews)
        reviews_list.extend(reviews['data'])
        # Get the next page URL (if available)
        url = reviews['links'].get('next', None)

    else:
        # Handle errors (e.g., invalid token, expired token, etc.)
        print(f"Error: {response.status_code}")
        print(response.json())
        break

# After collecting all reviews, you can print the result
# print(f"Collected {len(reviews_list)} reviews.")
# print(reviews_list)

                    # Convert the reviews list to a pandas DataFrame

df_reviews = pd.DataFrame(reviews_list)

# Flatten the 'attributes' fields
df_reviews['rating'] = df_reviews['attributes'].apply(lambda x: x.get('rating') if isinstance(x, dict) else None)
df_reviews['title'] = df_reviews['attributes'].apply(lambda x: x.get('title') if isinstance(x, dict) else None)
df_reviews['body'] = df_reviews['attributes'].apply(lambda x: x.get('body') if isinstance(x, dict) else None)
df_reviews['reviewerNickname'] = df_reviews['attributes'].apply(lambda x: x.get('reviewerNickname') if isinstance(x, dict) else None)
df_reviews['createdDate'] = df_reviews['attributes'].apply(lambda x: x.get('createdDate') if isinstance(x, dict) else None)
df_reviews['territory'] = df_reviews['attributes'].apply(lambda x: x.get('territory') if isinstance(x, dict) else None)

# Extract the 'response' link if available
df_reviews['response_link'] = df_reviews['relationships'].apply(lambda x: x.get('response', {}).get('links', {}).get('related', None) if isinstance(x, dict) else None)

# Drop the original 'attributes' and 'relationships' columns
df_reviews = df_reviews.drop(columns=['attributes', 'relationships'])

# Convert 'createdDate' to datetime format
# df_reviews['createdDate'] = pd.to_datetime(df_reviews['createdDate'])

# Sort by 'createdDate' in descending order
df_reviews = df_reviews.sort_values(by='createdDate', ascending=False)

df_reviews_last_month = df_reviews[df_reviews['createdDate'] >= last_month_str]
# print(f'last_month: {len(df_reviews_last_month)}')

# Function to fetch the developer's response (if available)
def fetch_developer_response(response_link, token):
    if response_link:
        #print(f"Fetching response from: {response_link}")  # Debugging: Log the response URL
        
        # Make the GET request to the response link
        response = requests.get(response_link, headers={'Authorization': f'Bearer {token}'})
        
        # Check the status code of the response
        if response.status_code == 200:
            response_data = response.json()
            
            # Debugging: Print the raw response data
            #print(f"Response Data: {response_data}")
            
            # Safely access the response data
            data = response_data.get('data', None)
            
            if data:
                # If 'data' exists, extract the 'responseBody'
                response_body = data.get('attributes', {}).get('responseBody', None)
                return response_body
            else:
                # No developer response found
                return None
        else:
            print(f"Failed to fetch response: {response.status_code}")  # Log if request fails
            return None
    return None

# Iterate over reviews and fetch the developer responses if they exist
df_reviews_last_month['developer_response'] = df_reviews_last_month['response_link'].apply(lambda link: fetch_developer_response(link, token))

# Create a 'has_reply' column to indicate if a developer reply exists
df_reviews_last_month['has_reply'] = df_reviews_last_month['developer_response'].apply(lambda x: True if x else False)

# Filtering last month Reviews that are not replied
df_no_reply = df_reviews_last_month[df_reviews_last_month['has_reply'] == False]
print(f'no_reply: {len(df_no_reply)}')

                ### GenAI Configure

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
generation_config = {"temperature": 1.0, "top_p": 0.95, "response_mime_type": "text/plain", "top_k": 64, "max_output_tokens": 8192}
model = genai.GenerativeModel(model_name="gemini-1.5-flash-latest", generation_config=generation_config)

### Generate GenAI Replies
for index, row in df_no_reply.iterrows():
    review = f'{row["title"]}. {row["body"]}'
    prompt = f"""I want you to reply to user reviews that are received for my IOS application in App Store. Please understand the context of the review and reply as concise as possible in maximum of 2 lines by avoiding aggressive words and emoji symbols.
    
If the review contains any query or question or if your are not able to answer then ask the user to write an email to 'your support email' with additional details of the issue, but don’t confirm we will follow up or any such sentences.
 
Also, follow below rules:
* If review contains both negative and positive words: Express sorry (e.g., "We're sorry to hear").
* For positive reviews: Express thanks (e.g., "Thank you for the feedback!")
 
Please respond to this user review of an IOS app:
"{review}" """
    reply = model.generate_content(prompt)
    df_no_reply.loc[index, 'genai_reply'] = f'{row["reviewerNickname"]}, {reply.text}'

                ### Final dataframe for repling the reviews

df_final = df_no_reply[['id', 'rating', 'title', 'body', 'reviewerNickname', 'createdDate', 'territory', 'genai_reply']]
df_final

                ## Reply Reviews

# API endpoint for replying to a review
reply_url = 'https://api.appstoreconnect.apple.com/v1/customerReviewResponses'

# Headers for the request
headers = {'Authorization': f'Bearer {token}','Content-Type': 'application/json',}

for index, review in df_final.iterrows():
    reply_text = review['genai_reply']
    review_id = review['id']
    # Data for the reply
    data = data = {
    "data": {
        "type": "customerReviewResponses",  # Resource type for the response
        "relationships": {
            "review": {
                "data": {
                    "id": review_id,
                    "type": "customerReviews"  # The type for customer review
                }
            }
        },
        "attributes": {
            "responseBody": reply_text  # The developer's reply text
        }
    }
    }
    response = requests.post(reply_url, headers=headers, json=data)
    print(response.json())
print("Successful")
