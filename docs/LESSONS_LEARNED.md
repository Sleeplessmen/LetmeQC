# Bài Học Kinh Nghiệm

Tài liệu tổng hợp các bài học rút ra từ quá trình triển khai và vận hành hệ thống LetmeQC.

---

## Bảng Tóm Tắt

| ID  | Ngày | Chủ đề | Vấn đề | Chi tiết | Bài học rút ra |
| --- | ---- | ------ | ------ | -------- | -------------- |

---

## Hướng dẫn Sử dụng

1. **Thêm bài học mới**: Điền thông tin vào hàng trống hoặc thêm hàng mới
2. **ID**: Số thứ tự tự động (1, 2, 3,...)
3. **Ngày**: Định dạng YYYY-MM-DD
4. **Chủ đề**: Lĩnh vực (VD: CVAT API, QC Rules, Performance, vv)
5. **Vấn đề**: Mô tả ngắn gọn vấn đề gặp phải
6. **Chi tiết**: Mô tả chi tiết vấn đề
7. **Bài học rút ra**: Giải pháp/điều cần ghi nhớ

---

## Ví dụ Điền

| ID  | Ngày       | Chủ đề         | Vấn đề                                   | Chi tiết                                       | Bài học rút ra                                                     |
| --- | ---------- | -------------- | ---------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------ |
| 1   | 2026-10-14 | CVAT API       | Lỗi 401 Unauthorized                     | Không truyền X-Organization header khi gọi API | Luôn truyền header `X-Organization: <org_slug>` cho tất cả request |
| 2   | 2026-10-14 | Issue Position | Box lỗi không hiển thị trên UI           | Truyền position=[0,0,0,0] thay vì tọa độ thực  | Tính position dựa trên loại lỗi theo bảng quy định                 |
| 3   | 2026-10-14 | Job Status     | Không thể cập nhật status sau khi submit | Sử dụng token của Assignee (Annotator)         | Phải dùng token có quyền Maintainer/Owner/Reviewer                 |

---

_Tài liệu được cập nhật liên tục trong quá trình phát triển hệ thống LetmeQC_
