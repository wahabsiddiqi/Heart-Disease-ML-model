import json
import os
import joblib
import pandas as pd
from http.server import BaseHTTPRequestHandler

# Load models outside the handler to take advantage of Vercel container caching
ROOT_DIR = os.path.join(os.path.dirname(__file__), '..')
MODEL_PATH = os.path.join(ROOT_DIR, 'KNN_heart.pkl')
SCALER_PATH = os.path.join(ROOT_DIR, 'scaler.pkl')

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    model = None
    scaler = None
    print("Error loading models:", e)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        try:
            if model is None or scaler is None:
                self.wfile.write(json.dumps({"error": "Model files could not be loaded."}).encode('utf-8'))
                return

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
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
            
            # One-Hot Encoding matching the 15 features exactly:
            # ['Age', 'RestingBP', 'Cholesterol', 'FastingBS', 'MaxHR', 'Oldpeak', 
            #  'Sex_M', 'ChestPainType_ATA', 'ChestPainType_NAP', 'ChestPainType_TA', 
            #  'RestingECG_Normal', 'RestingECG_ST', 'ExerciseAngina_Y', 'ST_Slope_Flat', 'ST_Slope_Up']
            
            sex_m = 1 if sex == 'Male' or sex == 'M' else 0
            
            cp_ata = 1 if chest_pain == 'ATA' else 0
            cp_nap = 1 if chest_pain == 'NAP' else 0
            cp_ta = 1 if chest_pain == 'TA' else 0
            
            ecg_normal = 1 if resting_ecg == 'Normal' else 0
            ecg_st = 1 if resting_ecg == 'ST' else 0
            
            angina_y = 1 if exercise_angina == 'Y' else 0
            
            slope_flat = 1 if st_slope == 'Flat' else 0
            slope_up = 1 if st_slope == 'Up' else 0

            # Create DataFrame with the exact column names expected by scaler and model
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
            # prediction will be an array like [1] or [0]
            result = int(prediction[0])
            
            # Probability if applicable
            prob = None
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba(input_scaled)
                prob = float(probabilities[0][1]) * 100 # percentage of being positive
            
            response = {
                "success": True,
                "prediction": result,
                "probability": prob
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            error_response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
