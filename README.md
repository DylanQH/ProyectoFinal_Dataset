# Control manual y captura de datos en Webots

Este proyecto contiene un controlador en Python para conducir manualmente un
vehículo en Webots y crear un dataset de imágenes con el ángulo del volante
asociado a cada captura.

El controlador principal se encuentra en `src/main.py`. Los parámetros que se
pueden ajustar están centralizados en `src/config.py`.

## Funcionalidades

- Conducción manual mediante las flechas del teclado.
- Velocidad y giro limitados mediante valores configurables.
- Restablecimiento del volante a su posición por defecto.
- Captura periódica de imágenes desde la cámara del vehículo.
- Creación automática de un CSV con el ángulo del volante de cada imagen.
- Creación automática de las carpetas de salida.
- Nombres de sesión basados en la fecha y hora para evitar sobrescrituras.
- Captura de imágenes sin interrumpir la conducción.

## Controles

| Tecla | Acción |
|---|---|
| Flecha arriba | Incrementa la velocidad. |
| Flecha abajo | Reduce la velocidad o activa la reversa si está configurada. |
| Flecha izquierda | Reduce el ángulo del volante para girar a la izquierda. |
| Flecha derecha | Incrementa el ángulo del volante para girar a la derecha. |
| `A` o `a` | Regresa el volante a `DEFAULT_STEERING_ANGLE`. |
| `R` o `r` | Inicia la sesión de captura de imágenes. |

Una vez iniciada con `R`, la captura permanece activa hasta que finaliza el
controlador o se detiene la simulación.

## Configuración

Los valores principales se encuentran en `src/config.py`.

### Control del vehículo

```python
INITIAL_SPEED_KMH = 0.0
MIN_SPEED_KMH = 0.0
MAX_SPEED_KMH = 50.0
SPEED_INCREMENT_KMH = 5.0

DEFAULT_STEERING_ANGLE = 0.0
MAX_STEERING_ANGLE = 0.25
STEERING_INCREMENT = 0.05
```

- `INITIAL_SPEED_KMH`: velocidad al iniciar el controlador.
- `MIN_SPEED_KMH`: velocidad mínima permitida. Puede utilizarse un valor
  negativo para permitir reversa.
- `MAX_SPEED_KMH`: velocidad máxima permitida.
- `SPEED_INCREMENT_KMH`: cambio aplicado al presionar arriba o abajo.
- `DEFAULT_STEERING_ANGLE`: ángulo al que regresa el volante con la tecla `A`.
- `MAX_STEERING_ANGLE`: límite de giro positivo y negativo.
- `STEERING_INCREMENT`: cambio de ángulo aplicado con cada pulsación.

Las velocidades se expresan en kilómetros por hora y los ángulos en radianes.

### Captura del dataset

```python
USER_PREFIX = "usuario"
CAPTURE_EVERY_N_FRAMES = 10
```

- `USER_PREFIX`: identifica al usuario o simulación en los archivos generados.
- `CAPTURE_EVERY_N_FRAMES`: número de frames entre cada imagen guardada.

La cámara utilizada también puede configurarse:

```python
CAMERA_NAME = "camera"
```

El nombre debe coincidir con el dispositivo definido en el mundo de Webots.

## Rutas de salida

Las rutas se construyen con `pathlib` tomando como raíz la carpeta
`proyectofinal_entrenamiento`, por lo que no dependen del directorio desde el
que se ejecute el controlador.

Las imágenes se almacenan en:

```text
resources/notebook_entrenamiento/dataset/dataset/JPEGImages
```

Los CSV de anotaciones se almacenan en:

```text
resources/notebook_entrenamiento/dataset/dataset/Annotations
```

Si estas carpetas no existen, `main.py` las crea automáticamente al iniciar
una sesión de captura.

## Formato de los archivos

Cuando se presiona `R`, el controlador obtiene la fecha y hora de inicio de la
sesión.

Las imágenes utilizan el formato:

```text
usuario_dd_mm_yyyy_HH_MM_frame_n.jpeg
```

Ejemplo:

```text
usuario_22_06_2026_14_30_frame_1.jpeg
```

El CSV utiliza el formato:

```text
usuario_dd_mm_yyyy_HH_MM.csv
```

Ejemplo:

```text
usuario_22_06_2026_14_30.csv
```

El archivo contiene las columnas:

```csv
image_name,steering_angle
usuario_22_06_2026_14_30_frame_1.jpeg,0.050000
usuario_22_06_2026_14_30_frame_2.jpeg,-0.100000
```

Cada fila se escribe y se descarga al disco inmediatamente después de guardar
la imagen correspondiente.

Si ya existen archivos de una sesión con el mismo minuto, el controlador busca
el último número de imagen y continúa con el siguiente consecutivo.

## Funcionamiento interno

El flujo principal es:

```text
Inicializar Driver, teclado y cámara
                ↓
Leer todas las teclas disponibles
                ↓
Actualizar velocidad o ángulo dentro de sus límites
                ↓
Aplicar el control mediante VehicleService
                ↓
Si la captura está activa, contar frames
                ↓
Guardar imagen y anotación al alcanzar el intervalo configurado
```

### `src/main.py`

Contiene:

- El loop principal de Webots.
- La lectura del teclado.
- La limitación de velocidad y dirección.
- La clase `CaptureSession`, encargada de las imágenes y del CSV.
- La validación de los valores configurados.

### `src/config.py`

Centraliza los parámetros de velocidad, giro, cámara, frecuencia de captura,
prefijo del usuario y rutas del dataset.

### `src/camera_service.py`

Habilita la cámara de Webots y encapsula el guardado de imágenes mediante
`Camera.saveImage()`.

### `src/vehicle_service.py`

Encapsula las llamadas al `Driver` de Webots para aplicar velocidad, dirección
y freno.

### `src/simple_controller_act_2_1.py`

Es un controlador básico de referencia conservado de actividades anteriores.
El controlador principal que debe ejecutarse es `src/main.py`.

## Requisitos

- Webots R2025a o una versión compatible.
- Python 3.10.
- Las dependencias incluidas en `environment.yml`.

Para crear el ambiente Conda:

```powershell
conda env create -f environment.yml
conda activate webots_env
```

## Ejecución

El vehículo del mundo debe tener configurado:

```text
controller "<extern>"
```

Después, desde la raíz del proyecto:

```powershell
conda activate webots_env
cd src
webots-controller.exe .\main.py
```

Para que Webots reciba las teclas, selecciona la ventana de la simulación antes
de utilizar las flechas, `A` o `R`.

## Consideraciones

- La tecla abajo disminuye la velocidad por incrementos; no aplica un frenado
  de emergencia.
- Para habilitar reversa, configura `MIN_SPEED_KMH` con un valor negativo.
- El ángulo escrito en el CSV es exactamente el valor de dirección vigente al
  momento de guardar la imagen.
- La tecla `R` solo inicia la captura una vez por ejecución.
- El CSV se cierra automáticamente cuando termina el controlador.
