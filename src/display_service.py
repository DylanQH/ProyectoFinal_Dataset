# display_service.py
# Servicio para mostrar imágenes procesadas en un Display de Webots.
#
# Este módulo separa la visualización del procesamiento principal.
# Su objetivo es mostrar en Webots las imágenes generadas durante el pipeline
# de detección de carriles, por ejemplo:
#   - imagen en escala de grises,
#   - imagen con ROI,
#   - líneas detectadas por Hough,
#   - línea seleccionada para el controlador PID.

from controller import Display
import numpy as np
import cv2


class DisplayService:
    """
    Servicio para manejar un Display de Webots.

    Responsabilidades:
        - Buscar el display por nombre dentro del robot/driver.
        - Mostrar imágenes en escala de grises.
        - Mostrar imágenes BGR generadas con OpenCV.
        - Convertir las imágenes al formato esperado por Webots.

    Webots espera imágenes en formato RGB para Display.imageNew().
    OpenCV normalmente trabaja en formato BGR, por eso se realiza una conversión
    antes de mostrar la imagen.
    """

    def __init__(self, robot, display_name):
        """
        Inicializa el servicio de display.

        Args:
            robot:
                Instancia del robot o Driver de Webots.

            display_name:
                Nombre del display dentro del mundo de Webots.
                Debe coincidir exactamente con el nombre configurado
                en el archivo .wbt.
        """

        self.robot = robot
        self.display_name = display_name

        # Obtener el dispositivo Display desde Webots.
        self.display = self.robot.getDevice(self.display_name)

        # El display no es crítico para el control del vehículo.
        # Si no existe, el programa continúa funcionando sin visualización.
        if self.display is None:
            print(f"WARNING: No se encontró el display: {self.display_name}")
            print("El programa continuará sin mostrar imagen procesada.")

    def show_gray_image(self, gray_image):
        """
        Muestra una imagen en escala de grises en el display de Webots.

        Como Webots espera una imagen RGB, la imagen de un solo canal se replica
        en tres canales:

            gray -> (gray, gray, gray)

        Args:
            gray_image:
                Imagen en escala de grises con forma (height, width).
        """

        if self.display is None or gray_image is None:
            return

        # Convertir imagen grayscale de 1 canal a RGB de 3 canales.
        image_rgb = np.dstack((gray_image, gray_image, gray_image)).astype(np.uint8)

        # Crear referencia de imagen compatible con Webots.
        image_ref = self.display.imageNew(
            image_rgb.tobytes(),
            Display.RGB,
            width=image_rgb.shape[1],
            height=image_rgb.shape[0],
        )

        # Pegar la imagen en la posición superior izquierda del display.
        self.display.imagePaste(image_ref, 0, 0, False)

        # Liberar la referencia para evitar acumulación de memoria.
        self.display.imageDelete(image_ref)

    def show_bgr_image(self, bgr_image):
        """
        Muestra una imagen BGR de OpenCV en el display de Webots.

        OpenCV usa BGR por defecto, mientras que Webots Display.imageNew()
        espera RGB. Por eso se realiza la conversión:

            BGR -> RGB

        Esta función se usa principalmente para mostrar la imagen de depuración,
        donde se dibujan:
            - ROI,
            - líneas detectadas por Hough,
            - líneas válidas,
            - línea seleccionada,
            - centro de la imagen.

        Args:
            bgr_image:
                Imagen en formato BGR con forma (height, width, 3).
        """

        if self.display is None or bgr_image is None:
            return

        # Convertir de BGR, formato de OpenCV, a RGB, formato esperado por Webots.
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

        # Crear imagen compatible con Webots.
        image_ref = self.display.imageNew(
            rgb_image.tobytes(),
            Display.RGB,
            width=rgb_image.shape[1],
            height=rgb_image.shape[0],
        )

        # Mostrar imagen en el display.
        self.display.imagePaste(image_ref, 0, 0, False)

        # Eliminar referencia para evitar fugas de memoria.
        self.display.imageDelete(image_ref)