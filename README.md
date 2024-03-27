[![Build Status](http://runbot.odoo.com/runbot/badge/flat/1/master.svg)](http://runbot.odoo.com/runbot)
[![Tech Doc](http://img.shields.io/badge/master-docs-875A7B.svg?style=flat&colorA=8F8F8F)](http://www.odoo.com/documentation/master)
[![Help](http://img.shields.io/badge/master-help-875A7B.svg?style=flat&colorA=8F8F8F)](https://www.odoo.com/forum/help-1)
[![Nightly Builds](http://img.shields.io/badge/master-nightly-875A7B.svg?style=flat&colorA=8F8F8F)](http://nightly.odoo.com/)

Odoo
----

Code cho 83 tiêu chí HIS Đông Á

  - http://his.dongabeauty.vn
  - http://666kangnam.scisoftware.xyz
  - http://84a.kangnam.com.vn

# Cài đặt
 1. Clone repo sau đó đổi cổng trong file docker-compose.yml
 2. Vào thư mục vừa clone về và chạy `docker-compose up`
 3. Chạy lệnh `docker-compose ps` và tìm container của odoo
 4. Cài đặt cho container:  
    ```docker exec container_name_odoo12_1 pip3 install xlrd wheel python-docx openpyxl```
 5. Chạy lệnh `chmod -R 777 etc`   
 6. Restore lại db
 
Odoo Apps can be used as stand-alone applications, but they also integrate seamlessly so you get
a full-featured <a href="https://www.odoo.com">Open Source ERP</a> when you install several Apps.


Getting started with Odoo
-------------------------
For a standard installation please follow the <a href="https://www.odoo.com/documentation/master/setup/install.html">Setup instructions</a>
from the documentation.

Then follow <a href="https://www.odoo.com/documentation/master/tutorials.html">the developer tutorials</a>
