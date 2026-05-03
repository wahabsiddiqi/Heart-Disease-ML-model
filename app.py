import json
import os
import joblib
import pandas as pd
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Attempt to connect to Vercel KV Database (Redis)
try:
    import redis
    kv_url = os.environ.get("KV_URL")
    if kv_url:
        r = redis.from_url(kv_url)
    else:
        r = None
except ImportError:
    r = None

# Load models
ROOT_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(ROOT_DIR, 'KNN_heart.pkl')
SCALER_PATH = os.path.join(ROOT_DIR, 'scaler.pkl')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    print("Error loading models:", e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/save-user', methods=['POST'])
def save_user():
    data = request.json
    name = data.get('name')
    age = data.get('age')
    gender = data.get('gender')

    if not name or not age or not gender:
        return jsonify({'message': 'Missing required fields: name, age, or gender.'}), 400

    new_user = {
        'id': str(datetime.now().timestamp()),
        'name': name,
        'age': age,
        'gender': gender,
        'timestamp': datetime.now().isoformat()
    }

    # If Vercel KV is configured, save there (Persistent!)
    if r:
        try:
            r.lpush("users_data", json.dumps(new_user))
            return jsonify({'message': 'User saved permanently to Database', 'user': new_user}), 200
        except Exception as e:
            print("Redis error:", e)
            return jsonify({'message': 'Error saving user to database.'}), 500

    # Fallback: Save to local users.json (Only works on Local PC, not Vercel)
    file_path = os.path.join(ROOT_DIR, 'users.json')
    
    users = []
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                users = json.load(f)
    except Exception as read_error:
        print("Could not read users.json, starting fresh.", read_error)

    users.append(new_user)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
    except Exception as write_error:
        print("Could not write to users.json", write_error)
        return jsonify({'message': 'Error saving user locally.'}), 500

    return jsonify({'message': 'User saved locally', 'user': new_user}), 200

@app.route('/api/predict', methods=['POST'])
def predict():
    if model is None or scaler is None:
        return jsonify({"success": False, "error": "Model files could not be loaded."}), 500

    try:
        data = request.json
        
        # Extract features (defaulting to 0 if missing)
        age = float(data.get('age', 0))
        sex = data.get('sex', 'M')
        chest_pain = data.get('chestPainType', 'ASY')
        resting_bp = float(data.get('restingBP', 120))
        cholesterol = float(data.get('cholesterol', 200))
        fasting_bs = float(data.get('fastingBS', 0))
        resting_ecg = data.get('restingECG', 'Normal')
        max_hr = float(data.get('maxHR', 150))
        exercise_angina = data.get('exerciseAngina', 'N')
        oldpeak = float(data.get('oldpeak', 0.0))
        st_slope = data.get('stSlope', 'Flat')
        
        sex_m = 1 if sex in ['Male', 'M'] else 0
        
        cp_ata = 1 if chest_pain == 'ATA' else 0
        cp_nap = 1 if chest_pain == 'NAP' else 0
        cp_ta = 1 if chest_pain == 'TA' else 0
        
        ecg_normal = 1 if resting_ecg == 'Normal' else 0
        ecg_st = 1 if resting_ecg == 'ST' else 0
        
        angina_y = 1 if exercise_angina == 'Y' else 0
        
        slope_flat = 1 if st_slope == 'Flat' else 0
        slope_up = 1 if st_slope == 'Up' else 0

        # Create DataFrame with the exact column names expected
        input_dict = {
            'Age': [age],
            'RestingBP': [resting_bp],
            'Cholesterol': [cholesterol],
            'FastingBS': [fasting_bs],
            'MaxHR': [max_hr],
            'Oldpeak': [oldpeak],
            'Sex_M': [sex_m],
            'ChestPainType_ATA': [cp_ata],
            'ChestPainType_NAP': [cp_nap],
            'ChestPainType_TA': [cp_ta],
            'RestingECG_Normal': [ecg_normal],
            'RestingECG_ST': [ecg_st],
            'ExerciseAngina_Y': [angina_y],
            'ST_Slope_Flat': [slope_flat],
            'ST_Slope_Up': [slope_up]
        }
        
        input_df = pd.DataFrame(input_dict)
        
        # Scale features
        input_scaled = scaler.transform(input_df)
        
        # Predict
        prediction = model.predict(input_scaled)
        result = int(prediction[0])
        
        # Probability if applicable
        prob = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(input_scaled)
            prob = float(probabilities[0][1]) * 100 # percentage of being positive
        
        return jsonify({
            "success": True,
            "prediction": result,
            "probability": prob
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

if __name__ == '__main__':
    # Get port from environment variable or use 5000 as fallback
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
