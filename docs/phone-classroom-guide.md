# Camera điện thoại + phòng học + loa ngoài

## Những phần đã triển khai

- Trang điện thoại dùng camera sau, gửi JPEG realtime có backpressure, sequence và timestamp nguồn.
- Dashboard máy tính theo dõi frame/trạng thái từ điện thoại độc lập; ghép phiên bằng QR/link và token tạm.
- Khai báo vùng bàn có ID/tên, vùng cửa và đường ra hữu hạn. Chỉ observed crossing trong cửa mới tạo nhắc rời phòng.
- Trạng thái từng bàn và câu đọc có số bàn. Model/track ID chỉ tạo liên hệ trong phiên, không xác minh danh tính hay ý định “ra về”.
- Loa phát từ trình duyệt dashboard trên máy tính, không từ điện thoại/backend. Có bật/tắt, chọn giọng Việt, nút thử loa và hàng đợi chống lặp.
- Camera dịch chuyển làm bằng chứng không gian mất hiệu lực; vẫn nhận diện realtime nhưng không kết luận rời phòng. Cần cố định lại và tạo phiên hiệu chuẩn mới.

## Cách thử ngay trên máy tính

Chạy server localhost theo README, chọn video/camera. Vào Cấu hình, bật chế độ phòng học, chỉnh tables và door polygon/exit theo ảnh. Các tọa độ từ0 tới1, không phải mét. Chỉ đánh dấu “đã hiệu chuẩn” khi thực sự kiểm tra trên nguồn hiện tại. Một vùng bàn hỗ trợ một liên hệ người–đồ tại một thời điểm, không phải lớp học đông người đã được xác minh.

Nối loa vào máy tính bằng cách thông thường. Chọn giọng Việt, bấm Thử loa để tự kiểm tra, sau đó bật đọc cảnh báo. Không có giọng Việt thì UI báo rõ và chỉ hiển thị chữ. Kết quả dispatch/voice end không chứng minh người ngoài phòng đã nghe; cần kiểm tra âm lượng/vị trí thực.

## Điện thoại: hai cách kết nối local

### A. Cùng Wi-Fi, HTTPS

Đây là đường chính cho Android/iPhone. Không dùng cloud/tunnel/public deployment.

1. Máy tính và điện thoại phải ở mạng cho phép liên lạc trực tiếp. Wi-Fi trường học có thể chặn thiết bị liên lạc; VPN/adapter ảo có thể chọn sai IP.
2. Xem IP Wi-Fi bằng `Get-NetIPAddress -AddressFamily IPv4`. Ở phiên chuẩn bị này Wi-Fi máy tính là `172.16.61.250`; kiểm tra lại vì IP có thể đổi. Không dùng IP VirtualBox/VPN.
3. Đã có helper tạo CA/cert trong Trice/data/tls, không tự cài trust hoặc sửa firewall. Chạy server:

```powershell
cd C:\Su\VinLab\phase2-track4\Trice
.\start-phone.ps1 -LanIP 172.16.61.250
```

4. Chứng chỉ local phải được bạn chủ động tin cậy trên cả máy tính và điện thoại. Chỉ chuyển file **data/tls/trice-local-ca.crt** sang thiết bị; **không chuyển ca-key.pem/server-key.pem**. Không tắt SSL validation, không bỏ qua trang cảnh báo trình duyệt như một cách thay thế hiệu chuẩn trust. Nếu IP thay đổi cần tạo cert vào thư mục mới và cập nhật cấu hình đường dẫn, không ghi đè CA đang tin cậy.
5. Mở dashboard trên **https://localhost:8443** tại máy tính. Đây phải là cùng process/backend với điện thoại; không tạo pair ở http8000 rồi dùng ở https8443 vì token nằm trong RAM của process tạo nó.
6. Trong panel điện thoại, nhập base URL **https://172.16.61.250:8443**, cấu hình bàn/cửa, tạo kết nối. Quét QR hoặc copy link sang điện thoại. Token thuộc phiên, hết hạn nếu chưa kết nối quá10phút; không chia sẻ link công khai.
7. Trên điện thoại bấm Bắt đầu, cấp quyền camera, chọn camera sau. Dashboard nhận ảnh và trạng thái. Điện thoại không được quyền đọc lịch sử/API quản trị; token chỉ cho gửi ảnh vào phiên đã ghép.
8. Đặt điện thoại cố định nhìn được cả bàn và cửa, không đi theo người ra cửa. Nếu camera di chuyển, dashboard báo cần hiệu chuẩn lại. Khi cần đổi góc, dừng phiên, đặt lại vùng và tạo phiên mới.

Trình duyệt yêu cầu secure context cho camera; HTTP qua IP LAN thường không mở camera. Tài liệu: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia. . Trên iPhone, chứng chỉ cài thủ công không tự được tin cậy cho SSL; thao tác do chủ thiết bị thực hiện: https://support.apple.com/en-sg/102390 . Chúng tôi chưa thực hiện thay đổi trust/firewall trên thiết bị.

### B. Android qua USB/Chrome port forwarding

Dùng khi muốn thử local mà không cấu hình CA trên Wi-Fi. Cần Android/Chrome và tự bật USB debugging theo chính sách thiết bị; không dùng nếu điện thoại được quản lý cấm thao tác này.

1. Máy tính chạy http://localhost:8000 như README.
2. Kết nối USB, tự xác nhận debugging trên điện thoại. Chrome máy tính mở `chrome://inspect/#devices`, thiết lập port forwarding: device port8000 tới `localhost:8000` trên máy tính.
3. Trong dashboard, bật lựa chọn USB localhost và dùng base URL `http://localhost:8000` để tạo QR/link. Chỉ trong trường hợp forwarding này localhost trên điện thoại mới trỏ đúng server máy tính.
4. Mở link trên Chrome Android, bấm bắt đầu và cấp quyền. Không có port forwarding thì localhost là chính điện thoại, sẽ không tới máy tính.

Nguồn Chrome: https://developer.chrome.com/docs/devtools/remote-debugging/local-server . Đây là hướng dẫn thao tác, không phải bằng chứng điện thoại đã kết nối thành công trong phiên phát triển.

## Pipeline theo Track4

Xem [track4-pipeline.md](track4-pipeline.md). Thực thi trực tiếp: detector pretrained, tracking, hình học vùng/cửa, uncertainty, chất lượng ảnh/camera-motion optical flow+RANSAC, trạng thái thời gian, source sequence/backpressure, log/event persistence và replay/test. Nguyên tắc split/provenance/stress/gate lấy từ các lab. Không thêm LiDAR/VLM/LoRA chỉ để có tên; không gọi camera-motion check là SLAM hoặc fusion đa cảm biến.

## Chứng minh chất lượng cần làm với đội

Độc lập gán nhãn người liên quan, table_id, thời điểm qua cửa và đồ còn/mang đi. Diễn: đi lấy sách trong phòng không nhắc; rời qua cửa để đồ nhắc đúng bàn; mang đồ đi không nhắc; quay lại hủy; che người không tự xem exit; camera pan không tự báo; hai bàn/hai người không gán bừa. Đo đúng bàn precision/recall, độ trễ source/decision/dispatch có giới hạn clock, FPS và tỷ lệ UNCERTAIN.

Hiện protocol TLS/token/observer đã có smoke với model thật và ảnh video local nhưng không phải điện thoại vật lý. Chưa có bằng chứng âm thanh tới tai người dùng, camera phòng học thật hay độ chính xác crowded classroom. Không dùng unit test/synthetic event làm số đo thực tế.

## Không có dây USB, dây LAN hoặc router riêng

Có thể dùng Wi-Fi hotspot của điện thoại: bật điểm phát trên điện thoại, kết nối máy tính vào hotspot, xem IPv4 của adapter Wi-Fi trên máy tính rồi chạy start-phone.ps1 với IP đó. Điện thoại mở QR/link https://IP_WIFI_PC:8443 do dashboard tạo. Đây vẫn là mạng local không dây giữa hai thiết bị, không cần deploy; phải kiểm tra điện thoại/hotspot có cho truy cập thiết bị kết nối hay không.

HTTPS được điện thoại tin cậy vẫn cần thiết; QR không bỏ qua yêu cầu này. Không có mạng chung (Wi-Fi/hotspot) và không có USB thì cần Internet+dịch vụ trung chuyển hoặc một giải pháp camera riêng; phiên hiện tại không tự bật tunnel/cloud. Không tự tắt firewall/VPN/certificate validation để cố kết nối.
