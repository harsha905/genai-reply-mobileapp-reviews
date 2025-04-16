# 🤖 GenAI Reply for Mobile App Reviews

Automated GenAI-powered replies for mobile app (iOS & Android) user reviews.

`genai-reply-mobileapp-reviews` is a Python-based automation that fetch user reviews from Google Play Store and Apple App Store, and uses Google Gemini LLM to generate smart, human-like replies. It helps mobile developers and product managers engage with users at scale, saving time while keeping responses consistent and thoughtful.

---

## ⚙️ Features

- 🔁 Automatically replies to app reviews using GenAI (Google Gemini 1.5 Flash model)
- 📱 Supports both **Google Play Store** and **Apple App Store**
- 🗣️ Multiple tone options (e.g., casual, professional)
- 🔐 Uses API keys securely to fetch and reply to reviews and LLM usage
- 📦 Clean and modular Python scripts for Android and iOS (in separate folders)

---

## 🛠️ Tech Stack

- **Python**
- **Gemini 1.5 Falsh API**
- **Google Play Developer API**
- **App Store Connect API**
- `pandas`, `requests`, `sqlalchemy`, `google-api-python-client`, etc.

---

## 🚀 Getting Started

### 1. Clone the Repository  
```bash
git clone https://github.com/harsha905/genai-reply-mobileapp-reviews.git
cd genai-reply-mobileapp-reviews
```
### 2. Install Dependencies
pip install -r requirements.txt

### 3. Set Up Your Config / API Keys
- Google Play API credentials (JSON file)
- App Store Connect credentials
- Gemini API key

---

## 💡 Usage
### Each platform has its own script inside its folder:
- android (for android app reviews)
- iOS (for iOS app reviews)

---

## 📂 Project Structure
```
genai-reply-mobileapp-reviews/
│
├── android/               # android-specific scripts       
│   └── README.md
│   └── config.py
│   └── replyreviews_android.py
│   └── replyreviews_android_storeindatabase.py
│   └── service-account-credentials.json
│   └── .env
│
├── iOS/                    # iOS-specific scripts
│   └── README.md
│   └── appstore_authkey.p8
│   └── replyreviews_ios.py
│   └── .env
│
├── requirements.txt
├── README.md
└── LICENSE
```
---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙌 Contributing
This is a personal project built for learning and reference. However, feel free to open an issue or pull request if you find something useful to add or improve.
