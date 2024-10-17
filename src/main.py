import requests
import yaml
import logging
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog, simpledialog
from threading import Thread
from PIL import Image, ImageTk
from io import BytesIO
import pyperclip
import os
import sys

# 경로 처리 함수 (PyInstaller와 호환)
def get_resource_path(relative_path):
    """ PyInstaller로 패키징된 실행 파일에서 리소스 파일 경로를 반환 """
    try:
        base_path = sys._MEIPASS  # PyInstaller가 생성한 임시 폴더 경로
    except Exception:
        base_path = os.path.abspath(".")  # 실행 파일 경로

    return os.path.join(base_path, relative_path)

# 사용자 홈 디렉토리에 .ImageFinder 폴더 경로 설정
HOME_DIR = os.path.expanduser("~")
CONFIG_DIR = os.path.join(HOME_DIR, ".ImageFinder")
CONFIG_PATH = os.path.join(CONFIG_DIR, "pixabay.yaml")

# 폴더가 없으면 생성
if not os.path.exists(CONFIG_DIR):
    os.makedirs(CONFIG_DIR)

IMAGES_PER_PAGE = 20

class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, msg + '\n')
        self.text_widget.config(state=tk.DISABLED)
        self.text_widget.yview(tk.END)

class PixabayDownloader:
    @staticmethod
    def load_api_key(config_path: str = CONFIG_PATH) -> str:
        """ pixabay.yaml 파일에서 API 키를 로드합니다. """
        try:
            # 파일이 없으면 오류를 발생시킴
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Config file {config_path} not found.")
            
            with open(config_path, 'r') as file:
                api_key = yaml.safe_load(file)
                return api_key
        except Exception as e:
            print(f"Failed to load API key: {e}")
            return None

    @staticmethod
    def save_api_key(new_key: str, config_path: str = CONFIG_PATH):
        """ 새로운 API 키를 pixabay.yaml 파일에 저장합니다. """
        try:
            # 디렉토리가 없으면 생성
            os.makedirs(CONFIG_DIR, exist_ok=True)
            
            with open(config_path, 'w') as file:
                yaml.safe_dump(new_key, file)
            logging.info("API key updated successfully.")
        except Exception as e:
            logging.error(f"Error updating API key: {e}")
            raise RuntimeError(f"Error updating API key: {e}")

    @staticmethod
    def fetch_image_urls(keyword: str, api_key: str, page: int = 1, images_per_page: int = IMAGES_PER_PAGE):
        url = f"https://pixabay.com/api/?key={api_key}&q={keyword}&per_page={images_per_page}&page={page}&image_type=photo&orientation=horizontal"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logging.error("Failed to fetch images from Pixabay.")
            raise RuntimeError("Failed to fetch images from Pixabay.") from e

        image_urls = []
        if 'hits' in data:
            for image in data['hits']:
                image_urls.append(image['webformatURL'])
                logging.info(f"Found image URL: {image['webformatURL']}")
        else:
            logging.info("No images found.")
        
        return image_urls

class PixabayGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ImageFinder")
        self.root.geometry("800x600")

        self.api_key = PixabayDownloader.load_api_key()
        self.page = 1
        self.keyword = ""

        self.create_widgets()
        self.setup_logging()

        self.image_refs = []
        self.selected_images = []

    def create_widgets(self):
        tk.Label(self.root, text="API Key:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.api_key_label = tk.Label(self.root, text=self.api_key, fg="blue")
        self.api_key_label.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)

        self.change_key_button = tk.Button(self.root, text="Change API Key", command=self.change_api_key)
        self.change_key_button.grid(row=0, column=2, padx=10, pady=5, sticky=tk.E)

        tk.Label(self.root, text="Search Keyword:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.keyword_entry = tk.Entry(self.root, width=30)
        self.keyword_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)

        self.download_button = tk.Button(self.root, text="Fetch Images", command=self.start_fetch_thread)
        self.download_button.grid(row=2, column=1, padx=10, pady=10, sticky=tk.E)

        self.log_text = scrolledtext.ScrolledText(self.root, width=60, height=10, state=tk.DISABLED)
        self.log_text.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky="nsew")

        self.image_frame = tk.Frame(self.root)
        self.image_frame.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky='nsew')

        # 스크롤바 및 캔버스 설정
        self.canvas = tk.Canvas(self.image_frame)
        self.scrollbar = ttk.Scrollbar(self.image_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 이미지가 표시될 내부 프레임 설정
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        self.inner_frame.bind("<Configure>", self.on_frame_configure)

        # 마우스 휠 이벤트 바인딩
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

        self.download_selected_button = tk.Button(self.root, text="Download Selected", command=self.choose_download_folder, state=tk.DISABLED)
        self.download_selected_button.grid(row=5, column=0, padx=10, pady=5, sticky='w')

        self.copy_url_button = tk.Button(self.root, text="Copy URLs", command=self.copy_selected_urls, state=tk.DISABLED)
        self.copy_url_button.grid(row=5, column=1, padx=10, pady=5, sticky='e')

        self.load_more_button = tk.Button(self.root, text="Load More Images", command=self.load_more_images, state=tk.NORMAL)
        self.load_more_button.grid(row=6, column=1, padx=10, pady=10, sticky=tk.E)

        # 모든 이미지 선택 및 선택 해제 버튼 추가
        self.select_all_button = tk.Button(self.root, text="Select All Images", command=self.select_all_images, state=tk.DISABLED)
        self.select_all_button.grid(row=6, column=0, padx=10, pady=10, sticky='w')

        self.deselect_all_button = tk.Button(self.root, text="Deselect All Images", command=self.deselect_all_images, state=tk.DISABLED)
        self.deselect_all_button.grid(row=6, column=2, padx=10, pady=10, sticky='e')

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(4, weight=1)

    def start_fetch_thread(self):
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("Input Error", "Please enter a search keyword.")
            return

        self.keyword = keyword
        self.page = 1
        self.image_refs.clear()
        self.inner_frame.destroy()
        self.inner_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor='nw')

        fetch_thread = Thread(target=self.fetch_images, args=(self.page,))
        fetch_thread.start()

    def fetch_images(self, page):
        try:
            if not self.keyword:
                logging.warning("No keyword entered.")
                return

            logging.info(f"'{self.keyword}'로 이미지 검색 중... (페이지 {page})")

            image_urls = PixabayDownloader.fetch_image_urls(self.keyword, self.api_key, page)

            if image_urls:
                self.display_images(image_urls)
                self.update_buttons_state(True)
                logging.info(f"'{self.keyword}'로 {len(image_urls)}개의 이미지 검색 완료.")
            else:
                logging.info(f"'{self.keyword}'로 검색된 이미지가 없습니다.")
                messagebox.showinfo("No Results", "No images found.")

        except Exception as e:
            logging.error(f"이미지 검색 중 오류 발생: {str(e)}")
            messagebox.showerror("Error", f"Error fetching images: {str(e)}")

    def load_more_images(self):
        self.page += 1
        fetch_thread = Thread(target=self.fetch_images, args=(self.page,))
        fetch_thread.start()

    def display_images(self, image_urls):
        img_width = 100
        canvas_width = self.canvas.winfo_width()
        images_per_row = max(1, canvas_width // (img_width + 10))

        for index, image_url in enumerate(image_urls):
            response = requests.get(image_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img = img.resize((img_width, img_width))
            img_tk = ImageTk.PhotoImage(img)

            row = len(self.image_refs) // images_per_row
            column = len(self.image_refs) % images_per_row

            label = tk.Label(self.inner_frame, image=img_tk, borderwidth=2, relief="solid")
            label.image = img_tk
            label.grid(row=row, column=column, padx=5, pady=5)

            label.bind("<Button-1>", lambda e, url=image_url, lbl=label: self.toggle_image_selection(e, url, lbl))

            self.image_refs.append((label, image_url))

        # 캔버스의 스크롤 영역을 갱신
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        # 새 이미지가 추가된 후, 스크롤을 가장 아래로 이동
        self.canvas.yview_moveto(1.0)

    def toggle_image_selection(self, event, url, label):
        if url in self.selected_images:
            self.selected_images.remove(url)
            label.config(borderwidth=2, relief="solid")
        else:
            self.selected_images.append(url)
            label.config(borderwidth=4, relief="sunken")
        self.update_buttons_state(bool(self.selected_images))

    def select_all_images(self):
        """
        모든 이미지를 선택하는 함수
        """
        for label, url in self.image_refs:
            if url not in self.selected_images:
                self.selected_images.append(url)
                label.config(borderwidth=4, relief="sunken")
        self.update_buttons_state(True)

    def deselect_all_images(self):
        """
        모든 이미지 선택을 해제하는 함수
        """
        self.selected_images.clear()
        for label, _ in self.image_refs:
            label.config(borderwidth=2, relief="solid")
        self.update_buttons_state(False)

    def clear_images(self):
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.image_refs.clear()
        self.selected_images.clear()

    def update_buttons_state(self, enable):
        """
        선택된 이미지가 있을 때 다운로드와 URL 복사 버튼을 활성화/비활성화.
        "Load More Images" 및 "모든 이미지 선택" 버튼은 항상 활성화.
        "모든 이미지 선택 해제" 버튼은 선택된 이미지가 있을 때만 활성화.
        """
        state = tk.NORMAL if enable else tk.DISABLED
        self.download_selected_button.config(state=state)
        self.copy_url_button.config(state=state)
        
        # "Load More Images" 및 "모든 이미지 선택" 버튼은 항상 활성화
        self.load_more_button.config(state=tk.NORMAL)
        self.select_all_button.config(state=tk.NORMAL)
        
        # "모든 이미지 선택 해제" 버튼은 선택된 이미지가 있을 때만 활성화
        self.deselect_all_button.config(state=state)


    def choose_download_folder(self):
        self.download_folder = filedialog.askdirectory()
        if self.download_folder:
            self.download_selected_images()

    def download_selected_images(self):
        for url in self.selected_images:
            response = requests.get(url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            filename = os.path.join(self.download_folder, os.path.basename(url))
            img.save(filename)
        messagebox.showinfo("Download Complete", "Images have been downloaded.")
        logging.info(f"Downloaded {len(self.selected_images)} images.")

    def copy_selected_urls(self):
        pyperclip.copy("\n".join(self.selected_images))
        messagebox.showinfo("Copied", "Selected URLs copied to clipboard.")
        logging.info("Copied selected image URLs to clipboard.")

    def change_api_key(self):
        new_key = simpledialog.askstring("Input", "Enter new API key:", parent=self.root)
        if new_key:
            try:
                PixabayDownloader.save_api_key(new_key)
                self.api_key = new_key
                self.api_key_label.config(text=new_key)  # UI에 업데이트
                messagebox.showinfo("Success", "API key updated successfully.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def setup_logging(self):
        handler = TextHandler(self.log_text)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)

    def on_frame_configure(self, event):
        """캔버스의 스크롤 영역을 내부 프레임의 크기에 맞게 조정"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """마우스 휠을 이용한 스크롤 이벤트 처리"""
        if event.delta > 0:
            self.canvas.yview_scroll(-1, "units")  # 위로 스크롤
        elif event.delta < 0:
            self.canvas.yview_scroll(1, "units")  # 아래로 스크롤

if __name__ == "__main__":
    root = tk.Tk()
    app = PixabayGUI(root)
    root.mainloop()
