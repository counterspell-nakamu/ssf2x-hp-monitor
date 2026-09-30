# HP Real-time Monitor for Fighting Games (Fightcade / Super Street Fighter II X)

対戦格闘ゲーム（ファイケ等）のHPゲージをリアルタイムで数値化するPythonツールです。
A real-time Python tool that captures and converts HP bars into numerical values.

> ⚠️ **Disclaimer / 注意:**
> I am a programming beginner, so this tool is imperfect and simple.
> （私はプログラミング素人ですので、このアプリは不完全です。試行錯誤しながら調整中のため、変更が入ることがあります。）

---

# Features / 特徴
- **Interactive Area Selection**: マウスドラッグで1Pと2PのHPゲージ全体を囲むだけで簡単にエリア指定できます。
- **Real-time Values**: HPをリアルタイムで数値化（144満点）します。
- **Noise Reduction**: メディアンフィルタ（5フレーム履歴）により、表示のブレを軽減しています。
- **Display Modes**: `m` キーでデバッグ画面と数字のみ（配信用）の表示を切り替えられます。

---

# Current Limitations & Compatibility / 現在の制限・相性について
- **Best Stage**: ファイケの**キャミィステージ**であれば、現状ほぼ完璧に動作します。
- **Stage Background Issue**: 背景の上部に黄色が含まれるステージ（バイソン / Boxer など）では正しく検出できません。
- **Image Quality**: 動画や画面の画質が少しでも粗くなると、正確な数値が出なくなります。

---

# Requirements / 必要環境
- Python 3.x
- Required libraries / 必要なライブラリ:
  `pip install opencv-python numpy mss pyautogui`

---

# How to Use / 使い方
1. スクリプトを実行する / Run the script:
   `python hp_drag_monitor.py`
2. ゲーム画面のあるモニターにマウスカーソルを合わせて **[Enter]** を押す。
   *(Move mouse cursor to the game monitor and press Enter)*
3. **ドラッグ選択 / Drag & Select**: 1Pの左端から2Pの右端まで（両方のゲージ）を1回でドラッグして囲み、**[Enter]** を押す。
   *(Drag from 1P left edge to 2P right edge, then press Enter)*
4. **操作キー / Controls**:
   - `m`: 表示モード切り替え（通常 ⇄ 数字のみ / Toggle view mode）
   - `q`: 終了 / Quit
