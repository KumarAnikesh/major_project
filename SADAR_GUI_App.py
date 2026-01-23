#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
from PIL import Image as PILImage, ImageTk

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
output_folder_path = None

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

# ---------------- SELECT OUTPUT FOLDER ----------------
def select_output_folder():
    global output_folder_path

    output_folder_path = filedialog.askdirectory(title="Select Output Folder")

    if output_folder_path:
        output_folder_display.config(
            text=os.path.basename(output_folder_path),
            fg=COLORS['success']
        )
        status.config(
            text=f"✓ Output folder selected: {os.path.basename(output_folder_path)}",
            fg=COLORS['success']
        )
    else:
        output_folder_display.config(
            text="Not selected",
            fg=COLORS['text_light']
        )

# ---------------- DISPLAY IMAGE PREVIEW ----------------
def display_image_preview(img_path):
    """Display image preview in the right panel"""
    try:
        from PIL import Image, ImageTk
        import matplotlib.pyplot as plt
        import io

        # Read the image using rasterio
        with rasterio.open(img_path) as src:
            # Read first band for preview
            band_data = src.read(1)

            # Normalize for display
            band_min = np.nanmin(band_data)
            band_max = np.nanmax(band_data)

            if band_max > band_min:
                normalized = (band_data - band_min) / (band_max - band_min)
            else:
                normalized = band_data

            # Convert to 0-255 range
            preview_data = (normalized * 255).astype(np.uint8)

            # Create PIL Image
            pil_img = Image.fromarray(preview_data, mode='L')

            # Get canvas size
            canvas_width = preview_canvas.winfo_width()
            canvas_height = preview_canvas.winfo_height()

            # If canvas not rendered yet, use default size
            if canvas_width <= 1:
                canvas_width = 600
            if canvas_height <= 1:
                canvas_height = 500

            # Calculate scaling to fit canvas
            img_width, img_height = pil_img.size
            scale = min(canvas_width / img_width, canvas_height / img_height) * 0.95

            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            # Resize image
            pil_img = pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(pil_img)

            # Clear canvas
            preview_canvas.delete("all")

            # Display image centered
            preview_canvas.create_image(
                canvas_width // 2,
                canvas_height // 2,
                image=photo,
                anchor='center'
            )

            # Keep reference to prevent garbage collection
            preview_canvas.image = photo

            # Hide the "no image" label
            preview_label.place_forget()

            # Update info label
            image_info_label.config(
                text=f"📐 {img_width} x {img_height} px  |  Band 1 preview",
                fg=COLORS['text']
            )

    except Exception as e:
        print(f"Preview error: {e}")
        preview_canvas.delete("all")
        preview_label.config(
            text=f"Preview not available\n\n{str(e)[:50]}",
            fg=COLORS['error']
        )
        preview_label.place(relx=0.5, rely=0.5, anchor='center')

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
    # btn_save removed

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
                # Smart band detection
                if band_count >= 11:
                    # Full satellite image - use B3 and B11
                    green_band = src.read(3).astype(float)
                    swir_band = src.read(11).astype(float)
                    image_data['band_mode'] = 'Full image (B3 & B11)'
                elif band_count == 2:
                    # Pre-processed 2-band image
                    green_band = src.read(1).astype(float)
                    swir_band = src.read(2).astype(float)
                    image_data['band_mode'] = '2-band (B3 & B11)'
                else:
                    # 3+ band image (not full satellite)
                    green_band = src.read(1).astype(float)
                    swir_band = src.read(2).astype(float)
                    image_data['band_mode'] = f'{band_count}-band (using first 2: B3 & B11)'

                image_data['green_min'] = np.nanmin(green_band)
                image_data['green_max'] = np.nanmax(green_band)
                image_data['green_mean'] = np.nanmean(green_band)
                image_data['swir_min'] = np.nanmin(swir_band)
                image_data['swir_max'] = np.nanmax(swir_band)
                image_data['swir_mean'] = np.nanmean(swir_band)

                # Calculate NDSI preview for information display
                denom = green_band + swir_band
                with np.errstate(divide='ignore', invalid='ignore'):
                    ndsi_preview = (green_band - swir_band) / denom
                ndsi_preview[denom == 0] = np.nan
                ndsi_preview = np.clip(ndsi_preview, -1, 1)

                image_data['ndsi_min'] = np.nanmin(ndsi_preview)
                image_data['ndsi_max'] = np.nanmax(ndsi_preview)
                image_data['ndsi_mean'] = np.nanmean(ndsi_preview)

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
        else:
            status.config(
                text=f"✓ Image {current_image_index + 1}/{len(image_files)} loaded - Ready to calculate",
                fg=COLORS['success']
            )
            btn_run.config(state='normal', bg=COLORS['button_bg'])
            display_image_preview(image_path)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image: {str(e)}")
        status.config(text=f"❌ Error loading image", fg=COLORS['error'])


# ---------------- CALCULATE SINGLE INDEX ----------------
def calculate_index(calc_type, threshold_val, src):
    """Calculate a single spectral index"""
    band_count = src.count

    # Read bands based on calculation type
    if calc_type == "NDSI":
        # NDSI = (Green - SWIR) / (Green + SWIR)
        if band_count >= 11:
            band1 = src.read(3).astype(float)   # B3 (Green)
            band2 = src.read(11).astype(float)  # B11 (SWIR)
            band_info = "B3 (Green) & B11 (SWIR)"
        else:
            band1 = src.read(1).astype(float)
            band2 = src.read(2).astype(float)
            band_info = "Band 1 (Green) & Band 2 (SWIR)"
        class1_name, class2_name = "Snow", "Non-snow"

    elif calc_type == "NDWI":
        # NDWI = (Green - NIR) / (Green + NIR)
        if band_count >= 11:
            band1 = src.read(3).astype(float)   # B3 (Green)
            band2 = src.read(8).astype(float)   # B8 (NIR)
            band_info = "B3 (Green) & B8 (NIR)"
        else:
            band1 = src.read(1).astype(float)
            band2 = src.read(2).astype(float)
            band_info = "Band 1 (Green) & Band 2 (NIR)"
        class1_name, class2_name = "Water", "Non-water"

    elif calc_type == "NDVI":
        # NDVI = (NIR - Red) / (NIR + Red)
        if band_count >= 11:
            band1 = src.read(8).astype(float)   # B8 (NIR)
            band2 = src.read(4).astype(float)   # B4 (Red)
            band_info = "B8 (NIR) & B4 (Red)"
        else:
            band1 = src.read(1).astype(float)
            band2 = src.read(2).astype(float)
            band_info = "Band 1 (NIR) & Band 2 (Red)"
        class1_name, class2_name = "Vegetation", "Non-vegetation"

    # Calculate index
    denom = band1 + band2
    with np.errstate(divide='ignore', invalid='ignore'):
        result = (band1 - band2) / denom
    result[denom == 0] = np.nan
    result = np.clip(result, -1, 1)

    # Calculate statistics
    total_pixels = result.size
    valid_mask = ~np.isnan(result)
    valid_pixels = np.sum(valid_mask)
    nodata_pixels = total_pixels - valid_pixels

    threshold_mask = result >= threshold_val
    positive_pixels = np.sum(threshold_mask & valid_mask)
    negative_pixels = valid_pixels - positive_pixels

    positive_percentage = (positive_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    negative_percentage = (negative_pixels / total_pixels) * 100 if total_pixels > 0 else 0
    nodata_percentage = (nodata_pixels / total_pixels) * 100 if total_pixels > 0 else 0

    range1 = np.sum((result >= -1) & (result < -0.5) & valid_mask)
    range2 = np.sum((result >= -0.5) & (result < 0) & valid_mask)
    range3 = np.sum((result >= 0) & (result < 0.5) & valid_mask)
    range4 = np.sum((result >= 0.5) & (result <= 1) & valid_mask)

    return {
        'result': result,
        'band_info': band_info,
        'class1_name': class1_name,
        'class2_name': class2_name,
        'min': np.nanmin(result),
        'max': np.nanmax(result),
        'mean': np.nanmean(result),
        'std': np.nanstd(result),
        'total_pixels': total_pixels,
        'valid_pixels': valid_pixels,
        'nodata_pixels': nodata_pixels,
        'positive_pixels': positive_pixels,
        'negative_pixels': negative_pixels,
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'nodata_percentage': nodata_percentage,
        'range1': range1,
        'range2': range2,
        'range3': range3,
        'range4': range4
    }

# ---------------- CALCULATE ALL INDICES ----------------
def calculate_all_indices():
    """Calculate NDSI, NDWI, and NDVI together - OPTIMIZED"""
    global result_data, profile

    try:
        # Check if output folder is selected
        if not output_folder_path:
            messagebox.showwarning("Warning", "Please select output folder first.")
            return

        status.config(text="⏳ Loading image data...", fg=COLORS['warning'])
        root.update()

        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # Read image ONCE and store all needed bands
        with rasterio.open(image_path) as src:
            profile = src.profile
            band_count = src.count

            # Check if we have enough bands
            if band_count < 2:
                messagebox.showerror("Error", "Image must have at least 2 bands")
                return

            # Read all bands once
            if band_count >= 11:
                green = src.read(3).astype(float)   # B3
                red = src.read(4).astype(float)     # B4
                nir = src.read(8).astype(float)     # B8
                swir = src.read(11).astype(float)   # B11
                band_mode = "Full satellite image (B3, B4, B8, B11)"
            else:
                # For 2-band images, reuse bands
                band1 = src.read(1).astype(float)
                band2 = src.read(2).astype(float)
                green = band1
                red = band2
                nir = band1
                swir = band2
                band_mode = "2-band mode (using available bands)"

        # Calculate NDSI
        status.config(text="⏳ Calculating NDSI (1/3)...", fg=COLORS['warning'])
        root.update()

        denom_ndsi = green + swir
        with np.errstate(divide='ignore', invalid='ignore'):
            ndsi = (green - swir) / denom_ndsi
        ndsi[denom_ndsi == 0] = np.nan
        ndsi = np.clip(ndsi, -1, 1)

        # Calculate NDWI
        status.config(text="⏳ Calculating NDWI (2/3)...", fg=COLORS['warning'])
        root.update()

        denom_ndwi = green + nir
        with np.errstate(divide='ignore', invalid='ignore'):
            ndwi = (green - nir) / denom_ndwi
        ndwi[denom_ndwi == 0] = np.nan
        ndwi = np.clip(ndwi, -1, 1)

        # Calculate NDVI
        status.config(text="⏳ Calculating NDVI (3/3)...", fg=COLORS['warning'])
        root.update()

        denom_ndvi = nir + red
        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = (nir - red) / denom_ndvi
        ndvi[denom_ndvi == 0] = np.nan
        ndvi = np.clip(ndvi, -1, 1)

        # Save all results
        status.config(text="💾 Saving results...", fg=COLORS['warning'])
        root.update()

        temp_profile = profile.copy()
        temp_profile.update(dtype=rasterio.float32, count=1, nodata=np.nan)

        results = {
            'NDSI': ndsi,
            'NDWI': ndwi,
            'NDVI': ndvi
        }

        stats = {}

        for idx_type, idx_data in results.items():
            # Save TIFF with _processed naming
            out_tif = os.path.join(output_folder_path, f"{base_name}_{idx_type}_processed.tiff")
            with rasterio.open(out_tif, 'w', **temp_profile) as dst:
                dst.write(idx_data.astype(np.float32), 1)

            # Calculate stats
            stats[idx_type] = {
                'min': np.nanmin(idx_data),
                'max': np.nanmax(idx_data),
                'mean': np.nanmean(idx_data)
            }

        # Create individual previews
        for idx_type, idx_data in results.items():
            png_path = os.path.join(output_folder_path, f"{base_name}_{idx_type}_processed_preview.png")

            fig, ax = plt.subplots(figsize=(8, 6))
            im = ax.imshow(idx_data, cmap='RdBu', vmin=-1, vmax=1)
            plt.colorbar(im, ax=ax, label=idx_type)
            ax.set_title(f"{idx_type} - {base_name}", fontsize=12, fontweight='bold')
            ax.axis('off')
            plt.tight_layout()
            plt.savefig(png_path, dpi=150, bbox_inches='tight')
            plt.close(fig)

        # ============ CREATE COMPOSITE TIFF (3-band) ============
        status.config(text="🎨 Creating composite TIFF...", fg=COLORS['warning'])
        root.update()

        # Create 3-band composite TIFF
        composite_tiff_path = os.path.join(output_folder_path, f"{base_name}_processed_composite.tiff")

        # Update profile for 3 bands
        composite_profile = profile.copy()
        composite_profile.update(
            dtype=rasterio.float32,
            count=3,  # 3 bands for NDSI, NDWI, NDVI
            nodata=np.nan
        )

        # Write composite TIFF
        with rasterio.open(composite_tiff_path, 'w', **composite_profile) as dst:
            dst.write(ndsi.astype(np.float32), 1)  # Band 1: NDSI
            dst.write(ndwi.astype(np.float32), 2)  # Band 2: NDWI
            dst.write(ndvi.astype(np.float32), 3)  # Band 3: NDVI

            # Add band descriptions
            dst.set_band_description(1, 'NDSI (Snow Index)')
            dst.set_band_description(2, 'NDWI (Water Index)')
            dst.set_band_description(3, 'NDVI (Vegetation Index)')

        # Create COMPOSITE PNG visualization with all three indices
        status.config(text="🎨 Creating composite PNG preview...", fg=COLORS['warning'])
        root.update()

        composite_path = os.path.join(output_folder_path, f"{base_name}_processed_composite.png")

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # NDSI
        im1 = axes[0].imshow(ndsi, cmap='RdBu', vmin=-1, vmax=1)
        axes[0].set_title(f'NDSI (Snow Index)\nMean: {stats["NDSI"]["mean"]:.3f}', 
                          fontsize=11, fontweight='bold')
        axes[0].axis('off')
        plt.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)

        # NDWI
        im2 = axes[1].imshow(ndwi, cmap='RdBu', vmin=-1, vmax=1)
        axes[1].set_title(f'NDWI (Water Index)\nMean: {stats["NDWI"]["mean"]:.3f}', 
                          fontsize=11, fontweight='bold')
        axes[1].axis('off')
        plt.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)

        # NDVI
        im3 = axes[2].imshow(ndvi, cmap='RdBu', vmin=-1, vmax=1)
        axes[2].set_title(f'NDVI (Vegetation Index)\nMean: {stats["NDVI"]["mean"]:.3f}', 
                          fontsize=11, fontweight='bold')
        axes[2].axis('off')
        plt.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)

        # Main title
        fig.suptitle(f'All Spectral Indices - {base_name}', 
                     fontsize=14, fontweight='bold', y=0.98)

        plt.tight_layout()
        plt.savefig(composite_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        status.config(
            text=f"✓ All files saved: 3 individual TIFFs + 3 PNGs + composite TIFF + composite PNG",
            fg=COLORS['success']
        )

        # Update image info
        image_info_label.config(
            text=f"✅ NDSI: {stats['NDSI']['mean']:.3f} | NDWI: {stats['NDWI']['mean']:.3f} | NDVI: {stats['NDVI']['mean']:.3f}",
            fg=COLORS['success']
        )

        messagebox.showinfo(
            "Success",
            f"All 3 indices calculated and saved!\n\n"
            f"Time saved by batch processing!\n\n"
            f"Location: {output_folder_path}\n\n"
            f"Individual TIFF Files (3):\n"
            f"• {base_name}_NDSI_processed.tiff\n"
            f"• {base_name}_NDWI_processed.tiff\n"
            f"• {base_name}_NDVI_processed.tiff\n\n"
            f"Individual PNG Previews (3):\n"
            f"• {base_name}_NDSI_processed_preview.png\n"
            f"• {base_name}_NDWI_processed_preview.png\n"
            f"• {base_name}_NDVI_processed_preview.png\n\n"
            f"Composite Files (2):\n"
            f"• {base_name}_processed_composite.tiff (3-band)\n"
            f"• {base_name}_processed_composite.png (visualization)\n\n"
            f"Total: 8 files created"
        )

    except Exception as e:
        messagebox.showerror("Error", f"Failed to calculate all indices:\n{str(e)}")
        status.config(text="❌ Calculation failed", fg=COLORS['error'])

# ---------------- RUN CALCULATION ----------------
def run_calculation():
    global result_data, profile, green, swir

    calc_type = calculation_var.get()

    # Check if "All Indices" is selected
    if calc_type == "All Indices":
        calculate_all_indices()
        return

    try:
        status.config(text=f"⏳ Calculating {calc_type}...", fg=COLORS['warning'])
        root.update()

        with rasterio.open(image_path) as src:
            band_count = src.count

            # Read bands based on calculation type
            if calc_type == "NDSI":
                # NDSI = (Green - SWIR) / (Green + SWIR)
                if band_count >= 11:
                    band1 = src.read(3).astype(float)   # B3 (Green)
                    band2 = src.read(11).astype(float)  # B11 (SWIR)
                    band_info = "Using B3 (Green) and B11 (SWIR)"
                elif band_count >= 2:
                    band1 = src.read(1).astype(float)
                    band2 = src.read(2).astype(float)
                    if band_count == 2:
                        band_info = "Using Band 1 (Green) and Band 2 (SWIR)"
                    else:
                        band_info = f"Using first 2 bands as Green & SWIR"
                else:
                    messagebox.showerror("Error", 
                        f"Insufficient bands: {band_count}\n"
                        "NDSI requires at least 2 bands (Green & SWIR)")
                    return

            elif calc_type == "NDWI":
                # NDWI = (Green - NIR) / (Green + NIR)
                if band_count >= 11:
                    band1 = src.read(3).astype(float)   # B3 (Green)
                    band2 = src.read(8).astype(float)   # B8 (NIR)
                    band_info = "Using B3 (Green) and B8 (NIR)"
                elif band_count >= 2:
                    band1 = src.read(1).astype(float)
                    band2 = src.read(2).astype(float)
                    if band_count == 2:
                        band_info = "Using Band 1 (Green) and Band 2 (NIR)"
                    else:
                        band_info = f"Using first 2 bands as Green & NIR"
                else:
                    messagebox.showerror("Error", 
                        f"Insufficient bands: {band_count}\n"
                        "NDWI requires at least 2 bands (Green & NIR)")
                    return

            elif calc_type == "NDVI":
                # NDVI = (NIR - Red) / (NIR + Red)
                if band_count >= 11:
                    band1 = src.read(8).astype(float)   # B8 (NIR)
                    band2 = src.read(4).astype(float)   # B4 (Red)
                    band_info = "Using B8 (NIR) and B4 (Red)"
                elif band_count >= 2:
                    band1 = src.read(1).astype(float)
                    band2 = src.read(2).astype(float)
                    if band_count == 2:
                        band_info = "Using Band 1 (NIR) and Band 2 (Red)"
                    else:
                        band_info = f"Using first 2 bands as NIR & Red"
                else:
                    messagebox.showerror("Error", 
                        f"Insufficient bands: {band_count}\n"
                        "NDVI requires at least 2 bands (NIR & Red)")
                    return

            profile = src.profile

        # Calculate index
        denom = band1 + band2

        with np.errstate(divide='ignore', invalid='ignore'):
            result_data = (band1 - band2) / denom

        result_data[denom == 0] = np.nan
        result_data = np.clip(result_data, -1, 1)

        # Calculate statistics for display
        total_pixels = result_data.size
        valid_mask = ~np.isnan(result_data)
        valid_pixels = np.sum(valid_mask)
        nodata_pixels = total_pixels - valid_pixels

        threshold_mask = result_data >= ndsi_threshold
        positive_pixels = np.sum(threshold_mask & valid_mask)
        negative_pixels = valid_pixels - positive_pixels

        # Calculate percentages
        positive_percentage = (positive_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        negative_percentage = (negative_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        nodata_percentage = (nodata_pixels / total_pixels) * 100 if total_pixels > 0 else 0

        # Value distribution
        range1 = np.sum((result_data >= -1) & (result_data < -0.5) & valid_mask)
        range2 = np.sum((result_data >= -0.5) & (result_data < 0) & valid_mask)
        range3 = np.sum((result_data >= 0) & (result_data < 0.5) & valid_mask)
        range4 = np.sum((result_data >= 0.5) & (result_data <= 1) & valid_mask)

        # Set meaningful labels based on index type
        if calc_type == "NDSI":
            class1_name = "Snow"
            class2_name = "Non-snow"
        elif calc_type == "NDWI":
            class1_name = "Water"
            class2_name = "Non-water"
        elif calc_type == "NDVI":
            class1_name = "Vegetation"
            class2_name = "Non-vegetation"

        calc_data = {
            'filename': os.path.basename(image_path),
            'index_type': calc_type,
            'threshold': ndsi_threshold,
            'min': np.nanmin(result_data),
            'max': np.nanmax(result_data),
            'mean': np.nanmean(result_data),
            'std': np.nanstd(result_data),
            'total_pixels': total_pixels,
            'valid_pixels': valid_pixels,
            'nodata_pixels': nodata_pixels,
            'positive_pixels': positive_pixels,
            'negative_pixels': negative_pixels,
            'positive_percentage': positive_percentage,
            'negative_percentage': negative_percentage,
            'nodata_percentage': nodata_percentage,
            'range1': range1,
            'range2': range2,
            'range3': range3,
            'range4': range4,
            'band_info': band_info,
            'class1_name': class1_name,
            'class2_name': class2_name
        }

        status.config(text=f"✓ {calc_type} calculated successfully ({band_info})", fg=COLORS['success'])

        # Update image info with calculation results
        image_info_label.config(
            text=f"📊 {calc_type} calculated | Min: {calc_data['min']:.3f} | Max: {calc_data['max']:.3f} | Mean: {calc_data['mean']:.3f}",
            fg=COLORS['success']
        )

        # Auto-save immediately
        root.update()
        save_output()

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status.config(text=f"❌ Calculation failed: {str(e)}", fg=COLORS['error'])

# ---------------- SAVE OUTPUT ----------------
def save_output():
    global output_folder_path

    if result_data is None:
        messagebox.showwarning("Warning", "No result to save. Please run calculation first.")
        return

    # Check if output folder is selected
    if not output_folder_path:
        messagebox.showwarning("Warning", "Please select output folder first.")
        return

    try:
        status.config(text="💾 Saving outputs...", fg=COLORS['warning'])
        root.update()

        # Get calculation type and base filename
        calc_type = calculation_var.get()
        base_name = os.path.splitext(os.path.basename(image_path))[0]

        # ---- SAVE TIFF ----
        out_tif = os.path.join(output_folder_path, f"{base_name}_{calc_type}_processed.tiff")
        profile.update(dtype=rasterio.float32, count=1, nodata=np.nan)

        with rasterio.open(out_tif, 'w', **profile) as dst:
            dst.write(result_data.astype(np.float32), 1)

        # ---- SAVE PNG ----
        png_path = os.path.join(output_folder_path, f"{base_name}_{calc_type}_processed_preview.png")
        plt.figure(figsize=(10, 8))
        plt.imshow(result_data, cmap='RdBu', vmin=-1, vmax=1)
        plt.colorbar(label=calc_type, shrink=0.8)
        plt.title(f"{calc_type} Map - {base_name}", fontsize=16, fontweight='bold')
        plt.axis("off")
        plt.savefig(png_path, dpi=200, bbox_inches='tight')
        plt.close()

        # ---- PDF REPORT ----
        pdf_path = os.path.join(output_folder_path, f"{base_name}_{calc_type}_processed_report.pdf")
        doc = SimpleDocTemplate(pdf_path)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f"<b>{calc_type} Analysis Report</b>", styles['Title']))
        story.append(Paragraph(f"<b>Image:</b> {base_name}", styles['Normal']))
        story.append(Paragraph(
            f"<b>Threshold:</b> {ndsi_threshold:.2f}",
            styles['Normal']
        ))

        story.append(Paragraph(f"<br/><b>{calc_type} Statistics</b><br/>", styles['Normal']))
        story.append(Paragraph(f"Min: {np.nanmin(result_data):.4f}", styles['Normal']))
        story.append(Paragraph(f"Max: {np.nanmax(result_data):.4f}", styles['Normal']))
        story.append(Paragraph(f"Mean: {np.nanmean(result_data):.4f}", styles['Normal']))

        story.append(Paragraph(f"<br/><b>{calc_type} Map</b><br/>", styles['Normal']))
        story.append(Image(png_path, width=400, height=300))

        doc.build(story)

        status.config(
            text=f"✓ Saved: {base_name}_{calc_type}_processed.tiff + preview + report", 
            fg=COLORS['success']
        )

        # Show success message with file names
        messagebox.showinfo(
            "Success", 
            f"Files saved successfully!\n\n"
            f"Location: {output_folder_path}\n\n"
            f"Files:\n"
            f"• {base_name}_{calc_type}_processed.tiff\n"
            f"• {base_name}_{calc_type}_processed_preview.png\n"
            f"• {base_name}_{calc_type}_processed_report.pdf"
        )

    except Exception as e:
        messagebox.showerror("Save Error", f"Failed to save files:\n{str(e)}")
        status.config(text="❌ Failed to save outputs", fg=COLORS['error'])

# ---------------- BUTTON HOVER EFFECTS ----------------
def on_enter_run(e):
    if btn_run['state'] == 'normal':
        btn_run['background'] = COLORS['button_hover']

def on_leave_run(e):
    if btn_run['state'] == 'normal':
        btn_run['background'] = COLORS['button_bg']

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
    text="🛰️ Raster Index Calculator",
    font=("SF Pro Display", 28, "bold") if os.name == 'darwin' else ("Segoe UI", 28, "bold"),
    bg=COLORS['primary'],
    fg="white",
    pady=15
)
title.pack()

subtitle = tk.Label(
    header_frame,
    text="Professional GeoTIFF Analysis Tool",
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
    text="📁 Folders",
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
    text="Select input and output folders",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
upload_info.pack(pady=(5, 10), fill='x')

# Input folder section
input_folder_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
input_folder_frame.pack(fill='x', pady=(0, 10))

input_folder_label = tk.Label(
    input_folder_frame,
    text="Input Folder:",
    font=("Segoe UI", 9, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    anchor='w'
)
input_folder_label.pack(fill='x')

folder_label = tk.Label(
    input_folder_frame,
    text="No folder selected",
    font=("Segoe UI", 10),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
folder_label.pack(pady=(2, 0), fill='x')

folder_info_label = tk.Label(
    input_folder_frame,
    text="",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
folder_info_label.pack(pady=(0, 5), fill='x')

# Upload buttons frame
upload_buttons_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
upload_buttons_frame.pack(fill='x', pady=4)

btn_input_folder = tk.Button(
    upload_buttons_frame,
    text="📂 Select Input Folder",
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
btn_input_folder.pack(side='left', fill='x', expand=True, padx=(0, 5))

btn_output_folder = tk.Button(
    upload_buttons_frame,
    text="💾 Select Output Folder",
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
    command=select_output_folder
)
btn_output_folder.pack(side='right', fill='x', expand=True, padx=(5, 0))

# Output folder display
output_folder_frame = tk.Frame(upload_section, bg=COLORS['card_bg'])
output_folder_frame.pack(fill='x', pady=(10, 0))

output_folder_label = tk.Label(
    output_folder_frame,
    text="Output Folder:",
    font=("Segoe UI", 9, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    anchor='w'
)
output_folder_label.pack(fill='x')

output_folder_display = tk.Label(
    output_folder_frame,
    text="Not selected",
    font=("Segoe UI", 10),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    anchor='w'
)
output_folder_display.pack(pady=(2, 0), fill='x')

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
    values=["NDSI", "NDWI", "NDVI", "All Indices"],
    state='readonly',
    font=("Segoe UI", 10)
)
calc_dropdown.pack(fill='x')

# Add event handler for dropdown change
def on_calculation_change(event):
    calc_type = calculation_var.get()
    if calc_type == "NDSI":
        threshold_label.config(text="NDSI Threshold:")
        threshold_slider.config(from_=0.0, to=1.0)
        threshold_slider.set(0.4)
    elif calc_type == "NDWI":
        threshold_label.config(text="NDWI Threshold:")
        threshold_slider.config(from_=-1.0, to=1.0)
        threshold_slider.set(0.3)
    elif calc_type == "NDVI":
        threshold_label.config(text="NDVI Threshold:")
        threshold_slider.config(from_=-1.0, to=1.0)
        threshold_slider.set(0.2)
    elif calc_type == "All Indices":
        threshold_label.config(text="Thresholds (Auto):")
        threshold_slider.config(state='disabled')

calc_dropdown.bind('<<ComboboxSelected>>', on_calculation_change)

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

# ========== RIGHT COLUMN CONTENT ==========
right_content = tk.Frame(right_column, bg=COLORS['card_bg'])
right_content.pack(fill='both', expand=True, padx=25, pady=25)

# Image Preview section
preview_section = tk.LabelFrame(
    right_content,
    text="🖼️ Image Preview",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    padx=15,
    pady=10
)
preview_section.pack(fill='both', expand=True)

# Create canvas for image display
preview_canvas = tk.Canvas(
    preview_section,
    bg='#2c2c2e',
    highlightthickness=1,
    highlightbackground=COLORS['border']
)
preview_canvas.pack(fill='both', expand=True, padx=5, pady=5)

# Initial message
preview_label = tk.Label(
    preview_canvas,
    text="No image loaded\n\n📂 Select an image to see preview",
    font=("Segoe UI", 12),
    bg='#2c2c2e',
    fg='#86868b',
    justify='center'
)
preview_label.place(relx=0.5, rely=0.5, anchor='center')

# Image info label below preview
image_info_label = tk.Label(
    preview_section,
    text="",
    font=("Segoe UI", 9),
    bg=COLORS['card_bg'],
    fg=COLORS['text_light'],
    justify='left',
    anchor='w'
)
image_info_label.pack(fill='x', padx=5, pady=(5, 0))

# Status bar (bigger and prominent)
status_frame = tk.Frame(main_container, bg=COLORS['card_bg'], height=70)
status_frame.pack(fill='x', pady=(10, 0))
status_frame.pack_propagate(False)

status = tk.Label(
    status_frame,
    text="⚪ Ready - Select input folder to begin",
    font=("Segoe UI", 12, "bold"),
    bg=COLORS['card_bg'],
    fg=COLORS['text'],
    anchor='w',
    padx=20,
    pady=15
)
status.pack(fill='both', expand=True)

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




