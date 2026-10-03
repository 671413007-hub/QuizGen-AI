# QuizGen AI – ระบบสร้างข้อสอบอัตโนมัติด้วย AI

**QuizGen AI** คือระบบที่ช่วยให้ผู้ใช้สามารถนำเนื้อหาบทเรียนภาษาไทยเข้ามา แล้วให้ AI วิเคราะห์เนื้อหาเพื่อสร้างข้อสอบพร้อมเฉลยและคำอธิบายโดยอัตโนมัติ

---

## 🎯 วัตถุประสงค์ของโปรเจกต์
1. ช่วยผู้สอนและผู้เรียนประหยัดเวลาในการสร้างแบบทดสอบจากเนื้อหาบทเรียนภาษาไทย
2. มีระบบทดสอบความรู้และตรวจคำตอบพร้อมแสดงผลวิเคราะห์ความเข้าใจทันที
3. ช่วยพัฒนาการเรียนรู้เฉพาะบุคคล (Personalized Learning) ผ่านการสร้างข้อสอบซ่อมเสริมเฉพาะจุดที่ผู้เรียนยังไม่เข้าใจ

---

## 🏗️ โครงสร้างโฟลเดอร์โปรเจกต์
```text
QuizGen-AI/
├── frontend/                  # ฝั่งหน้าบ้าน (HTML, CSS, JavaScript)
│   ├── index.html             # หน้าเว็บหลัก
│   ├── css/
│   │   └── style.css          # ไฟล์จัดสไตล์ (Responsive)
│   └── js/
│       └── app.js             # ควบคุมการทำงานของหน้าเว็บ
│
├── backend/                   # ฝั่งหลังบ้าน (Python FastAPI REST API)
│   ├── app/
│   │   ├── main.py            # ไฟล์หลักสำหรับรัน FastAPI Application
│   │   ├── api/               # จัดการ Routing / Endpoints
│   │   │   └── health.py
│   │   ├── services/          # Business logic ของระบบ
│   │   │   └── health_service.py
│   │   ├── models/            # Data Models
│   │   └── schemas/           # Pydantic Schemas สำหรับตรวจสอบข้อมูล
│   │       └── health.py
│   └── requirements.txt       # รายการ Library ของ Backend
│
├── docs/                      # เอกสารประกอบการพัฒนา (Requirement & Architecture)
├── .gitignore
└── README.md
```

---

## 💻 วิธีการรันโปรเจกต์ (บน Windows / PowerShell)

### 1. วิธีรัน Backend (FastAPI)
เปิด PowerShell และไปที่โฟลเดอร์ `backend`:
```powershell
# 1. เข้าไปที่โฟลเดอร์ backend
cd backend

# 2. สร้าง Virtual Environment (ทำครั้งแรก)
python -m venv venv

# 3. เปิดใช้งาน Virtual Environment
.\venv\Scripts\Activate.ps1

# 4. ติดตั้ง Package ที่จำเป็น
pip install -r requirements.txt

# 5. เริ่มรันเซิร์ฟเวอร์
uvicorn app.main:app --reload
```
- ตรวจสอบสถานะ API ได้ที่: `http://localhost:8000/api/health`
- หน้า API Documentation (Swagger UI): `http://localhost:8000/docs`

---

### 2. วิธีรัน Frontend
เนื่องจาก Frontend พัฒนาด้วย Pure HTML/CSS/JavaScript สามารถเปิดใช้งานได้ง่าย:
- **วิธีที่ 1 (สะดวกที่สุด):** ดับเบิลคลิกเปิดไฟล์ `frontend/index.html` บนเว็บเบราว์เซอร์ได้ทันที
- **วิธีที่ 2 (ผ่าน Live Server / HTTP Server):** ใช้ extension เช่น Live Server ใน VS Code หรือสั่งผ่าน Python:
```powershell
cd frontend
python -m http.server 3000
```
เปิดเบราว์เซอร์ไปที่ `http://localhost:3000`
