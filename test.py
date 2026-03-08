import requests

# ทดสอบแบบ Dataset จริง (ยาวเหมือน user_inputs จริงๆ)
res = requests.post("http://127.0.0.1:8000/predict", json={
    "user_inputs": "BR-1817' OR '1'='1 small_airport Cloud County Health Center -0.141092 -87.820918",
    "query_template_id": "airport-I1"
})
print("=== Attack Payload (realistic) ===")
print(res.json())

# Normal
res2 = requests.post("http://127.0.0.1:8000/predict", json={
    "user_inputs": "BR-1817 small_airport Cloud County Health Center -0.141092 -87.820918",
    "query_template_id": "airport-I1"
})
print("\n=== Normal Payload ===")
print(res2.json())