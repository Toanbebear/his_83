# Hướng dẫn sử dụng

- Clone addons_base vao workspace, sau đó đổi lại addons thành addons_base trong phần config parameter khi chạy
```
    --addons-path="addons_base, addons_custom"
```
 - Hoặc đổi tên addons_base thành addons trong workspace
 
# Quy trình commit code
Khi update code trong addons_base, phải đẩy code lên branch của dev trước sau đó mới merge vào dev, rồi từ dev merge vào master

Ví dụ, developer thond, cần update 1 issue trong addons_base:
   - 1. Sửa code
   - 2. Commit lên nhánh thond
   - 3. Push lên nhánh thond
   - 4. Yêu cầu review code
   - 5. Sau khi revewer đã xong, merge vào nhánh dev
   - 6. Test lại issue
   - 7. Vấn đề giải quyết xong thì merge vào master
