"""Controlador manual del vehículo y captura de datos para Webots."""

import csv
import traceback
from datetime import datetime
from pathlib import Path

from controller import Keyboard
from vehicle import Driver

from camera_service import CameraService
from config import (
    ANNOTATIONS_OUTPUT_DIR,
    CAMERA_NAME,
    CAPTURE_EVERY_N_FRAMES,
    DEFAULT_STEERING_ANGLE,
    IMAGE_OUTPUT_DIR,
    INITIAL_SPEED_KMH,
    MAX_SPEED_KMH,
    MAX_STEERING_ANGLE,
    MIN_SPEED_KMH,
    NAV_LEFT,
    NAV_RIGHT,
    NAV_STRAIGHT,
    SPEED_INCREMENT_KMH,
    STEERING_INCREMENT,
    USER_PREFIX,
)
from vehicle_service import VehicleService


def clamp(value, minimum, maximum):
    """Limita un valor numérico al intervalo indicado."""

    return max(minimum, min(maximum, value))


class CaptureSession:
    """Administra las imágenes y el CSV pertenecientes a una sesión."""

    def __init__(
        self,
        camera_service,
        user_prefix,
        image_output_dir,
        annotations_output_dir,
    ):
        self.camera_service = camera_service
        self.user_prefix = user_prefix
        self.image_output_dir = Path(image_output_dir)
        self.annotations_output_dir = Path(annotations_output_dir)

        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%d_%m_%Y_%H_%M")
        self.session_name = f"{self.user_prefix}_{timestamp}"
        self.csv_path = self.annotations_output_dir / f"{self.session_name}.csv"
        self.next_image_number = self._find_next_image_number()

        csv_is_empty = not self.csv_path.exists() or self.csv_path.stat().st_size == 0
        self.csv_file = self.csv_path.open("a", newline="", encoding="utf-8")
        self.csv_writer = csv.writer(self.csv_file)

        if csv_is_empty:
            self.csv_writer.writerow(["image_name", "steering_angle", "nav_command"])
            self.csv_file.flush()

    def _find_next_image_number(self):
        """Obtiene el siguiente consecutivo sin sobrescribir imágenes existentes."""

        highest_number = 0
        pattern = f"{self.session_name}_frame_*.jpeg"

        for image_path in self.image_output_dir.glob(pattern):
            try:
                number = int(image_path.stem.rsplit("_frame_", 1)[1])
            except (IndexError, ValueError):
                continue
            highest_number = max(highest_number, number)

        return highest_number + 1

    def save(self, steering_angle, nav_command):
        """Guarda una imagen y registra su ángulo de volante y comando de navegación en el CSV."""

        while True:
            image_name = f"{self.session_name}_frame_{self.next_image_number}.jpeg"
            image_path = self.image_output_dir / image_name
            if not image_path.exists():
                break
            self.next_image_number += 1

        self.camera_service.save_image(str(image_path), quality=100)

        if not image_path.exists():
            raise RuntimeError(f"Webots no pudo guardar la imagen: {image_path}")

        self.csv_writer.writerow([image_name, f"{steering_angle:.6f}", nav_command])
        self.csv_file.flush()
        self.next_image_number += 1

        return image_path

    def close(self):
        """Cierra el CSV de la sesión si todavía está abierto."""

        if not self.csv_file.closed:
            self.csv_file.close()


def validate_configuration():
    """Valida los parámetros configurables antes de iniciar Webots."""

    if MIN_SPEED_KMH > MAX_SPEED_KMH:
        raise ValueError("MIN_SPEED_KMH no puede ser mayor que MAX_SPEED_KMH.")
    if SPEED_INCREMENT_KMH <= 0:
        raise ValueError("SPEED_INCREMENT_KMH debe ser mayor que cero.")
    if MAX_STEERING_ANGLE < 0:
        raise ValueError("MAX_STEERING_ANGLE no puede ser negativo.")
    if STEERING_INCREMENT <= 0:
        raise ValueError("STEERING_INCREMENT debe ser mayor que cero.")
    if CAPTURE_EVERY_N_FRAMES <= 0:
        raise ValueError("CAPTURE_EVERY_N_FRAMES debe ser mayor que cero.")


def main():
    """Ejecuta el control manual y la captura periódica sin bloquear la conducción."""

    validate_configuration()

    driver = Driver()
    timestep = int(driver.getBasicTimeStep())

    keyboard = Keyboard()
    keyboard.enable(timestep)

    camera_service = CameraService(
        robot=driver,
        camera_name=CAMERA_NAME,
        timestep=timestep,
    )

    speed = clamp(INITIAL_SPEED_KMH, MIN_SPEED_KMH, MAX_SPEED_KMH)
    steering_angle = 0.0
    vehicle_service = VehicleService(
        driver=driver,
        cruising_speed=speed,
        max_steering_angle=MAX_STEERING_ANGLE,
    )

    capture_session = None
    capture_frame_counter = 0
    nav_command = NAV_STRAIGHT

    print("==========================================")
    print("Control manual iniciado")
    print("Flechas: acelerar, frenar y girar")
    print("A: regresar el volante al ángulo por defecto")
    print("R: iniciar captura de imágenes")
    print("1: comando izquierda | 2: comando recto | 3: comando derecha")
    print(f"Velocidad inicial: {speed:.1f} km/h")
    print(f"Captura cada {CAPTURE_EVERY_N_FRAMES} frames")
    print("Comando activo: RECTO")
    print("==========================================")

    try:
        while driver.step() != -1:
            control_changed = False
            key = keyboard.getKey()

            # Procesar todas las teclas disponibles sin detener el loop de Webots.
            while key != -1:
                if key == Keyboard.UP:
                    speed = clamp(
                        speed + SPEED_INCREMENT_KMH,
                        MIN_SPEED_KMH,
                        MAX_SPEED_KMH,
                    )
                    control_changed = True
                elif key == Keyboard.DOWN:
                    speed = clamp(
                        speed - SPEED_INCREMENT_KMH,
                        MIN_SPEED_KMH,
                        MAX_SPEED_KMH,
                    )
                    control_changed = True
                elif key == Keyboard.LEFT:
                    steering_angle = clamp(
                        steering_angle - STEERING_INCREMENT,
                        -MAX_STEERING_ANGLE,
                        MAX_STEERING_ANGLE,
                    )
                    control_changed = True
                elif key == Keyboard.RIGHT:
                    steering_angle = clamp(
                        steering_angle + STEERING_INCREMENT,
                        -MAX_STEERING_ANGLE,
                        MAX_STEERING_ANGLE,
                    )
                    control_changed = True
                elif key in (ord("a"), ord("A")):
                    steering_angle = clamp(
                        DEFAULT_STEERING_ANGLE,
                        -MAX_STEERING_ANGLE,
                        MAX_STEERING_ANGLE,
                    )
                    control_changed = True
                elif key == ord("1"):
                    nav_command = NAV_LEFT
                    print("Comando de navegación: IZQUIERDA")
                elif key == ord("2"):
                    nav_command = NAV_STRAIGHT
                    print("Comando de navegación: RECTO")
                elif key == ord("3"):
                    nav_command = NAV_RIGHT
                    print("Comando de navegación: DERECHA")
                elif key in (ord("r"), ord("R")) and capture_session is None:
                    capture_session = CaptureSession(
                        camera_service=camera_service,
                        user_prefix=USER_PREFIX,
                        image_output_dir=IMAGE_OUTPUT_DIR,
                        annotations_output_dir=ANNOTATIONS_OUTPUT_DIR,
                    )
                    capture_frame_counter = 0
                    print("------------------------------------------")
                    print("Captura iniciada")
                    print(f"Imágenes: {capture_session.image_output_dir}")
                    print(f"CSV: {capture_session.csv_path}")
                    print("------------------------------------------")

                key = keyboard.getKey()

            if control_changed:
                vehicle_service.release_brake()
                vehicle_service.set_speed(speed)
                vehicle_service.set_steering_angle(steering_angle)
                print(
                    f"Velocidad: {speed:.1f} km/h | "
                    f"Ángulo: {steering_angle:.3f} rad"
                )

            if capture_session is not None:
                capture_frame_counter += 1

                if capture_frame_counter >= CAPTURE_EVERY_N_FRAMES:
                    saved_path = capture_session.save(steering_angle, nav_command)
                    capture_frame_counter = 0
                    print(f"Imagen guardada: {saved_path.name}")
    finally:
        if capture_session is not None:
            capture_session.close()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("El controlador terminó con una excepción:")
        traceback.print_exc()
