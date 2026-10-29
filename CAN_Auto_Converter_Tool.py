import os
import sys
import zipfile
import glob
import time
import subprocess
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import shutil
import threading

# ================= 屏幕 DPI 适配 =================
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# ================= 核心坐标基准 (基于 150% 缩放) =================
BASE_SCALE = 150 
POS_TAB_CONVERT = (1227, 116)  
POS_FILE_PATH   = (545, 199)   
POS_SAVE_PATH   = (492, 289)   
POS_CONVERT_BTN = (882, 387)   
POS_OK_BTN      = (840, 640)   

CHECKBOXES_TO_UNCHECK = [
    (128, 339), (236, 331), (349, 327), (569, 325), (689, 330), 
    (807, 324), (918, 340), (1038, 337), (1144, 328), (1263, 331)
]
# ==========================================

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAN 数据自动化转换工具")
        self.root.geometry("700x600")
        
        self.is_running = False
        self.user_scale = 150 
        
        self.setup_ui()

    def setup_ui(self):
        frame_paths = tk.LabelFrame(self.root, text="路径配置", padx=10, pady=10)
        frame_paths.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_paths, text="Source 目录 (ZIP所在):").grid(row=0, column=0, sticky="e", pady=5)
        self.entry_source = tk.Entry(frame_paths, width=50)
        self.entry_source.grid(row=0, column=1, padx=5)
        tk.Button(frame_paths, text="浏览", command=lambda: self.select_dir(self.entry_source)).grid(row=0, column=2)

        tk.Label(frame_paths, text="Final 目录 (输出所在):").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_final = tk.Entry(frame_paths, width=50)
        self.entry_final.grid(row=1, column=1, padx=5)
        tk.Button(frame_paths, text="浏览", command=lambda: self.select_dir(self.entry_final)).grid(row=1, column=2)

        tk.Label(frame_paths, text="转换软件 (exe路径):").grid(row=2, column=0, sticky="e", pady=5)
        self.entry_software = tk.Entry(frame_paths, width=50)
        self.entry_software.grid(row=2, column=1, padx=5)
        tk.Button(frame_paths, text="浏览", command=lambda: self.select_file(self.entry_software)).grid(row=2, column=2)

        frame_params = tk.LabelFrame(self.root, text="参数设置", padx=10, pady=10)
        frame_params.pack(fill="x", padx=10, pady=5)

        tk.Label(frame_params, text="当前电脑缩放比例 (%):").pack(side="left")
        self.entry_scale = tk.Entry(frame_params, width=10)
        self.entry_scale.insert(0, "150")
        self.entry_scale.pack(side="left", padx=10)
        tk.Label(frame_params, text="(请在 Windows 设置->显示->缩放与布局 中查看)").pack(side="left")

        frame_controls = tk.Frame(self.root)
        frame_controls.pack(fill="x", padx=10, pady=5)

        self.btn_start = tk.Button(frame_controls, text="▶ 开始转换", bg="#4CAF50", fg="white", font=("微软雅黑", 12, "bold"), command=self.start_conversion)
        self.btn_start.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_stop = tk.Button(frame_controls, text="⏹ 停止", bg="#f44336", fg="white", font=("微软雅黑", 12, "bold"), state="disabled", command=self.stop_conversion)
        self.btn_stop.pack(side="left", padx=5, expand=True, fill="x")

        frame_log = tk.LabelFrame(self.root, text="运行日志", padx=10, pady=10)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.text_log = scrolledtext.ScrolledText(frame_log, height=15, state="disabled", bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 10))
        self.text_log.pack(fill="both", expand=True)

    def select_dir(self, entry_widget):
        path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def select_file(self, entry_widget):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, path)

    def log(self, message, is_error=False):
        self.text_log.config(state="normal")
        if is_error:
            self.text_log.insert(tk.END, f"❌ {message}\n", "error")
            self.text_log.tag_config("error", foreground="red")
        else:
            self.text_log.insert(tk.END, f"{message}\n")
        self.text_log.see(tk.END)
        self.text_log.config(state="disabled")

    def update_coord(self, pos):
        x, y = pos
        scale_factor = self.user_scale / BASE_SCALE
        return int(x * scale_factor), int(y * scale_factor)

    def click_mouse(self, pos):
        x, y = self.update_coord(pos)
        ctypes.windll.user32.SetCursorPos(x, y)
        ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0) 
        ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0) 
        time.sleep(0.2)

    def copy_to_clipboard(self, text):
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()

    def press_hotkey_ctrl_v(self):
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x56, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
        time.sleep(0.2)

    def press_hotkey_ctrl_a(self):
        ctypes.windll.user32.keybd_event(0x11, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x41, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x41, 0, 2, 0)
        ctypes.windll.user32.keybd_event(0x11, 0, 2, 0)
        time.sleep(0.1)

    def press_delete_key(self):
        ctypes.windll.user32.keybd_event(0x2E, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x2E, 0, 2, 0)
        time.sleep(0.1)

    def start_conversion(self):
        source_dir = self.entry_source.get().strip().replace('\u202a', '')
        final_dir = self.entry_final.get().strip().replace('\u202a', '')
        software_exe = self.entry_software.get().strip().replace('\u202a', '')
        
        try:
            self.user_scale = float(self.entry_scale.get().strip())
        except ValueError:
            messagebox.showerror("错误", "缩放比例必须是数字！(例如 100 或 150)")
            return

        if not all([source_dir, final_dir, software_exe]):
            messagebox.showerror("错误", "请填满所有路径输入框！")
            return
        if not os.path.exists(software_exe):
            messagebox.showerror("错误", "找不到指定的转换软件 exe！")
            return

        os.makedirs(final_dir, exist_ok=True)

        self.is_running = True
        self.btn_start.config(state="disabled", bg="#cccccc")
        self.btn_stop.config(state="normal", bg="#f44336")
        self.text_log.config(state="normal")
        self.text_log.delete(1.0, tk.END)
        self.text_log.config(state="disabled")

        thread = threading.Thread(target=self.run_pipeline, args=(source_dir, final_dir, software_exe))
        thread.daemon = True
        thread.start()

    def stop_conversion(self):
        self.is_running = False
        self.log("\n⚠️ 用户请求停止，正在终止当前任务...", is_error=True)

    def run_pipeline(self, source_dir, final_dir, software_exe):
        try:
            self.log(f"📂 源目录: {source_dir}")
            self.log(f"📂 目标目录: {final_dir}")
            self.log(f"🛠️ 软件路径: {software_exe}")
            self.log(f"🖥️ 电脑缩放比例: {self.user_scale}%")
            self.log("-" * 50)

            self.log("正在扫描和解压压缩包...")
            temp_dir = os.path.join(final_dir, "temp_extract")
            try:
                zst_folders = self.extract_and_isolate(source_dir, temp_dir)
            except Exception as e:
                self.log(f"❌ 解压过程发生权限错误: {e}", is_error=True)
                self.reset_ui()
                return
            
            if not self.is_running: return
            if not zst_folders:
                self.log("没有找到任何包含 zst 文件的压缩包！", is_error=True)
                self.reset_ui()
                return

            self.log(f"成功定位到 {len(zst_folders)} 个待处理文件夹。")
            self.log("正在尝试启动转换软件...")
            
            # ================= 🚨 半自动确认启动逻辑 =================
            exe_dir = os.path.dirname(software_exe)
            try:
                # 依然尝试发一次启动指令，万一成功了呢
                ctypes.windll.shell32.ShellExecuteW(None, "open", software_exe, None, exe_dir, 1)
            except:
                pass
            
            time.sleep(2) # 给软件 2 秒的反应时间
            
            # 无论成功与否，弹窗让用户确认
            msg = ("由于公司安全策略限制，程序无法强制拉起转换软件。\n\n"
                   "1. 如果软件【已经弹出】，请直接点击【是】开始自动化。\n"
                   "2. 如果软件【没有弹出】，请先手动双击打开转换软件，\n"
                   "   然后再点击【是】。\n\n"
                   "（点击后请勿触碰鼠标键盘，程序将接管操作）")
            
            dialog_event = threading.Event()
            user_response = [False]
            
            def ask_user():
                user_response[0] = messagebox.askyesno("确认软件状态", msg)
                dialog_event.set()
                
            self.root.after(0, ask_user)
            dialog_event.wait() # 暂停子线程，等待用户点击
            
            if not user_response[0]:
                self.log("用户取消了任务。", is_error=True)
                self.is_running = False
                self.reset_ui()
                return
                
            self.log("用户确认软件已就绪，开始执行自动化！")
            
            # 给一点点缓冲时间让用户的手离开鼠标
            self.log("3 秒后接管鼠标...")
            time.sleep(3)
            # =========================================================

            for idx, folder in enumerate(zst_folders):
                if not self.is_running:
                    break
                self.log(f"\n[{idx+1}/{len(zst_folders)}] 开始处理...")
                is_first = (idx == 0)
                self.process_single_folder(folder, final_dir, is_first)

            if self.is_running:
                self.log("\n🎊 全部任务处理完毕！")
                messagebox.showinfo("完成", "所有文件转换完毕！")
                
        except Exception as e:
            self.log(f"发生致命错误: {e}", is_error=True)
            messagebox.showerror("错误", f"发生异常: {e}")
        finally:
            self.reset_ui()

    def reset_ui(self):
        self.is_running = False
        self.btn_start.config(state="normal", bg="#4CAF50")
        self.btn_stop.config(state="disabled", bg="#cccccc")

    def extract_and_isolate(self, source_dir, extract_base_dir):
        zst_folders = []
        os.makedirs(extract_base_dir, exist_ok=True)
        zip_files = glob.glob(os.path.join(source_dir, "*.[zZ][iI][pP]"))
        
        for zip_path in zip_files:
            if not self.is_running: break
            zip_name = os.path.splitext(os.path.basename(zip_path))[0]
            extract_target = os.path.join(extract_base_dir, zip_name)
            os.makedirs(extract_target, exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as z:
                    z.extractall(extract_target)
                    
                for root, dirs, files in os.walk(extract_target):
                    if any(f.lower().endswith('.zst') for f in files):
                        zst_folders.append(root)
                        break
            except Exception as e:
                self.log(f"解压失败 {zip_name}: {e}", is_error=True)
                    
        return zst_folders

    def process_single_folder(self, target_folder, final_dir, is_first_run=False):
        start_time = time.time()
        
        self.click_mouse(POS_TAB_CONVERT)
        time.sleep(1)
        
        self.copy_to_clipboard(target_folder)
        self.click_mouse(POS_FILE_PATH)
        self.press_hotkey_ctrl_a()
        self.press_delete_key()
        self.press_hotkey_ctrl_v()
        time.sleep(0.5)
        
        self.copy_to_clipboard(target_folder)
        self.click_mouse(POS_SAVE_PATH)
        self.press_hotkey_ctrl_a()
        self.press_delete_key()
        self.press_hotkey_ctrl_v()
        time.sleep(0.5)
        
        if is_first_run:
            self.log("  └─ 首次运行，正在取消多余 CAN 通道...")
            for pos in CHECKBOXES_TO_UNCHECK:
                self.click_mouse(pos)
                time.sleep(0.1)
            time.sleep(0.5)
        
        self.click_mouse(POS_CONVERT_BTN)
        self.log("  └─ 已点击转换，等待完成...")
        
        timeout = 180
        success = False
        new_asc_files = []
        
        while time.time() - start_time < timeout and self.is_running:
            time.sleep(1) 
            current_asc_files = glob.glob(os.path.join(target_folder, "*.asc"))
            for f in current_asc_files:
                if os.path.getmtime(f) > start_time:
                    new_asc_files.append(f)
            
            if new_asc_files:
                time.sleep(1.5)
                self.click_mouse(POS_OK_BTN)
                time.sleep(1) 
                
                for asc_file in set(new_asc_files):
                    file_name = os.path.basename(asc_file)
                    dest_path = os.path.join(final_dir, file_name)
                    try:
                        if os.path.exists(dest_path):
                            os.remove(dest_path)
                        shutil.move(asc_file, dest_path)
                        self.log(f"  └─ ✅ 成功: {file_name}")
                    except Exception as e:
                        self.log(f"  └─ ❌ 移动文件失败: {e}", is_error=True)
                
                success = True
                break
                
        if not success and self.is_running:
            self.log(f"  └─ ⚠️ 超时未检测到新文件！", is_error=True)
            self.click_mouse(POS_OK_BTN) 

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()