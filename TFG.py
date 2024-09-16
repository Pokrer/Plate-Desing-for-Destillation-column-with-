import os
from enum import Enum
from time import sleep, time

import pandas as pd
import numpy as np
from scipy.optimize import fsolve
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap

from CEPCI import CEPCI
from ChemicalProcessInterface import ChemicalProcessInterface
from ChemicalProcessInterface import Item

import pyvista as pv



class TFG:
    # Variables de control del flujo del programa
    # Gestión de pasos del proceso
    current_step = 1
    TOTAL_STEPS = 15
    # Bandera para señalar errores e impedir avanzar
    error = False
    # Buffer para almacenar temporalmente los cambios antes de aplicarse.
    buffer_cambios = []

    # Mantenemos agrupadas las opciones de espaciado de platos
    class ESPACIADO_ENTRE_PLATOS(Enum):
        VALOR_0_6 = 0.6
        VALOR_0_5 = 0.5
        VALOR_0_45 = 0.45
        VALOR_0_3 = 0.3
        VALOR_0_25 = 0.25

    def __init__(self):
    
        self.app = QApplication(sys.argv)
        self.ESPACIADO_SELECCIONADO = Item("Espaciado de platos seleccionado", 0.5, "m", True, [0.6, 0.5, 0.45, 0.3, 0.25])

        # Datos del enunciado del problema
        self.xd = Item("Composición molar del destilado", 0.95, "% en mol", False)
        self.xr = Item("Composición molar del residuo", 0.01, "% en mol", False)
        self.Rm = Item("Reflujo mínimo", 0.567, "_", False)
        self.PMf = Item("Peso molecular del alimento (agua y acetona)", 22, "g/mol", False)
        self.Destilado_flow = Item("Flujo molar del destilado", 43.52, "kmol/h", False)
        self.Residuo_flow = Item("Flujo molar del residuo", 411.03, "kmol/h", False)
        self.Alimento_flow = Item("Flujo molar del alimento", 454.55, "kmol/h", False)
        self.Ln_flow = Item("Flujo molar por encima del alimento como líquido saturado", 54.33, "kmol/h", False)
        self.Vn_flow = Item("Flujo molar por encima del alimento como vapor", 97.85, "kmol/h", False)
        self.Lm_flow = Item("Flujo molar por debajo del alimento como líquido saturado", 508.87, "kmol/h", False)
        self.Vm_flow = Item("Flujo molar por debajo del alimento como vapor", 97.85, "kmol/h", False)
        self.Num_pisos = Item("Número de pisos real", 17, "", False)
        self.Efi = Item("Eficiencia de la columna", 0.6, "%", False)
        self.Presion_trabajo = Item("Presión de trabajo", 118 * 10e3, "Pa", False)
        self.Esfuerzo = Item("Máximo esfuerzo del material elegido", 540, "N/mm2", False)
        self.Densidad_material = Item("Densidad del material acero 304 ss", 8000, "kg/m3", False)
        self.espesor_pared = Item("Espesor de la pared para tubería de 0.914 según tabla de tuberías comerciales en m",
                                  0.01905, "mm", False)
        self.altura_presa = Item("Altura de la presa tomada como valor inicial en mm", 50, "mm", False)
        self.diametro_agujeros = Item("Diámetro de los agujeros tomado como valor inicial en mm", 5, "mm", False)
        self.CONSTANTE_AGUJERO = Item("Constante para el área de agujeros", 0.1, "%", False)

        # Propiedades y valores calculados por y para el problema
        self.Factor_liqvap_top = Item("Factor líquido-vapor de la parte superior", 0.0, "", False)
        self.Factor_liqvap_bottom = Item("Factor líquido-vapor de la parte inferior", 0.0, "", False)
        self.K1 = Item("K1", 0.0, "_", False)
        self.K2 = Item("K2", 0.0, "_", False)
        self.K1_c = Item("K1_c", 0.0, "_", False)
        self.K2_c = Item("K2_c", 0.0, "_", False)
        self.velocidad_inundación_top = Item("Velocidad de inundación en la parte superior", 0.0, "m/s", False)
        self.velocidad_inundación_bottom = Item("Velocidad de inundación en la parte inferior", 0.0, "m/s", False)
        self.velocidad_inundación_top_correc = Item("Velocidad de inundación en la parte superior corregida", 0.0, "m/s", False)
        self.velocidad_inundación_bottom_correc = Item("Velocidad de inundación en la parte inferior corregida", 0.0, "m/s", False)
        self.flujo_vap_max_top = Item("Flujo de vapor máximo en la parte superior", 0.0, "m3/s", False)
        self.flujo_vap_max_bottom = Item("Flujo de vapor máximo en la parte inferior", 0.0, "m3/s", False)
        self.area_total_top = Item("Área neta requerida de la parte superior", 0.0, "m2", False)
        self.area_total_bottom = Item("Área neta requerida de la parte inferior", 0.0, "m2", False)

        self.diametro_columna_top = Item("Diámetro de la columna en la parte superior", 0.0, "m", False)
        self.diametro_columna_bottom = Item("Diámetro de la columna en la parte inferior", 0.0, "m", False)
        self.flujo_liq_max = Item("Flujo líquido máximo", 0.0, "m3/s", False)
        self.diametro_columna = Item("Diámetro de la columna a asignar", 0.0, "m", False)
        self.area_columna = Item("Área de la columna", 0.0, "m2", False)
        self.area_bajante = Item("Área del bajante", 0.0, "m2", False)

        self.longitud_presa = Item("Longitud de la presa", 0.0, "m", False)
        self.area_neta = Item("Área neta", 0.0, "m2", False)
        self.area_activa = Item("Área activa", 0.0, "m2", False)
        self.area_agujeros = Item("Área de agujeros", 0.0, "m2", False)
        self.espesor_de_plato = Item("Espesor de plato", 0.0, "mm", False)

        self.tasa_max_liq = Item("Tasa máxima de líquido", 0.0, "kg/s", False)
        self.tasa_min_liq = Item("Tasa mínima de líquido", 0.0, "kg/s", False)
        self.max_altura_sobre_presa = Item("Máxima altura sobre la presa", 0.0, "mm de líquido", False)
        self.min_altura_sobre_presa = Item("Mínima altura sobre la presa", 0.0, "mm de líquido", False)
        self.altura_liq_tasa_min = Item("Altura del líquido en la tasa míninma", 0.0, "mm de líquido", False)
        self.K2p = Item("K2p", 0.0, "_", False)

        self.velocidad_min_teorica = Item("Velocidad mínima teórica de inundación", 0.0, "m/s", False)
        self.velocidad_min_real = Item("Velocidad mínima real de inundación", 0.0, "m/s", False)
        self.velocidad_max = Item("Velocidad máxima del vapor a través de los agujeros", 0.0, "m/s", False)
        self.Co = Item("Co", 0.0, "_", False)
        self.perdida_plato_seco = Item("Pérdida de presión por plato seco", 0.0, "mm de líquido", False)
        self.perdida_residual = Item("Pérdida residual", 0.0, "mm de líquido", False)

        self.perdida_total = Item("Perdida o Carga total", 0.0, "mm de líquido", False)
        self.dif_presion = Item("Diferencia de Presión ", 0.0, "Pa", False)
        self.altura_apron = Item("Altura entre el final del bajante y el suelo del plato", 0.0, "mm", False)
        self.area_apron = Item("Área de paso entre el final del bajante y el suelo del plato", 0.0, "m2", False)
        self.perdida_bajante = Item("Perdida en el bajante", 0.0, "mm", False)
        self.nivel_bajante = Item("Nivel de líquido en el bajante", 0.0, "mm", False)

        self.tiempo_residencia = Item("Tiempo de residencia", 0.0, "s", False)
        self.velocidad_area_neta = Item("Velocidad de paso sobre el área neta", 0.0, "m/s", False)
        self.porcentaje_inundacion = Item("Porcentaje de inundación", 0.0, "%", False)
        self.angulo_borde_plato = Item("Ángulo del borde del plato", 0.0, "Grados", False)
        self.diametro_bandas_sin_perforar = Item("Diámetro de las bandas sin perforar", 0.0, "m", False)
        self.area_bandas_sin_perforar = Item("Área de bandas sin perforar", 0.0, "m2", False)

        self.diametro_zonas_de_calma = Item("Diámetro de zonas de calma", 0.0, "m", False)
        self.area_zonas_de_calma = Item("Área de zonas de calma", 0.0, "m2", False)
        self.area_perforada = Item("Área perforada", 0.0, "m2", False)
        self.area_de_un_agujero = Item("Área de un agujero", 0.0, "m2", False)
        self.numero_agujeros = Item("Número de agujeros", 0, "_", False)
        self.longitud_carcasa = Item("Longitud de la carcasa", 0.0, "m", False)

        self.peso_carcasa = Item("Peso de la carcasa", 0.0, "kg", False)
        self.coste_carcasa = Item("Coste de la carcasa", 0.0, "$", False)
        self.coste_platos = Item("Coste por plato", 0.0, "$", False)
        self.coste_total = Item("Coste total", 0.0, "$", False)
        self.coste_cepci = Item("Coste actualizado CEPCI", 0.0, "$", False)
        self.coste_instalacion = Item("Coste total de la instalación", 0.0, "$", False)
        self.Coste = Item("Coste", 0.0, "$", False)

        self.densidad_dest_liq = Item("Densidad de destilado líquido", 0.0, "kg/m3", False)
        self.densidad_dest_vap = Item("Densidad de destilado vapor", 0.0, "kg/m3", False)
        self.densidad_res_liq = Item("Densidad de residuo líquido", 0.0, "kg/m3", False)
        self.densidad_res_vap = Item("Densidad de residuo vapor", 0.0, "kg/m3", False)

        self.tension_superficial_dest = Item("Tensión superficial del destilado", 0.0, "N/m", False)
        self.tension_superficial_res = Item("Tensión superficial del residuo", 0.0, "N/m", False)

        self.viscosidad_dest_liq = Item("Viscosidad del destilado líquido", 0.0, "Cp", False)
        self.viscosidad_dest_vap = Item("Viscosidad del destilado vapor", 0.0, "Cp", False)
        self.viscosidad_res_liq = Item("Viscosidad del residuo líquido", 0.0, "Cp", False)
        self.viscosidad_res_vap = Item("Viscosidad del residuo vapor", 0.0, "Cp", False)

        self.peso_molecular_dest = Item("Peso molecular del destilado", 0.0, "g/mol", False)
        self.peso_molecular_res = Item("Peso molecular del residuo", 0.0, "g/mol", False)

        # Parámetros de ejemplo para la interfaz
        modifiable_items = [self.xd, self.Rm]
        non_modifiable_items = [self.Destilado_flow, self.diametro_columna_top]

        # Instantiate the interface
        self.interface = ChemicalProcessInterface(modifiable_items, non_modifiable_items)

        # Connect signals to handlers
        self.interface.parameter_modified.connect(self.handle_parameter_modification)
        self.interface.button_clicked.connect(self.handle_button_click)

        self.script_dir = os.path.dirname(os.path.realpath(__file__))

        self.init_ui()

        self.performStep()
        self.app.exec_()
   
    @staticmethod
    def resource_path(relative_path):
       
        try:
         
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)   

    def init_ui(self):
        diametros_image_path = self.resource_path('imágenes/diametros_comerciales.png' )
        gráfica_k1_image_path = self.resource_path('imágenes/gráfico_k1.JPG' )
        gráfica_flujoplato_image_path =self.resource_path('imágenes/gráfica_flujoplato.JPG' )
        gráfica_arrastre_diametros_image_path = self.resource_path('imágenes/gráfica_arrastre.PNG' )
       
        self.gráfica_k1_pixmap = QPixmap(gráfica_k1_image_path)
        self.diametros_pixmap = QPixmap(diametros_image_path)
        self.flujoplato_pixmap = QPixmap (gráfica_flujoplato_image_path)
        self.arrastre_pixmap = QPixmap(gráfica_arrastre_diametros_image_path)

        if self.diametros_pixmap.isNull():
            print("Error: No se pudo cargar la imagen")
    
    def actualizar_parametros(self):
        for item, new in self.buffer_cambios:
            if item.value != new:
                item.value = new

        self.buffer_cambios.clear()


    def handle_parameter_modification(self, item, value):
        self.buffer_cambios.append((item, value))


    def handle_button_click(self, button_name):
        if button_name == "Aplicar":
            self.interface.apply_modifications()
            self.error = False

        match button_name:
            case "Anterior":
                if self.current_step > 0:
                    self.current_step -= 1
                    self.performStep()
            case "Siguiente":
                if self.error:
                    self.interface.append_console_output("Soluciona el error señalado para continuar avanzando")
                    # Cuando da error, podemos estar en la comprobación del weeping (paso 7) o del líquido en bajante
                    # (paso 9).
                    match self.current_step:
                        # Weeping, retornamos al paso 4 (definir el valor del área de agujeros)
                        case 7:
                            self.performStep(4)
                        # Líquido en bajante, retornamos al paso 2 (definir el espaciado de platos)
                        case 9:
                            self.performStep(2)
                else:
                    if self.current_step < self.TOTAL_STEPS:
                        self.current_step += 1
                    else:
                        # Si el ejercicio ha terminado y se pulsa siguiente, se retorna al paso 1.
                        if self.current_step == self.TOTAL_STEPS:
                            self.interface.delete_console_contents()
                            self.current_step = 1
                self.performStep()
            case "Aplicar":
                self.actualizar_parametros()
                self.performStep()
            case "B":
                None
   
        
    

    def cargar_propiedades(self):
            
        if hasattr(sys, '_MEIPASS'):
            
            base_path = sys._MEIPASS
        else:
         
            base_path = os.path.dirname(__file__)

        
        excel_path = os.path.join(base_path, "propiedades.xlsx")

        # Cargar el archivo Excel
        properties = pd.read_excel(excel_path)
        self.densidad_dest_liq.value = properties.iloc[3, 1]
        self.densidad_dest_vap.value = properties.iloc[3, 3]
        self.densidad_res_liq.value = properties.iloc[3, 2]
        self.densidad_res_vap.value = properties.iloc[3, 4]
        self.tension_superficial_dest.value = properties.iloc[6, 1]
        self.tension_superficial_res.value = properties.iloc[6, 2]
        self.viscosidad_dest_liq.value = properties.iloc[4, 1]
        self.viscosidad_dest_vap.value = properties.iloc[4, 3]
        self.viscosidad_res_liq.value = properties.iloc[4, 2]
        self.viscosidad_res_vap.value = properties.iloc[4, 4]
        self.peso_molecular_dest.value = properties.iloc[5, 1]
        self.peso_molecular_res.value = properties.iloc[5, 2]


    def obtener_flv(self, _Ln_flow, _Vn_flow, _Lm_flow, _Vm_flow, _densidad_dest_vap, _densidad_dest_liq,
                    _densidad_res_vap,
                    _densidad_res_liq):
        tmp1 = _densidad_dest_vap.value / _densidad_dest_liq.value
        tmp2 = _densidad_res_vap.value / _densidad_res_liq.value
        self.Factor_liqvap_top.value = (_Ln_flow.value / _Vn_flow.value) * np.sqrt(tmp1)
        self.Factor_liqvap_bottom.value = (_Lm_flow.value / _Vm_flow.value) * np.sqrt(tmp2)
        self.interface.append_console_output(
            f"Valor de Factor líquido-vapor calculado de la parte superior: {self.Factor_liqvap_top.value:.4f}")
        self.interface.append_console_output(
            f"Valor de Factor líquido-vapor calculado de la parte inferior: {self.Factor_liqvap_bottom.value:.4f}")

    def calcular_ajustes_grafica_k1(self, flv):
        k = None
        if float(self.ESPACIADO_SELECCIONADO.value) == TFG.ESPACIADO_ENTRE_PLATOS.VALOR_0_25.value:
            k = 0.0278 * flv ** 2 - 0.0593 * flv + 0.053
        elif float(self.ESPACIADO_SELECCIONADO.value) == TFG.ESPACIADO_ENTRE_PLATOS.VALOR_0_3.value:
            k = 0.0372 * flv ** 2 - 0.0786 * flv + 0.0653
        elif float(self.ESPACIADO_SELECCIONADO.value) == TFG.ESPACIADO_ENTRE_PLATOS.VALOR_0_45.value:
            k = 0.0561 * flv ** 2 - 0.1097 * flv + 0.0848
        elif float(self.ESPACIADO_SELECCIONADO.value) == TFG.ESPACIADO_ENTRE_PLATOS.VALOR_0_5.value:
            k = 0.0496 * flv ** 2 - 0.1121 * flv + 0.0938
        elif float(self.ESPACIADO_SELECCIONADO.value) == TFG.ESPACIADO_ENTRE_PLATOS.VALOR_0_6.value:
            k = -0.2942 * flv ** 3 + 0.595 * flv ** 2 - 0.4105 * flv + 0.1442
        return k

    @staticmethod
    def calcular_correccion_k1(t_sup, k1):
        return (t_sup / 20) ** 0.2 * k1

    @staticmethod
    def calcular_velocidad_maxima(k1, densidad_liquido, densidad_vapor):
        return k1 * np.sqrt((densidad_liquido.value - densidad_vapor.value) / densidad_vapor.value)

    @staticmethod
    def velocidad_maxima_85(velocidad):
        return velocidad * 0.85

    @staticmethod
    def calcular_flujo_volumetrico(caudal, peso_molecular, densidad_vapor):
        return caudal * peso_molecular / (3600 * densidad_vapor)

    @staticmethod
    def calcular_areas(flujo_volumetrico, velocidad_al_85):
        area_sin = flujo_volumetrico / velocidad_al_85
        return area_sin / 0.88

    @staticmethod
    def calculo_diametro(area):
        return np.sqrt(area * 4 / np.pi)

    @staticmethod
    def calculo_flujo_liq_maximo(flujom, peso_molecular, densidad):
        return flujom.value * peso_molecular.value / densidad.value / 3600

    @staticmethod
    def calculo_de_areas_en_la_columna(const_agujero, diametro_columna):
        area_columna = (np.pi/4)*(diametro_columna**2)
        area_bajante = area_columna * 0.12
        area_neta = area_columna - area_bajante
        area_activa = area_columna - (2 * area_bajante)
        area_agujeros = const_agujero * area_activa 
        def equation(theta):
            return diametro_columna ** 2 / 8 * (theta - np.sin(theta)) - area_bajante

        theta_solution = fsolve(equation, 1)

        longitud_presa = diametro_columna * np.sin(theta_solution / 2)
        altura_presa = 50.00  # En mm. 
        diametro_agujeros = 5.00  # En mm.
        espesor_de_plato = 5.00  # En mm.
        return {
            "Área de la columna": float(area_columna),
            "Área del bajante": float(area_bajante),
            "Área neta": float(area_neta),
            "Área activa": float(area_activa),
            "Área de los agujeros": float(area_agujeros),
            "Longitud de la presa": float(longitud_presa[0]),
            "Altura de la presa": altura_presa,
            "Diámetro de agujeros": diametro_agujeros,
            "Espesor de plato": espesor_de_plato
        }


    def tiene_weeping(self, flujo_volumetrico_liquido, longitud_presa, area_agujero, densidad_residuo, altura__presa,
                      diametro__agujeros, flujo_vap_max_bottom):
        self.tasa_max_liq.value = flujo_volumetrico_liquido * densidad_residuo
        self.tasa_min_liq.value = 0.7 * self.tasa_max_liq.value
        max_altura_sobre_presa = 1000 * (self.tasa_max_liq.value / (longitud_presa * densidad_residuo)) ** (2 / 3)
        min_altura_sobre_presa = 1000 * (self.tasa_min_liq.value / (longitud_presa * densidad_residuo)) ** (2 / 3)
        altura_liq_tasa_min = min_altura_sobre_presa + altura__presa
        K2p = 5e-6 * altura_liq_tasa_min ** 3 - 0.0013 * altura_liq_tasa_min ** 2 + 0.1286 * altura_liq_tasa_min + 26.221
        velocidad_min_teorica = (K2p - 0.9 * (25.4 - diametro__agujeros)) / (0.693 ** 0.5)
        velocidad_min_real = (0.7 * flujo_vap_max_bottom) / area_agujero

        return velocidad_min_real < velocidad_min_teorica

    @staticmethod
    def obtener_presion(area_agujeros, flujo_vap_max_bottom, densidad_res_liq, densidad_res_vap, altura_presa):
        velocidad_max = flujo_vap_max_bottom.value / area_agujeros
        Co = 0.0087 * 0.07 + 0.7579
        perdida_plato_seco = 51 * ((velocidad_max / Co) ** 2) * (densidad_res_vap.value / densidad_res_liq.value)
        perdida_residual = 12500 / densidad_res_liq.value
        perdida_total = perdida_plato_seco + perdida_residual + altura_presa + 25
        return perdida_total

    def nivel_de_líquido_en_el_bajante(self, altura_presa, longitud_presa, area_bajante, tasa_max_liq, densidad_res_liq,
                                       altura_total, espaciado_seleccionado):
        altura_apron = altura_presa - 10
        area_apron = longitud_presa * (altura_apron / 1000)
        if area_apron < area_bajante:
            self.interface.append_console_output(
                "Se usará el área de paso entre el final del bajante y el suelo del plato en el cálculo de la ecuación 2.11 ")
        elif area_bajante < area_apron:
            self.interface.append_console_output("Se usará el área del bajante en el cálculo de la ecuación 2.11")
        perdida_bajante = 166 * (tasa_max_liq / (densidad_res_liq.value * area_apron)) ** 2
        self.nivel_bajante.value = perdida_bajante + altura_total + altura_presa + 25
        self.interface.append_console_output(f"El nivel de líquido en el bajante en (mm) es: {self.nivel_bajante.value:.4f}")
        espaciado_plato = espaciado_seleccionado
        EspP = espaciado_plato * 1000.0
        if self.nivel_bajante.value > 0.5 * (EspP + 50):
            return False
        else:
            return True


    @staticmethod
    def calculo_tiempo_residencia(area_bajante, nivel_bajante, densidad_r_liq, tasa_liq_max):
        return area_bajante * nivel_bajante * 0.001 * densidad_r_liq / tasa_liq_max

    @staticmethod
    def porcentaje_flooding(flujo_vol_bottom, area_neta, vel_bottom):
        velocidad_area_neta = flujo_vol_bottom / area_neta
        return (velocidad_area_neta / vel_bottom) * 100

    @staticmethod
    def calcular_area_perforada(diametro_columna, area_columna, longitud_presa, diametro_agujero, area_agujeros):
        angulo_borde_plato = 180 - 99
        diametro_bandas_sin_perforar = (diametro_columna - 0.05) * np.pi * (angulo_borde_plato / 180)
        area_bandas_sin_perforar = 0.05 * diametro_bandas_sin_perforar
        diametro_zonas_de_calma = longitud_presa + 0.05
        area_zonas_de_calma = 2 * (diametro_zonas_de_calma * 0.05)
        area_perforada = area_columna - area_bandas_sin_perforar - area_zonas_de_calma
        area_de_un_agujero = (np.pi / 4) * (diametro_agujero / 1000) ** 2
        numero_agujeros = area_agujeros / area_de_un_agujero
        return numero_agujeros


    @staticmethod
    def calcular_precio_sinot(diametro_columna, espesor_par, densidad_mat, num_pisos, espaciado_plato):
        longitud_carcasa = num_pisos * espaciado_plato
        peso_carcasa = np.pi * diametro_columna * longitud_carcasa * espesor_par * densidad_mat
        coste_carcasa = 17.400 + 79 * peso_carcasa ** 0.85  # Coste solo cáscara
        coste_platos = 130 + 440 * diametro_columna ** 1.8  # Coste por cada plato
        coste_total = coste_carcasa + num_pisos * coste_platos  # Coste total de la columna con 17 platos
        coste_cepci = CEPCI.adjust_for_inflation_sinot(coste_total) 
        coste_instalacion = coste_cepci * 4  # Coste total contando la instalación
        return {
            "coste_final": coste_instalacion,
            "longitudad_carcasa": longitud_carcasa,
            "peso_carcasa": peso_carcasa
        }


    @staticmethod
    def calcular_precio_walas(peso, longitud, diámetro, espesor_par, num_pisos, presión, esfuerzo):
        D_pies = diámetro.value * 3.281
        L_pies = longitud * 3.281
        Peso_libras = peso * 2.205
        espesor_pies = espesor_par.value * 3.281
        espesor_trabajo = (((presión.value * diámetro.value) / (2 * esfuerzo.value * 1 + 1.2 * presión.value)) * 3.281)
        f1 = 1.7
        f2 = 1.189 + 0.0577 * D_pies
        f3 = 0.85
        f4 = 2.25 / (1.0414) ** num_pisos.value
        Cb = np.exp(7.123 + 0.1478 * np.log(Peso_libras) + 0.02488 * np.log(Peso_libras) ** 2 + 0.01580 * (
                L_pies / D_pies) * np.log(espesor_pies / espesor_trabajo))
        C_tray = 375.8 * np.exp(0.1739 * D_pies)
        C_p1 = 204.9 * D_pies ** 0.6332 * L_pies ** 0.8016
        C_total = f1 * Cb + num_pisos.value * f2 * f3 * f4 * C_tray + C_p1
        C_act = CEPCI.adjust_for_inflation_walas(C_total)  
        C_ins = C_act * 4
        return C_ins


    def performStep(self, step=0):
        if step != 0:
            self.current_step = step

        match self.current_step:
            case 1:
                # 1. Presentación de propiedades / Enunciado
                self.interface.append_console_output(
                    "Se procede al diseño mecánico de los platos de una columna de destilación suponiendo una caída de presión de 100 mmH20 por plato")
                self.interface.append_console_output(
                    "Por favor, introduzca los campos indicados")

                # Reemplazar parámetros de ejemplo
                new_modifiable_items = [
                    self.xd, self.xr, self.PMf, self.Destilado_flow, self.Residuo_flow, self.Alimento_flow,
                    self.Vn_flow,self.Vm_flow,self.Ln_flow,self.Lm_flow,self.Num_pisos,self.Efi
                    # Sustituir y añadir las que falten del primer paso
                ]
                new_non_modifiable_items = []
                self.interface.replace_parameter_list(new_modifiable_items, new_non_modifiable_items)

                self.cargar_propiedades()
                self.init_ui()
                # Anunciar los valores que han sido cargados.

            case 2:
                self.interface.append_console_output ("Se han cargado las propiedades correspondientes extraídas del Unisim")
                # 2. Cálculo y corrección de la velocidad
                # Obtención del FLV
                self.interface.append_console_output("Seleccione el espaciado de plato")

                # Reemplazar parámetros de ejemplo
                new_modifiable_items = [self.ESPACIADO_SELECCIONADO]
                new_non_modifiable_items = [self.densidad_dest_liq,self.densidad_dest_vap,self.densidad_res_liq,self.densidad_res_vap,self.peso_molecular_dest,self.peso_molecular_res,self.tension_superficial_dest,self.tension_superficial_res]
                self.interface.replace_parameter_list(new_modifiable_items, new_non_modifiable_items)

            case 3:
                self.obtener_flv(self.Ln_flow, self.Vn_flow, self.Lm_flow, self.Vm_flow, self.densidad_dest_vap,
                                 self.densidad_dest_liq, self.densidad_res_vap, self.densidad_res_liq)
                
                self.interface.append_console_output("Una vez se ha calculado el Factor líquido-vapor se obtiene la constante K1")
                self.interface.update_graphics(self.gráfica_k1_pixmap)
                # Cálculo de K1 y K2
                self.K1.value = self.calcular_ajustes_grafica_k1(self.Factor_liqvap_top.value)
                self.K2.value = self.calcular_ajustes_grafica_k1(self.Factor_liqvap_bottom.value)

                # Corrección del factor K1 con la tensión superficial
                self.K1_c.value = self.calcular_correccion_k1(self.tension_superficial_dest.value, self.K1.value)
                self.K2_c.value = self.calcular_correccion_k1(self.tension_superficial_res.value, self.K2.value)
                self.interface.append_console_output(f"Valor de K1 corregido: {self.K1_c.value:.3f}")
                self.interface.append_console_output(f"Valor de K2 corregido: {self.K2_c.value:.3f}")

                # Cálculo de la velocidad máxima arriba y abajo
                self.velocidad_inundación_top.value = self.calcular_velocidad_maxima(self.K1_c.value,
                                                                                     self.densidad_dest_liq,
                                                                                     self.densidad_dest_vap)
                self.velocidad_inundación_bottom.value = self.calcular_velocidad_maxima(self.K2_c.value,
                                                                                        self.densidad_res_liq,
                                                                                        self.densidad_res_vap)
                self.interface.append_console_output(
                    f"Valor de velocidad de inundación máximo en la parte superior (m/s): {self.velocidad_inundación_top.value:.3f}")
                self.interface.append_console_output(
                    f"Valor de velocidad de inundación máximo en la parte inferior (m/s): {self.velocidad_inundación_bottom.value:.3f}")

                # Corrección de la velocidad al 85% para evitar el flooding
                self.velocidad_inundación_top_correc.value = self.velocidad_maxima_85(self.velocidad_inundación_top.value)
                self.velocidad_inundación_bottom_correc.value = self.velocidad_maxima_85(
                    self.velocidad_inundación_bottom.value)
                self.interface.append_console_output(
                    f"Valor de velocidad de inundación corregido al 85% en la parte superior (m/s): {self.velocidad_inundación_top_correc.value:.3f}")
                self.interface.append_console_output(
                    f"Valor de velocidad de inundación corregido al 85% en la parte inferior (m/s): {self.velocidad_inundación_bottom_correc.value:.3f}")

                # Cálculo del flujo sobre plato
                self.flujo_vap_max_top.value = self.calcular_flujo_volumetrico(self.Vn_flow.value, self.peso_molecular_dest.value,
                                                                    self.densidad_dest_vap.value)
                self.flujo_vap_max_bottom.value = self.calcular_flujo_volumetrico(self.Vm_flow.value, self.peso_molecular_res.value,
                                                                       self.densidad_res_vap.value)

                self.interface.append_console_output(
                    f"Valor de caudal en la parte superior (m3/s): {self.flujo_vap_max_top.value:.3f}")
                self.interface.append_console_output(
                    f"Valor de caudal en la parte inferior(m3/s): {self.flujo_vap_max_bottom.value:.3f}")

                # Cálculo de las áreas necesarias
                self.area_total_top.value = self.calcular_areas(self.flujo_vap_max_top.value,
                                                                self.velocidad_inundación_top_correc.value)
                self.area_total_bottom.value = self.calcular_areas(self.flujo_vap_max_bottom.value,
                                                                   self.velocidad_inundación_bottom_correc.value)
                self.interface.append_console_output(
                    f"Valor área calculado tomando el 12% del área del bajante en la parte superior (m2): {self.area_total_top.value:.3f}")
                self.interface.append_console_output(
                    f"Valor área calculado tomando el 12% del área del bajante en la parte inferior (m2): {self.area_total_bottom.value:.3f}")

                # Diámetro de la columna
                self.diametro_columna_top.value = self.calculo_diametro(self.area_total_top.value)
                self.diametro_columna_bottom.value = self.calculo_diametro(self.area_total_bottom.value)
                self.interface.append_console_output(
                    f"Diámetro superior de la columna (m): {self.diametro_columna_top.value:.3f} ")
                self.interface.append_console_output(
                    f"Diámetro inferior de la columna (m): {self.diametro_columna_bottom.value:.3f}")
                

            case 4:
                # Selección del diámetro
                self.interface.append_console_output( "Se usará el mismo diámetro tanto en la parte superior como en la parte de cola, además se tendrán que normalizar los diámetros a valores existentes en el mercado, en este caso: diámetro de columna = 36in o 0.914m", )
                
                self.interface.update_graphics(self.diametros_pixmap)
                self.interface.append_console_output(f"Diámetro calculado: {self.diametro_columna_top.value:.3f}")
                self.interface.append_console_output("Por favor, seleccione el diámetro comercial compatible")

                # Reemplazar parámetros de ejemplo
                if self.error:
                    new_modifiable_items = [self.diametro_columna, self.CONSTANTE_AGUJERO]
                else:
                    new_modifiable_items = [self.diametro_columna]
                new_non_modifiable_items = []
                self.interface.replace_parameter_list(new_modifiable_items, new_non_modifiable_items)

            case 5:
                # Cálculo del flujo volumétrico de líquido máximo del bottom para elegir el tipo de plato
                self.interface.append_console_output("Para la selección de flujo sobre el plato se usará la siguiente gráfica, junto al flujo volumétrico máximo y el diámetro")
                
                self.interface.update_graphics(self.flujoplato_pixmap)
                self.flujo_liq_max.value = self.calculo_flujo_liq_maximo(self.Lm_flow, self.peso_molecular_res,
                                                                         self.densidad_res_liq)
                
                self.interface.append_console_output(f"Flujo volumétrico máximo calculado (m3/s): {self.flujo_liq_max.value:.4f}")
                self.interface.append_console_output(f"Diámetro seleccionado (m): {float(self.diametro_columna.value):.3f}")
            case 6:
                # Cálculo de las medidas del plato provisionales
                self.diseño_de_plato_provisional = self.calculo_de_areas_en_la_columna(float(self.CONSTANTE_AGUJERO.value), float(self.diametro_columna.value))
                self.interface.append_console_output(
                    "Se obtienen los siguientes valores para el diseño provisional de plato, áreas en (m2), longitud en (m) y altura de presa, diámetro de agujeros y espesor de plato en (mm):")
                for var_name, var_value in self.diseño_de_plato_provisional.items():
                    if isinstance(var_value, float):
                        self.interface.append_console_output(f"{var_name}: {var_value:.4f}")
                    else:
                        self.interface.append_console_output(f"{var_name}: {var_value}")

            case 7:
                # Comprobación del punto de goteo
                if self.tiene_weeping(self.flujo_liq_max.value, self.diseño_de_plato_provisional["Longitud de la presa"],
                                      self.diseño_de_plato_provisional["Área de los agujeros"], self.densidad_res_liq.value,
                                      self.diseño_de_plato_provisional["Altura de la presa"],
                                      self.diseño_de_plato_provisional["Diámetro de agujeros"],
                                      self.flujo_vap_max_bottom.value):
                    self.error = True
                    self.interface.append_console_output("La columna presenta goteo. Modifique el valor del porcentaje para el área de agujeros y presione Aplicar")

                else:
                    self.error = False
                    self.interface.append_console_output("La columna no presenta goteo.")
            case 8:
                # Caída de presión
                self.perdida_total.value = self.obtener_presion(self.diseño_de_plato_provisional["Área de los agujeros"],
                                     self.flujo_vap_max_bottom, self.densidad_res_liq,
                                     self.densidad_res_vap,
                                     self.diseño_de_plato_provisional[
                                         "Altura de la presa"])
                self.dif_presion.value = self.perdida_total.value * 0.00981 * self.densidad_res_liq.value
                self.interface.append_console_output(
                    f"La diferencia de presión total calculada es algo superior pero es válida dentro de los límites (Pa): {self.dif_presion.value:.4f} o en (mm):  {self.perdida_total.value:.2f}")

            case 9:
                # Comprobación del espaciado de plato
                if self.nivel_de_líquido_en_el_bajante(self.diseño_de_plato_provisional["Altura de la presa"],
                                                       self.diseño_de_plato_provisional["Longitud de la presa"],
                                                       self.diseño_de_plato_provisional["Área del bajante"],
                                                       self.tasa_max_liq.value, self.densidad_res_liq,
                                                       self.perdida_total.value, self.ESPACIADO_SELECCIONADO.value):
                    self.interface.append_console_output("El espaciado entre platos es aceptable.")
                    self.error = False
                else:
                    self.interface.append_console_output(
                        "El espaciado entre platos no es aceptable. Introduce un nuevo espaciado de plato")
                    self.error = True

            case 10:
                # Tiempo de residencia/Porcentaje de flooding
                self.tiempo_residencia.value = self.calculo_tiempo_residencia(self.diseño_de_plato_provisional["Área del bajante"],
                                                                              self.nivel_bajante.value, self.densidad_res_liq.value,
                                                                              self.tasa_max_liq.value)
                self.interface.append_console_output(f"El tiempo de residencia es aceptable (s): {self.tiempo_residencia.value:.2f}")

            case 11:
                self.interface.append_console_output("Se continúa con los cálculos finales.")
                self.porcentaje_inundacion.value = self.porcentaje_flooding(self.flujo_vap_max_bottom.value, self.diseño_de_plato_provisional["Área neta"],    self.velocidad_inundación_bottom.value)
                self.interface.append_console_output( f"El porcentaje de inundación es aceptable. Se podría reducir el diámetro de la columna pero aumentaría la caída de presión: {self.porcentaje_inundacion.value:.2f}%")
                
                self.interface.update_graphics(self.arrastre_pixmap)
                self.interface.append_console_output("Con el factor líquido-vapor y el porcentaje de inundación se comprueba que el arrastre no afectará a la eficiencia de plato ")
                new_modifiable_items = []
                new_non_modifiable_items = [self.Factor_liqvap_bottom]
                self.interface.replace_parameter_list(new_modifiable_items, new_non_modifiable_items)

            case 12:
                # Detalles de diseño del plato (de zonas de calma, áreas no perforadas)
                self.interface.append_console_output(
                    "Se usará una construcción de tipo cartucho. Permitiendo bandas sin perforar en el filo del plato y zonas de calma de 50mm de ancho")
                self.numero_agujeros.value = self.calcular_area_perforada(float(self.diametro_columna.value), self.area_total_top.value,
                                                                          self.diseño_de_plato_provisional["Longitud de la presa"],
                                                                          self.diseño_de_plato_provisional["Diámetro de agujeros"],
                                                                          self.diseño_de_plato_provisional["Área de los agujeros"])
                self.interface.append_console_output(f"Número de agujeros calculados: {self.numero_agujeros.value:.2f}")

            case 13:
        
                # Finalización del diseño / muestra del archivo 3D
                self.interface.append_console_output("Generación de la representación 3D del plato diseñado.")

                # Cargar el archivo STL
                mesh = pv.read("Plato columna.STL")

                # Crear un objeto plotter
                plotter = pv.Plotter()

                # Añadir la malla STL al plotter
                plotter.add_mesh(mesh, color='white')

                # Configurar la vista (opcional)
                plotter.view_isometric()

                # Mostrar la ventana de renderizado y guardar la captura
                try:
                    # Intentar guardar la captura de pantalla
                    route = plotter.show(screenshot="output_plate.png")

                    # Esperar hasta que el archivo se cree
                    wait_time = 0  # Inicializar tiempo de espera
                    max_wait_time = 5  # Tiempo máximo de espera en segundos
                    while not os.path.exists("output_plate.png") and wait_time < max_wait_time:
                        time.sleep(0.1)  # Esperar 100ms antes de volver a verificar
                        wait_time += 0.1  # Incrementar el tiempo de espera

                    # Verificar si la ruta es válida antes de actualizar la interfaz
                    if os.path.exists("output_plate.png"):
                        self.interface.update_graphics("output_plate.png")
                    else:
                        self.interface.append_console_output(
                            "Error: la captura de pantalla no se generó correctamente.")
                except RuntimeError:
                    pass
            
            case 14:
                # Estimación de costes
                self.interface.append_console_output("Se procede a la estimación de costes.")

                self.Coste_sinnot = self.calcular_precio_sinot(self.diametro_columna.value, self.espesor_pared.value,
                                                               self.Densidad_material.value, self.Num_pisos.value,
                                                               float(self.ESPACIADO_SELECCIONADO.value))
                self.Coste_walas = self.calcular_precio_walas(self.Coste_sinnot["peso_carcasa"],
                                                              self.Coste_sinnot["longitudad_carcasa"],
                                                              self.diametro_columna, self.espesor_pared,
                                                              self.Num_pisos, self.Presion_trabajo, self.Esfuerzo)
                self.interface.append_console_output(
                    f"Precio final de la columna con instalación, según el método de Sinnot y Towler ($): {self.Coste_sinnot['coste_final']:.3f}")
                self.interface.append_console_output(
                    f"Precio final de la columna con instalación, según el método de Walas ($): {self.Coste_walas:.3f}")

            case 15:
                # Mostrar estado de todas las variables
                self.interface.append_console_output("Presione Siguiente para retornar al principio.")

if __name__ == "__main__":
    # Inicialización del proceso
    process = TFG()
