import pandas as pd

# Load your exported CSV
df = pd.read_csv("transactions.csv")

# --- STEP 1: Clean up / simplify ---
# Keep only useful columns
df = df[["Date", "Description", "Amount", "Category", "Card", "Note"]]

# Example: Combine Description + Note into one field
df["Details"] = df["Description"].astype(str) + " " + df["Note"].fillna("")

# --- STEP 2: Filter examples ---
# Incoming payments (Amount > 0)
incoming = df[df["Amount"] > 0]

# Outgoing eBay purchases (Description contains "eBay" and Amount < 0)
ebay_outgoing = df[(df["Description"].str.contains("eBay", case=False)) & (df["Amount"] < 0)]

# --- STEP 3: Save filtered CSVs ---
incoming.to_csv("incoming_payments.csv", index=False)
ebay_outgoing.to_csv("ebay_outgoing.csv", index=False)

# Or save one simplified master version
df.to_csv("cleaned_transactions.csv", index=False)
