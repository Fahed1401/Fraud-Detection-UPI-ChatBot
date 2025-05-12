# 💬 Fraud Detection UPI Chatbot 🚨

## Abstract

The rapid adoption of digital payment systems like the Unified Payments Interface (UPI) has revolutionized financial transactions in India and beyond. However, this convenience also increases exposure to cyber fraud. This project introduces a UPI Fraud Detection Chatbot—an intelligent, real-time, ML-powered tool designed to assist both users and institutions in detecting potentially fraudulent transactions.

Using an ensemble of machine learning models—Isolation Forest, One-Class SVM, and XGBoost—the system analyzes transaction amount and timestamp data to flag anomalies. A majority-vote mechanism ensures robust fraud prediction while minimizing false positives and negatives.

The architecture includes a Flask backend and a responsive web-based frontend using HTML, CSS, JavaScript, and Flatpickr. The chatbot interface allows users to input transaction details and receive immediate fraud risk assessments. A PDF report generation module further enhances the system's utility by providing downloadable summaries.
This project bridges advanced analytics with intuitive design to offer a scalable solution for proactive digital transaction security.

---

## 🚀 Introduction

The project's goal is to develop a real-time fraud detection system for UPI transactions using machine learning. Unlike rule-based systems that react after fraud occurs, this system proactively identifies suspicious activity before the transaction completes.

Leveraging unsupervised and supervised learning techniques, the system detects anomalies in transaction data without relying on static fraud rules. The solution is packaged in an easy-to-use chatbot interface, ensuring accessibility for both tech-savvy users and laypersons.

Educationally, the project serves as a complete ML deployment case study—from data generation and model training to API integration and frontend interfacing.

---

## ❓Problem Statement

Despite the growth of UPI transactions, proactive fraud detection remains inaccessible to individual users. Existing solutions are mostly internal to banks, rule-based, and reactive.

This project addresses:
- Lack of real-time, user-facing fraud assessment tools.
- Inflexibility of static fraud rules against evolving scam tactics.
- Absence of lightweight, deployable ML-driven fraud detection systems.
 
The chatbot offers fraud prediction in real-time, empowering users to cancel suspicious transactions before confirmation. Its architecture is designed for extensibility, making it suitable for fintech startups or community-level deployment.

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

## 📌 Architecture
- Frontend (HTML, JS)
  - Collects user input (amount, timestamp) via chatbot UI
  - Sends data to backend via HTTP POST
- Backend (Flask)
  - Receives and parses input
  - Routes to ML prediction function
  - Returns prediction ("Fraud" / "Not Fraud")
- ML Engine (Ensemble Model)
  - Isolation Forest: Unsupervised anomaly detection
  - One-Class SVM: Detects deviations from normal
  - XGBoost: Supervised classification
  - Majority Voting: Final decision output
- Output
  - JSON response displayed on frontend
  - Optional downloadable PDF report

---

## 🛠️ Installation & Setup

1. **Clone the repo**  
   ```bash
   git clone https://github.com/yourusername/fraud-detection-upi-chatbot.git
   cd fraud-detection-upi-chatbot
