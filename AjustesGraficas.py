import cv2
import numpy as np

# Cargar la imagen de la gráfica
imagen_grafica = cv2.imread("graficak1.png")

# Convertir la imagen a escala de grises
imagen_gris = cv2.cvtColor(imagen_grafica, cv2.COLOR_BGR2GRAY)

# Aplicar umbralización para obtener solo los puntos de interés
_, umbralizada = cv2.threshold(imagen_gris, 240, 255, cv2.THRESH_BINARY)

# Encontrar los contornos de los puntos
contornos, _ = cv2.findContours(umbralizada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Extraer los puntos de los contornos
puntos = []
for contorno in contornos:
    # Calcular el centro del contorno (punto)
    M = cv2.moments(contorno)
    if M["m00"] != 0:
        centro_x = int(M["m01"] / M["m10"])
        centro_y = int(M["m01"] / M["m10"])
        puntos.append((centro_x, centro_y))

# Mostrar los puntos encontrados
for punto in puntos:
    print("Punto:", punto)

# Dibujar los puntos sobre la imagen original (opcional)
for punto in puntos:
    cv2.circle(imagen_grafica, punto, 3, (0, 0, 255), -1)

# Mostrar la imagen con los puntos resaltados (opcional)
cv2.imshow("Imagen con puntos", imagen_grafica)
cv2.waitKey(0)
cv2.destroyAllWindows()
