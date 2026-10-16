'use strict';
const el=id=>document.getElementById(id);
const params=new URLSearchParams(location.hash.slice(1));
const sessionId=params.get('session'),token=params.get('token');
let socket=null,camera=null,active=false,starting=false,generation=0,sequence=0,received=0,awaiting=false,replyTimer=null;
const video=el('phoneVideo'),canvas=el('phoneCapture'),context=canvas.getContext('2d');
el('phoneSession').textContent=sessionId?sessionId.slice(0,12)+'…':'Không có mã phiên';
function error(message){el('phoneNotice').textContent=message;el('phoneNotice').hidden=!message;}
function updateControls(){el('phoneStart').disabled=active||starting||!sessionId||!token;el('phoneStop').disabled=!active&&!starting;el('phoneIdle').hidden=Boolean(camera);}
if(!sessionId||!token)error('Thiếu mã ghép nối. Tạo phiên trên dashboard máy tính rồi mở đầy đủ liên kết trên điện thoại.');
if(!window.isSecureContext)error('Camera cần HTTPS với chứng chỉ được tin cậy. Liên kết HTTP qua địa chỉ LAN không mở được camera.');
updateControls();
async function stop(message='Đã dừng. Cần tạo liên kết mới trên máy tính để chạy lại.'){
 generation++;active=false;starting=false;awaiting=false;clearTimeout(replyTimer);
 if(socket){socket.onclose=null;socket.close();socket=null;}
 if(camera){camera.getTracks().forEach(track=>track.stop());camera=null;video.srcObject=null;}
 el('phoneConnection').textContent=message;el('phoneSecurity').textContent='Đã dừng nguồn ảnh trên điện thoại.';updateControls();
}
async function start(){if(active||starting)return;const epoch=++generation;starting=true;updateControls();error('');try{
 if(!window.isSecureContext||!navigator.mediaDevices?.getUserMedia)throw new Error('Camera cần HTTPS tin cậy và trình duyệt hỗ trợ.');
 const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'},width:{ideal:1280},height:{ideal:720}},audio:false});
 if(epoch!==generation){stream.getTracks().forEach(t=>t.stop());return;}
 camera=stream;video.srcObject=stream;await video.play();if(epoch!==generation)return;
 el('phoneConnection').textContent='Đang xác thực với máy tính…';
 socket=new WebSocket(`${location.protocol==='https:'?'wss':'ws'}://${location.host}/ws/${encodeURIComponent(sessionId)}`);
 socket.onopen=()=>{if(epoch===generation)socket.send(JSON.stringify({type:'auth',token}));};
 socket.onmessage=message=>{if(epoch!==generation)return;try{const data=JSON.parse(message.data);
  if(data.type==='error')throw new Error(data.error||'Máy tính từ chối xử lý.');
  if(data.type==='complete'){stop('Máy tính đã kết thúc phiên. Tạo mã ghép nối mới để tiếp tục.');return;}
  if(data.type==='authenticated'){clearTimeout(replyTimer);starting=false;active=true;awaiting=false;updateControls();el('phoneConnection').textContent='Đã xác thực. Đang gửi ảnh tuần tự về máy tính.';el('phoneSecurity').textContent='Camera đang gửi ảnh về máy tính đã ghép nối. Trang điện thoại không phát âm thanh.';sendFrame(epoch);return;}
  if(data.observation&&data.decision){clearTimeout(replyTimer);awaiting=false;received++;el('phoneFrames').textContent=String(received);el('phoneTiming').textContent=Number(data.processing_ms||0).toFixed(0)+' ms';el('phoneConnection').textContent=data.decision.requires_recalibration?'Camera đã dịch chuyển. Dừng và cấu hình lại bàn/cửa trên máy tính.':'Máy tính đã xử lý ảnh. Giữ nguyên vị trí điện thoại.';if(active)requestAnimationFrame(()=>sendFrame(epoch));}
 }catch(err){error(err.message);stop('Đã dừng do lỗi xử lý. Tạo mã ghép nối mới để thử lại.');}};
 socket.onerror=()=>{if(epoch===generation)error('Không kết nối được máy tính. Kiểm tra Wi-Fi, HTTPS/chứng chỉ, địa chỉ và máy chủ đang chạy.');};
 socket.onclose=()=>{if(epoch===generation)stop('Kết nối đã đóng. Không gửi thêm ảnh; tạo mã ghép nối mới trên máy tính.');};
 replyTimer=setTimeout(()=>{if(epoch===generation){error('Chưa xác thực được trong 15 giây. Kiểm tra mã còn hạn và cùng máy chủ HTTPS.');stop();}},15000);
 }catch(err){if(epoch!==generation)return;error(err.name==='NotAllowedError'?'Quyền camera bị từ chối. Cho phép camera trong trình duyệt rồi tạo lại phiên.':err.message);await stop('Chưa mở được camera hoặc kết nối.');}}
function sendFrame(epoch){if(epoch!==generation||!active||awaiting||socket?.readyState!==WebSocket.OPEN)return;if(!video.videoWidth){error('Camera chưa cung cấp ảnh.');stop();return;}
 awaiting=true;const ratio=Math.min(1,960/video.videoWidth);canvas.width=Math.round(video.videoWidth*ratio);canvas.height=Math.round(video.videoHeight*ratio);const captureTime=performance.now();context.drawImage(video,0,0,canvas.width,canvas.height);
 canvas.toBlob(blob=>{if(epoch!==generation||!active||socket?.readyState!==WebSocket.OPEN)return;if(!blob){error('Không mã hóa được ảnh camera.');stop();return;}socket.send(JSON.stringify({type:'frame',seq:sequence++,capture_t_ms:captureTime,source_clock:'browser_monotonic'}));socket.send(blob);replyTimer=setTimeout(()=>{if(epoch===generation){error('Máy tính chưa phản hồi ảnh trong 30 giây. Đã dừng để tránh đếm thời gian khi mất dữ liệu.');stop();}},30000);},'image/jpeg',.8);
}
el('phoneStart').addEventListener('click',start);el('phoneStop').addEventListener('click',()=>stop());window.addEventListener('pagehide',()=>stop());
