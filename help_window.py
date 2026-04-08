import customtkinter as ctk

class HelpWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Documentación / Ayuda")
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
            text="Guía de Uso",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=(10, 20))

        # 1. Cargar
        self._add_section(
            "1. Cargar Imágenes",
            "Seleccione todas las imágenes (cortes) que componen su tomografía.\n"
            "El sistema verificará que todas tengan la misma resolución."
        )

        # 2. Escala
        self._add_section(
            "2. Escala (Geometría)",
            "Es CRÍTICO ingresar los valores correctos para obtener volúmenes reales:\n"
            "• Dimensión del pixel: Cuántos mm mide el lado de un píxel.\n"
            "   Este valor se puede encontrar a partir de la división entre la dimensión real conocida en la imagen (mm)y la dimensión en píxeles (px).\n"
            "• Distancia entre imágenes: El paso en Z entre cada corte.\n"
            "   Este valor se puede encontrar a partir de la división entre la altura total de la muestra (mm) y el número de imagenes totales."
        )

        # 3. ROI
        self._add_section(
            "3. Región de Interés",
            "Recorte la imagen para analizar solo la zona de interés.\n\n"
            "Parámetros de recorte:\n"
            "• Y min / Y max: límites verticales.\n"
            "• X min / X max: límites horizontales.\n"
            "El recorte se aplica como: imagen[y_min:y_max, x_min:x_max].\n\n"
            "Máscara Circular:\n"
            "Permite definir una región circular dentro del recorte para limitar el análisis.\n\n"
            "Parámetros de la máscara:\n"
            "• ΔY Centro: desplazamiento vertical del centro respecto al centro de la imagen.\n"
            "• ΔX Centro: desplazamiento horizontal del centro.\n"
            "• Margen: distancia en píxeles entre el borde del recorte y el borde del círculo."
        )

        # 4. Umbral
        self._add_section(
            "4. Umbralización",
            "Ajuste el valor de corte (0-255).\n"
            "• Píxeles < Umbral se consideran POROS (negro).\n"
            "• Píxeles > Umbral se consideran MATERIAL (blanco/gris).\n"
            "Use la pestaña 'Binarizada' para verificar qué se está detectando."
        )

        self._add_section(
            "4.1 Suavizado de imágenes (Median + Gauss)",
            "La opción 'Suavizado (Median+Gauss)' se aplica ANTES de la segmentación.\n"
            "Su objetivo es limpiar ruido y obtener una binarización más estable.\n\n"
            "• Mediana: Toma la mediana de todos los píxeles dentro del área del kernel (3x3) y reemplaza el elemento central con ese valor mediano.\n"
            "• Gaussiano: suaviza variaciones pequeñas de intensidad y hace más uniforme la imagen alaplicar una función en cada pixel que realiza la convolución de la imagen de entrada con el kernel gaussiano\n"
            "       La documentación se puede consultar mediante el siguiente enlace: https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html\n\n"
            "Cuándo conviene activarlo:\n"
            "• Si la imagen tiene grano, ruido o pequeñas manchas.\n"
            "• Si el contorno de los poros aparece muy irregular por el ruido.\n\n"
            "Cuándo conviene probar sin activarlo:\n"
            "• Si los poros son muy finos o pequeños y no quiere perder detalle.\n"
            "• Si la imagen ya viene limpia y bien contrastada.\n\n"
            "Recomendación:\n"
            "Compare la pestaña 'Binarizada' con y sin suavizado para verificar qué opción representa mejor los poros reales."
        )

        # 5. Ejecución
        self._add_section(
            "5. Análisis y Exportación",
            "Presione 'EJECUTAR ANÁLISIS'.\n"
            "Al finalizar, podrá exportar:\n"
            "• STL: Modelo 3D de los poros seleccionados.\n"
            "• CSV (Volúmenes 3D): Lista de poros conectados y sus volúmenes.\n"
            "• CSV (Análisis de poros): Métricas detalladas corte a corte."
        )


        # 7. Suavizado del STL
        self._add_section(
            "5.1. Suavizado del STL",
            "Estas opciones se aplican SOLO al modelo 3D exportado y no cambian el análisis 2D ni los volúmenes ya calculados.\n\n"
            "• Suavizado Gaussiano:\n"
            "  Se aplica al volumen 3D antes de generar la malla. Ayuda a redondear superficies escalonadas.\n"
            "  Aplica un desenfoque (suavizado) a un array multidimensional usando un filtro gaussiano, reduciendo el ruido al promediar los valores cercanos según una distribución normal.\n"
            "  - Sigma Z: controla el suavizado entre cortes.\n"
            "  - Sigma XY: controla el suavizado dentro de cada imagen.\n"
            "  Valores más altos generan una superficie más lisa, pero también pueden alterar más la forma original.\n"
            "  Se puede consultar la documentación mediante el siguiente enlace: https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.gaussian_filter.html\n\n"
            "• Suavizado Taubin:\n"
            "  Se aplica después, sobre la malla STL ya generada. Sirve para suavizar la superficie triangulada sin deformarla en exceso.\n"
            "  Ajusta la forma mediante difusión/laplaciano o calculando propiedades como normales y operadores necesarios para esas transformaciones.\n"
            "  - Iteraciones Taubin: a mayor cantidad, mayor suavizado.\n"
            "  Se puede consultar la documentación mediante el siguiente enlace: https://trimesh.org/trimesh.smoothing.html\n\n"
            "Uso sugerido:\n"
            "• Si el STL sale muy escalonado, active primero Gaussiano con valores moderados.\n"
            "• Si además la malla queda rugosa, active Taubin.\n"
            "• Evite valores demasiado altos si necesita conservar la geometría original con mayor fidelidad.\n\n"
            "Los valores recomendados para estos parámetros dependen de la resolución de su tomografía y del nivel de detalle que quiera conservar en el STL. Se sugiere probar con valores bajos e ir ajustando según el la necesidad"
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
