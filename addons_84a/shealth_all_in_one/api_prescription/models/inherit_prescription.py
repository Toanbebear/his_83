import json

import requests
import time

from odoo import fields, api, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, date, timedelta

import logging

_logger = logging.getLogger(__name__)
class InheritSHealthPrescriptions(models.Model):
    _inherit = 'sh.medical.prescription'

    state_prescription = fields.Selection([
        ('draft', 'Chưa gửi'), ('sent', 'Gửi thành công')
    ], string='Đơn thuốc điện tử', default='draft', required=True)

    type_prescription = fields.Selection([
        ('c', 'Đơn thuốc chuẩn'), ('n', 'Đơn thuốc gây nghiện'), ('h', 'ĐƠn thuốc hướng thần'), ('y', 'Đơn thuốc y học cổ truyền')
    ], string='Loại đơn thuốc', default='c')

    isbuy = fields.Selection([
        ('1','Có bán'), ('2','Không bán')
    ], string='Đơn thuốc điện tử', default='2')

    # Gửi đơn thuốc điện tử lên sở
    def action_sync_his_prescription(self):
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})

        date_out = self.date_out
        date_recheck = None

        if self.days_reexam and self.days_reexam[0].date_recheck:
            date_recheck = datetime.combine(self.days_reexam[0].date_recheck, datetime.min.time())

        if date_recheck:
            # Tính số ngày giữa hai ngày tháng
            so_ngay = (date_out - date_recheck).days
        else:
            # Xử lý trường hợp không có ngày kiểm tra hoặc không có dữ liệu hợp lệ
            so_ngay = None  # Hoặc bạn có thể xử lý khác tùy theo yêu cầu của bạn

        # Khởi tạo list để lưu thông tin thuốc
        thong_tin_don_thuoc_list = []
        #  lấy về thông tin thuốc
        for rec in self.prescription_line:
            if rec.name.national_prescription == True:
                # Thay đổi cấu trúc dữ liệu
                thong_tin_don_thuoc = {
                    "ma_thuoc": rec.name.code_national if rec.name.code_national else '',
                    "biet_duoc": rec.name.composition if rec.name else '',
                    "ten_thuoc": rec.name.name_use if rec.name else '',
                    "don_vi_tinh": rec.dose_unit_related.name if rec.dose_unit_related else '',
                    "so_luong": rec.qty if rec.qty else '',
                    "cach_dung": rec.info if rec.info else '',
                    "ma_thuoc_ban": rec.name.default_code if rec.name else '',
                    "biet_duoc_ban": rec.name.name_medicine if rec.name else '',
                    "ten_thuoc_ban": rec.name.name_use if rec.name else '',
                    "don_vi_tinh_ban": rec.dose_unit_related.name if rec.dose_unit_related else '',
                    "so_luong_ban": rec.qty if rec.qty else '',
                    "cach_dung_ban": rec.info if rec.info else '',
                }

                # Thêm thông tin thuốc vào danh sách
                thong_tin_don_thuoc_list.append(thong_tin_don_thuoc)
        # Khởi tạo list để lưu thông tin Chẩn đoán
        thong_tin_chan_doan_list = []
        #  lấy về thông tin chaarn đoán
        for path in self.walkin.pathology:
            ket_luan = self.walkin.service.mapped('diagnose')
            ket_luan_filtered = [value for value in ket_luan if value is not False]
            # Thay đổi cấu trúc dữ liệu
            thong_tin_chan_doan = {
                "ma_chan_doan": path.code if path.code else '',
                "ten_chan_doan": path.name if path.name else '',
                "ket_luan": ', '.join([str(value) for value in ket_luan_filtered])
            }

            # Thêm thông tin thuốc vào danh sách
            thong_tin_chan_doan_list.append(thong_tin_chan_doan)
        if self.doctor.token_his_physician:
            url = self.doctor.institution.url_api_prescription
            access_token = self.doctor.token_his_physician
            ngay_gio_ke_don = self.date_out + timedelta(hours=7)
            payload = json.dumps({
                "isbuy": 0 if self.isbuy == '2' else (1 if self.isbuy == '1' else ''),
                "ma_lien_thong_co_so_kham_chua_benh":  self.doctor.institution.ma_lien_thong_co_so_kham_chua_benh if self.doctor.institution.ma_lien_thong_co_so_kham_chua_benh else '',
                "password_co_so": self.doctor.institution.password_co_so if self.doctor.institution.password_co_so else '',
                "ma_lien_thong_bac_si": self.doctor.code_connected if self.doctor.code_connected else '',
                "password": self.doctor.pass_prescription if self.doctor.pass_prescription else '',
                "loai_don_thuoc": self.type_prescription if self.type_prescription else '',
                "ma_don_thuoc": self.name if self.name else '',
                "ho_ten_benh_nhan": self.patient.name if self.patient else '',
                "ngay_sinh_benh_nhan": self.patient.dob.strftime('%d/%m/%Y') if self.patient else '',
                "ma_dinh_danh_y_te": self.patient.identification_code if self.patient.identification_code else '',
                "ma_dinh_danh_cong_dan": None,
                "can_nang": self.walkin.weight if self.walkin.weight else '',
                "gioi_tinh": 2 if self.patient.sex == 'Male' else (3 if self.patient.sex == 'Female' else ''),
                "ma_so_bao_hiem_y_te": '',
                "thong_tin_nguoi_giam_ho": '',
                "dia_chi": self.patient.street if self.patient.street else '',
                "chan_doan": thong_tin_chan_doan_list,
                "luu_y": self.info if self.info else '',
                "hinh_thuc_dieu_tri": 2,
                "dot_dung_thuoc": '',
                "thong_tin_don_thuoc":  thong_tin_don_thuoc_list,
                "loi_dan": '',
                "so_dien_thoai_nguoi_kham_benh": self.patient.phone if self.patient.phone else '02873089993',
                "ngay_tai_kham": so_ngay,
                "ngay_gio_ke_don": ngay_gio_ke_don.strftime('%Y-%m-%d %H:%M:%S'),
                "signature": '',
            })

            headers = {
                'access-token': access_token,
                'Content-Type': 'application/json',
            }
            request_content = json.dumps({
                'type': 'POST',
                'url': url,
                'headers': headers,
                'data': payload,
            }, ensure_ascii=False).encode('utf-8').decode('unicode-escape')
            _logger.info("*************************************Response from API: %s", request_content.encode('utf-8').decode('unicode-escape'))
            response = requests.request("POST", url, headers=headers, data=payload)
            response = response.json()

            # Ghi log để xem kết quả trả về từ cuộc gọi API
            _logger.info("####################################Kết quả trả về: %s", response)
            if 'status' in response and response['status'] == 'success':
                time.sleep(3)
                url_sale = ' http://10.10.10.197:9991/api/eprescription/sale?api=2b11k2h3foes9f0809zdn398f0fasdmkj30'
                response_sale = requests.request("POST", url_sale, headers=headers, data=payload)
                response_sale = response_sale.json()
                # Ghi log để xem kết quả trả về từ cuộc gọi API
                _logger.info("####################################: %s", response_sale)
                context['message'] = 'Gửi đơn thuốc thành công !!!'
                self.state_prescription = 'sent'
                return {
                    'name': 'THÔNG BÁO THÀNH CÔNG',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view_id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
            else:
                context['message'] = 'Gửi đơn thuốc thất bại!' + ' ' + str(response['message'])
                return {
                    'name': 'THÔNG BÁO THẤT BẠI',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view_id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
        else:
            raise ValidationError(
                _('Hiện tại, chưa cấu hình cho bác sĩ %s, liên hệ IT để được hỗ trợ') % self.doctor.name)