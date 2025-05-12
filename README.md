# 💬 Fraud Detection UPI Chatbot 🚨

An intelligent, machine learning-based chatbot that helps users detect potentially fraudulent UPI transactions in real-time. It utilizes an ensemble of ML models to analyze transaction amount and time data, offering instant feedback and downloadable fraud reports.

---

## 🚀 Overview

With the rise in UPI-based digital payments, frauds have become more frequent and sophisticated. Traditional detection methods rely on fixed rules or post-transaction checks, which are reactive and limited. This chatbot provides a **real-time, proactive fraud detection system** using machine learning, accessible via a friendly chatbot interface.

---

## 🎯 Features

- 🔍 **Fraud Detection**: Real-time prediction using ensemble ML models.
- 💬 **Chatbot UI**: Easy-to-use conversational interface for input.
- 🧠 **ML Models Used**:
  - Isolation Forest
  - One-Class SVM
  - XGBoost
- 🧾 **PDF Report**: Downloadable prediction summary.
- ⚡ **Fast API Responses**: Backend served via Flask.
- 📊 **Synthetic Data Generation**: Trainable and extendable with custom data.

---

## 🧠 Tech Stack

| Layer        | Technology                     |
| ------------ | ------------------------------ |
| Frontend     | HTML, CSS, JavaScript, Flatpickr |
| Backend      | Python, Flask                  |
| ML Models    | scikit-learn, XGBoost          |
| Data Handling| Pandas, NumPy                  |
| PDF Export   | html2pdf.js                    |

---

## 🛠️ Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/fraud-detection-upi-chatbot.git
   cd fraud-detection-upi-chatbot
