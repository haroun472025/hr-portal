from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# عنوان Manager API (اللي عندك)
MANAGER_BASE_URL = "https://ahtelecom.eu-west-1.manager.io/api2"
API_KEY = os.getenv("API_KEY")  # التوكين هيجي من Variables في Railway

if not API_KEY:
    print("تحذير: API_KEY مش موجود! ضيفه في Variables.")

HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

# دالة لتنظيف البيانات المالية (تشيل balance, status, controlAccount)
def sanitize_employee(emp):
    if isinstance(emp, dict):
        # احذف الحقول الحساسة
        for field in ["balance", "status", "controlAccount"]:
            if field in emp:
                del emp[field]
        # لو في array من الموظفين، نظّف كل واحد
        if "employees" in emp:
            emp["employees"] = [sanitize_employee(e) for e in emp["employees"]]
    return emp

# الصفحة الرئيسية (للـ HR) - محدّثة لترحيب أفضل
@app.route("/")
def home():
    return jsonify({
        "message": "بوابة HR شغالة ✅",
        "endpoints": {
            "GET /employees": "جلب قائمة الموظفين (من غير بيانات مالية)",
            "POST /employees": "إضافة موظف جديد"
        },
        "instructions": "جرب /employees في نهاية الرابط لجلب الموظفين!"
    })

# جلب قائمة الموظفين (GET /employees)
@app.route("/employees", methods=["GET"])
def get_employees():
    skip = request.args.get("skip", 0, type=int)
    page_size = request.args.get("pageSize", 50, type=int)
    
    url = f"{MANAGER_BASE_URL}/employees?skip={skip}&pageSize={page_size}"
    response = requests.get(url, headers=HEADERS, timeout=10)
    
    if response.status_code != 200:
        return jsonify({"error": f"فشل في جلب البيانات: {response.status_code} - تأكد من API_KEY"}), 500
    
    data = response.json()
    # نظّف البيانات قبل الإرجاع (شيل الأرقام المالية)
    sanitized_data = sanitize_employee(data)
    return jsonify(sanitized_data)

# إضافة موظف جديد (POST /employees)
@app.route("/employees", methods=["POST"])
def add_employee():
    employee_data = request.json
    if not employee_data:
        return jsonify({"error": "البيانات مطلوبة (مثل name, code)"}), 400
    
    url = f"{MANAGER_BASE_URL}/employees"
    response = requests.post(url, headers=HEADERS, json=employee_data, timeout=10)
    
    if response.status_code not in (200, 201):
        return jsonify({"error": f"فشل في إضافة الموظف: {response.text} - تأكد من API_KEY"}), 500
    
    created = response.json()
    # نظّف الرد
    sanitized_created = sanitize_employee(created)
    return jsonify({
        "message": "تم إضافة الموظف بنجاح!",
        "employee": sanitized_created
    }), 201

# تشغيل السيرفر (مع Port من Railway)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
