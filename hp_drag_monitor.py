import os
import time
import ctypes
from collections import deque
import cv2
import numpy as np
import mss
import pyautogui

# --- マウスが存在するモニター番号を特定する関数 ---
def get_monitor_under_mouse(sct):
    mx, my = pyautogui.position()
    for idx, mon in enumerate(sct.monitors[1:], start=1):
        if (mon["left"] <= mx < mon["left"] + mon["width"]) and \
           (mon["top"] <= my < mon["top"] + mon["height"]):
            return idx, mon
    return 1, sct.monitors[1]

# --- マウスドラッグで範囲を選択する処理（枠線常時描画） ---
ref_point = []
cropping = False
current_mouse_pos = (0, 0)

def select_crop_area(event, x, y, flags, param):
    global ref_point, cropping, current_mouse_pos

    if event == cv2.EVENT_LBUTTONDOWN:
        ref_point = [(x, y)]
        cropping = True
        current_mouse_pos = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE:
        current_mouse_pos = (x, y)

    elif event == cv2.EVENT_LBUTTONUP:
        ref_point.append((x, y))
        cropping = False
        current_mouse_pos = (x, y)

def main():
    sct = mss.mss()
    
    print("==================================================")
    print("【1P + 2P HP リアルタイムモニター（メディアンフィルタ版）】")
    print("==================================================")

    print("\nゲーム画面のあるディスプレイにマウスカーソルを移動してください。")
    input("準備ができたら [Enter] キーを押してください...")

    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
    except Exception:
        pass

    time.sleep(0.5)

    # マウスがあるモニターを特定
    mon_idx, target_monitor = get_monitor_under_mouse(sct)
    print(f"-> モニター {mon_idx} を自動検出しました。")

    full_img = np.array(sct.grab(target_monitor))
    full_frame = cv2.cvtColor(full_img, cv2.COLOR_BGRA2BGR)
    
    cv2.namedWindow("Select BOTH HP Areas (1P + 2P) - Drag & Press ENTER")
    param = {'image': full_frame}
    cv2.setMouseCallback("Select BOTH HP Areas (1P + 2P) - Drag & Press ENTER", select_crop_area, param)

    print("\n【ドラッグ操作手順】")
    print("1. 満タン状態の1Pゲージ左端から2Pゲージ右端まで（両方のゲージ全体）を1回で囲みます。")
    print("2. 囲み終わったら 『ENTER』 キーを押して確定します。")

    global ref_point, cropping, current_mouse_pos
    ref_point = []
    cropping = False

    while True:
        display_img = full_frame.copy()
        if cropping and len(ref_point) == 1:
            cv2.rectangle(display_img, ref_point[0], current_mouse_pos, (0, 255, 0), 2)
        elif len(ref_point) == 2:
            cv2.rectangle(display_img, ref_point[0], ref_point[1], (0, 255, 0), 2)

        cv2.imshow("Select BOTH HP Areas (1P + 2P) - Drag & Press ENTER", display_img)
        key = cv2.waitKey(15) & 0xFF

        if key == ord("c"):
            ref_point = []
            cropping = False
        elif key in (13, 32): # Enter or Space
            if len(ref_point) == 2:
                break

    cv2.destroyWindow("Select BOTH HP Areas (1P + 2P) - Drag & Press ENTER")

    x1, y1 = ref_point[0]
    x2, y2 = ref_point[1]
    
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x1 - x2)
    height = abs(y1 - y2)

    monitor_hp = {
        "top": target_monitor["top"] + top,
        "left": target_monitor["left"] + left,
        "width": width,
        "height": height
    }

    # 黄色検出用HSV範囲（高閾値 220）
    lower_yellow = np.array([15, 220, 220])
    upper_yellow = np.array([35, 255, 255])

    print("\n画面の安定を待っています（1秒待機）...")
    time.sleep(1.0)

    # 突発ノイズ除去用の5フレーム履歴（メディアンフィルタ用）
    hp_history_1p = deque(maxlen=5)
    hp_history_2p = deque(maxlen=5)
    
    # 基準位置および最大幅の記憶用
    max_yellow_width_1p = None
    fixed_base_x_1p = None  # 1Pの固定基準点（右端）
    
    max_yellow_width_2p = None
    fixed_base_x_2p = None  # 2Pの固定基準点（左端）

    # 表示モードフラグ（True: 通常/デバッグ, False: 数字のみ/配信用）
    show_debug_view = True

    print("【1P & 2P】同時リアルタイム監視を開始します...")
    print(" ・『m』キー : 表示モード切り替え（通常 ⇄ 数字のみ）")
    print(" ・『q』キー : 終了")

    # --- リアルタイム監視ループ ---
    while True:
        img = np.array(sct.grab(monitor_hp))
        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        h, w, _ = frame.shape
        mid_x = w // 2  # 左右均等分割（左半分=1P, 右半分=2P）

        # 上下の枠線ノイズをカット（中央領域 35%〜65%）
        y_start = int(h * 0.35)
        y_end = int(h * 0.65)
        crop_inner = frame[y_start:y_end, :]

        hsv = cv2.cvtColor(crop_inner, cv2.COLOR_BGR2HSV)
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

        # --- 1列ごとの縦連続ドット判定 ---
        valid_cols_1p = set()
        valid_cols_2p = set()

        for col in range(w):
            col_pixels = mask_yellow[:, col]
            
            max_consecutive = 0
            current_consecutive = 0
            for pixel in col_pixels:
                if pixel > 0:
                    current_consecutive += 1
                    if current_consecutive > max_consecutive:
                        max_consecutive = current_consecutive
                else:
                    current_consecutive = 0
            
            # 縦2ピクセル以上の連続を有効列とする
            if max_consecutive >= 2:
                if col < mid_x:
                    valid_cols_1p.add(col)
                else:
                    valid_cols_2p.add(col)

        # --- 初回（満タン時）の基準位置と最大幅決定 ---
        if fixed_base_x_1p is None and len(valid_cols_1p) > 0:
            fixed_base_x_1p = max(valid_cols_1p)  # 1Pの右端
            left_x_1p = min(valid_cols_1p)         # 1Pの左端
            max_yellow_width_1p = fixed_base_x_1p - left_x_1p + 1

        if fixed_base_x_2p is None and len(valid_cols_2p) > 0:
            fixed_base_x_2p = min(valid_cols_2p)  # 2Pの左端
            right_x_2p = max(valid_cols_2p)        # 2Pの右端
            max_yellow_width_2p = right_x_2p - fixed_base_x_2p + 1

        # --- 端の座標から幅を計算 ---
        detected_width_1p = 0
        if fixed_base_x_1p is not None and len(valid_cols_1p) > 0:
            current_leftmost_1p = min(valid_cols_1p)
            if current_leftmost_1p <= fixed_base_x_1p:
                detected_width_1p = fixed_base_x_1p - current_leftmost_1p + 1

        detected_width_2p = 0
        if fixed_base_x_2p is not None and len(valid_cols_2p) > 0:
            current_rightmost_2p = max(valid_cols_2p)
            if current_rightmost_2p >= fixed_base_x_2p:
                detected_width_2p = current_rightmost_2p - fixed_base_x_2p + 1

        # --- 144〜0 計算モデル ---
        if max_yellow_width_1p and max_yellow_width_1p > 0:
            raw_hp_1p = round((detected_width_1p / max_yellow_width_1p) * 144)
            raw_hp_1p = max(0, min(144, raw_hp_1p))
        else:
            raw_hp_1p = 0

        if max_yellow_width_2p and max_yellow_width_2p > 0:
            raw_hp_2p = round((detected_width_2p / max_yellow_width_2p) * 144)
            raw_hp_2p = max(0, min(144, raw_hp_2p))
        else:
            raw_hp_2p = 0

        # --- 中央値（メディアン）フィルタ処理 ---
        hp_history_1p.append(raw_hp_1p)
        hp_history_2p.append(raw_hp_2p)

        # 直近5フレームの中央値（Median）を取得して突発ノイズをカット
        final_hp_1p = int(np.median(hp_history_1p))
        final_hp_2p = int(np.median(hp_history_2p))

        # --- UI表示作成 ---
        header_height = 45
        header_bg = np.zeros((header_height, w, 3), dtype=np.uint8)
        
        text_str = f"1P: {final_hp_1p:3d} / 144   |   2P: {final_hp_2p:3d} / 144"
        cv2.putText(header_bg, text_str, (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # モードに応じたウィンドウ描画
        if show_debug_view:
            mask_yellow_full = np.zeros((h, w, 3), dtype=np.uint8)
            if fixed_base_x_1p is not None and detected_width_1p > 0:
                start_x = fixed_base_x_1p - detected_width_1p + 1
                mask_yellow_full[y_start:y_end, start_x:fixed_base_x_1p+1] = (0, 255, 0)
            
            if fixed_base_x_2p is not None and detected_width_2p > 0:
                end_x = fixed_base_x_2p + detected_width_2p
                mask_yellow_full[y_start:y_end, fixed_base_x_2p:end_x] = (0, 0, 255)

            debug_view = cv2.vconcat([
                header_bg, 
                frame, 
                mask_yellow_full
            ])
            cv2.imshow("HP Realtime Monitor (q: Quit, m: Toggle Mode)", debug_view)
        else:
            cv2.imshow("HP Realtime Monitor (q: Quit, m: Toggle Mode)", header_bg)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('m'):
            show_debug_view = not show_debug_view

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
