import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Optional

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from help_window import HelpWindow

from backend_poros import (
    MaskConfig,
    ThresholdConfig,
    GeometryConfig,
    StlExportConfig,
    run_full_analysis,
    export_pores_stl,
    compute_per_image_analysis,
    export_per_image_analysis_to_csv,
)


ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class PorosApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pore Analysis")
        self.geometry("1400x900")

        # --- Variables de Estado ---
        self.image_paths: List[str] = []
        self.current_image_index: int = 0
        self.analysis = None
        self.geom_cfg: Optional[GeometryConfig] = None
        self.mask_cfg: Optional[MaskConfig] = None
        self.help_window = None

        # Variables de UI
        self.selected_images_var = tk.StringVar(value="No images selected")
        self.resolution_info_var = tk.StringVar(value="")
        self.current_slice_info = tk.StringVar(value="Slice: -/-")

        # Variables de Configuración (valores por defecto)
        self.default_crop = {"y_min": 10, "y_max": 745, "x_min": 15, "x_max": 750}
        self.default_circle = {"use": True, "dy": -15, "dx": 0, "margin": 15}
        self.default_geom = {"pixel": 0.1, "slice_dist": 0.5}
        self.default_stl = {"tipo": "Internal", "sigma_z": 0.6, "sigma_xy": 1.0, "iteraciones_taubin": 10}

        # --- Layout Principal ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Frame Izquierdo: Controles (Sidebar)
        self.sidebar = ctk.CTkScrollableFrame(self, width=350, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self._build_sidebar()

        # Frame Derecho: Visualización
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self._build_main_area()

        # Binding inicial
        self._update_all_previews()

    def _build_sidebar(self):
        # Botón de ayuda
        btn_help = ctk.CTkButton(
            self.sidebar,
            text="Help",
            width=30,
            height=30,
            corner_radius=15,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="gray",
            hover_color="#555555",
            command=self.open_help,
        )
        btn_help.pack(padx=20, pady=(10, 0), anchor="e")

        # PASO 1: CARGA DE DATOS
        self._create_step_label("1. Load Images")

        self.btn_load = ctk.CTkButton(self.sidebar, text="Select Files", command=self.on_select_images)
        self.btn_load.pack(padx=20, pady=5, fill="x")

        self.lbl_file_status = ctk.CTkLabel(self.sidebar, textvariable=self.selected_images_var, text_color="gray")
        self.lbl_file_status.pack(padx=20, pady=(0, 2), anchor="w")

        self.lbl_resolution = ctk.CTkLabel(
            self.sidebar,
            textvariable=self.resolution_info_var,
            text_color="gray",
            font=ctk.CTkFont(size=11),
        )
        self.lbl_resolution.pack(padx=20, pady=(0, 10), anchor="w")

        # PASO 2: GEOMETRÍA
        self._create_step_label("2. Scale")

        frame_geom = ctk.CTkFrame(self.sidebar)
        frame_geom.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(frame_geom, text="Pixel dimension (mm):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_pixel = ctk.CTkEntry(frame_geom, width=80)
        self.entry_pixel.insert(0, str(self.default_geom["pixel"]))
        self.entry_pixel.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_geom, text="Distance between images (mm):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_slice = ctk.CTkEntry(frame_geom, width=80)
        self.entry_slice.insert(0, str(self.default_geom["slice_dist"]))
        self.entry_slice.grid(row=1, column=1, padx=5, pady=5)

        # PASO 3: REGIÓN DE INTERÉS (ROI)
        self._create_step_label("3. Region of Interest (ROI)")

        frame_crop = ctk.CTkFrame(self.sidebar)
        frame_crop.pack(padx=20, pady=5, fill="x")
        frame_crop.grid_columnconfigure((1, 3), weight=1)

        self.entry_ymin = self._create_labeled_entry(frame_crop, "Y min:", str(self.default_crop["y_min"]), 0, 0)
        self.entry_ymax = self._create_labeled_entry(frame_crop, "Y max:", str(self.default_crop["y_max"]), 0, 2)
        self.entry_xmin = self._create_labeled_entry(frame_crop, "X min:", str(self.default_crop["x_min"]), 1, 0)
        self.entry_xmax = self._create_labeled_entry(frame_crop, "X max:", str(self.default_crop["x_max"]), 1, 2)

        for entry in [self.entry_ymin, self.entry_ymax, self.entry_xmin, self.entry_xmax]:
            entry.bind("<FocusOut>", lambda e: self._update_all_previews())
            entry.bind("<Return>", lambda e: self._update_all_previews())

        self.switch_circle = ctk.CTkSwitch(self.sidebar, text="Circular Mask", command=self._update_all_previews)
        self.switch_circle.select()
        self.switch_circle.pack(padx=20, pady=(10, 5), anchor="w")

        frame_circle = ctk.CTkFrame(self.sidebar)
        frame_circle.pack(padx=20, pady=5, fill="x")

        self.entry_dy = self._create_labeled_entry(frame_circle, "Center ΔY:", str(self.default_circle["dy"]), 0, 0)
        self.entry_dx = self._create_labeled_entry(frame_circle, "Center ΔX:", str(self.default_circle["dx"]), 0, 2)
        self.entry_margin = self._create_labeled_entry(frame_circle, "Margin:", str(self.default_circle["margin"]), 1, 0)

        for entry in [self.entry_dy, self.entry_dx, self.entry_margin]:
            entry.bind("<FocusOut>", lambda e: self._update_all_previews())
            entry.bind("<Return>", lambda e: self._update_all_previews())

        # PASO 4: UMBRALIZACIÓN
        self._create_step_label("4. Threshold")

        self.switch_smooth = ctk.CTkSwitch(self.sidebar, text="Smoothing (Median+Gauss)", command=self._update_all_previews)
        self.switch_smooth.pack(padx=20, pady=5, anchor="w")

        self.slider_thresh = ctk.CTkSlider(self.sidebar, from_=0, to=255, number_of_steps=255, command=self._on_slider_change)
        self.slider_thresh.set(60)
        self.slider_thresh.pack(padx=20, pady=(10, 0), fill="x")

        self.lbl_thresh_val = ctk.CTkLabel(self.sidebar, text="Value: 60")
        self.lbl_thresh_val.pack(padx=20, pady=(0, 10))

        # PASO 5: EJECUCIÓN
        self._create_step_label("5. Analysis")

        self.btn_run = ctk.CTkButton(
            self.sidebar,
            text="RUN ANALYSIS",
            fg_color="green",
            height=40,
            font=ctk.CTkFont(weight="bold"),
            command=self.on_run_analysis,
        )
        self.btn_run.pack(padx=20, pady=10, fill="x")

        # PASO 6: EXPORTAR
        self._create_step_label("6. Export Results")

        self.switch_stl_gauss = ctk.CTkSwitch(self.sidebar, text="Gaussian Smoothing")
        self.switch_stl_gauss.pack(padx=20, pady=(5, 2), anchor="w")

        self.switch_stl_taubin = ctk.CTkSwitch(self.sidebar, text="Taubin Smoothing")
        self.switch_stl_taubin.pack(padx=20, pady=(2, 8), anchor="w")

        frame_stl_params = ctk.CTkFrame(self.sidebar)
        frame_stl_params.pack(padx=20, pady=5, fill="x")
        frame_stl_params.grid_columnconfigure((1, 3), weight=1)

        self.entry_sigma_z = self._create_labeled_entry(
            frame_stl_params, "Sigma Z:", str(self.default_stl["sigma_z"]), 0, 0
        )
        self.entry_sigma_xy = self._create_labeled_entry(
            frame_stl_params, "Sigma XY:", str(self.default_stl["sigma_xy"]), 0, 2
        )
        self.entry_iteraciones_taubin = self._create_labeled_entry(
            frame_stl_params, "Taubin Iter.:", str(self.default_stl["iteraciones_taubin"]), 1, 0
        )

        frame_stl = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        frame_stl.pack(padx=20, pady=5, fill="x")

        self.stl_type_var = ctk.StringVar(value=self.default_stl["tipo"])

        self.btn_exp_stl = ctk.CTkButton(
            frame_stl,
            text="Export STL",
            state="disabled",
            command=self.on_generate_stl,
        )
        self.btn_exp_stl.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.combo_stl_type = ctk.CTkComboBox(
            frame_stl,
            values=["Internal", "External", "All"],
            variable=self.stl_type_var,
            state="readonly",
            width=120,
        )
        self.combo_stl_type.pack(side="right")

        self.btn_exp_csv = ctk.CTkButton(
            self.sidebar,
            text="Export CSV (3D Volumes)",
            state="disabled",
            command=self.on_export_csv,
        )
        self.btn_exp_csv.pack(padx=20, pady=5, fill="x")

        self.btn_exp_csv2d = ctk.CTkButton(
            self.sidebar,
            text="Export CSV (Pore Analysis)",
            state="disabled",
            command=self.on_export_csv_por_imagen,
        )
        self.btn_exp_csv2d.pack(padx=20, pady=5, fill="x")

        ctk.CTkLabel(self.sidebar, text="Version 2", text_color="gray").pack(side="bottom", pady=20)

    def open_help(self):
        if self.help_window is not None and self.help_window.winfo_exists():
            self.help_window.lift()
        else:
            self.help_window = HelpWindow(self)

    def _build_main_area(self):
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=0)
        self.main_area.grid_rowconfigure(2, weight=0)

        self.tabview = ctk.CTkTabview(self.main_area)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        self.tab_orig = self.tabview.add("Original")
        self.tab_proc = self.tabview.add("Crop/Mask")
        self.tab_bin = self.tabview.add("Binarized")

        for tab in [self.tab_orig, self.tab_proc, self.tab_bin]:
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        self.lbl_img_orig = ctk.CTkLabel(self.tab_orig, text="Load images to view", text_color="gray")
        self.lbl_img_orig.grid(row=0, column=0)

        self.lbl_img_proc = ctk.CTkLabel(self.tab_proc, text="...", text_color="gray")
        self.lbl_img_proc.grid(row=0, column=0)

        self.lbl_img_bin = ctk.CTkLabel(self.tab_bin, text="...", text_color="gray")
        self.lbl_img_bin.grid(row=0, column=0)

        frame_nav = ctk.CTkFrame(self.main_area, fg_color="transparent")
        frame_nav.grid(row=1, column=0, sticky="ew", pady=10)

        self.btn_prev = ctk.CTkButton(frame_nav, text="<< Previous", width=100, command=self.on_prev_image, state="disabled")
        self.btn_prev.pack(side="left", padx=10)

        self.lbl_slice_info = ctk.CTkLabel(frame_nav, textvariable=self.current_slice_info, font=ctk.CTkFont(size=14))
        self.lbl_slice_info.pack(side="left", expand=True)

        self.btn_next = ctk.CTkButton(frame_nav, text="Next >>", width=100, command=self.on_next_image, state="disabled")
        self.btn_next.pack(side="right", padx=10)

        frame_bottom = ctk.CTkFrame(self.main_area)
        frame_bottom.grid(row=2, column=0, sticky="nsew", pady=10)
        frame_bottom.grid_columnconfigure(0, weight=1)
        frame_bottom.grid_columnconfigure(1, weight=1)

        self.frame_hist = ctk.CTkFrame(frame_bottom, fg_color="white", width=400, height=200)
        self.frame_hist.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.frame_hist.grid_propagate(False)

        self.hist_figure = Figure(figsize=(5, 2), dpi=100)
        self.hist_ax = self.hist_figure.add_subplot(111)
        self.hist_ax.set_title("Gray Histogram", fontsize=8)
        self.hist_figure.tight_layout()

        self.hist_canvas = FigureCanvasTkAgg(self.hist_figure, master=self.frame_hist)
        self.hist_canvas.get_tk_widget().pack(fill="both", expand=True)

        self.textbox_results = ctk.CTkTextbox(frame_bottom, height=200)
        self.textbox_results.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.textbox_results.insert("0.0", "Analysis results will appear here...")

    # --- Helpers UI ---
    def _create_step_label(self, text):
        ctk.CTkLabel(self.sidebar, text=text, font=ctk.CTkFont(weight="bold")).pack(padx=20, pady=(15, 5), anchor="w")

    def _create_labeled_entry(self, parent, text, default_val, r, c):
        ctk.CTkLabel(parent, text=text).grid(row=r, column=c, padx=2, pady=2, sticky="e")
        entry = ctk.CTkEntry(parent, width=50)
        entry.insert(0, default_val)
        entry.grid(row=r, column=c + 1, padx=2, pady=2)
        return entry

    def _on_slider_change(self, value):
        val_int = int(value)
        self.lbl_thresh_val.configure(text=f"Value: {val_int}")
        self._update_all_previews()

    # --- Logic ---
    def on_select_images(self):
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.tif;*.tiff;*.bmp"), ("All", "*.*")],
        )
        if paths:
            self.image_paths = sorted(list(paths))
            self.current_image_index = 0
            self.selected_images_var.set(f"{len(self.image_paths)} images loaded")
            self._check_and_update_resolutions()
            self.btn_prev.configure(state="normal")
            self.btn_next.configure(state="normal")
            self._update_all_previews()

    def _check_and_update_resolutions(self):
        if not self.image_paths:
            self.resolution_info_var.set("")
            return

        img0 = self.imread_unicode(self.image_paths[0])
        if img0 is None:
            return
        h0, w0 = img0.shape[:2]
        self.resolution_info_var.set(f"{w0} x {h0} px")

    def on_prev_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_paths)
            self._update_all_previews()

    def on_next_image(self):
        if self.image_paths:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_paths)
            self._update_all_previews()

    def imread_unicode(self, path):
        with open(path, "rb") as f:
            data = np.frombuffer(f.read(), np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)

    def _update_all_previews(self, *args):
        if not self.image_paths:
            return

        idx = self.current_image_index
        path = self.image_paths[idx]

        self.current_slice_info.set(f"Slice: {idx + 1}/{len(self.image_paths)} - {os.path.basename(path)}")

        try:
            mask_cfg = self._build_mask_config_safe()
            thr_cfg = self._build_threshold_config_safe()

            img_bgr = self.imread_unicode(path)
            if img_bgr is None:
                return
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            h, w = img_rgb.shape[:2]

            y_min, y_max, x_min, x_max = mask_cfg.crop
            y_min, y_max = max(0, min(h, y_min)), max(0, min(h, y_max))
            x_min, x_max = max(0, min(w, x_min)), max(0, min(w, x_max))

            img_crop = img_rgb[y_min:y_max, x_min:x_max].copy()
            if img_crop.size == 0:
                return

            circle_mask = np.ones(img_crop.shape[:2], dtype=bool)
            if mask_cfg.use_circular_mask:
                ch, cw = img_crop.shape[:2]
                dy, dx = mask_cfg.circle_center_offset
                cy, cx = ch // 2 + dy, cw // 2 + dx
                radius = max(1, min(ch, cw) // 2 - mask_cfg.circle_margin)
                y_grid, x_grid = np.ogrid[:ch, :cw]
                dist2 = (x_grid - cx) ** 2 + (y_grid - cy) ** 2
                circle_mask = dist2 <= radius**2

            img_masked = img_crop.copy()
            img_masked[~circle_mask] = 0

            gray = cv2.cvtColor(img_crop, cv2.COLOR_RGB2GRAY)
            if thr_cfg.apply_smoothing:
                gray = cv2.medianBlur(gray, 3)
                gray = cv2.GaussianBlur(gray, (3, 3), 0)

            val_thresh = thr_cfg.manual_threshold
            _, binaria = cv2.threshold(gray, val_thresh, 255, cv2.THRESH_BINARY_INV)
            binaria[~circle_mask] = 0

            self._display_image(img_rgb, self.lbl_img_orig)
            self._display_image(img_masked, self.lbl_img_proc)
            self._display_image(binaria, self.lbl_img_bin, is_gray=True)

            self._update_histogram(gray[circle_mask], val_thresh)

        except Exception as e:
            print(f"Error preview: {e}")

    def _display_image(self, img_array, label_widget, is_gray=False):
        h, w = img_array.shape[:2]

        max_h = 500
        scale = max_h / h if h > max_h else 1.0
        new_w, new_h = int(w * scale), int(h * scale)

        pil_img = Image.fromarray(img_array)
        ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))

        label_widget.configure(image=ctk_img, text="")
        label_widget.image = ctk_img

    def _update_histogram(self, values, threshold):
        self.hist_ax.clear()
        self.hist_ax.hist(values.ravel(), bins=100, range=(0, 255), color="gray", alpha=0.7)
        self.hist_ax.axvline(threshold, color="red", linestyle="--")
        self.hist_ax.set_title(f"Histogram (Thresh={threshold})", fontsize=9, color="black")
        self.hist_ax.tick_params(axis="both", labelsize=8)
        self.hist_canvas.draw_idle()

    # --- Config Builders ---
    def _get_int(self, entry_widget, default=0):
        try:
            return int(entry_widget.get())
        except Exception:
            return default

    def _get_float(self, entry_widget, default=0.0):
        try:
            return float(entry_widget.get())
        except Exception:
            return default

    def _build_mask_config_safe(self):
        y_min = self._get_int(self.entry_ymin, 0)
        y_max = self._get_int(self.entry_ymax, 100)
        x_min = self._get_int(self.entry_xmin, 0)
        x_max = self._get_int(self.entry_xmax, 100)

        dy = self._get_int(self.entry_dy, 0)
        dx = self._get_int(self.entry_dx, 0)
        margin = self._get_int(self.entry_margin, 0)
        use = bool(self.switch_circle.get())

        return MaskConfig(
            crop=(y_min, y_max, x_min, x_max),
            use_circular_mask=use,
            circle_center_offset=(dy, dx),
            circle_margin=margin,
        )

    def _build_threshold_config_safe(self):
        val = int(self.slider_thresh.get())
        smooth = bool(self.switch_smooth.get())
        return ThresholdConfig(use_otsu=False, manual_threshold=val, apply_smoothing=smooth)

    def _build_geo_config_safe(self):
        px = self._get_float(self.entry_pixel, 0.1)
        dz = self._get_float(self.entry_slice, 0.5)
        return GeometryConfig(pixel_size_mm=px, slice_distance_mm=dz)

    def _build_stl_export_config_safe(self):
        return StlExportConfig(
            tipo=self.stl_type_var.get(),
            aplicar_gaussiano=bool(self.switch_stl_gauss.get()),
            aplicar_taubin=bool(self.switch_stl_taubin.get()),
            sigma_z=self._get_float(self.entry_sigma_z, self.default_stl["sigma_z"]),
            sigma_xy=self._get_float(self.entry_sigma_xy, self.default_stl["sigma_xy"]),
            iteraciones_taubin=self._get_int(
                self.entry_iteraciones_taubin,
                self.default_stl["iteraciones_taubin"],
            ),
        )

    # --- Acciones principales ---
    def on_run_analysis(self):
        if not self.image_paths:
            messagebox.showwarning("Attention", "Select images first.")
            return

        self.btn_run.configure(state="disabled", text="Processing...")
        self.textbox_results.delete("0.0", "end")
        self.textbox_results.insert("0.0", "Starting analysis... please wait.\n")
        self.update()

        try:
            mask_cfg = self._build_mask_config_safe()
            thr_cfg = self._build_threshold_config_safe()
            geom_cfg = self._build_geo_config_safe()

            self.mask_cfg = mask_cfg
            self.geom_cfg = geom_cfg

            self.analysis = run_full_analysis(
                image_paths=self.image_paths,
                mask_cfg=mask_cfg,
                thr_cfg=thr_cfg,
                geom_cfg=geom_cfg,
            )

            self._show_results_summary()

            self.btn_exp_stl.configure(state="normal")
            self.btn_exp_csv.configure(state="normal")
            self.btn_exp_csv2d.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            self.textbox_results.insert("end", f"\nError: {str(e)}")

        self.btn_run.configure(state="normal", text="RUN ANALYSIS")

    def _show_results_summary(self):
        if not self.analysis:
            return

        res = self.analysis
        n_imgs = len(res.segmentation.labels_by_image)
        n_int = len(res.internal_pore_ids)
        vol_total = res.total_internal_volume_mm3

        summary = (
            f"=== ANALYSIS COMPLETED ===\n\n"
            f"Processed Images: {n_imgs}\n"
            f"Internal Pores (Closed): {n_int}\n"
            f"Total Internal Pore Volume: {vol_total:.4f} mm³\n\n"
            f"3D components detected: {len(res.internal_components)}\n"
            f"Pores connected to the outside: {len(res.external_pore_ids)}\n"
        )
        self.textbox_results.insert("end", summary)

    def on_generate_stl(self):
        if self.analysis is None or self.geom_cfg is None:
            messagebox.showwarning("Attention", "Please run the analysis first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".stl",
            filetypes=[("STL", "*.stl")],
        )
        if path:
            original_text = self.btn_exp_stl.cget("text")
            self.btn_exp_stl.configure(state="disabled", text="Exporting...")
            self.update()
            try:
                export_cfg = self._build_stl_export_config_safe()

                n, final_path = export_pores_stl(
                    self.analysis,
                    self.geom_cfg,
                    path,
                    export_cfg=export_cfg,
                )

                messagebox.showinfo(
                    "Success",
                    f"{export_cfg.tipo} pores STL saved with {n} pores.\n\nPath: {final_path}",
                )
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                self.btn_exp_stl.configure(state="normal", text=original_text)

    def on_export_csv(self):
        if self.analysis is None:
            messagebox.showwarning("Attention", "Please run the analysis first.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            original_text = self.btn_exp_csv.cget("text")
            self.btn_exp_csv.configure(state="disabled", text="Exporting...")
            self.update()
            try:
                import csv

                comps = sorted(self.analysis.internal_components, key=lambda c: c.volume_mm3, reverse=True)
                with open(path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f, delimiter=";")
                    writer.writerow(["id", "vol_mm3", "n_slices"])
                    for c in comps:
                        writer.writerow([c.component_id, f"{c.volume_mm3:.5f}", c.n_slices])
                messagebox.showinfo("Success", "CSV saved.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                self.btn_exp_csv.configure(state="normal", text=original_text)

    def on_export_csv_por_imagen(self):
        if self.analysis is None or self.mask_cfg is None or self.geom_cfg is None:
            messagebox.showwarning("Attention", "Please run the analysis first.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            original_text = self.btn_exp_csv2d.cget("text")
            self.btn_exp_csv2d.configure(state="disabled", text="Exporting...")
            self.update()
            try:
                records = compute_per_image_analysis(self.analysis, self.mask_cfg, self.geom_cfg)
                export_per_image_analysis_to_csv(records, path)
                messagebox.showinfo("Success", "2D CSV saved.")
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                self.btn_exp_csv2d.configure(state="normal", text=original_text)


if __name__ == "__main__":
    app = PorosApp()
    app.mainloop()
