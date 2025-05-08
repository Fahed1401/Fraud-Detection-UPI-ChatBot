from flask import Flask, request, jsonify, send_from_directory
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from xgboost import XGBClassifier
from sklearn.feature_selection import SelectKBest, f_classif
from datetime import datetime
from generate_transactions import generate_transactions

app = Flask(__name__, static_folder='../frontend', static_url_path='/')

# Generate transactions if CSV missing or too small
csv_path = os.path.join(os.path.dirname(__file__), "transactions.csv")
if not os.path.exists(csv_path) or os.path.getsize(csv_path) < 1000:
    generate_transactions()

# Global model variables
isolation_forest = None
svm_model = None
selector = None
xgb_model = None

def train_models():
    global isolation_forest, svm_model, selector, xgb_model
    data = generate_transactions(num_transactions=20000)
    if data is not None:
        data.dropna(inplace=True)
        data['Hour'] = pd.to_datetime(data['Timestamp']).dt.hour
        features = ['Amount (INR)', 'Hour']

        # Adjust contamination to match actual fraud ratio and increase n_estimators
        isolation_forest = IsolationForest(n_estimators=200, contamination=0.03, random_state=42)
        isolation_forest.fit(data[features])

        # Adjust SVM parameters for better normal transaction detection
        svm_model = OneClassSVM(nu=0.01, kernel="rbf", gamma='scale')
        svm_model.fit(data[features])

        # Use isolation forest predictions for training XGBoost
        data['Synthetic_Fraud_Label'] = (data['Amount (INR)'] > 8000).astype(int)
        X = data[features]
        y = data['Synthetic_Fraud_Label']

        selector = SelectKBest(score_func=f_classif, k=2)
        X_reduced = selector.fit_transform(X, y)

        # Adjust XGBoost parameters for better balance
        xgb_model = XGBClassifier(
            use_label_encoder=False,
            eval_metric='logloss',
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            scale_pos_weight=20,
            min_child_weight=5,
            random_state=42
        )
        xgb_model.fit(X_reduced, y)

    else:
        # If data is None, set models to None to avoid NoneType errors
        globals()['isolation_forest'] = None
        globals()['svm_model'] = None
        globals()['selector'] = None
        globals()['xgb_model'] = None

def preprocess_transaction(amount, timestamp):
    try:
        # Remove currency symbol and commas, convert to float
        if isinstance(amount, str):
            amount = amount.replace('₹', '').replace(',', '').strip()
        amount = float(amount)
        
        # More robust timestamp parsing
        try:
            hour = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").hour
        except ValueError:
            # Try alternative format if first attempt fails
            hour = datetime.strptime(timestamp, "%Y-%m-%d %H:%M").hour
            
        return np.array([[amount, hour]])
    except Exception as e:
        raise ValueError(f"Error processing transaction: {str(e)}")

@app.route('/api/check_fraud', methods=['POST'])
def check_fraud():
    global isolation_forest, svm_model, selector, xgb_model
    data = request.json
    amount = data.get('amount')
    timestamp = data.get('timestamp')
    if amount is None or timestamp is None:
        return jsonify({'error': 'Missing amount or timestamp'}), 400

    if isolation_forest is None or svm_model is None or selector is None or xgb_model is None:
        return jsonify({'error': 'Models are not loaded yet'}), 500

    try:
        features = preprocess_transaction(amount, timestamp)
        
        # Adjust fraud detection logic
        iso_pred = isolation_forest.predict(features)[0]
        iso_result = 'Normal' if iso_pred == 1 else 'Potential Fraud'

        svm_pred = svm_model.predict(features)[0]
        svm_result = 'Normal' if svm_pred == 1 else 'Potential Fraud'

        features_reduced = selector.transform(features)
        xgb_pred = xgb_model.predict(features_reduced)[0]
        xgb_result = 'Potential Fraud' if xgb_pred == 1 else 'Normal'

        # Implement majority voting
        fraud_votes = sum([
            1 if result == 'Potential Fraud' else 0
            for result in [iso_result, svm_result, xgb_result]
        ])
        
        # Only mark as fraud if at least 2 models agree
        fraud_detected = fraud_votes >= 2

        return jsonify({
            'isolation_forest': iso_result,
            'svm': svm_result,
            'xgboost': xgb_result,
            'fraud_detected': fraud_detected
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/report')
def serve_report():
    return send_from_directory(app.static_folder, 'report.html')

if __name__ == '__main__':
    train_models()
    app.run(debug=True, host='0.0.0.0', port=5001)