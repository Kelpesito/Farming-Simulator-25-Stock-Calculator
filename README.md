# 🚜 Farming Simulator 25 Stock Calculator

A desktop stock management and sales optimization tool for **Farming Simulator 25**.

Track your farm inventory, calculate optimal sales to reach a target income, and export professional PDF reports — all in a modern Kivy-based interface.

---

## 📦 Overview

**Farming Simulator 25 Stock Calculator** is a Python application built with **Kivy + KivyMD** that helps you:

- 📊 Manage your farm stock (liters, prices, capacities)
- 🎯 Calculate the optimal selling plan to reach a € target
- 🚛 Minimize the number of selling trips
- 📄 Export detailed PDF reports
- 🏡 Manage multiple farms
- ➕ Add custom products

The application runs locally and stores your farm data in a persistent JSON file.

---

## 🧠 Core Features

### 📋 Stock Management

- Add products from a built-in catalog
- Create **custom products**
- Set:
  - Quantity (L)
  - Maximum price (€/1000L)
  - Capacity per trip
  - Minimum stock to keep
- Enable/disable products for optimization
- Sort by:
  - Added
  - Stock
  - Money value
  - Name

---

### 🎯 Sales Objective Optimizer

Enter a target amount in € and the app will:

- Compute the **minimum number of trips**
- Maximize remaining stock when multiple optimal solutions exist
- Respect:
  - Minimum stock to keep
  - Capacity per trip
  - Product enable/disable state

This allows you to sell smarter and reduce unnecessary trips.

---

### 📄 PDF Report Export

Generate a professional PDF including:

- Current stock
- Total value
- Sales plan (if calculated)
- Farm name
- Timestamp

Reports are exported to:

```
<user_data_dir>/exports/
```

---

### 🏡 Multi-Farm Support

- Create multiple farms
- Switch between farms
- Rename / delete farms
- Each farm stores:
  - Stock
  - Custom products
  - Last calculated plan

---

## 🖥 Tech Stack

- **Python 3.12.4**
- **Kivy 2.3.1**
- **KivyMD 1.2.0**
- **ReportLab 4.4.9** (PDF export)
- JSON-based local storage

---

## 🚀 Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Kelpesito/farming-simulator-25-stock-calculator.git
cd farming-simulator-25-stock-calculator
```

### 2️⃣ Create virtual environment (recommended uv)

```bash
uv venv --python 3.12 --seed
venv\Scripts\activate     # Windows
```

### 3️⃣ Install dependencies

```bash
python -m pip install -r requirements.txt
```

---

## ▶️ Run the App

```bash
python main.py
```

---

## 📂 Project Structure

```
fsstock/
│
├── assets/
│   ├── catalog/catalog.json        # Base products information
│   ├── icons/                      # Icons (.png)
|   └── i18n/                       # Language dictionaries                    
│
├── core/
│   ├── optimizer.py                # Minimize number of trips, maximizing revenue
│   ├── storage.py                  # Loading and saving data
│   ├── pdf_export.py               # Export report into PDF
│   ├── models.py                   # Dataclasses 
│   ├── catalog.py                  # Import catalog.json
|   ├── find_stock.py               # Return a StockEntry given the product ID 
│   ├── get_product_name.py         # Get product name given the product ID
|   ├── money_value.py              # Get money value of a product, in €/L
|   ├── new_farm_id.py              # Generate a random ID for a new farm
|   ├── paths.py                    # Give the important path locations
|   └── i18n.py                     # Loads the language dictionary
|
├── ui/
│   ├── screens/
|   |   ├── add_product.py          # Screen to add a product into stock
|   |   ├── objective.py            # Screen to calculate the optimal trip plan
|   |   ├── settings.py             # Settings screen (to extract report, change farm, language...)   
|   |   └── stock.py                # Main screen: stock list
|   |
│   ├── widgets/navigation_bar.py   # Botton navigation bar
|   ├── colors/colors.py            # Colors list (hex)    
|   |
|   ├── root.py                     # Root Layout definition (screens)
│   └── app.py                      # Main application functionability
│
└── main.py                         # Entry point
```

---

## 📌 Current Status

- ✅ Desktop application (tested with Python 3.12.4)
- 🔄 Language selector implemented: Two languages (English & Spanish)
- 🪟 Windows standalone executable (.exe) — planned
- 📱 Android APK — planned

---

## 🌍 Future Roadmap

- [x] Full language support (EN / ES)
- [ ] Android APK build
- [ ] Windows standalone executable

---

## 💾 Data Storage

All farm data is saved locally in:

```
- <user_data_dir>/fs_stock_state.json
- <user_data_dir>/fs_stock_settings.json
```

Each farm stores:
- Name
- Stock entries
- Custom products
- Last optimization plan

---

## 👨‍🌾 About

This tool is designed to help Farming Simulator 25 players make smarter selling decisions and reduce unnecessary trips.

Efficient farming starts with efficient logistics 🚜💰
