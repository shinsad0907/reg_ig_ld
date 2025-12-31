"""Instagram Registration Workflow"""
from auto_instagram import ldplayer
from time import sleep
import threading
from threading import Lock


class IGWorkflow:
    """Workflow để mở LDPlayer và Instagram"""
    
    # Global locks
    _device_list_lock = Lock()
    _ldplayer_launch_lock = Lock()
    
    def __init__(self, ldplayer_name, ldplayer_path, account_index=0, progress_callback=None):
        self.ldplayer_name = ldplayer_name
        self.ldplayer_path = ldplayer_path
        self.account_index = account_index
        self.progress_callback = progress_callback
        self.should_stop = False
        
        # Khởi tạo ldplayer controller
        self.ld = ldplayer(index=account_index)
        self.ld.ADB = ldplayer_path
        self.device_id = None
    
    def log(self, message):
        """Gửi log về GUI"""
        print(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def stop(self):
        """Dừng workflow"""
        self.should_stop = True
    
    def open_and_wait_ldplayer(self):
        """Mở LDPlayer và đợi khởi động"""
        self.log(f"\n{'='*50}")
        self.log(f"📱 Đang xử lý: {self.ldplayer_name}")
        self.log(f"{'='*50}")
        
        # 1. Mở LDPlayer
        self.log(f"🔄 Đang mở LDPlayer...")
        
        with IGWorkflow._ldplayer_launch_lock:
            if not self.ld.open_ldplayer(self.ldplayer_name, self.ldplayer_path):
                self.log(f"❌ Không thể mở LDPlayer")
                return False
        
        # Đợi LDPlayer khởi động
        self.log(f"⏳ Chờ LDPlayer khởi động (15s)...")
        sleep(15)
        
        # 2. Đợi ADB kết nối
        self.log(f"⏳ Chờ ADB kết nối...")
        
        retry_count = 0
        max_retries = 60  # 5 phút
        
        while retry_count < max_retries:
            if self.should_stop:
                self.log(f"⏹️ Đã dừng")
                return False
            
            with IGWorkflow._device_list_lock:
                devices = self.ld.DEVICE()
            
            if len(devices) > self.account_index:
                self.device_id = devices[self.account_index]
                self.log(f"✅ Đã kết nối device: {self.device_id}")
                break
            
            retry_count += 1
            if retry_count % 5 == 0:
                self.log(f"   ⏳ Đang chờ ADB... ({retry_count * 5}s)")
            
            sleep(5)
        
        if not self.device_id:
            self.log(f"❌ Timeout - Không lấy được device ID")
            return False
        
        # 3. Kiểm tra màn hình chính
        self.log(f"🔍 Kiểm tra màn hình chính...")
        
        retry_count = 0
        max_retries = 60  # 5 phút
        
        while retry_count < max_retries:
            if self.should_stop:
                self.log(f"⏹️ Đã dừng")
                return False
            
            try:
                if self.ld.is_ldplayer_in_home(self.device_id, self.ldplayer_path):
                    self.log(f"✅ Đã vào màn hình chính!")
                    return True
            except Exception as e:
                self.log(f"⚠️ Lỗi check home: {e}")
            
            retry_count += 1
            if retry_count % 5 == 0:
                self.log(f"   ⏳ Chờ màn hình chính... ({retry_count * 5}s)")
            
            sleep(5)
        
        self.log(f"❌ Timeout - Không vào được màn hình chính")
        return False
    
    def open_instagram(self):
        """Mở Instagram"""
        if not self.device_id:
            self.log(f"❌ Chưa có device ID")
            return False
        
        self.log(f"📸 Đang mở Instagram...")
        
        if self.ld.open_instagram(self.device_id, self.ldplayer_path):
            self.log(f"✅ Đã mở Instagram!")
            sleep(3)  # Đợi Instagram khởi động
            return True
        else:
            self.log(f"⚠️ Không mở được Instagram (có thể chưa cài)")
            return False
    
    def run(self):
        """Chạy workflow hoàn chỉnh"""
        try:
            # Bước 1: Mở và đợi LDPlayer
            if not self.open_and_wait_ldplayer():
                self.log(f"❌ Không thể khởi động LDPlayer")
                return False
            
            if self.should_stop:
                self.log(f"⏹️ Đã dừng")
                return False
            
            # Bước 2: Mở Instagram
            if not self.open_instagram():
                self.log(f"⚠️ Không mở được Instagram")
                return False
            
            if self.should_stop:
                self.log(f"⏹️ Đã dừng")
                return False
            
            # Hoàn thành
            self.log(f"\n✅ HOÀN THÀNH: {self.ldplayer_name}")
            self.log(f"   Device ID: {self.device_id}")
            self.log(f"   Instagram: Đã mở")
            self.log(f"{'='*50}\n")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Lỗi: {e}")
            import traceback
            self.log(traceback.format_exc())
            return False