# Làm song song và merge

## Baseline duy nhất

Hiện workspace chưa được init Git. Khi đội chọn dùng Git, C thiết lập **một repo tại Trice**, commit bộ khung làm baseline rồi mới chia nhánh/clone. Không init repo ở phase2-track4, không tạo bốn repo độc lập rồi cố ghép lịch sử.

```powershell
Set-Location C:\Su\VinLab\phase2-track4\Trice
git init -b main
git add .
git commit -m "add shared team scaffold"
```

Remote/chia sẻ repo do đội cung cấp; không tự bịa URL/publish. Bốn người clone baseline vào thư mục riêng có root tên Trice trên máy mỗi người. Nếu chỉ một máy, dùng thư mục chung và file ownership, không checkout bốn nhánh luân phiên trong cùng thư mục khi người khác đang sửa.

## Nhánh và ownership

A: `member-a-cv`; B: `member-b-engine`; C: `member-c-integration`; D: `member-d-evidence`.

Mỗi người tạo nhánh từ baseline; chỉ stage file sở hữu trong README. Tránh `git add .` sau baseline nếu có file người khác. Shared contract/fixtures đổi qua C; config thuộc B nhưng C có thể đề nghị đổi ROI, không tự chỉnh bản khác.

Trước bàn giao: chạy tests phần mình và smoke chung; commit ngắn; báo commit hash, file, lệnh/kết quả, limitations. Không commit .venv/weights/raw video/runs.

## C tích hợp tại checkpoint

Working tree phải sạch và có checkpoint trước merge. Thứ tự ưu tiên B engine → A detector → C glue/recorder → D evaluator/docs; các module độc lập vẫn merge sớm nếu chưa đủ chức năng, ghi rõ trạng thái.

```powershell
git status --short
git switch main
git merge --no-ff member-b-engine
python tools/check_contract.py
python -m unittest discover -s tests -v
```

Lặp với nhánh A/C/D đã fetch từ repo đội hoặc cùng local repo. Không chạy tên nhánh chưa được chia sẻ. Không force-push, không ghi đè nguyên project bằng zip cũ. Conflict thì C trao đổi owner và giữ contract, không chọn ours/theirs toàn bộ một cách mù quáng.

Sau checkpoint, các thành viên đồng bộ main vào nhánh của mình trước tiếp tục. Nếu contract đổi: C tăng schema_version khi không tương thích và cập nhật consumer/test cùng lúc; trong 3 giờ ưu tiên tránh thay đổi này.

## Không có Git/remote

Mỗi người gửi patch hoặc zip **chỉ file sở hữu**, kèm danh sách thay đổi. C áp dụng vào bản chính trong Trice, chạy smoke/tests trước xác nhận nhận. Shared file được C xử lý riêng. Không gửi nguyên .venv hoặc chép đè thư mục bằng bản zip đầy đủ.

## Merge được không đồng nghĩa chức năng đúng

Smoke chỉ chứng minh import/schema nối được. Nghiệm thu cuối cần webcam thật, tests logic/scorer/replay, nhãn độc lập và evidence. Không báo PASS toàn dự án chỉ vì test_contract qua.
