# System Architecture - QuizGen AI

## 1. Overview Architecture (Decoupled Client-Server)
ระบบถูกออกแบบโดยแยกฝั่ง Frontend และ Backend ออกจากกันอย่างชัดเจน เพื่อความยืดหยุ่นและการพัฒนาที่ง่ายสำหรับ Mini Project:

```
[ Frontend: React / Web App ]
            │
            │ HTTP / JSON REST API
            ▼
[ Backend: Python FastAPI ]
  ├── Routers (Endpoints)
  ├── Quiz Service (Business Logic & Scoring)
  └── AI Provider Layer (Interface)
            │
            ├── [ Mock AI Service (For Development & Testing) ]
            └── [ Future: AI for Thai / ThaiLLM API ]
```

## 2. Component Responsibilities
- **Frontend (`/frontend`):**
  - แสดงผลหน้าจอสร้างข้อสอบ, ทำข้อสอบ, และผลการวิเคราะห์
  - จัดการ Client State และการสื่อสารกับ Backend ผ่าน REST API
- **Backend (`/backend`):**
  - ตรวจสอบความถูกต้องของข้อมูล (Data Validation)
  - ประมวลผลคำตอบ คำนวณคะแนน และวิเคราะห์ข้อผิดพลาด
  - เป็นตัวกลางในการสื่อสารกับ AI Engine ในอนาคต
- **Docs (`/docs`):**
  - เก็บเอกสารความต้องการ (Requirement) และสถาปัตยกรรม (Architecture)
