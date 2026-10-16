# Kết nối máy tính Windows vào Wi-Fi do điện thoại phát

## 1. Bật hotspot trên điện thoại

Android: vào Cài đặt → Kết nối/Mạng và Internet → Điểm truy cập cá nhân/Điểm phát sóng di động → bật. Ghi tên Wi-Fi và mật khẩu hiển thị trên máy. Tên menu tùy hãng.

iPhone: Cài đặt → Điểm truy cập cá nhân → bật Cho phép người khác kết nối. Xem Mật khẩu Wi-Fi. Tên mạng thường là tên iPhone; giữ màn hình này mở lúc máy tính kết nối lần đầu.

Nếu máy tính không tìm thấy mạng, thử băng tần2,4GHz trong cấu hình hotspot Android, hoặc Tối đa hóa tương thích trên iPhone nếu có. Một số điện thoại cần bật dữ liệu di động để cho phép bật hotspot; luồng camera gửi nội bộ không tự bắt buộc sử dụng Internet.

## 2. Kết nối trên Windows

Bấm biểu tượng mạng ở góc phải thanh taskbar → mở danh sách Wi-Fi → chọn đúng tên hotspot → Kết nối → nhập mật khẩu trên điện thoại → Tiếp theo. Xác nhận Windows ghi Đã kết nối ở đúng tên mạng đó. Không cần dây LAN/USB, không cần router riêng. Nếu ghi Không có Internet nhưng vẫn Đã kết nối, mạng local có thể vẫn dùng được; phải kiểm tra kết nối Trice thực tế.

## 3. Lấy IPv4 máy tính trên hotspot

Mở PowerShell và chạy:

```powershell
ipconfig
```

Tìm adapter Wi-Fi đang kết nối hotspot, đọc dòng IPv4 Address. Không lấy IP Ethernet/VirtualBox/NordLynx/VPN hoặc127.0.0.1. IP gateway là điện thoại, không phải địa chỉ máy chủ Trice. Ví dụ192.168.43.120 chỉ minh họa, không được copy thay IP thực.

Có thể kiểm tra thêm:

```powershell
Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway } | Format-List InterfaceAlias,IPv4Address,IPv4DefaultGateway
```

## 4. Mở Trice sau khi kết nối mạng

Dùng IP Wi-Fi vừa đọc với start-phone.ps1 theo phone-classroom-guide.md. Camera trình duyệt trên điện thoại cần HTTPS được tin cậy; mở http://IP:8000 không tự đủ quyền camera. Máy tính mở dashboard https://localhost:8443 cùng backend; base URL điện thoại là https://IP_WIFI_PC:8443; tạo QR/link ghép phiên.

Nếu cert hiện có tạo cho IP Wi-Fi cũ thì chưa hợp lệ với IP hotspot mới. Không bỏ qua cảnh báo trình duyệt hoặc tắt kiểm tra SSL; cần tạo cert cho IP mới trong thư mục mới và cập nhật đường dẫn/trust theo hướng dẫn. Chỉ chuyển public CA cert, không chia sẻ private keys.

## 5. Nếu chưa kết nối được

Kiểm tra lần lượt: đúng tên/mật khẩu; máy tính thực sự ở hotspot; đúng IP adapter Wi-Fi; server đúng cổng; hotspot có cho phép truy cập thiết bị kết nối; điều kiện firewall được chủ máy kiểm tra theo chính sách. Không tự tắt toàn bộ firewall hoặc VPN để thử. Chưa có kết nối mạng không phải lỗi model AI.

Hướng dẫn tiếp: phone-classroom-guide.md. Chưa xác minh điện thoại vật lý/hotspot/loa ngoài trong phiên phát triển; cần thao tác thực trên thiết bị của người dùng.
