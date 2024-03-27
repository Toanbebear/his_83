# Cài pip: 

```
sudo docker exec 83kangnam84_odoo12_1 pip3 install
sudo docker exec 83kangnam84_odoo12_1 pip3 install openpyxl
sudo docker exec 83kangnam84_odoo12_1 pip3 install wheel openpyxl
sudo docker exec 83kangnam84_odoo12_1 pip3 install xlrd wheel python-docx openpyxl
```

#Cài đặt
Cài module:

1. SCI Health All In One (shealth_all_in_one)
2. Report Pdf Preview (Để preview các phiếu trước khi in) hoặc Report Pdf Print (in phiếu)
3. web_groupby_expand: expand all group tree view
3. mass_editing: sửa nhanh nhiều bản ghi ở tree view
4. odoo_web_login: chỉnh sửa trang đăng nhập

#Cấu hình: Thiết lập -> Thiết tập chung
1. Người dùng -> Quyền truy cập: để mặc định là ko có quyền gì (ngoài excel template), set Múi giờ, set default partner
2. Tài khoản khách hàng: -> On invitation
3. Sản phẩm -> Đơn vị sản phẩm
4. Truy vết -> Số Lô seri, Display Lots & Serial Numbers, Ngày hết hạn
5. Kho hàng -> Nhiều địa điệm; Các tuyến nhiều bước
6. Kỹ thuật:	Độ chính xác thập phân => Product Unit of Measure => 2
                Hành động của sổ: Tìm hành động "Gửi biên nhận thanh toán" => thêm group admin bệnh viện ở tab Bảo mật
7. Công ty => CTCP BVTM KANGNAM HÀ NỘI và chi tiết thông tin
#Cấu hình địa điểm kho
- Đổi tên WH/Stock => WH/Kho Dược; Vendor -> Nhà cung cấp;Customer -> Khách hàng
- Nếu chốt chạy xuất kho theo FEFO thì cấu hình các tủ trực FEFO
- Import data (FILE EXCEL)
- Import Đơn vị Đo lường sản phẩm (đơn vị, thể tích, khối lượng): (Kho -> Cấu hình)
Trước khi import khối lượng cần sửa đơn vị kg thành đơn vị lớn hơn đơn vị gốc
- Import user: (Thiết lập -> Người dùng)
- Import chức vụ: bật debug-> mở giao diện-> hr.job (tree)
- Import bác sĩ
- Import data dân tộc, ngoại kiều, mã icd10 (Bệnh viện -> Cấu hình)
- Import thuốc, vật tư(Bệnh viện -> Kho Dược -> Thuốc, vật tư)
- Import danh sách dịch vụ (Bệnh viện -> Cấu hình -> Dịch vụ)
- Cấu hình các xn, cđha, bom, đơn thuốc cho từng dịch vụ (Bệnh viện -> Cấu hình -> Dịch vụ)
- Cấu hình hướng dẫn sau dịch vụ
- Vào Bệnh viện => Cấu hình => Cơ sở y tế => Thêm người dùng được phép truy cập (ĐANG TẮT - BAO GIỜ VẬN HÀNH MỚI CẦN SETUP)

#Dịch lại text
- Ngày loại bỏ (removal_date) -> Ngày hết hạn
- Đơn mua hàng -> Hóa đơn nhà cung cấp (module purchase)
- You cannot delete a payment that is already posted. -> Bạn không thể xóa các phiếu thu đã được xác nhận. (Tạo các từ còn thiếu -> module account)
- You have not recorded done quantities yet, by clicking on apply Odoo will process all the reserved quantities. => Bạn chưa ghi nhận số lượng hoàn thành!<br/> Bạn có muốn hệ thống tự động xử lý để ghi nhận số lượng giữ trước cho đơn hàng của bạn?<br> Áp dụng ngay!
- Create Backorder? -> Áp dụng ngay!
- Immediate Transfer? => Thông báo
- Theorical Cost Price => Giá theo sổ sách
- Điều chỉnh tồn kho => Kiểm kho
- Quy tắc tái cung ứng => Cấu hình Cơ số tủ trực
- Chạy trình điều độ => Chạy cơ số tủ trực
- Ngày Loại bỏ => Ngày hết hạn
- State (base 887) => Thành phố
- Địa điểm đích => Kho nhập
- Xí trước => Giữ trước
- Thôi xí => Bỏ giữ trước
- Create a new inventory adjustment =>Tạo phiếu kiểm kê kho mới
- This is used to correct the product quantities you have in stock. =>Điều này được sử dụng để điều chỉnh số lượng sản phẩm bạn có trong kho.
- You cannot validate a transfer if no quantites are reserved nor done. To force the transfer, switch in edit more and encode the done quantities. => Bạn không thể xác nhận phiếu vì không còn hàng khả dụng trong kho.
- Define a new transfer in stock => Thông tin phiếu kho
- Bizapps -> Hệ thống
- The stock will be reserved for operations waiting for availability and the reordering rules will be triggered. => Chạy trình tổng hợp nhu cầu ở các tất cả các Tủ 
- <span class="o_stat_text">Purchase Orders</span> => <span class="o_stat_text">HĐ mua hàng</span>
- Expiration Alert -> Cảnh báo hết hạn
- Date to determine the expired lots and serial numbers using the filter "Expiration Alerts". -> Ngày để xác định lô đã hết hạn và số sê-ri bằng bộ lọc "Cảnh báo hết hạn". 

#Hướng dẫn
