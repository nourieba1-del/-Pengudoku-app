import os
import glob
from kivy.app import App
from kivy.utils import platform
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from kivy.uix.togglebutton import ToggleButton
from PIL import Image, ImageDraw

class PengudokuSolverApp(App):
    def build(self):
        self.title = "Pengudoku AI Solver"
        self.target_count = 1
        
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE
            ])
        
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        self.status_label = Label(
            text="Ready to solve latest screenshot",
            size_hint=(1, 0.1),
            font_size='18sp'
        )
        layout.add_widget(self.status_label)
        
        mode_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), spacing=10)
        btn_1 = ToggleButton(text="1 Penguin Mode", group="mode", state="down")
        btn_2 = ToggleButton(text="2 Penguins Mode", group="mode")
        btn_1.bind(on_press=lambda x: self.set_mode(1))
        btn_2.bind(on_press=lambda x: self.set_mode(2))
        mode_layout.add_widget(btn_1)
        mode_layout.add_widget(btn_2)
        layout.add_widget(mode_layout)
        
        self.result_image = KivyImage(source="", size_hint=(1, 0.65))
        layout.add_widget(self.result_image)
        
        solve_btn = Button(
            text="Analyze & Solve Latest Image",
            size_hint=(1, 0.15),
            background_color=(0.1, 0.7, 0.3, 1),
            font_size='20sp'
        )
        solve_btn.bind(on_press=self.process_latest_image)
        layout.add_widget(solve_btn)
        
        return layout

    def set_mode(self, count):
        self.target_count = count
        self.status_label.text = f"Selected Mode: {count} Penguin(s)"

    def detect_grid_size(self, img):
        w, h = img.size
        mid_y = h // 2
        transitions = 0
        prev_pixel = img.getpixel((0, mid_y))
        for x in range(1, w):
            pixel = img.getpixel((x, mid_y))
            dist = sum(abs(a-b) for a, b in zip(pixel, prev_pixel))
            if dist > 45:
                transitions += 1
            prev_pixel = pixel
        estimated_size = int((transitions / 2) + 1)
        if estimated_size <= 5: return 5
        elif 6 <= estimated_size <= 7: return 6
        elif estimated_size == 8: return 8
        elif 9 <= estimated_size <= 11: return 9
        else: return 10

    def is_valid_move(self, board, row, col, regions, n, target):
        if board[row].count("P") >= target: return False
        if sum(1 for i in range(n) if board[i][col] == "P") >= target: return False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < n and 0 <= nc < n:
                    if board[nr][nc] == "P": return False
        current_region = regions[row][col]
        region_penguins = sum(1 for r in range(n) for c in range(n) if regions[r][c] == current_region and board[r][c] == "P")
        if region_penguins >= target: return False
        return True

    def solve_multi(self, board, regions, n, target, row=0, col=0, placed=0):
        if row == n: return True
        if placed == target:
            return self.solve_multi(board, regions, n, target, row + 1, 0, 0)
        for c in range(col, n):
            if (n - c) < (target - placed): break
            if self.is_valid_move(board, row, c, regions, n, target):
                board[row][c] = "P"
                if self.solve_multi(board, regions, n, target, row, c + 1, placed + 1):
                    return True
                board[row][c] = "."
        return False

    def process_latest_image(self, instance):
        extensions = ('*.jpg', '*.jpeg', '*.png')
        folders = [
            "/sdcard/Download",
            "/sdcard/Pictures/Screenshots",
            "/sdcard/DCIM/Screenshots"
        ]
        files = []
        for folder in folders:
            for ext in extensions:
                files.extend(glob.glob(os.path.join(folder, ext)))
            
        valid_files = [
            f for f in files 
            if not os.path.splitext(os.path.basename(f))[0].endswith(('x', 'X'))
        ]
        if not valid_files:
            self.status_label.text = "No original screenshots found!"
            return

        latest_file = max(valid_files, key=os.path.getmtime)
        self.status_label.text = f"Analyzing: {os.path.basename(latest_file)}"
        
        try:
            raw_img = Image.open(latest_file).convert('RGB')
            width, height = raw_img.size
            start_y, end_y = int(height * 0.388), int(height * 0.760)
            start_x, end_x = int(width * 0.082), int(width * 0.918)
            
            img = raw_img.crop((start_x, start_y, end_x, end_y))
            grid_size = self.detect_grid_size(img)
            w, h = img.size
            cell_w, cell_h = w / grid_size, h / grid_size
            
            grid_regions_colors = []
            collected_colors = []
            for r in range(grid_size):
                row_colors = []
                for c in range(grid_size):
                    offsets = [(0.25, 0.25), (0.5, 0.2), (0.75, 0.25), (0.2, 0.5), (0.8, 0.5), (0.25, 0.75), (0.5, 0.8), (0.75, 0.75)]
                    points = [img.getpixel((int((c + ox) * cell_w), int((r + oy) * cell_h))) for ox, oy in offsets]
                    best_color = max(set(points), key=points.count)
                    row_colors.append(best_color)
                    collected_colors.append(best_color)
                grid_regions_colors.append(row_colors)
                
            def get_color_dist(c1, c2):
                return sum(abs(a - b) for a, b in zip(c1, c2))
                
            tolerance = 20 if grid_size >= 15 else 45
            unique_centers = []
            while len(unique_centers) != grid_size and tolerance < 220:
                unique_centers = []
                for color in collected_colors:
                    if not unique_centers: unique_centers.append(color)
                    else:
                        if all(get_color_dist(color, center) > tolerance for center in unique_centers):
                            if len(unique_centers) < grid_size: unique_centers.append(color)
                if len(unique_centers) > grid_size: tolerance += 5
                elif len(unique_centers) < grid_size: break
            while len(unique_centers) < grid_size: unique_centers.append((0, 0, 0))
            
            regions = []
            for row in grid_regions_colors:
                row_ids = []
                for col in row:
                    dists = [get_color_dist(col, center) for center in unique_centers[:grid_size]]
                    row_ids.append(dists.index(min(dists)))
                regions.append(row_ids)
                
            board = [["." for _ in range(grid_size)] for _ in range(grid_size)]
            if self.solve_multi(board, regions, grid_size, self.target_count):
                draw = ImageDraw.Draw(raw_img)
                for r in range(grid_size):
                    for c in range(grid_size):
                        if board[r][c] == "P":
                            cx = int(start_x + (c + 0.5) * cell_w)
                            cy = int(start_y + (r + 0.5) * cell_h)
                            radius = int(cell_w * 0.22)
                            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(255, 0, 0), outline=(255, 255, 255), width=4)
                
                base_dir = os.path.dirname(latest_file)
                name_part, _ = os.path.splitext(os.path.basename(latest_file))
                output_path = os.path.join(base_dir, f"{name_part}x.jpg")
                raw_img.save(output_path)
                
                self.result_image.source = output_path
                self.result_image.reload()
                self.status_label.text = f"Solved ({grid_size}x{grid_size}) -> {name_part}x.jpg"
            else:
                self.status_label.text = "No valid solution found!"
                
        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"

if __name__ == "__main__":
    PengudokuSolverApp().run()
      
