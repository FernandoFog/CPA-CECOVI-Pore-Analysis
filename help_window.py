import customtkinter as ctk

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Documentation / Help")
        self.geometry("600x780")

        # Make sure it floats on top
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))  # normalize after open

        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.pack(fill="both", expand=True, padx=10, pady=10)

        self._add_content()

    def _add_content(self):
        # Title
        ctk.CTkLabel(
            self.scroll,
            text="User Guide",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(10, 20))

        # 1. Cargar
        self._add_section(
            "1. Load Images",
            "Select all the images (slices) that make up your tomography.\n"
            "The system will verify that they all have the same resolution."
        )

        # 2. Escala
        self._add_section(
            "2. Scale (Geometry)",
            "It is CRITICAL to enter the correct values to obtain real volumes:\n"
            "• Pixel dimension: How many mm one side of a pixel measures.\n"
            "   This value can be found by dividing the known real dimension in the image (mm) by the dimension in pixels (px).\n"
            "• Distance between images: The Z step between each slice.\n"
            "   This value can be found by dividing the total height of the sample (mm) by the total number of images."
        )

        # 3. ROI
        self._add_section(
            "3. Region of Interest",
            "Crop the image to analyze only the zone of interest.\n\n"
            "Cropping parameters:\n"
            "• Y min / Y max: vertical limits.\n"
            "• X min / X max: horizontal limits.\n"
            "The crop is applied as: image[y_min:y_max, x_min:x_max].\n\n"
            "Circular Mask:\n"
            "Allows defining a circular region within the crop to limit the analysis.\n\n"
            "Mask parameters:\n"
            "• Center ΔY: vertical displacement of the center relative to the image center.\n"
            "• Center ΔX: horizontal displacement of the center.\n"
            "• Margin: distance in pixels between the crop edge and the circle edge."
        )

        # 4. Umbral
        self._add_section(
            "4. Thresholding",
            "Adjust the cutoff value (0-255).\n"
            "• Pixels < Threshold are considered PORES (black).\n"
            "• Pixels > Threshold are considered MATERIAL (white/gray).\n"
            "Use the 'Binarized' tab to check what is being detected."
        )

        self._add_section(
            "4.1 Image Smoothing (Median + Gauss)",
            "The 'Smoothing (Median+Gauss)' option is applied BEFORE segmentation.\n"
            "Its goal is to clean noise and obtain a more stable binarization.\n\n"
            "• Median: Takes the median of all pixels within the kernel area (3x3) and replaces the central element with that median value.\n"
            "• Gaussian: smooths small intensity variations and makes the image more uniform by applying a function on each pixel that performs the convolution of the input image with the gaussian kernel\n"
            "       Documentation can be consulted through the following link: https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html\n\n"
            "When to activate it:\n"
            "• If the image has grain, noise, or small spots.\n"
            "• If the pore contour appears very irregular due to noise.\n\n"
            "When to try without activating it:\n"
            "• If the pores are very fine or small and you don't want to lose detail.\n"
            "• If the image is already clean and well contrasted.\n\n"
            "Recommendation:\n"
            "Compare the 'Binarized' tab with and without smoothing to verify which option best represents the real pores."
        )

        # 5. Ejecución
        self._add_section(
            "5. Analysis and Export",
            "Press 'RUN ANALYSIS'.\n"
            "Once finished, you can export:\n"
            "• STL: 3D model of the selected pores.\n"
            "• CSV (3D Volumes): List of connected pores and their volumes.\n"
            "• CSV (Pore Analysis): Detailed slice-by-slice metrics."
        )


        # 7. Suavizado del STL
        self._add_section(
            "5.1. STL Smoothing",
            "These options apply ONLY to the exported 3D model and do not change the 2D analysis or the calculated volumes.\n\n"
            "• Gaussian Smoothing:\n"
            "  Applied to the 3D volume before generating the mesh. Helps round off stepped surfaces.\n"
            "  Applies a blur (smoothing) to a multidimensional array using a Gaussian filter, reducing noise by averaging nearby values according to a normal distribution.\n"
            "  - Sigma Z: controls smoothing between slices.\n"
            "  - Sigma XY: controls smoothing within each image.\n"
            "  Higher values generate a smoother surface, but may also alter the original shape more.\n"
            "  Documentation can be consulted through the following link: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html\n\n"
            "• Taubin Smoothing:\n"
            "  Applied afterwards, on the already generated STL mesh. Used to smooth the triangulated surface without distorting it excessively.\n"
            "  Adjusts the shape via diffusion/laplacian or by calculating properties like normals and operators needed for those transformations.\n"
            "  - Taubin Iterations: the higher the amount, the more smoothing.\n"
            "  Documentation can be consulted through the following link: https://trimesh.org/trimesh.smoothing.html\n\n"
            "Suggested usage:\n"
            "• If the STL looks very stepped, activate Gaussian first with moderate values.\n"
            "• If the mesh is also rough, activate Taubin.\n"
            "• Avoid excessively high values if you need to preserve the original geometry with greater fidelity.\n\n"
            "The recommended values for these parameters depend on the resolution of your tomography and the level of detail you want to keep in the STL. It is suggested to try low values and adjust as needed."
        )

    def _add_section(self, title, text):
        ctk.CTkLabel(
            self.scroll,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        ).pack(fill="x", pady=(10, 5))

        ctk.CTkLabel(
            self.scroll,
            text=text,
            anchor="w",
            justify="left"
        ).pack(fill="x", pady=(0, 10))

        # Separator (visual)
        ctk.CTkFrame(self.scroll, height=2, fg_color="gray").pack(fill="x", pady=5)
