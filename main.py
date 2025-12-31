"""Instagram Account Manager with LDPlayer Integration"""
import sys
import os
import subprocess
import json
import random
import string
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QTreeWidget, QTreeWidgetItem,
                             QPushButton, QLabel, QLineEdit, QSpinBox, QGroupBox,
                             QFileDialog, QMessageBox, QProgressBar, QTextEdit,
                             QCheckBox, QComboBox, QGridLayout, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import win32gui
import win32con
from ig_workflow import IGWorkflow


class LDPlayerManager:
    """LDPlayer management utilities"""
    
    @staticmethod
    def find_ldplayer_path():
        """Auto-detect LDPlayer installation path"""
        possible_paths = [
            r"C:\LDPlayer\LDPlayer9",
            r"C:\LDPlayer\LDPlayer4",
            r"D:\LDPlayer\LDPlayer9",
            r"D:\LDPlayer\LDPlayer4",
            r"C:\Program Files\LDPlayer9",
            r"C:\Program Files\LDPlayer4"
        ]
        
        for path in possible_paths:
            console_path = os.path.join(path, "ldconsole.exe")
            if os.path.exists(console_path):
                return path
        return None
    
    @staticmethod
    def find_tesseract_path():
        """Auto-detect Tesseract-OCR path"""
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"D:\Tesseract-OCR\tesseract.exe"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    @staticmethod
    def get_devices(ldplayer_path):
        """Get list of LDPlayer devices"""
        try:
            console = os.path.join(ldplayer_path, "ldconsole.exe")
            result = subprocess.run([console, "list2"], 
                                  capture_output=True, text=True, timeout=10)
            devices = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 4:
                        devices.append({
                            'index': parts[0],
                            'name': parts[1],
                            'title': parts[2],
                            'status': parts[4] if len(parts) > 4 else 'unknown'
                        })
            return devices
        except Exception as e:
            print(f"Error getting devices: {e}")
            return []
    
    @staticmethod
    def modify_device(ldplayer_path, index, **settings):
        """Modify LDPlayer device settings"""
        try:
            console = os.path.join(ldplayer_path, "ldconsole.exe")
            commands = []
            
            if 'cpu' in settings:
                commands.append([console, "modify", "--index", str(index), 
                               "--cpu", str(settings['cpu'])])
            if 'memory' in settings:
                commands.append([console, "modify", "--index", str(index), 
                               "--memory", str(settings['memory'])])
            if 'resolution' in settings:
                commands.append([console, "modify", "--index", str(index), 
                               "--resolution", settings['resolution']])
            if 'name' in settings:
                commands.append([console, "rename", "--index", str(index), 
                               "--title", settings['name']])
            
            for cmd in commands:
                subprocess.run(cmd, timeout=10)
            return True
        except Exception as e:
            print(f"Error modifying device: {e}")
            return False


class RegThread(QThread):
    """Thread for registration process"""
    progress = pyqtSignal(str)
    account_created = pyqtSignal(dict)
    finished = pyqtSignal()
    
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.running = True
    
    def run(self):
        """Run registration process"""
        total = self.settings['num_accounts']
        threads = self.settings['threads']
        delay = self.settings['delay']
        
        for i in range(total):
            if not self.running:
                break
                
            self.progress.emit(f"🔄 Đang tạo tài khoản {i+1}/{total}...")
            
            # Simulate account creation
            username = f"ig_{self.random_string(8)}"
            password = self.settings['password']
            email = f"{username}@temp-mail.com"
            
            # Simulate registration delay
            self.msleep(delay * 1000)
            
            account = {
                'username': username,
                'password': password,
                'email': email,
                'cookie': self.random_string(64),
                'status': 'Đã tạo'
            }
            
            self.account_created.emit(account)
            self.progress.emit(f"✅ Tạo thành công: {username}")
        
        self.finished.emit()
    
    def stop(self):
        self.running = False
    
    @staticmethod
    def random_string(length):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class WorkflowThread(QThread):
    """Thread to run IGWorkflow"""
    log_signal = pyqtSignal(str)
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)
    
    def __init__(self, settings_json, thread_id=0, ldplayer_name=None, account_index=None):
        super().__init__()
        self.settings_json = settings_json
        self.thread_id = thread_id
        self.ldplayer_name = ldplayer_name  # ✅ LDPlayer cụ thể cho thread này
        self.account_index = account_index   # ✅ Account index riêng
        self.running = True
    
    def run(self):
        """Run IGWorkflow with settings"""
        try:
            # Parse settings from JSON
            settings = json.loads(self.settings_json)
            ldplayer_settings = settings.get('ldplayer_settings', {})
            reg_settings = settings.get('reg_settings', {})
            
            # Print đầy đủ dữ liệu
            self.log_signal.emit("\n" + "="*60)
            self.log_signal.emit(f"🔷 THREAD #{self.thread_id + 1}")
            self.log_signal.emit(f"📱 LDPlayer: {self.ldplayer_name}")
            self.log_signal.emit(f"🔢 Account Index: {self.account_index}")
            self.log_signal.emit("="*60)
            self.log_signal.emit("📋 LDPlayer Settings:")
            for key, value in ldplayer_settings.items():
                self.log_signal.emit(f"   • {key}: {value}")
            self.log_signal.emit("\n📋 Registration Settings:")
            for key, value in reg_settings.items():
                self.log_signal.emit(f"   • {key}: {value}")
            self.log_signal.emit("="*60 + "\n")
            
            ldplayer_path = reg_settings.get('ldplayer_path', '')
            
            # ✅ Dùng ldplayer_name và account_index riêng biệt
            workflow = IGWorkflow(
                ldplayer_name=self.ldplayer_name,
                ldplayer_path=ldplayer_path,
                account_index=self.account_index,
                progress_callback=self.on_progress
            )
            
            # Chạy workflow
            self.log_signal.emit(f"🚀 [Thread #{self.thread_id + 1}] Bắt đầu chạy workflow...")
            
            result = workflow.run()
            
            if result:
                self.log_signal.emit(f"✅ [Thread #{self.thread_id + 1}] Hoàn thành!")
                self.finished.emit(True)
            else:
                self.log_signal.emit(f"❌ [Thread #{self.thread_id + 1}] Thất bại!")
                self.finished.emit(False)
        
        except Exception as e:
            error_msg = f"❌ [Thread #{self.thread_id + 1}] Lỗi: {str(e)}"
            self.log_signal.emit(error_msg)
            self.error.emit(str(e))
            self.finished.emit(False)
            import traceback
            self.log_signal.emit(traceback.format_exc())
    
    def on_progress(self, message):
        """Callback from workflow"""
        self.log_signal.emit(f"   {message}")
    
    def stop(self):
        self.running = False


class AccountManagerTab(QWidget):
    """Tab 1: Account Management"""
    
    def __init__(self):
        super().__init__()
        self.accounts = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_import = QPushButton("📂 Import")
        self.btn_export = QPushButton("💾 Export")
        self.btn_delete = QPushButton("🗑️ Xóa")
        self.btn_refresh = QPushButton("🔄 Refresh")
        
        toolbar.addWidget(self.btn_import)
        toolbar.addWidget(self.btn_export)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Account table
        self.tree_accounts = QTreeWidget()
        self.tree_accounts.setHeaderLabels(['Username', 'Password', 'Email', 'Cookie', 'Trạng thái'])
        self.tree_accounts.setColumnWidth(0, 150)
        self.tree_accounts.setColumnWidth(1, 120)
        self.tree_accounts.setColumnWidth(2, 200)
        self.tree_accounts.setColumnWidth(3, 300)
        layout.addWidget(self.tree_accounts)
        
        # Connect signals
        self.btn_import.clicked.connect(self.import_accounts)
        self.btn_export.clicked.connect(self.export_accounts)
        self.btn_delete.clicked.connect(self.delete_account)
        self.btn_refresh.clicked.connect(self.refresh_table)
    
    def add_account(self, account):
        """Add account to table"""
        item = QTreeWidgetItem([
            account['username'],
            account['password'],
            account['email'],
            account['cookie'][:30] + '...' if len(account['cookie']) > 30 else account['cookie'],
            account.get('status', 'Active')
        ])
        self.tree_accounts.addTopLevelItem(item)
        self.accounts.append(account)
    
    def import_accounts(self):
        """Import accounts from file"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Accounts", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    accounts = json.load(f)
                    for acc in accounts:
                        self.add_account(acc)
                QMessageBox.information(self, "Thành công", f"Đã import {len(accounts)} tài khoản!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể import: {e}")
    
    def export_accounts(self):
        """Export accounts to file"""
        if not self.accounts:
            QMessageBox.warning(self, "Cảnh báo", "Không có tài khoản để export!")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Accounts", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    json.dump(self.accounts, f, indent=2)
                QMessageBox.information(self, "Thành công", f"Đã export {len(self.accounts)} tài khoản!")
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể export: {e}")
    
    def delete_account(self):
        """Delete selected account"""
        current = self.tree_accounts.currentItem()
        if current:
            index = self.tree_accounts.indexOfTopLevelItem(current)
            self.tree_accounts.takeTopLevelItem(index)
            self.accounts.pop(index)
    
    def refresh_table(self):
        """Refresh account table"""
        self.tree_accounts.clear()
        for acc in self.accounts:
            item = QTreeWidgetItem([
                acc['username'],
                acc['password'],
                acc['email'],
                acc['cookie'][:30] + '...',
                acc.get('status', 'Active')
            ])
            self.tree_accounts.addTopLevelItem(item)


class RegTab(QWidget):
    """Tab 2: Registration"""
    
    def __init__(self, account_tab, viewer_tab=None):
        super().__init__()
        self.account_tab = account_tab
        self.viewer_tab = viewer_tab
        self.ldplayer_path = None
        self.tesseract_path = None
        self.reg_thread = None
        self.workflow_threads = []
        self.init_ui()
        self.auto_detect_paths()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Main split layout
        main_layout = QHBoxLayout()
        
        # Left side - Settings
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # LDPlayer Settings Group
        ld_group = QGroupBox("⚙️ Cài đặt LDPlayer")
        ld_layout = QGridLayout()
        
        ld_layout.addWidget(QLabel("CPU Cores:"), 0, 0)
        self.spin_cpu = QSpinBox()
        self.spin_cpu.setRange(1, 8)
        self.spin_cpu.setValue(2)
        ld_layout.addWidget(self.spin_cpu, 0, 1)
        
        ld_layout.addWidget(QLabel("RAM (MB):"), 1, 0)
        self.spin_ram = QSpinBox()
        self.spin_ram.setRange(512, 8192)
        self.spin_ram.setSingleStep(512)
        self.spin_ram.setValue(2048)
        ld_layout.addWidget(self.spin_ram, 1, 1)
        
        ld_layout.addWidget(QLabel("Resolution:"), 2, 0)
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(['720x1280', '1080x1920', '480x800'])
        ld_layout.addWidget(self.combo_resolution, 2, 1)
        
        ld_layout.addWidget(QLabel("DPI:"), 3, 0)
        self.spin_dpi = QSpinBox()
        self.spin_dpi.setRange(120, 480)
        self.spin_dpi.setValue(240)
        ld_layout.addWidget(self.spin_dpi, 3, 1)
        
        ld_layout.addWidget(QLabel("FPS:"), 4, 0)
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(30, 120)
        self.spin_fps.setValue(60)
        ld_layout.addWidget(self.spin_fps, 4, 1)
        
        self.check_random_device = QCheckBox("🎲 Random Device Info (Name, Model, IMEI)")
        self.check_random_device.setChecked(False)
        ld_layout.addWidget(self.check_random_device, 5, 0, 1, 2)
        
        ld_group.setLayout(ld_layout)
        left_layout.addWidget(ld_group)
        
        # Registration Settings Group
        reg_group = QGroupBox("📝 Cài đặt Đăng ký")
        reg_layout = QGridLayout()
        
        reg_layout.addWidget(QLabel("Số luồng:"), 0, 0)
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 10)
        self.spin_threads.setValue(3)
        reg_layout.addWidget(self.spin_threads, 0, 1)
        
        reg_layout.addWidget(QLabel("Delay (giây):"), 1, 0)
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(1, 300)
        self.spin_delay.setValue(30)
        reg_layout.addWidget(self.spin_delay, 1, 1)
        
        reg_layout.addWidget(QLabel("Số tài khoản:"), 2, 0)
        self.spin_accounts = QSpinBox()
        self.spin_accounts.setRange(1, 1000)
        self.spin_accounts.setValue(10)
        reg_layout.addWidget(self.spin_accounts, 2, 1)
        
        reg_layout.addWidget(QLabel("Mật khẩu:"), 3, 0)
        self.edit_password = QLineEdit()
        self.edit_password.setPlaceholderText("Password123@")
        self.edit_password.setText("Password123@")
        reg_layout.addWidget(self.edit_password, 3, 1)
        
        reg_group.setLayout(reg_layout)
        left_layout.addWidget(reg_group)
        
        # Path Settings Group
        path_group = QGroupBox("📂 Đường dẫn")
        path_layout = QVBoxLayout()
        
        ld_path_layout = QHBoxLayout()
        self.edit_ldplayer_path = QLineEdit()
        self.edit_ldplayer_path.setPlaceholderText("Đường dẫn LDPlayer...")
        self.btn_browse_ld = QPushButton("...")
        self.btn_browse_ld.setMaximumWidth(40)
        ld_path_layout.addWidget(QLabel("LDPlayer:"))
        ld_path_layout.addWidget(self.edit_ldplayer_path)
        ld_path_layout.addWidget(self.btn_browse_ld)
        path_layout.addLayout(ld_path_layout)
        
        tess_path_layout = QHBoxLayout()
        self.edit_tesseract_path = QLineEdit()
        self.edit_tesseract_path.setPlaceholderText("Đường dẫn Tesseract-OCR...")
        self.btn_browse_tess = QPushButton("...")
        self.btn_browse_tess.setMaximumWidth(40)
        tess_path_layout.addWidget(QLabel("Tesseract:"))
        tess_path_layout.addWidget(self.edit_tesseract_path)
        tess_path_layout.addWidget(self.btn_browse_tess)
        path_layout.addLayout(tess_path_layout)
        
        path_group.setLayout(path_layout)
        left_layout.addWidget(path_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶️ Bắt đầu")
        self.btn_start.setStyleSheet("background: #10b981; color: white; font-weight: bold; padding: 10px;")
        self.btn_stop = QPushButton("⏸️ Dừng")
        self.btn_stop.setEnabled(False)
        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        left_layout.addLayout(control_layout)
        
        # Progress
        self.progress_bar = QProgressBar()
        left_layout.addWidget(self.progress_bar)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        left_layout.addWidget(QLabel("📋 Log:"))
        left_layout.addWidget(self.log_text)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget, 1)
        
        # Right side - Device list & Accounts
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Device list
        right_layout.addWidget(QLabel("🖥️ Danh sách LDPlayer:"))
        self.tree_devices = QTreeWidget()
        self.tree_devices.setHeaderLabels(['Index', 'Tên', 'Trạng thái'])
        self.tree_devices.setMaximumHeight(200)
        right_layout.addWidget(self.tree_devices)
        
        self.btn_refresh_devices = QPushButton("🔄 Refresh Devices")
        right_layout.addWidget(self.btn_refresh_devices)
        
        # Accounts created
        right_layout.addWidget(QLabel("📱 Tài khoản đã tạo:"))
        self.tree_created = QTreeWidget()
        self.tree_created.setHeaderLabels(['Username', 'Password', 'Email', 'Cookie'])
        right_layout.addWidget(self.tree_created)
        
        # Export button for created accounts
        self.btn_export_created = QPushButton("💾 Export Tài khoản")
        self.btn_export_created.setStyleSheet("background: #10b981; color: white; font-weight: bold; padding: 8px;")
        right_layout.addWidget(self.btn_export_created)
        
        main_layout.addWidget(right_widget, 1)
        
        layout.addLayout(main_layout)
        
        # Connect signals
        self.btn_browse_ld.clicked.connect(self.browse_ldplayer)
        self.btn_browse_tess.clicked.connect(self.browse_tesseract)
        self.btn_refresh_devices.clicked.connect(self.refresh_devices)
        self.btn_start.clicked.connect(self.start_registration)
        self.btn_stop.clicked.connect(self.stop_registration)
        self.btn_export_created.clicked.connect(self.export_created_accounts)
    
    def auto_detect_paths(self):
        """Auto-detect installation paths"""
        ld_path = LDPlayerManager.find_ldplayer_path()
        if ld_path:
            self.ldplayer_path = ld_path
            self.edit_ldplayer_path.setText(ld_path)
            self.log("✅ Đã tìm thấy LDPlayer tại: " + ld_path)
            self.refresh_devices()
        else:
            self.log("⚠️ Không tìm thấy LDPlayer. Vui lòng cài đặt hoặc chọn thủ công.")
        
        tess_path = LDPlayerManager.find_tesseract_path()
        if tess_path:
            self.tesseract_path = tess_path
            self.edit_tesseract_path.setText(tess_path)
            self.log("✅ Đã tìm thấy Tesseract-OCR tại: " + tess_path)
        else:
            self.log("⚠️ Không tìm thấy Tesseract-OCR. Vui lòng cài đặt từ: https://github.com/tesseract-ocr/tesseract")
    
    def browse_ldplayer(self):
        """Browse for LDPlayer path"""
        path = QFileDialog.getExistingDirectory(self, "Chọn thư mục LDPlayer")
        if path:
            self.ldplayer_path = path
            self.edit_ldplayer_path.setText(path)
            self.refresh_devices()
    
    def browse_tesseract(self):
        """Browse for Tesseract path"""
        path, _ = QFileDialog.getOpenFileName(self, "Chọn tesseract.exe", "", "Executable (*.exe)")
        if path:
            self.tesseract_path = path
            self.edit_tesseract_path.setText(path)
    
    def refresh_devices(self):
        """Refresh device list"""
        if not self.ldplayer_path:
            return
        
        self.tree_devices.clear()
        devices = LDPlayerManager.get_devices(self.ldplayer_path)
        
        for device in devices:
            item = QTreeWidgetItem([
                device['index'],
                device['name'],
                device['status']
            ])
            self.tree_devices.addTopLevelItem(item)
        
        self.log(f"🔄 Đã tìm thấy {len(devices)} thiết bị LDPlayer")
    
    def export_created_accounts(self):
        """Export created accounts to JSON file"""
        if self.tree_created.topLevelItemCount() == 0:
            QMessageBox.warning(self, "Cảnh báo", "Không có tài khoản nào để export!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export Tài khoản", 
            "accounts_" + str(random.randint(1000, 9999)) + ".json",
            "JSON Files (*.json)"
        )
        
        if file_path:
            try:
                accounts = []
                for i in range(self.tree_created.topLevelItemCount()):
                    item = self.tree_created.topLevelItem(i)
                    accounts.append({
                        'username': item.text(0),
                        'password': item.text(1),
                        'email': item.text(2),
                        'cookie': item.text(3) if len(item.text(3)) > 35 else item.text(3) + '...'
                    })
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(accounts, f, indent=2, ensure_ascii=False)
                
                self.log(f"✅ Đã export {len(accounts)} tài khoản vào: {file_path}")
                QMessageBox.information(self, "Thành công", f"Đã export {len(accounts)} tài khoản thành công!")
            except Exception as e:
                self.log(f"❌ Lỗi khi export: {e}")
                QMessageBox.critical(self, "Lỗi", f"Không thể export: {e}")
    
    def start_registration(self):
        """Start registration process with multiple threads"""
        if not self.ldplayer_path:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn đường dẫn LDPlayer!")
            return
        
        if not self.tesseract_path:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn đường dẫn Tesseract-OCR!")
            return
        
        # ✅ Lấy danh sách tất cả LDPlayer
        from auto_instagram import ldplayer
        ld = ldplayer()
        ld.ADB = self.ldplayer_path
        ldplayer_names = ld.get_ldplayer_names_list()
        
        if not ldplayer_names:
            QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy LDPlayer nào trong hệ thống!")
            self.log("❌ Không tìm thấy LDPlayer!")
            return
        
        self.log(f"✅ Tìm thấy {len(ldplayer_names)} LDPlayer: {', '.join(ldplayer_names)}\n")
        
        # ✅ Lưu danh sách LDPlayer để embed sau
        self._ldplayer_names = ldplayer_names
        
        # Collect all settings
        ldplayer_settings = {
            'cpu': self.spin_cpu.value(),
            'ram': self.spin_ram.value(),
            'resolution': self.combo_resolution.currentText(),
            'dpi': self.spin_dpi.value(),
            'fps': self.spin_fps.value(),
            'random_device': self.check_random_device.isChecked()
        }
        
        reg_settings = {
            'threads': self.spin_threads.value(),
            'delay': self.spin_delay.value(),
            'num_accounts': self.spin_accounts.value(),
            'password': self.edit_password.text(),
            'ldplayer_path': self.ldplayer_path,
            'tesseract_path': self.tesseract_path,
            'ldplayer_name': 'LDPlayer',  # Will be overridden per thread
            'account_index': 0
        }
        
        # Create combined settings JSON
        all_settings = {
            'ldplayer_settings': ldplayer_settings,
            'reg_settings': reg_settings
        }
        
        settings_json = json.dumps(all_settings, indent=2, ensure_ascii=False)
        
        # Log settings
        self.log("="*60)
        self.log("📋 CÀI ĐẶT HỆ THỐNG")
        self.log("="*60)
        self.log(settings_json)
        self.log("="*60 + "\n")
        
        # Tạo nhiều WorkflowThread theo số luồng
        num_threads = self.spin_threads.value()
        self.workflow_threads = []
        
        # ✅ Chỉ chạy max số LDPlayer có sẵn
        num_threads = min(num_threads, len(ldplayer_names))
        
        self.log(f"🔷 Bắt đầu {num_threads} luồng xử lý với {num_threads} LDPlayer...\n")
        
        for i in range(num_threads):
            # ✅ Gán LDPlayer khác nhau cho mỗi thread
            ldplayer_name = ldplayer_names[i]
            account_index = i
            
            # Tạo thread với settings riêng biệt
            thread = WorkflowThread(settings_json, thread_id=i, 
                                   ldplayer_name=ldplayer_name, 
                                   account_index=account_index)
            thread.log_signal.connect(self.log)
            thread.finished.connect(lambda success, thread_id=i: self.on_workflow_finished(success, thread_id))
            thread.error.connect(self.on_workflow_error)
            
            self.workflow_threads.append(thread)
            thread.start()
        
        # Disable nút Start, enable nút Stop
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.log(f"✅ Đã khởi động {num_threads} luồng")
        
        # Tự động embed LDPlayer sau 20 giây
        QTimer.singleShot(20000, self.auto_embed_ldplayers)
    
    def stop_registration(self):
        """Stop registration process"""
        if self.workflow_threads:
            for thread in self.workflow_threads:
                if thread.isRunning():
                    thread.stop()
                    thread.quit()
                    thread.wait()
            self.log("⏸️ Tất cả workflows đã dừng")
            self.workflow_threads = []
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
        else:
            self.log("⚠️ Không có workflow đang chạy")
    
    def on_workflow_finished(self, success, thread_id=0):
        """Handle workflow completion"""
        if success:
            self.log(f"✅ [Thread #{thread_id + 1}] Hoàn thành!")
        else:
            self.log(f"❌ [Thread #{thread_id + 1}] Thất bại!")
        
        # Kiểm tra nếu tất cả threads đã xong
        all_finished = all(not thread.isRunning() for thread in self.workflow_threads)
        if all_finished:
            self.log("\n" + "="*60)
            self.log("🏁 TẤT CẢ LUỒNG ĐÃ HOÀN THÀNH")
            self.log("="*60)
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
    
    def on_workflow_error(self, error_msg):
        """Handle workflow error"""
        self.log(f"❌ Lỗi workflow: {error_msg}")
        QMessageBox.critical(self, "Lỗi", f"Lỗi xảy ra: {error_msg}")
    
    def auto_embed_ldplayers(self):
        """Tự động embed tất cả LDPlayer vào ViewerTab"""
        if self.viewer_tab and hasattr(self, '_ldplayer_names'):
            self.log("\n🔄 Tự động nhúng LDPlayer vào View...")
            self.viewer_tab.embed_ldplayers(self._ldplayer_names)
    
    def on_account_created(self, account):
        """Handle account creation - Not implemented yet"""
        pass
    
    def on_registration_finished(self):
        """Handle registration completion - Not implemented yet"""
        pass
    
    def log(self, message):
        """Add message to log"""
        self.log_text.append(message)


class EmbedThread(QThread):
    """Thread để embed LDPlayer không block UI"""
    embed_signal = pyqtSignal(int, int, str)  # slot_index, hwnd, title
    finished_signal = pyqtSignal(int)  # tổng số embed
    
    def __init__(self, ldplayer_names, ldplayer_count):
        super().__init__()
        self.ldplayer_names = ldplayer_names
        self.ldplayer_count = ldplayer_count
    
    def run(self):
        """Tìm LDPlayer windows và emit signals"""
        def enum_handler(hwnd, results):
            if not win32gui.IsWindowVisible(hwnd):
                return
            
            try:
                title = win32gui.GetWindowText(hwnd)
                # ✅ CHỈ lấy windows có tên CHÍNH XÁC là LDPlayer (không PyQt5)
                # LDPlayer window title format: "LDPlayer-X" hoặc "LDPlayer 9.1"
                if ('LDPlayer' in title and 
                    any(name in title for name in self.ldplayer_names) and
                    'Instagram' not in title):  # ✅ LOẠI BỎ Instagram Manager app
                    # ✅ Skip nếu là child window hoặc helper
                    style = win32gui.GetWindowLong(hwnd, -16)  # GWL_STYLE
                    if not (style & 0x40000000):  # WS_CHILD
                        results.append((hwnd, title))
            except:
                pass
        
        windows = []
        try:
            win32gui.EnumWindows(enum_handler, windows)
        except:
            pass
        
        # ✅ Sort windows để embed đúng thứ tự
        windows.sort(key=lambda x: x[1])
        
        # ✅ Emit embed signals từ slot 0 (không skip slot 0)
        for i, (hwnd, title) in enumerate(windows[:self.ldplayer_count]):
            self.embed_signal.emit(i, hwnd, title)
            self.msleep(500)  # Delay để tránh race condition
        
        self.finished_signal.emit(len(windows))


class ViewerTab(QWidget):
    """Tab 3: LDPlayer Viewer"""
    
    def __init__(self):
        super().__init__()
        self.slots = []
        self.slots_per_row = 3
        self.embed_thread = None
        self.ldplayer_names = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.btn_scan = QPushButton("🔍 Scan Windows")
        self.btn_embed = QPushButton("📌 Embed Selected")
        self.btn_clear = QPushButton("🧹 Clear All")
        
        toolbar.addWidget(self.btn_scan)
        toolbar.addWidget(self.btn_embed)
        toolbar.addWidget(self.btn_clear)
        
        # Slots per row setting
        toolbar.addWidget(QLabel("   |   LDPlayer mỗi hàng:"))
        self.spin_per_row = QSpinBox()
        self.spin_per_row.setRange(1, 6)
        self.spin_per_row.setValue(3)
        self.spin_per_row.setMaximumWidth(60)
        self.spin_per_row.valueChanged.connect(self.update_grid_layout)
        toolbar.addWidget(self.spin_per_row)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Scroll area for slots
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.slots_layout = QGridLayout(self.scroll_widget)
        self.scroll.setWidget(self.scroll_widget)
        
        layout.addWidget(self.scroll)
        
        # Initialize 6 slots (2x3 grid by default)
        self.create_initial_slots()
        
        # Connect signals
        self.btn_scan.clicked.connect(self.scan_windows)
        self.btn_clear.clicked.connect(self.clear_slots)
        self.btn_embed.clicked.connect(self.embed_ldplayers)
    
    def create_initial_slots(self):
        """Create initial 6 slots"""
        for i in range(6):
            slot = self.create_slot(i)
            self.slots.append(slot)
        self.update_grid_layout()
    
    def update_grid_layout(self):
        """Update grid layout based on slots per row"""
        self.slots_per_row = self.spin_per_row.value()
        
        # Clear current layout
        for i in reversed(range(self.slots_layout.count())): 
            self.slots_layout.itemAt(i).widget().setParent(None)
        
        # Re-add slots with new layout
        for i, slot in enumerate(self.slots):
            row = i // self.slots_per_row
            col = i % self.slots_per_row
            self.slots_layout.addWidget(slot, row, col)
    
    def create_slot(self, slot_id):
        """Create a viewer slot"""
        from ldplayer_slot import PlayerSlot
        return PlayerSlot(slot_id, width=320, height=580)
    
    def scan_windows(self):
        """Scan for LDPlayer windows"""
        def enum_handler(hwnd, results):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if 'LDPlayer' in title or 'LD' in title:
                    results.append((hwnd, title))
        
        windows = []
        win32gui.EnumWindows(enum_handler, windows)
        
        if windows:
            msg = "Tìm thấy các cửa sổ LDPlayer:\n\n"
            for hwnd, title in windows:
                msg += f"• {title}\n"
            QMessageBox.information(self, "Scan Results", msg)
        else:
            QMessageBox.information(self, "Scan Results", "Không tìm thấy cửa sổ LDPlayer nào!")
    
    def embed_ldplayers(self, ldplayer_names=None):
        """Auto scan và embed LDPlayer windows - async threading"""
        if ldplayer_names:
            self.ldplayer_names = ldplayer_names
        
        if not self.ldplayer_names:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chạy workflow trước!")
            return
        
        # ✅ Chạy embedding trên thread riêng để không block UI
        self.embed_thread = EmbedThread(self.ldplayer_names, len(self.slots))
        self.embed_thread.embed_signal.connect(self.on_embed_slot)
        self.embed_thread.finished_signal.connect(self.on_embed_finished)
        self.embed_thread.start()
        
        print(f"🔄 Bắt đầu embed {len(self.ldplayer_names)} LDPlayer...")
    
    def on_embed_slot(self, slot_index, hwnd, title):
        """Callback khi embed 1 slot"""
        try:
            if slot_index < len(self.slots):
                self.slots[slot_index].embed_window(hwnd, title)
                print(f"✅ Nhúng {title} vào Slot {slot_index + 1}")
        except Exception as e:
            print(f"❌ Lỗi nhúng slot {slot_index + 1}: {e}")
    
    def on_embed_finished(self, count):
        """Callback khi embed xong"""
        if count > 0:
            msg = f"✅ Đã nhúng thành công {count} LDPlayer!\n\n⚠️ Lưu ý: Bạn vẫn có thể click vào ứng dụng chính bên ngoài (không vào slot)"
            print(msg)
            QMessageBox.information(self, "Hoàn tất", msg)
        else:
            QMessageBox.warning(self, "Cảnh báo", "Không tìm thấy LDPlayer nào!")
    
    def clear_slots(self):
        """Clear all slots"""
        for slot in self.slots:
            if slot.is_embedded:
                slot.placeholder.show()
                slot.header.setText(f"Slot {slot.slot_id + 1}: Trống")
                slot.is_embedded = False


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📱 Instagram Account Manager")
        self.setGeometry(100, 100, 1400, 900)
        self.init_ui()
        self.apply_styles()
    
    def init_ui(self):
        """Initialize UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("📱 Instagram Manager")
        header.setFont(QFont("Arial", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #3b82f6; padding: 10px;")
        layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.account_tab = AccountManagerTab()
        self.viewer_tab = ViewerTab()
        self.reg_tab = RegTab(self.account_tab, self.viewer_tab)
        
        self.tabs.addTab(self.account_tab, "👥 Quản lý Accounts")
        self.tabs.addTab(self.reg_tab, "📝 Đăng ký IG")
        self.tabs.addTab(self.viewer_tab, "🖥️ View LDPlayer")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage("Sẵn sàng")
    
    def apply_styles(self):
        """Apply application styles"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #16213e;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 2px solid #3e3e3e;
                border-radius: 5px;
            }
            QTabBar::tab {
                background: #0f0f0f;
                color: #888888;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #4b5563;
                color: #9ca3af;
            }
            QLineEdit, QSpinBox, QComboBox {
                background: #0f0f0f;
                border: 2px solid #3e3e3e;
                border-radius: 5px;
                padding: 5px;
                color: #e0e0e0;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #3b82f6;
            }
            QTreeWidget {
                background: #0f0f0f;
                border: 2px solid #3e3e3e;
                border-radius: 5px;
                color: #e0e0e0;
                alternate-background-color: #1a1a2e;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QTreeWidget::item:hover {
                background: #2563eb;
            }
            QHeaderView::section {
                background: #0f0f0f;
                color: #64b5f6;
                padding: 5px;
                border: 1px solid #3e3e3e;
                font-weight: bold;
            }
            QGroupBox {
                border: 2px solid #3e3e3e;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #64b5f6;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background: #16213e;
            }
            QTextEdit {
                background: #0f0f0f;
                border: 2px solid #3e3e3e;
                border-radius: 5px;
                padding: 5px;
                color: #e0e0e0;
            }
            QProgressBar {
                border: 2px solid #3e3e3e;
                border-radius: 5px;
                text-align: center;
                background: #0f0f0f;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3b82f6, stop:1 #10b981);
                border-radius: 3px;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QLabel {
                color: #e0e0e0;
            }
            QStatusBar {
                background: #0f0f0f;
                color: #64b5f6;
                border-top: 2px solid #3e3e3e;
            }
        """)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Instagram Manager")
    app.setOrganizationName("IGManager")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()