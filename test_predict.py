import requests
import json

url = "http://localhost:5000/api/predict"

test_data_1 = {
    "age": "25",
    "sex": "Female",
    "restingBP": "120",
    "cholesterol": "150",
    "maxHR": "180",
    "oldpeak": "0",
    "fastingBS": "0",
    "chestPainType": "ATA",
    "restingECG": "Normal",
    "stSlope": "Up",
    "exerciseAngina": "N"
}

test_data_2 = {
    "age": "65",
    "sex": "Male",
    "restingBP": "180",
    "cholesterol": "300",
    "maxHR": "100",
    "oldpeak": "3.5",
    "fastingBS": "1",
    "chestPainType": "ASY",
    "restingECG": "ST",
    "stSlope": "Flat",
    "exerciseAngina": "Y"
}

print("Testing 1 (Low Risk expected):")
try:
    r1 = requests.post(url, json=test_data_1)
    print(r1.json())
except Exception as e:
    print(e)

print("\nTesting 2 (High Risk expected):")
try:
    r2 = requests.post(url, json=test_data_2)
    print(r2.json())
except Exception as e:
    print(e)
