# Luồng Track 4 trong Trice Classroom

## Điều hệ thống thực sự xác định

Camera quan sát **người liên quan tới đồ tại bàn** bằng track ID và bằng chứng không gian–thời gian. Hệ thống không xác minh danh tính, quyền sở hữu hoặc ý định quên đồ. Loa máy tính nhắc tên bàn, không đọc tên cá nhân.

Điện thoại có thể cầm để tìm góc quan sát; lúc camera di chuyển vẫn chạy detection nhưng không được sử dụng vùng ảnh cũ để kết luận người rời phòng. Sau khi có bằng chứng camera dịch chuyển, dừng phiên, đặt camera ổn định, cấu hình lại bàn/cửa trên ảnh mới và tạo phiên mới. `reset()` đơn thuần không xóa khóa camera movement.

## Flow thực thi

1. Điện thoại gửi JPEG tới backend; timestamp và thông tin nguồn được giữ trong phiên.
2. Detector trả box, class, confidence và observed/predicted. YOLO11n pretrained phát hiện; ByteTrack giữ ID tạm. Không tự train model trong sản phẩm này.
3. `MotionGuard` trong `camera_quality.py` dùng góc đặc trưng, optical flow và affine RANSAC so với ảnh tham chiếu đầu phiên. Camera dịch chuyển, xoay, đổi tỷ lệ hoặc thiếu texture làm quyết định không đủ bằng chứng. Score là độ dịch ảnh chuẩn hóa, không phải xác suất.
4. `ClassroomEngine` phân đồ vào polygon bàn theo tâm box. Một track đồ không được liên kết sang hai bàn. Người có thể gần nhiều bàn nên quan hệ ban đầu mơ hồ sẽ không được gán.
5. Mỗi bàn dùng `EventEngine`: đồ đứng yên quanh anchor và duy nhất một người gần liên tục đủ ngưỡng mới liên kết. Người đi ngang không thay người liên quan; đổi ID cần khởi tạo phiên lại thay vì tự đoán danh tính.
6. Đáy giữa box người đo được phải đi qua **đoạn** exit hữu hạn; giao điểm còn phải nằm trong polygon cửa. Crossing đường kéo dài bên ngoài cửa không đủ bằng chứng. Frame gap hoặc mất dấu không thay crossing.
7. Crossing hợp lệ tạo `REMINDER` có `room_exit_confirmed=true`, tên bàn và câu nhắc tiếng Việt. Đồ còn được đo thấy trong bàn sau thời gian chờ mới tạo `UNATTENDED_ALERT`. Hai giây xác nhận nằm trong năm giây chờ mặc định. Người quay vào hủy chờ; đồ ra khỏi bàn hoặc camera mất ổn định ngắt bằng chứng.
8. Backend lưu metadata/sự kiện; dashboard và loa là đầu ra. Log/replay phục vụ đánh giá. Phát âm thanh không chứng minh người đã nghe.

## Bảy trụ cột và sản phẩm bằng chứng

| Trụ cột | Module/biểu diễn | Đo hoặc kiểm tra |
|---|---|---|
| Học | `detector.py`, model card; ảnh → box/class/confidence | Nguồn weights/dataset, version/hash; ca model bỏ sót đồ |
| Hình học | Polygon bàn/cửa, tâm đồ, đáy giữa người, đoạn giao cắt | Overlay cùng ảnh; test crossing trong/ngoài cửa; không suy ra mét |
| Bất định | observed-only, mất ID, `MotionGuard`, `UNCERTAIN` | Độ phủ đủ bằng chứng, ca che khuất, camera pan, thiếu texture |
| Biểu diễn | bảng bàn, person/object ID, quan hệ, trạng thái/episode | `decision.tables`, các event có seat_id và table_name |
| Thời gian | Timestamp, khoảng đứng yên, thời gian association, timer sau crossing | Delay reminder/alert và p50/p95 xử lý; phân biệt thời gian media với nhận frame live |
| Dữ liệu | Session, metadata SQLite/log, nhãn độc lập, replay | Tách calibration/test theo phiên; consent; không lưu ảnh nhận dạng vào DB |
| Bằng chứng | Tests, event evaluator, video có nhãn, failure ledger | TP/FP/FN và số mẫu; một lỗi thật kèm timestamp; phạm vi chưa chứng minh |

Đào sâu **hình học + biểu diễn + thời gian**; **bất định** ngăn biến mất dấu/camera rung thành kết luận rời phòng.

## Liên hệ source trong repo Phase 2

Những liên hệ sau là kiến thức được vận dụng; không có nghĩa sao chép nguyên pipeline lab hoặc triển khai đủ mọi kỹ thuật.

- [Lab 7 chạy detection và tracking](../../lec7-tracking-forecasting/K4-Track4-Day22-Tracking-Student/scripts/run_tracking.py): tách detector, tracker, class và thông số benchmark. Lab dùng weights riêng; sản phẩm giữ YOLO11n đã có, không tuyên bố dùng cùng weights.
- [Lab 8 association](../../lec8-bev-sensor-fusion/K4-Track4-Day23-Sensor-Fusion-Student/student/workspace/association.py) và [track lifecycle](../../lec8-bev-sensor-fusion/K4-Track4-Day23-Sensor-Fusion-Student/student/workspace/track_management.py): measurement khác prediction, mất dấu và lifecycle cần quản lý. Trice không triển khai LiDAR/camera fusion hay covariance Kalman của lab.
- [Lab 9 kiểm tra dữ liệu](../../lec9-datapipeline/K4-L3L4-Track4-DataPipeline4ComputerVision/scripts/check_data.py) và [pipeline verify](../../lec9-datapipeline/K4-L3L4-Track4-DataPipeline4ComputerVision/pipeline/verify.py): schema, chất lượng dữ liệu và kiểm chứng pipeline. Trice không thêm Airflow chỉ để có tên công nghệ.
- [Lab 12 các bước evidence/replay/gate](../../lec12-replay-closeopenlooop/K4-Track4-Replay-CloseOpenLoop/lab12/steps.py): đánh giá bằng dữ liệu có nguồn, tách tập, lưu kết quả và giới hạn. Replay không tự chứng minh live đủ nhanh hoặc precision/recall cao.
- Lab 1–3 liên hệ input/output, dữ liệu huấn luyện, detector và benchmark; Lab 4 liên hệ nhiễu/che khuất; Lab 5–6 liên hệ measurement, tọa độ và giới hạn 2D; Lab 10–11 liên hệ provenance và stress scenario. VLM/VLA, point cloud, LiDAR, homography ra mét và robot control **chưa được triển khai** trong Trice Classroom.

## Ca kiểm tra bắt buộc

1. Người đặt đồ tại bàn, đứng gần đủ lâu, đi qua đúng cửa: một reminder và một alert sau ngưỡng; loa đọc đúng bàn.
2. Người đi ngang đường exit ở ngoài cửa: không reminder/alert.
3. Người rời bàn nhưng vẫn trong lớp: không kết luận ra khỏi phòng.
4. Người bị che khuất hoặc ID đổi: `UNCERTAIN`, không tự chọn chủ mới.
5. Camera pan nhanh và pan chậm tích lũy: detection vẫn hiển thị, spatial evidence khóa chờ phiên/geometry mới.
6. Ảnh thiếu texture: tạm `UNCERTAIN`, có thể phục hồi khi chất lượng đủ; không đồng nghĩa camera đã di chuyển.
7. Một người gần hai đồ ở hai bàn: chưa gán quan hệ thay vì đoán.

Unit tests synthetic chỉ chứng minh quy tắc trên đầu vào kiểm soát. Cần video tự diễn, ground truth độc lập và chạy điện thoại/loa thật trước khi báo hiệu năng.

## Giới hạn cần nêu khi bảo vệ

Camera 2D không biết quyền sở hữu. Đồ che khuất, ID switch và phối cảnh gây sai liên hệ. Polygon ảnh chỉ hợp lệ với góc camera đã cấu hình; không hỗ trợ quét tự do đồng thời giữ bản đồ lớp. MotionGuard dùng đặc trưng ảnh, không phải SLAM/visual odometry đã hiệu chuẩn; vùng người di chuyển chiếm phần lớn ảnh hoặc cảnh ít texture có thể làm hệ thống thận trọng quá mức hoặc bỏ sót rung rất nhỏ. Thử nghiệm ít phiên không đại diện lớp học thật. Nhiều món trong cùng bàn chưa giải được ownership; hệ thống phải tránh gán khi mơ hồ.
