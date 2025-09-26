
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
````

---

## ▶️ Usage

Run the script with your exported CSV:

```bash
python main.py report.csv
```

### First Run

* You will be asked to log into Google in your browser.
* Approve access for the app.
* A `token.json` file will be created for offline access (so you won’t need to log in every time).

### Example Flow

1. Script detects CSV columns and asks you to confirm mappings.
2. Shows you a cleaned preview.
3. Asks which dataset you want to upload (master, incoming, outgoing, eBay).
4. Creates a Google Sheet (or reuses existing one) and uploads the data.

---

## ⚠️ Common Issues

* **403: access_denied (App not verified)**
  → Make sure you added your Google account as a **Test user** in the OAuth consent screen.
  → Only those accounts can use the app until you publish it.

* **403: accessNotConfigured (Drive API)**
  → You must enable both **Google Sheets API** and **Google Drive API** in your Google Cloud project.

* **`ValueError: Client secrets must be for a web or installed app.`**
  → Make sure you created an **OAuth client ID → Desktop app**, not a service account or API key.

---

## 📂 Output

The script also saves local CSV files for:

* `cleaned_master.csv`
* `incoming_payments.csv`
* `outgoing_payments.csv`
* `ebay_outgoing.csv`

These are created in your project directory.

---

## 🛠️ Future Improvements

* Add support for multiple bank formats automatically
* Error handling when Drive API is disabled (fallback to Sheets-only mode)
* Command-line flags for non-interactive runs

---

## 📜 License

MIT License – feel free to use, modify, and share.

```

---

Would you like me to also generate a **requirements.txt** you can drop in the repo so users can just `pip install -r requirements.txt` and have everything working?
```
