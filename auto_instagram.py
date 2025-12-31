"""LDPlayer Controller for Instagram Automation"""
import subprocess
from time import sleep
import os


class ldplayer:
    """LDPlayer control and automation"""
    
    def __init__(self, index=0):
        self.ADB = r'C:\LDPlayer\LDPlayer9'
        self.index = index
    
    def adb_command(self, command):
        """Execute ADB command"""
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8'), result.stderr.decode('utf-8')
    
    def get_ldplayer_names(self):
        """Lấy danh sách tên LDPlayer"""
        ldconsole = os.path.join(self.ADB, "ldconsole.exe")
        
        result = subprocess.run(
            [ldconsole, "list2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        names = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[1].strip()
                    names.append(name)
        
        return names
    
    def get_ldplayer_ids(self):
        """Lấy danh sách ID và tên LDPlayer"""
        ldconsole = os.path.join(self.ADB, "ldconsole.exe")
        
        result = subprocess.run(
            [ldconsole, "list2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        ids = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 2:
                    ld_id = parts[0].strip()
                    ld_name = parts[1].strip()
                    ids.append((ld_id, ld_name))
        
        return ids
    
    def get_ldplayer_names_list(self):
        """Lấy danh sách tên LDPlayer để chạy multiple threads"""
        ldconsole = os.path.join(self.ADB, "ldconsole.exe")
        
        result = subprocess.run(
            [ldconsole, "list2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        names = []
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                parts = line.split(",")
                if len(parts) >= 2:
                    name = parts[1].strip()
                    names.append(name)
        
        return names
    
    def open_ldplayer(self, name, ld_path=None):
        """Mở LDPlayer theo tên"""
        if ld_path is None:
            ld_path = self.ADB
        
        ldconsole = os.path.join(ld_path, "ldconsole.exe")
        
        try:
            subprocess.run([ldconsole, "launch", "--name", name])
            print(f"✅ Đã gửi lệnh mở: {name}")
            return True
        except Exception as e:
            print(f"❌ Lỗi mở LDPlayer: {e}")
            return False
    
    def DEVICE(self):
        """Lấy danh sách device ID từ ADB"""
        proc = subprocess.Popen(
            os.path.join(self.ADB, "adb.exe") + " devices",
            shell=True,
            stdout=subprocess.PIPE
        )
        serviceList = proc.communicate()[0].decode('ascii').split('\n')
        
        self.list_device = []
        for i in range(1, len(serviceList) - 2):
            try:
                device = serviceList[i].split('\t')[0]
                self.list_device.append(device)
            except:
                pass
        
        return self.list_device
    
    def is_ldplayer_in_home(self, device_id, adb_path=None):
        """Kiểm tra LDPlayer đã vào màn hình chính chưa"""
        if adb_path is None:
            adb_path = self.ADB
        
        cmd = [
            os.path.join(adb_path, "adb.exe"),
            "-s", device_id,
            "shell", "dumpsys", "activity", "activities"
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            output = result.stdout
            
            # Check launcher home screen
            if "com.android.launcher3" in output or "com.miui.home" in output:
                return True
            
            return False
        except Exception as e:
            print(f"⚠️ Lỗi check home: {e}")
            return False
    
    def open_instagram(self, device_id, adb_path=None):
        """Mở Instagram app"""
        if adb_path is None:
            adb_path = self.ADB
        
        # Instagram package name
        ig_package = "com.instagram.android"
        
        cmd = [
            os.path.join(adb_path, "adb.exe"),
            "-s", device_id,
            "shell", "monkey", "-p", ig_package, "1"
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
            
            if "monkey" in result.stdout.lower() or result.returncode == 0:
                print(f"✅ Đã mở Instagram")
                return True
            else:
                print(f"⚠️ Instagram có thể chưa cài đặt")
                return False
        except Exception as e:
            print(f"❌ Lỗi mở Instagram: {e}")
            return False
    
    def click(self, x, y):
        """Click tại tọa độ x, y"""
        device = self.DEVICE()[self.index]
        command = os.path.join(self.ADB, f'adb.exe -s {device} shell input tap {x} {y}')
        self.adb_command(command)
        sleep(1)