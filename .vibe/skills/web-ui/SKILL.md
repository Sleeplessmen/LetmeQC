---
name: web-ui
description: >-
  Reusable skill and instructions for building a modern, responsive Web UI dashboard for the LetmeQC 2D Bbox and Segmentation Quality Control tool, referencing the provided UI layout structure (sidebar navigation, summary metric cards, error type distribution bar chart, daily trend bar chart, labeler accuracy table, and live status footer). Use when asked to design, code, or generate Web UI components/dashboard for LetmeQC or CVAT QC tool.
---

# Build LetmeQC Web UI Dashboard

Skill này cung cấp hướng dẫn và cấu trúc mã nguồn tiêu chuẩn để xây dựng giao diện Web UI trực quan, hiện đại cho công cụ LetmeQC (Auto QC 2D Bbox & Segmentation) dựa trên giao diện Dashboard mẫu.

## 🎯 Mục tiêu Giao diện

- **Tính trực quan**: Hiển thị nhanh các chỉ số chất lượng gán nhãn (tỉ lệ đạt, % box đúng, số lỗi chắc chắn/không chắc chắn, issue đã đẩy lên CVAT).
- **Phân tích lỗi**: Biểu đồ phân bố loại lỗi hay gặp (Thiếu, Sai kích thước, Sai nhãn, Thừa, Trùng) và xu hướng theo ngày.
- **Quản lý Labeler**: Bảng thống kê chi tiết hiệu suất từng annotator/labeler (số lần review, số job, % box đúng, tỉ lệ đạt, số lỗi, thời gian gần nhất).
- **Kết nối CVAT**: Trạng thái kết nối real-time tới CVAT server và thông tin thiết bị (GPU/CPU).

## 📐 Cấu trúc Giao diện (Layout Blueprint)

### 1. Sidebar Navigation (Bên trái)

**Header**: Logo & Title QC nhãn 2D.

**Menu Links**:

- Tổng quan (Active)
- Review job
- Lịch sử
- Guideline
- Kết nối CVAT
- Cài đặt

**Trạng thái Footer**:

- Trạng thái CVAT Server (VD: cvat-test.vantixapps.net - Online)
- GPU/Hardware Info (VD: NVIDIA GeForce RTX 4050...)
- User profile badge (admin - Admin).

### 2. Header Filter (Góc trên bên phải)

Bộ lọc thời gian: 7 ngày | 30 ngày | 90 ngày.

### 3. Summary Metric Cards (Các thẻ chỉ số chính)

- **Lần review xong**: Tổng số lượt QC hoàn thành.
- **Tỉ lệ đạt**: % job vượt qua ngưỡng QC (ngưỡng mẫu: 97%).
- **% box đúng trung bình**: Tỉ lệ phần trăm box gán chuẩn.
- **Lỗi chắc chắn / 4 không chắc chắn**: Phân loại mức độ nghiêm trọng của lỗi.
- **Issue đã đẩy lên CVAT**: Số lượng issue được tự động đăng lên CVAT qua API.
- **Tỉ lệ tool nhầm**: Tỉ lệ báo lỗi sai của QC engine.

### 4. Charts & Analytics (Khu vực biểu đồ)

- **Loại lỗi hay gặp**: Horizontal Bar Chart liệt kê các lỗi (Thiếu, Sai kích thước, Sai nhãn, Thừa, Trùng).
- **Xu hướng theo ngày**: Vertical Bar Chart theo dõi tỉ lệ % box đúng qua từng ngày.

### 5. Labeler Performance Table (Bảng thống kê Labeler)

**Columns**: LABELER, SỐ LẦN REVIEW, SỐ JOB, % BOX ĐÚNG TB, TỈ LỆ ĐẠT, LỖI / KHÔNG CHẮC, GẦN NHẤT.

## 💻 Công nghệ Đề xuất (Tech Stack Options)

### Option A (Nhanh & Gọn với Streamlit/Gradio - Cho Python Backend)

Dùng streamlit với custom CSS hoặc nicegui để tích hợp trực tiếp vào codebase Python LetmeQC hiện tại.

### Option B (Modern Web Framework - Production Ready)

- **Frontend**: React (Next.js) / Vue 3 / Vite.
- **UI Component Library**: Shadcn/UI + TailwindCSS hoặc Ant Design / Mantine.
- **Charts**: Recharts / Chart.js / Tremor.

## 🛠️ Code Mẫu Nhanh (React + TailwindCSS + Recharts)

```typescript
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const errorData = [
  { name: 'Thiếu', count: 7 },
  { name: 'Sai kích thước', count: 2 },
  { name: 'Sai nhãn', count: 1 },
  { name: 'Thừa', count: 1 },
  { name: 'Trùng', count: 1 },
];

export default function QCDashboard() {
  return (
    <div className="flex h-screen bg-slate-50 text-slate-800">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col justify-between p-4">
        <div>
          <h1 className="text-xl font-bold mb-8 flex items-center gap-2">
            <span className="bg-blue-600 p-2 rounded">QC</span> QC nhãn 2D
          </h1>
          <nav className="space-y-2">
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg bg-blue-600/20 text-blue-400 font-medium">Tổng quan</a>
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-400">Review job</a>
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-400">Lịch sử</a>
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-400">Guideline</a>
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-400">Kết nối CVAT</a>
            <a href="#" className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-800 text-slate-400">Cài đặt</a>
          </nav>
        </div>
        <div className="text-xs text-slate-400 space-y-2 border-t border-slate-800 pt-4">
          <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> cvat-test.vantixapps.net</div>
          <div className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-emerald-500"></span> NVIDIA RTX 4050</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold">Tổng quan</h2>
            <p className="text-sm text-slate-500">Chất lượng nhãn qua các lần review: tỉ lệ đạt, loại lỗi hay gặp, từng labeler.</p>
          </div>
          <div className="flex bg-slate-200 p-1 rounded-lg text-sm">
            <button className="px-3 py-1 rounded">7 ngày</button>
            <button className="px-3 py-1 rounded bg-white shadow font-semibold">30 ngày</button>
            <button className="px-3 py-1 rounded">90 ngày</button>
          </div>
        </div>

        {/* Metric Cards Grid */}
        <div className="grid grid-cols-6 gap-4 mb-6">
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold">1</span>
            <p className="text-xs text-slate-500 mt-1">Lần review xong · 30 ngày</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold text-red-500">0.0%</span>
            <p className="text-xs text-slate-500 mt-1">Tỉ lệ đạt (ngưỡng 97%)</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold">94.4%</span>
            <p className="text-xs text-slate-500 mt-1">% box đúng trung bình</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold text-red-500">8</span>
            <p className="text-xs text-slate-500 mt-1">Lỗi chắc chắn · 4 không chắc</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold">0</span>
            <p className="text-xs text-slate-500 mt-1">Issue đã đẩy lên CVAT</p>
          </div>
          <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
            <span className="text-3xl font-bold">0.0%</span>
            <p className="text-xs text-slate-500 mt-1">Tỉ lệ tool nhầm · 0 lỗi</p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 className="font-semibold mb-4">Loại lỗi hay gặp</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={errorData}>
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={100} tickLine={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
            <h3 className="font-semibold mb-4">Xu hướng theo ngày</h3>
            <div className="h-48 flex items-center justify-center text-slate-400">
              Biểu đồ xu hướng % box đúng
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
```
