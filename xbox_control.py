"""
xbox_control.py — Xbox Controller Control Software for a Soft Robotic Needle Insertion Platform
==========================================================

Controller Mapping:
  Left Stick Y-axis   → Motor X (retract cable / release cable)
  Right Stick Y-axis  → Motor Z (injection / withdrawal)
  RT Trigger          → Z-axis speed scaling (the more you squeeze, the faster it moves)
  LB                  → Speed mode: Slow → Medium → Fast
  RB                  → Speed mode: Fast → Medium → Slow
  A Button            → Start CSV recording
  B Button            → Stop recording
  Y Button            → Tare (zero) the load cell
  Back Button         → Reset Z-axis position to zero
  Start Button        → Exit program
"""

import pygame
import serial
import csv
import time
import threading
from datetime import datetime
from collections import deque

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ══════════════════════════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════════════════════════
PORT     = 'COM8'
BAUD     = 115200
DEADZONE = 0.15
MAX_POINTS = 300          # Maximum number of data points displayed on the live graph

SPEED_PRESETS = [800, 250, 100]
SPEED_LABELS = ["Slow", "Medium", "Fast"]

# ══════════════════════════════════════════════════════════════════
# 初始化 pygame + 串口
# ══════════════════════════════════════════════════════════════════
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("[ERROR] No controller detected")
    pygame.quit()
    exit(1)

joy = pygame.joystick.Joystick(0)
joy.init()
print(f"[Controller] {joy.get_name()}")

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)
    time.sleep(2)
    print(f"Serial port connected {PORT}")
except Exception as e:
    print(f"[ERROR] Serial connection failed：{e}")
    pygame.quit()
    exit(1)

# ══════════════════════════════════════════════════════════════════
# Real-Time Data Buffers (deque automatically discards old data)
# ══════════════════════════════════════════════════════════════════
buf_lock = threading.Lock()
buf_t     = deque(maxlen=MAX_POINTS)
buf_vol   = deque(maxlen=MAX_POINTS)
buf_relP  = deque(maxlen=MAX_POINTS)
buf_disp  = deque(maxlen=MAX_POINTS)
buf_force = deque(maxlen=MAX_POINTS)
plot_running = True   # Controls plot thread shutdown

# ══════════════════════════════════════════════════════════════════
# State Variables
# ══════════════════════════════════════════════════════════════════
speed_idx       = 1
x_cmd_last      = None
z_cmd_last      = None
z_speed_last    = -1
last_speed_send = 0

is_logging    = False
csv_file      = None
csv_writer    = None
csv_path      = None
sample_count  = 0
last_sample_t = 0
t0            = time.time()   # Program start time for relative time axis

lb_prev = rb_prev = a_prev = b_prev = y_prev = back_prev = x_prev = False

# ══════════════════════════════════════════════════════════════════
# Serial Communication / Logging Utilities
# ══════════════════════════════════════════════════════════════════
def send(cmd):
    try:
        ser.write(cmd.encode())
    except Exception as e:
        print(f"[Serial Error] {e}")

def start_logging():
    global is_logging, csv_file, csv_writer, csv_path, sample_count, t0
    if is_logging:
        return

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path   = f"dynamic_{ts}.csv"
    csv_file   = open(csv_path, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow([
        'time_s',
        'vol_ml',
        'absP_mbar',
        'relP_mbar',
        'angle_deg',
        'disp_mm',
        'force_g'
    ])

    is_logging   = True
    sample_count = 0
    t0           = time.time()

    # Clear real-time plot buffers
    with buf_lock:
        buf_t.clear()
        buf_vol.clear()
        buf_relP.clear()
        buf_disp.clear()
        buf_force.clear()

    print(f"[LOG] Started logging → {csv_path}")

def stop_logging():
    global is_logging, csv_file, csv_writer

    if not is_logging:
        return

    is_logging = False

    if csv_file:
        csv_file.close()
        csv_file = csv_writer = None

    print(f"[LOG] Stopped. Total {sample_count} rows → {csv_path}")

def try_log(line):
    global sample_count

    if not line.startswith('# LIVE'):
        return

    parts = line.split('\t')

    if len(parts) != 7:
        return

    try:
        vals = [float(p) for p in parts[1:]]

        # vals = volume, absP, relP, angle, displacement, force
        t_rel = round(time.time() - t0, 3)

        # Write to CSV
        if is_logging and csv_writer is not None:
            csv_writer.writerow([t_rel] + vals)
            csv_file.flush()
            sample_count += 1

        # Update plotting buffers even when not recording
        with buf_lock:
            buf_t.append(t_rel)
            buf_vol.append(vals[0])    # Volume (mL)
            buf_relP.append(vals[2])   # Relative Pressure (mbar)
            buf_disp.append(vals[4])   # Displacement (mm)
            buf_force.append(vals[5])  # Force (g)

    except ValueError:
        pass

# ══════════════════════════════════════════════════════════════════
# Real-Time Plotting (runs in a separate thread)
# ══════════════════════════════════════════════════════════════════
def plot_thread():

    fig, axes = plt.subplots(4, 1, figsize=(8, 9), sharex=True)
    fig.suptitle('Real-Time Sensor Data', fontsize=12)

    ax_vol, ax_relP, ax_disp, ax_force = axes

    ax_vol.set_ylabel('Vol (mL)')
    ax_relP.set_ylabel('Rel P (mbar)')
    ax_disp.set_ylabel('Disp (mm)')
    ax_force.set_ylabel('Force (g)')
    ax_force.set_xlabel('Time (s)')

    for ax in axes:
        ax.grid(True, alpha=0.3)

    line_vol,   = ax_vol.plot([], [], 'b-', linewidth=1.2)
    line_relP,  = ax_relP.plot([], [], 'g-', linewidth=1.2)
    line_disp,  = ax_disp.plot([], [], 'orange', linewidth=1.2)
    line_force, = ax_force.plot([], [], 'r-', linewidth=1.2)

    status_txt = ax_vol.text(
        0.01, 0.92,
        'IDLE',
        transform=ax_vol.transAxes,
        fontsize=8,
        color='gray',
        bbox=dict(
            boxstyle='round',
            facecolor='wheat',
            alpha=0.5
        )
    )

    plt.tight_layout()

    def update(frame):

        if not plot_running:
            return (
                line_vol,
                line_relP,
                line_disp,
                line_force,
                status_txt
            )

        with buf_lock:
            if len(buf_t) == 0:
                return (
                    line_vol,
                    line_relP,
                    line_disp,
                    line_force,
                    status_txt
                )

            t     = list(buf_t)
            vol   = list(buf_vol)
            relP  = list(buf_relP)
            disp  = list(buf_disp)
            force = list(buf_force)

        line_vol.set_data(t, vol)
        line_relP.set_data(t, relP)
        line_disp.set_data(t, disp)
        line_force.set_data(t, force)

        for ax in axes:
            ax.relim()
            ax.autoscale_view()

        status = (
            f"{'● REC' if is_logging else '○ IDLE'}  "
            f"{sample_count} pts"
        )

        status_txt.set_text(status)
        status_txt.set_color('red' if is_logging else 'gray')

        return (
            line_vol,
            line_relP,
            line_disp,
            line_force,
            status_txt
        )

    ani = animation.FuncAnimation(
        fig,
        update,
        interval=200,
        blit=False,
        cache_frame_data=False
    )

    plt.show()

# Start plotting thread
threading.Thread(
    target=plot_thread,
    daemon=True
).start()

# ══════════════════════════════════════════════════════════════════
# Main Loop
# ══════════════════════════════════════════════════════════════════

print(
    f"\nStartup complete. "
    f"Speed mode: {SPEED_LABELS[speed_idx]}  "
    f"A=Start Logging  B=Stop Logging  Start=Exit"
)

send(f"V{SPEED_PRESETS[speed_idx]}\n")

clock   = pygame.time.Clock()
running = True

while running:

    clock.tick(50)
    pygame.event.pump()

    # Read axes
    ly = joy.get_axis(1)
    rx = joy.get_axis(2)
    rt = (joy.get_axis(5) + 1) / 2

    # Read buttons
    a_btn    = joy.get_button(0)
    b_btn    = joy.get_button(1)
    y_btn    = joy.get_button(3)
    lb_btn   = joy.get_button(4)
    rb_btn   = joy.get_button(5)
    back_btn = joy.get_button(6)
    start    = joy.get_button(7)
    x_btn = joy.get_button(2)

    if start:
        running = False
        break

    # Speed selection
    if lb_btn and not lb_prev:
        speed_idx = (speed_idx - 1) % 3
        send(f"V{SPEED_PRESETS[speed_idx]}\n")
        print(
            f"[Speed] {SPEED_LABELS[speed_idx]} "
            f"({SPEED_PRESETS[speed_idx]} μs)"
        )

    if rb_btn and not rb_prev:
        speed_idx = (speed_idx + 1) % 3
        send(f"V{SPEED_PRESETS[speed_idx]}\n")
        print(
            f"[Speed] {SPEED_LABELS[speed_idx]} "
            f"({SPEED_PRESETS[speed_idx]} μs)"
        )

    lb_prev, rb_prev = lb_btn, rb_btn

    # Logging control
    if a_btn and not a_prev:
        start_logging()

    if b_btn and not b_prev:
        stop_logging()

    a_prev, b_prev = a_btn, b_btn
    if x_btn:
        print("X detected")

    if x_btn and not x_prev:
        print("Sending M")
        send('M')


    x_prev = x_btn

    # Load cell tare
    if y_btn and not y_prev:
        send('T')
        print("[Tare] Zeroed")

    y_prev = y_btn

    # Reset Z-axis position
    if back_btn and not back_prev:
        send('Z')
        print("[Reset] Z-axis position cleared")

    back_prev = back_btn

    # Motor X control
    if ly < -DEADZONE:
        x_cmd = 'U'
    elif ly > DEADZONE:
        x_cmd = 'D'
    else:
        x_cmd = 'S'

    if x_cmd != x_cmd_last:
        send(x_cmd)
        x_cmd_last = x_cmd

    # Motor Z control
    if abs(rx) < DEADZONE:
        z_cmd = 'W'
    elif rx < 0:
        z_cmd = 'R'
    else:
        z_cmd = 'L'

    if z_cmd != z_cmd_last:
        send(z_cmd)
        z_cmd_last = z_cmd

    # RT speed scaling (max update every 200 ms)
    if z_cmd != 'W':
        now = time.time()

        if now - last_speed_send > 0.2:
            mag   = (abs(rx) - DEADZONE) / (1.0 - DEADZONE)
            scale = 0.3 + rt * 0.7

            us = int(
                SPEED_PRESETS[speed_idx]
                / (mag * scale + 0.01)
            )

            us = max(75, min(5000, us))

            if abs(us - z_speed_last) > 50:
                send(f"V{us}\n")
                z_speed_last    = us
                last_speed_send = now

    # Periodic sampling
    now = time.time()

    if now - last_sample_t > 0.05:
        send('Q')
        last_sample_t = now

    # Read serial data
    while ser.in_waiting:

        try:
            line = (
                ser.readline()
                .decode('utf-8', errors='ignore')
                .strip()
            )
        except Exception:
            break

        if line:
            print(line)
            try_log(line)

# ══════════════════════════════════════════════════════════════════
# Shutdown
# ══════════════════════════════════════════════════════════════════

plot_running = False

send('W')
send('S')

if is_logging:
    stop_logging()

ser.close()
pygame.quit()

print("Exited.")