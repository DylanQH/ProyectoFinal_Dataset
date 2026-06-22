# pid_controller.py
# Controlador PID para calcular el ángulo de dirección del vehículo.
#
# Este módulo implementa un controlador PID simple usado para convertir
# el error horizontal de la línea detectada en un ángulo de dirección.
#
# En esta actividad:
#   - El setpoint es el centro horizontal de la imagen.
#   - La variable medida es el centro horizontal de la línea seleccionada.
#   - El error se calcula en pixeles.
#   - La salida del PID se usa como ángulo de conducción del vehículo.

import time


class PIDController:
    """
    Controlador PID simple.

    Entrada:
        error = centro_imagen - centro_linea_detectada

    Salida:
        ángulo de dirección del vehículo.

    Componentes:
        P: proporcional al error actual.
        I: proporcional al error acumulado.
        D: proporcional al cambio del error.

    La salida se limita entre output_min y output_max para evitar comandos
    de dirección demasiado grandes.
    """

    def __init__(self, kp, ki, kd, output_min=-0.5, output_max=0.5):
        """
        Inicializa el controlador PID.

        Args:
            kp:
                Ganancia proporcional. Aumenta la respuesta directa al error.

            ki:
                Ganancia integral. Corrige errores acumulados en el tiempo.
                Debe usarse con cuidado para evitar acumulación excesiva
                cuando se pierde la línea.

            kd:
                Ganancia derivativa. Ayuda a reducir oscilaciones porque
                responde a cambios rápidos del error.

            output_min:
                Límite inferior de la salida del controlador.

            output_max:
                Límite superior de la salida del controlador.
        """

        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.output_min = output_min
        self.output_max = output_max

        # Error anterior usado para calcular el término derivativo.
        self.previous_error = 0.0

        # Acumulación del error usada para el término integral.
        self.integral = 0.0

        # Tiempo anterior usado para calcular dt.
        self.previous_time = None

    def reset(self):
        """
        Reinicia los estados internos del PID.

        Es útil llamar este método cuando:
            - se pierde la línea,
            - se reinicia la simulación,
            - se cambia de modo de control,
            - se quiere evitar acumulación integral.
        """

        self.previous_error = 0.0
        self.integral = 0.0
        self.previous_time = None

    def compute(self, error):
        """
        Calcula la salida PID a partir del error actual.

        Args:
            error:
                Error actual en pixeles.

        Returns:
            float:
                Salida del PID limitada entre output_min y output_max.
        """

        current_time = time.time()

        # Calcular el tiempo transcurrido entre iteraciones.
        # En la primera iteración no existe tiempo anterior, por eso dt = 0.
        if self.previous_time is None:
            dt = 0.0
        else:
            dt = current_time - self.previous_time

        self.previous_time = current_time

        # ------------------------------------------------------------
        # Término proporcional
        # ------------------------------------------------------------
        # Corrige de forma directa según el error actual.
        #
        # Si el error es grande, la corrección será grande.
        # Si el error es pequeño, la corrección será pequeña.
        # ------------------------------------------------------------

        proportional = self.kp * error

        # ------------------------------------------------------------
        # Término integral
        # ------------------------------------------------------------
        # Acumula el error a través del tiempo.
        #
        # Sirve para corregir errores pequeños pero constantes.
        # Debe usarse con cuidado porque puede acumular demasiado error
        # si la línea se pierde durante varios frames.
        # ------------------------------------------------------------

        if dt > 0:
            self.integral += error * dt

        integral = self.ki * self.integral

        # ------------------------------------------------------------
        # Término derivativo
        # ------------------------------------------------------------
        # Calcula qué tan rápido está cambiando el error.
        #
        # Ayuda a reducir oscilaciones y cambios bruscos en el giro.
        # ------------------------------------------------------------

        if dt > 0:
            derivative = self.kd * ((error - self.previous_error) / dt)
        else:
            derivative = 0.0

        self.previous_error = error

        # Salida total del PID.
        output = proportional + integral + derivative

        # ------------------------------------------------------------
        # Saturación de salida
        # ------------------------------------------------------------
        # Se limita la salida para no exceder el rango permitido de dirección.
        # ------------------------------------------------------------

        if output > self.output_max:
            output = self.output_max
        elif output < self.output_min:
            output = self.output_min

        return output