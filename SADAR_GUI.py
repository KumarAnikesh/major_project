#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# ==========================================
# IMPROVED TKINTER + RASTERIO TOOL
# FULL SCREEN + ENHANCED UI
# ==========================================

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import rasterio
import numpy as np
import os
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- GLOBALS ----------------
image_path = None
result_data = None
profile = None
green = None
swir = None
ndsi_threshold = 0.4
folder_path = None
image_files = []
current_image_index = 0

# ---------------- MODERN COLORS ----------------
COLORS = {
    'primary': '#1d1d1f',           # Dark gray (Apple style)
    'secondary': '#0071e3',         # Apple blue
    'accent': '#0077ed',            # Brighter blue
    'button_bg': '#000000',         # Black for all buttons
    'button_hover': '#2c2c2e',      # Dark gray on hover
    'button_disabled': '#86868b',   # Gray for disabled
    'success': '#34c759',
    'warning': '#ff9500',
    'error': '#ff3b30',
    'background': '#f5f5f7',        # Light gray background
    'card_bg': '#ffffff',
    'text': '#1d1d1f',
    'text_light': '#86868b',        # Apple gray
    'border': '#d2d2d7'
}

# ---------------- THRESHOLD HANDLER ----------------
def on_threshold_change(val):
    global ndsi_threshold
    ndsi_threshold = float(val)
    threshold_value_label.config(
        text=f"{ndsi_threshold:.2f}"
    )

# ---------------- UPLOAD FOLDER ----------------
def upload_folder():
    global folder_path, image_files, current_image_index, image_path, result_data

    folder_path = filedialog.askdirectory(title="Select Folder Containing GeoTIFF Images")

    if not folder_path:
        return

    # Find all TIFF files in the folder
    image_files = []
    for file in os.listdir(folder_path):
        if file.lower().endswith(('.tif', '.tiff')):
            image_files.append(os.path.join(folder_path, file))

    image_files.sort()  # Sort alphabetically

    if not image_files:
        messagebox.showwarning("No Images Found", "No GeoTIFF files found in the selected folder.")
        folder_path = None
        return

    current_image_index = 0
    result_data = None

    # Update UI
    folder_label.config(
        text=f"{os.path.basename(folder_path)}",
        fg=COLORS['success']
    )

    folder_info_label.config(
        text=f"{len(image_files)} GeoTIFF images found",
        fg=COLORS['text_light']
    )

    # Show and populate image listbox
    listbox_frame.pack(fill='both', expand=True, pady=(10, 0))
    image_listbox.delete(0, tk.END)
    for img_file in image_files:
        image_listbox.insert(tk.END, os.path.basename(img_file))

    # Select first image
    if image_files:
        image_listbox.selection_set(0)
        load_selected_image()

    status.config(
        text=f"✓ Folder loaded with {len(image_files)} images - Select an image to begin",
        fg=COLORS['success']
    )

# ---------------- LOAD SELECTED IMAGE ----------------
def load_selected_image(event=None):
    global image_path, current_image_index, result_data

    selection = image_listbox.curselection()
    if not selection:
        return

    current_image_index = selection[0]
    image_path = image_files[current_image_index]
    result_data = None

    btn_run.config(state='disabled', bg=COLORS['button_disabled'])
    btn_save.config(state='disabled', bg=COLORS['button_disabled'])

    try:
        with rasterio.open(image_path) as src:
            band_count = src.count
            width = src.width
            height = src.height
            dtype = str(src.dtypes[0])
            crs = str(src.crs) if src.crs else "Not specified"

            # Get band statistics if available
            image_data = {
                'filename': os.path.basename(image_path),
                'bands': band_count,
                'width': width,
                'height': height,
                'dtype': dtype,
                'crs': crs
            }

            if band_count >= 2:
                green_band = src.read(1).astype(float)
                swir_band = src.read(2).astype(float)

                image_data['green_min'] = np.nanmin(green_band)
                image_data['green_max'] = np.nanmax(green_band)
                image_data['green_mean'] = np.nanmean(green_band)
                image_data['swir_min'] = np.nanmin(swir_band)
                image_data['swir_max'] = np.nanmax(swir_band)
                image_data['swir_mean'] = np.nanmean(swir_band)

        file_name_label.config(
            text=f"Current: {os.path.basename(image_path)}",
            fg=COLORS['success']
        )

        file_info_label.config(
            text=f"{band_count} bands | {width}x{height} pixels",
            fg=COLORS['text_light']
        )

        if band_count < 2:
            status.config(
                text="❌ Error: Image must contain at least 2 bands (Green & SWIR)",
                fg=COLORS['error']
            )
            update_info_display('initial')
        else:
            status.config(
                text=f"✓ Image {current_image_index + 1}/{len(image_files)} loaded - Ready to calculate",
                fg=COLORS['success']
            )
            btn_run.config(state='normal', bg=COLORS['button_bg'])
            update_info_display('image_loaded', image_data=image_data)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        status.config(text=f"❌ Error loading image", fg=COLORS['error'])
        update_info_display('initial')

# ---------------- UPLOAD SINGLE IMAGE ----------------
def upload_image():
    global image_path, result_data, folder_path, image_files

    image_path = filedialog.askopenfilename(
        filetypes=[("GeoTIFF files", "*.tif *.tiff")]
    )

    result_data = None
    folder_path = None
    image_files = []

    btn_run.config(state='disabled', bg=COLORS['button_disabled'])
    btn_save.config(state='disabled', bg=COLORS['button_disabled'])

    if not image_path:
        return

    # Hide listbox and clear folder display
    listbox_frame.pack_forget()
    folder_label.config(text=os.path.basename(image_path), fg=COLORS['success'])
    folder_info_label.config(text="Single file selected", fg=COLORS['text_light'])
    image_listbox.delete(0, tk.END)

    try:
        with rasterio.open(image_path) as src:
            band_count = src.count
            width = src.width
            height = src.height
            dtype = str(src.dtypes[0])
            crs = str(src.crs) if src.crs else "Not specified"

            # Get band statistics if available
            image_data = {
                'filename': os.path.basename(image_path),
                'bands': band_count,
                'width': width,
                'height': height,
                'dtype': dtype,
                'crs': crs
            }

            if band_count >= 2:
                green_band = src.read(1).astype(float)
                swir_band = src.read(2).astype(float)

                image_data['green_min'] = np.nanmin(green_band)
                image_data['green_max'] = np.nanmax(green_band)
                image_data['green_mean'] = np.nanmean(green_band)
                image_data['swir_min'] = np.nanmin(swir_band)
                image_data['swir_max'] = np.nanmax(swir_band)
                image_data['swir_mean'] = np.nanmean(swir_band)

        file_name_label.config(
            text=f"Current: {os.path.basename(image_path)}",
            fg=COLORS['success']
        )

        file_info_label.config(
            text=f"{band_count} bands | {width}x{height} pixels",
            fg=COLORS['text_light']
        )

        if band_count < 2:
            status.config(
                text="❌ Error: Image must contain at least 2 bands (Green & SWIR)",
                fg=COLORS['error']
            )
            update_info_display('initial')
        else:
            status.config(
                text="✓ Image loaded successfully - Ready to calculate",
                fg=COLORS['success']
            )
            btn_run.config(state='normal', bg=COLORS['button_bg'])
            update_info_display('image_loaded', image_data=image_data)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        status.config(text=f"❌ Error loading image", fg=COLORS['error'])
        update_info_display('initial')

# ---------------- RUN CALCULATION ----------------
def run_calculation():
    global result_data, profile, green, swir

    calc_type = calculation_var.get()

    if calc_type != "NDSI":
        messagebox.showwarning("Info", "Only NDSI is implemented for now.")
        return

    try:
        status.config(text="⏳ Calculating NDSI...", fg=COLORS['warning'])
        root.update()

        with rasterio.open(image_path) as src:
            green = src.read(1).astype(float)   # B3
            swir  = src.read(2).astype(float)   # B11
            profile = src.profile

        denom = green + swir

        with np.errstate(divide='ignore', invalid='ignore'):
            result_data = (green - swir) / denom

        result_data[denom == 0] = np.nan
        result_data = np.clip(result_data, -1, 1)

        # Calculate statistics for display
        total_pixels = result_data.size
        valid_mask = ~np.isnan(result_data)
        valid_pixels = np.sum(valid_mask)
        nodata_pixels = total_pixels - valid_pixels

        snow_mask = result_data >= ndsi_threshold
        snow_pixels = np.sum(snow_mask & valid_mask)
        non_snow_pixels = valid_pixels - snow_pixels

        # Calculate percentages
        snow_percentage = (snow_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        non_snow_percentage = (non_snow_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        nodata_percentage = (nodata_pixels / total_pixels) * 100 if total_pixels > 0 else 0

        # Value distribution
        range1 = np.sum((result_data >= -1) & (result_data < -0.5) & valid_mask)
        range2 = np.sum((result_data >= -0.5) & (result_data < 0) & valid_mask)
        range3 = np.sum((result_data >= 0) & (result_data < 0.5) & valid_mask)
        range4 = np.sum((result_data >= 0.5) & (result_data <= 1) & valid_mask)

        calc_data = {
            'filename': os.path.basename(image_path),
            'threshold': ndsi_threshold,
            'min': np.nanmin(result_data),
            'max': np.nanmax(result_data),
            'mean': np.nanmean(result_data),
            'std': np.nanstd(result_data),
            'total_pixels': total_pixels,
            'valid_pixels': valid_pixels,
            'nodata_pixels': nodata_pixels,
            'snow_pixels': snow_pixels,
            'non_snow_pixels': non_snow_pixels,
            'snow_percentage': snow_percentage,
            'non_snow_percentage': non_snow_percentage,
            'nodata_percentage': nodata_percentage,
            'range1': range1,
            'range2': range2,
            'range3': range3,
            'range4': range4
        }

        status.config(text="✓ NDSI calculated successfully - Ready to save", fg=COLORS['success'])
        btn_save.config(state='normal', bg=COLORS['button_bg'])
        update_info_display('calculated', calc_data=calc_data)

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status.config(text=f"❌ Calculation failed: {str(e)}", fg=COLORS['error'])

# ---------------- SAVE OUTPUT ----------------
def save_output():
    if result_data is None:
        messagebox.showwarning("Warning", "No result to save")
        return

    folder = filedialog.askdirectory()
    if not folder:
        return

    status.config(text="💾 Saving outputs...", fg=COLORS['warning'])
    root.update()

    # ---- SAVE TIFF ----
    out_tif = os.path.join(folder, "ndsi.tiff")
    profile.update(dtype=rasterio.float32, count=1, nodata=np.nan)

    with rasterio.open(out_tif, 'w', **profile) as dst:
        dst.write(result_data.astype(np.float32), 1)

    # ---- SAVE PNG ----
    png_path = os.path.join(folder, "ndsi_preview.png")
    plt.figure(figsize=(10, 8))
    plt.imshow(result_data, cmap='RdBu', vmin=-1, vmax=1)
    plt.colorbar(label="NDSI", shrink=0.8)
    plt.title("NDSI Map", fontsize=16, fontweight='bold')
    plt.axis("off")
    plt.savefig(png_path, dpi=200, bbox_inches='tight')
    plt.close()

    # ---- PDF REPORT ----
    pdf_path = os.path.join(folder, "ndsi_report.pdf")
    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>NDSI Analysis Report</b>", styles['Title']))
    story.append(Paragraph(
        f"<b>User-selected Threshold:</b> {ndsi_threshold:.2f}",
        styles['Normal']
    ))

    story.append(Paragraph("<br/><b>NDSI Statistics</b><br/>", styles['Normal']))
    story.append(Paragraph(f"Min: {np.nanmin(result_data):.4f}", styles['Normal']))
    story.append(Paragraph(f"Max: {np.nanmax(result_data):.4f}", styles['Normal']))
    story.append(Paragraph(f"Mean: {np.nanmean(result_data):.4f}", styles['Normal']))

    story.append(Paragraph("<br/><b>NDSI Map</b><br/>", styles['Normal']))
    story.append(Image(png_path, width=400, height=300))

    doc.build(story)

    status.config(text="✓ All outputs saved successfully!", fg=COLORS['success'])
    messagebox.showinfo("Success", f"Files saved to:\n{folder}\n\n• ndsi.tiff\n• ndsi_preview.png\n• ndsi_report.pdf")

# ---------------- BUTTON HOVER EFFECTS ----------------
def on_enter_upload(e):
    if btn_upload['state'] == 'normal':
        btn_upload['background'] = COLORS['button_hover']

def on_leave_upload(e):
    if btn_upload['state'] == 'normal':
        btn_upload['background'] = COLORS['button_bg']

def on_enter_folder(e):
    if btn_upload_folder['state'] == 'normal':
        btn_upload_folder['background'] = COLORS['button_hover']

def on_leave_folder(e):
    if btn_upload_folder['state'] == 'normal':
        btn_upload_folder['background'] = COLORS['button_bg']

def on_enter_run(e):
    if btn_run['state'] == 'normal':
        btn_run['background'] = COLORS['button_hover']

def on_leave_run(e):
    if btn_run['state'] == 'normal':
        btn_run['background'] = COLORS['button_bg']

def on_enter_save(e):
    if btn_save['state'] == 'normal':
        btn_save['background'] = COLORS['button_hover']

def on_leave_save(e):
    if btn_save['state'] == 'normal':
        btn_save['background'] = COLORS['button_bg']

# ---------------- GUI ----------------
root = tk.Tk()
root.title("Raster Index Calculator - Professional Edition")

# Get screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set window to full screen
root.geometry(f"{screen_width}x{screen_height}+0+0")
root.state('zoomed')  # Maximized state

root.config(bg=COLORS['background'])

# Main container with padding
main_container = tk.Frame(root, bg=COLORS['background'])
main_container.pack(fill='both', expand=True, padx=30, pady=20)

# Header section
header_frame = tk.Frame(main_container, bg=COLORS['primary'], height=100)
header_frame.pack(fill='x', pady=(0, 20))
header_frame.pack_propagate(False)

title = tk.Label(
    header_frame,
    text="🛰️ SADAR",
    font=("SF Pro Display", 28, "bold") if os.name == 'darwin' else ("Segoe UI", 28, "bold"),
    bg=COLORS['primary'],
    fg="white",
    pady=15
)
title.pack()

subtitle = tk.Label(
    header_frame,
    text="Satellite Avalanche Debris Analysis & Reporting",
    font=("SF Pro Display", 12) if os.name == 'darwin' else ("Segoe UI", 12),
    bg=COLORS['primary'],
    fg="#a1a1a6"
)
subtitle.pack()

# Content area with two columns
content_frame = tk.Frame(main_container, bg=COLORS['background'])
content_frame.pack(fill='both', expand=True)

# Configure grid weights for better space distribution
content_frame.grid_rowconfigure(0, weight=1)
content_frame.grid_columnconfigure(0, weight=1)
content_frame.grid_columnconfigure(1, weight=1)

# Left column - Controls (with scrollbar)
left_column_container = tk.Frame(content_frame, bg=COLORS['card_bg'], relief='flat', bd=0)
left_column_container.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
left_column_container.config(highlightbackground=COLORS['border'], highlightthickness=1)

# Create canvas and scrollbar for left column
left_canvas = tk.Canvas(left_column_container, bg=COLORS['card_bg'], highlightthickness=0)
left_scrollbar = tk.Scrollbar(left_column_container, orient="vertical", command=left_canvas.yview)

left_column = tk.Frame(left_canvas, bg=COLORS['card_bg'])

left_scrollbar.pack(side="right", fill="y")
left_canvas.pack(side="left", fill="both", expand=True)
left_canvas.create_window((0, 0), window=left_column, anchor="nw", width=left_canvas.winfo_reqwidth())

left_canvas.configure(yscrollcommand=left_scrollbar.set)

def on_left_frame_configure(event):
    left_canvas.configure(scrollregion=left_canvas.bbox("all"))

def on_left_canvas_configure(event):
    # Update the width of the frame to fill the canvas
    canvas_width = event.width
    left_canvas.itemconfig(left_canvas.find_withtag("all")[0], width=canvas_width)

left_column.bind("<Configure>", on_left_frame_configure)
left_canvas.bind("<Configure>", on_left_canvas_configure)

# Mouse wheel scrolling for left column
def on_left_mousewheel(event):
    left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

left_canvas.bind_all("<MouseWheel>", on_left_mousewheel)

# Right column - Information
right_column = tk.Frame(content_frame, bg=COLORS['card_bg'], relief='flat', bd=0)
right_column.grid(row=0, column=1, sticky='nsew', padx=(10, 0))
right_column.config(highlightbackground=COLORS['border'], highlightthickness=1)

# ========== LEFT COLUMN CONTENT ==========
left_content = tk.Frame(left_column, bg=COLORS['card_bg'])
left_content.pack(fill='both', expand=True, padx=20, pady=20)

# Unified upload section
upload_section = tk.LabelFrame(
    left_content,
    text="📁 Image Upload (File or Folder)",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
upload_section.pack(fill='both', expand=True, pady=(0, 15))

# Info label
upload_info = tk.Label(
    upload_section,
    text="Choose single image or entire folder",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
upload_info.pack(pady=(5, 10), fill='x')

folder_label = tk.Label(
    upload_section,
    text="No file or folder selected",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light']
)
folder_label.pack(pady=(0, 0), anchor='w')

folder_info_label = tk.Label(
    upload_section,
    text="",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light']
)
folder_info_label.pack(pady=(0, 10))

# Upload buttons frame
upload_buttons_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
upload_buttons_frame.pack(fill='x', pady=4)

btn_upload = tk.Button(
    upload_buttons_frame,
    text="📄 Upload Single Image",
    font=("SF Pro Display", 11, "bold") if os.name == 'darwin' else ("Segoe UI", 11, "bold"),
    bg=COLORS['button_bg'],
    fg="white",
    activebackground=COLORS['button_hover'],
    activeforeground="white",
    pady=12,
    cursor="hand2",
    relief='flat',
    bd=0,
    highlightthickness=0,
    command=upload_image
)
btn_upload.pack(side='left', fill='x', expand=True, padx=(0, 5))
btn_upload.bind("<Enter>", on_enter_upload)
btn_upload.bind("<Leave>", on_leave_upload)

btn_upload_folder = tk.Button(
    upload_buttons_frame,
    text="📁 Upload Folder",
    font=("SF Pro Display", 11, "bold") if os.name == 'darwin' else ("Segoe UI", 11, "bold"),
    bg=COLORS['button_bg'],
    fg="white",
    activebackground=COLORS['button_hover'],
    activeforeground="white",
    pady=12,
    cursor="hand2",
    relief='flat',
    bd=0,
    highlightthickness=0,
    command=upload_folder
)
btn_upload_folder.pack(side='right', fill='x', expand=True, padx=(5, 0))
btn_upload_folder.bind("<Enter>", on_enter_folder)
btn_upload_folder.bind("<Leave>", on_leave_folder)

# Image listbox with scrollbar (hidden initially)
listbox_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
listbox_frame.pack(fill='both', expand=True, pady=(10, 0))

listbox_label = tk.Label(
    listbox_frame,
    text="Select an image:",
    font=("Segoe UI", 9, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    anchor='w'
)
listbox_label.pack(fill='x', pady=(0, 5))

listbox_scroll_container = tk.Frame(listbox_frame, bg=COLORS['card_bg'])
listbox_scroll_container.pack(fill='both', expand=True)

listbox_scrollbar = tk.Scrollbar(listbox_scroll_container)
listbox_scrollbar.pack(side='right', fill='y')

image_listbox = tk.Listbox(
    listbox_scroll_container,
    font=("Segoe UI", 9),
    bg='white',
    fg=COLORS['text'],
    selectmode='single',
    height=6,
    yscrollcommand=listbox_scrollbar.set,
    relief='solid',
    bd=1
)
image_listbox.pack(side='left', fill='both', expand=True)
listbox_scrollbar.config(command=image_listbox.yview)
image_listbox.bind('<<ListboxSelect>>', load_selected_image)

# Hide listbox initially
listbox_frame.pack_forget()

# File info section (shows current selected file)
file_info_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
file_info_frame.pack(fill='x', pady=(10, 0))

file_name_label = tk.Label(
    file_info_frame,
    text="",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    anchor='w'
)
file_name_label.pack(fill='x')

file_info_label = tk.Label(
    file_info_frame,
    text="",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
file_info_label.pack(fill='x')

# Calculation settings section
calc_section = tk.LabelFrame(
    left_content,
    text="⚙️ Calculation Settings",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
calc_section.pack(fill='x', pady=(0, 15))

# Calculation type
calc_type_frame = tk.Frame(calc_section, bg=COLORS['card_bg'])
calc_type_frame.pack(fill='x', pady=(5, 10))

calc_label = tk.Label(
    calc_type_frame,
    text="Index Type:",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text']
)
calc_label.pack(anchor='w', pady=(0, 3))

calculation_var = tk.StringVar(value="NDSI")
calc_dropdown = ttk.Combobox(
    calc_type_frame,
    textvariable=calculation_var,
    values=["NDSI"],
    state='readonly',
    font=("Segoe UI", 10)
)
calc_dropdown.pack(fill='x')

# Threshold slider
threshold_frame = tk.Frame(calc_section, bg=COLORS['card_bg'])
threshold_frame.pack(fill='x', pady=(0, 5))

threshold_header = tk.Frame(threshold_frame, bg=COLORS['card_bg'])
threshold_header.pack(fill='x')

threshold_label = tk.Label(
    threshold_header,
    text="NDSI Threshold:",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text']
)
threshold_label.pack(side='left')

threshold_value_label = tk.Label(
    threshold_header,
    text="0.40",
    font=("Segoe UI", 10, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['secondary']
)
threshold_value_label.pack(side='right')

threshold_slider = tk.Scale(
    threshold_frame,
    from_=0.0,
    to=1.0,
    resolution=0.05,
    orient='horizontal',
    command=on_threshold_change,
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    highlightthickness=0,
    troughcolor=COLORS['border'],
    activebackground=COLORS['secondary']
)
threshold_slider.set(0.4)
threshold_slider.pack(fill='x', pady=(5, 0))

# Action buttons section
action_section = tk.LabelFrame(
    left_content,
    text="🚀 Actions",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
action_section.pack(fill='x', pady=(0, 15))

btn_run = tk.Button(
    action_section,
    text="▶️ Run Calculation",
    font=("SF Pro Display", 11, "bold") if os.name == 'darwin' else ("Segoe UI", 11, "bold"),
    bg=COLORS['button_disabled'],
    fg="white",
    activebackground=COLORS['button_hover'],
    activeforeground="white",
    pady=12,
    state='disabled',
    cursor="hand2",
    relief='flat',
    bd=0,
    highlightthickness=0,
    command=run_calculation
)
btn_run.pack(fill='x', pady=4)
btn_run.bind("<Enter>", on_enter_run)
btn_run.bind("<Leave>", on_leave_run)

btn_save = tk.Button(
    action_section,
    text="💾 Save Output (TIFF + PDF)",
    font=("SF Pro Display", 11, "bold") if os.name == 'darwin' else ("Segoe UI", 11, "bold"),
    bg=COLORS['button_disabled'],
    fg="white",
    activebackground=COLORS['button_hover'],
    activeforeground="white",
    pady=12,
    state='disabled',
    cursor="hand2",
    relief='flat',
    bd=0,
    highlightthickness=0,
    command=save_output
)
btn_save.pack(fill='x', pady=4)
btn_save.bind("<Enter>", on_enter_save)
btn_save.bind("<Leave>", on_leave_save)

# ========== RIGHT COLUMN CONTENT ==========
right_content = tk.Frame(right_column, bg=COLORS['card_bg'])
right_content.pack(fill='both', expand=True, padx=25, pady=25)

# Status section
status_section = tk.LabelFrame(
    right_content,
    text="📊 Status",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
status_section.pack(fill='x', pady=(0, 15))

status = tk.Label(
    status_section,
    text="⚪ Ready - Upload an image to begin",
    font=("Segoe UI", 11),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    wraplength=400,
    justify='left'
)
status.pack(pady=10, anchor='w')

# Information section
info_section = tk.LabelFrame(
    right_content,
    text="ℹ️ Information",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
info_section.pack(fill='both', expand=True)

# Create a Text widget for dynamic information display
info_text = tk.Text(
    info_section,
    font=("Segoe UI", 10),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    wrap='word',
    relief='flat',
    padx=10,
    pady=10,
    state='normal',
    height=20
)
info_text.pack(fill='both', expand=True, pady=5)

# Configure text tags for styling
info_text.tag_config('title', font=("Segoe UI", 11, "bold"), foreground=COLORS['text'])
info_text.tag_config('heading', font=("Segoe UI", 10, "bold"), foreground=COLORS['secondary'])
info_text.tag_config('data', font=("Segoe UI", 10), foreground=COLORS['text'])
info_text.tag_config('success', font=("Segoe UI", 10), foreground=COLORS['success'])
info_text.tag_config('warning', font=("Segoe UI", 10), foreground=COLORS['warning'])

# Initial information display
def update_info_display(mode='initial', image_data=None, calc_data=None):
    """Update the information panel dynamically based on current state"""
    info_text.config(state='normal')
    info_text.delete(1.0, tk.END)

    if mode == 'initial':
        # Initial state - show general NDSI information
        info_text.insert(tk.END, "🔍 NDSI (Normalized Difference Snow Index)\n\n", 'title')
        info_text.insert(tk.END, "Formula:\n", 'heading')
        info_text.insert(tk.END, "NDSI = (Green - SWIR) / (Green + SWIR)\n\n", 'data')

        info_text.insert(tk.END, "📌 Requirements:\n", 'heading')
        info_text.insert(tk.END, "• Band 1: Green (B3)\n", 'data')
        info_text.insert(tk.END, "• Band 2: SWIR (B11)\n\n", 'data')

        info_text.insert(tk.END, "📈 Output Range:\n", 'heading')
        info_text.insert(tk.END, "• -1 to +1\n", 'data')
        info_text.insert(tk.END, "• Higher values → More snow/ice\n", 'data')
        info_text.insert(tk.END, "• Lower values → Less snow/ice\n\n", 'data')

        info_text.insert(tk.END, "💡 Typical Threshold: 0.4\n", 'heading')
        info_text.insert(tk.END, "Values above threshold indicate snow presence\n\n", 'data')

        info_text.insert(tk.END, "📁 Output Files:\n", 'heading')
        info_text.insert(tk.END, "• GeoTIFF raster file\n", 'data')
        info_text.insert(tk.END, "• PNG preview image\n", 'data')
        info_text.insert(tk.END, "• PDF analysis report\n", 'data')

    elif mode == 'image_loaded':
        # Show image information
        info_text.insert(tk.END, "📂 Image Information\n\n", 'title')

        info_text.insert(tk.END, "File Name:\n", 'heading')
        info_text.insert(tk.END, f"{image_data['filename']}\n\n", 'data')

        info_text.insert(tk.END, "Dimensions:\n", 'heading')
        info_text.insert(tk.END, f"• Width: {image_data['width']} pixels\n", 'data')
        info_text.insert(tk.END, f"• Height: {image_data['height']} pixels\n", 'data')
        info_text.insert(tk.END, f"• Total pixels: {image_data['width'] * image_data['height']:,}\n\n", 'data')

        info_text.insert(tk.END, "Bands:\n", 'heading')
        info_text.insert(tk.END, f"• Total bands: {image_data['bands']}\n", 'data')
        if image_data['bands'] >= 2:
            info_text.insert(tk.END, "• Band 1 (Green): Available ✓\n", 'success')
            info_text.insert(tk.END, "• Band 2 (SWIR): Available ✓\n\n", 'success')
        else:
            info_text.insert(tk.END, "• Insufficient bands for NDSI ✗\n\n", 'warning')

        info_text.insert(tk.END, "Data Type:\n", 'heading')
        info_text.insert(tk.END, f"{image_data['dtype']}\n\n", 'data')

        info_text.insert(tk.END, "Coordinate System:\n", 'heading')
        info_text.insert(tk.END, f"{image_data['crs']}\n\n", 'data')

        if image_data['bands'] >= 2:
            info_text.insert(tk.END, "Band Statistics (Green):\n", 'heading')
            info_text.insert(tk.END, f"• Min: {image_data['green_min']:.2f}\n", 'data')
            info_text.insert(tk.END, f"• Max: {image_data['green_max']:.2f}\n", 'data')
            info_text.insert(tk.END, f"• Mean: {image_data['green_mean']:.2f}\n\n", 'data')

            info_text.insert(tk.END, "Band Statistics (SWIR):\n", 'heading')
            info_text.insert(tk.END, f"• Min: {image_data['swir_min']:.2f}\n", 'data')
            info_text.insert(tk.END, f"• Max: {image_data['swir_max']:.2f}\n", 'data')
            info_text.insert(tk.END, f"• Mean: {image_data['swir_mean']:.2f}\n\n", 'data')

        info_text.insert(tk.END, "Status: ", 'heading')
        info_text.insert(tk.END, "Ready for calculation ✓\n", 'success')

    elif mode == 'calculated':
        # Show calculation results
        info_text.insert(tk.END, "📊 NDSI Calculation Results\n\n", 'title')

        info_text.insert(tk.END, "Image: ", 'heading')
        info_text.insert(tk.END, f"{calc_data['filename']}\n\n", 'data')

        info_text.insert(tk.END, "Applied Threshold: ", 'heading')
        info_text.insert(tk.END, f"{calc_data['threshold']:.2f}\n\n", 'data')

        info_text.insert(tk.END, "NDSI Statistics:\n", 'heading')
        info_text.insert(tk.END, f"• Minimum: {calc_data['min']:.4f}\n", 'data')
        info_text.insert(tk.END, f"• Maximum: {calc_data['max']:.4f}\n", 'data')
        info_text.insert(tk.END, f"• Mean: {calc_data['mean']:.4f}\n", 'data')
        info_text.insert(tk.END, f"• Std Dev: {calc_data['std']:.4f}\n\n", 'data')

        info_text.insert(tk.END, "Pixel Classification:\n", 'heading')
        info_text.insert(tk.END, f"• Total pixels: {calc_data['total_pixels']:,}\n", 'data')
        info_text.insert(tk.END, f"• Valid pixels: {calc_data['valid_pixels']:,}\n", 'data')
        info_text.insert(tk.END, f"• Snow pixels (≥{calc_data['threshold']:.2f}): {calc_data['snow_pixels']:,}\n", 'success')
        info_text.insert(tk.END, f"• Non-snow pixels (<{calc_data['threshold']:.2f}): {calc_data['non_snow_pixels']:,}\n", 'data')
        info_text.insert(tk.END, f"• No-data pixels: {calc_data['nodata_pixels']:,}\n\n", 'data')

        info_text.insert(tk.END, "Coverage Analysis:\n", 'heading')
        info_text.insert(tk.END, f"• Snow coverage: {calc_data['snow_percentage']:.2f}%\n", 'success')
        info_text.insert(tk.END, f"• Non-snow coverage: {calc_data['non_snow_percentage']:.2f}%\n", 'data')
        info_text.insert(tk.END, f"• No-data coverage: {calc_data['nodata_percentage']:.2f}%\n\n", 'data')

        info_text.insert(tk.END, "Value Distribution:\n", 'heading')
        info_text.insert(tk.END, f"• Pixels in range [-1, -0.5]: {calc_data['range1']:,}\n", 'data')
        info_text.insert(tk.END, f"• Pixels in range [-0.5, 0]: {calc_data['range2']:,}\n", 'data')
        info_text.insert(tk.END, f"• Pixels in range [0, 0.5]: {calc_data['range3']:,}\n", 'data')
        info_text.insert(tk.END, f"• Pixels in range [0.5, 1]: {calc_data['range4']:,}\n\n", 'data')

        info_text.insert(tk.END, "Status: ", 'heading')
        info_text.insert(tk.END, "Calculation complete ✓ Ready to save\n", 'success')

    info_text.config(state='disabled')

# Show initial information
update_info_display('initial')

# Footer
footer = tk.Label(
    main_container,
    text="Powered by Rasterio & Tkinter | © 2026",
    font=("Segoe UI", 9),
    bg=COLORS['background'],
    fg=COLORS['text_light']
)
footer.pack(pady=(20, 0))

root.mainloop()


# In[ ]:




