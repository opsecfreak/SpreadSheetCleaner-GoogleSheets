# Bank CSV Cleaner & Google Sheets Uploader

This project takes exported banking transactions in CSV format, cleans them up, and uploads the processed data into **Google Sheets**.  
It supports filtering for specific datasets like **incoming payments**, **outgoing payments**, or **eBay purchases**.

---

## 🚀 Features
- Reads and cleans raw banking CSV exports.
- Lets you map CSV columns interactively.
- Splits data into separate datasets:
  - Cleaned master list
  - Incoming payments only
  - Outgoing payments only
  - eBay outgoing purchases
- Uploads the selected dataset to **Google Sheets** automatically.

---

## 📦 Requirements

- Python 3.9+ (tested on Python 3.11/3.13)
- A Google Cloud project with:
  - **Google Sheets API** enabled
  - **Google Drive API** enabled
- OAuth 2.0 client credentials (JSON file)

---

## 🔑 Google Cloud Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a **new project** (or select an existing one).
3. Enable APIs:
   - Go to **APIs & Services → Library**
   - Enable **Google Sheets API**
   - Enable **Google Drive API**
4. Configure OAuth consent screen:
   - Go to **APIs & Services → OAuth consent screen**
   - Choose **External**
   - Fill in the required fields (app name, user support email, etc.)
   - Add your Google account under **Test users** (important!)
5. Create OAuth client credentials:
   - Go to **APIs & Services → Credentials**
   - Click **Create credentials → OAuth client ID**
   - Choose **Desktop app** as the application type
   - Download the JSON file
   - Save it to your project folder as `credentials.json`

---

## ⚙️ Installation

Clone this repo and install dependencies:

```bash
git clone https://github.com/YOURUSERNAME/bank-cleaner.git
cd bank-cleaner
pip install -r requirements.txt
