import pandas as pd
import numpy as np
from datetime import timedelta

class SateliteSimulacion:
    def __init__(self, satelite_path, nodo_tierra_path, estaciones_terrenas_path):
        self.satelite_df = pd.read_csv(satelite_path)
        self.nodo_tierra_df = pd.read_csv(nodo_tierra_path)
        self.estaciones_terrenas_df = pd.read_csv(estaciones_terrenas_path)

        self._procesar_datos_satelite()
        self.nodo_tierra = self.nodo_tierra_df.iloc[0].values

        self.radio_cobertura = 2300  # Este valor puede ajustarse según sea necesario
        self.altura_satelite = 600

    def _procesar_datos_satelite(self):
        if 'Time' not in self.satelite_df.columns:
            raise KeyError("La columna 'Time' no se encuentra en el archivo CSV. Asegúrate de que el archivo tenga la columna 'Time'.")
        self.satelite_df['Time'] = pd.to_datetime(self.satelite_df['Time'], infer_datetime_format=True, errors='coerce')
        if self.satelite_df['Time'].isnull().any():
            raise ValueError("Se encontraron valores no válidos en la columna 'Time'. Verifica que todos los datos de tiempo tengan el formato correcto.")

    def calcular_distancia(self, p1, p2):
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 + (p1[2] - p2[2])**2)

    def en_zona_cobertura(self, distancia):
        hipotenusa = np.sqrt(self.radio_cobertura**2 + self.altura_satelite**2)
        return distancia <= hipotenusa

    def calcular_latencia(self, distancia):
        velocidad_senal = 300000  # km/s (aprox. velocidad de la luz)
        return distancia / velocidad_senal

    def preparar_datos(self):
        self.satelite_df['distancia_nodo'] = self.satelite_df.apply(
            lambda row: self.calcular_distancia([row['x (km)'], row['y (km)'], row['z (km)']], self.nodo_tierra), axis=1)
        self.satelite_df['nodo_en_cobertura'] = self.satelite_df['distancia_nodo'].apply(
            lambda d: self.en_zona_cobertura(d))

class EstacionTerrena:
    def __init__(self, nombre, coordenadas):
        self.nombre = nombre
        self.coordenadas = coordenadas

class SimulacionComunicacion:
    def __init__(self, satelite_simulacion, time_on_air=0.741376, processing_delay_factor=0.01):
        self.satelite_simulacion = satelite_simulacion
        self.time_on_air = time_on_air
        self.processing_delay = processing_delay_factor * time_on_air
        self.resultados = {}

    def simular_comunicacion(self, estacion):
        nodo_puede_transmitir = True
        paquete_pendiente_enviar = False
        ultimo_tiempo_recepcion = self.satelite_simulacion.satelite_df['Time'].iloc[0] - timedelta(minutes=30)
        
        transmisiones = {'pkt_node_to_satellite': [], 'pkt_satellite_to_ground': [], 'pkt_ground_to_satellite': [], 'pkt_satellite_to_node': []}
        tiempos_recorrido = []

        for step in range(len(self.satelite_simulacion.satelite_df)):
            satelite_pos = [self.satelite_simulacion.satelite_df['x (km)'].iloc[step],
                            self.satelite_simulacion.satelite_df['y (km)'].iloc[step],
                            self.satelite_simulacion.satelite_df['z (km)'].iloc[step]]
            hora_actual = self.satelite_simulacion.satelite_df['Time'].iloc[step]

            if nodo_puede_transmitir and self.satelite_simulacion.satelite_df['nodo_en_cobertura'].iloc[step] and (hora_actual - ultimo_tiempo_recepcion >= timedelta(minutes=30)):
                delay_nodo_satelite = self.satelite_simulacion.calcular_latencia(self.satelite_simulacion.satelite_df['distancia_nodo'].iloc[step]) + self.time_on_air
                transmisiones['pkt_node_to_satellite'].append(delay_nodo_satelite)
                tiempo_inicio = hora_actual
                print(f'{hora_actual.time()} | Paquete enviado del nodo al satélite. Delay: {delay_nodo_satelite:.8f} segundos. Distancia: {self.satelite_simulacion.satelite_df["distancia_nodo"].iloc[step]:.2f} km. Total de envíos: {len(transmisiones["pkt_node_to_satellite"])}')
                nodo_puede_transmitir = False
                paquete_pendiente_enviar = True

            if paquete_pendiente_enviar:
                distancia_estacion = self.satelite_simulacion.calcular_distancia(satelite_pos, estacion.coordenadas)
                if self.satelite_simulacion.en_zona_cobertura(distancia_estacion):
                    delay_satelite_estacion = self.satelite_simulacion.calcular_latencia(distancia_estacion) + self.processing_delay
                    transmisiones['pkt_satellite_to_ground'].append(delay_satelite_estacion)
                    print(f'{hora_actual.time()} | Paquete enviado del satélite a la {estacion.nombre}. Delay: {delay_satelite_estacion:.8f} segundos. Distancia: {distancia_estacion:.2f} km. Total de envíos: {len(transmisiones["pkt_satellite_to_ground"])}')
                    paquete_pendiente_enviar = False

                    delay_estacion_satelite = self.satelite_simulacion.calcular_latencia(distancia_estacion)
                    transmisiones['pkt_ground_to_satellite'].append(delay_estacion_satelite)
                    print(f'{hora_actual.time()} | Paquete enviado de la {estacion.nombre} al satélite. Delay: {delay_estacion_satelite:.8f} segundos. Distancia: {distancia_estacion:.2f} km. Total de envíos: {len(transmisiones["pkt_ground_to_satellite"])}')

                    for future_step in range(step, len(self.satelite_simulacion.satelite_df)):
                        if self.satelite_simulacion.satelite_df['nodo_en_cobertura'].iloc[future_step]:
                            satelite_pos_future = [self.satelite_simulacion.satelite_df['x (km)'].iloc[future_step],
                                                   self.satelite_simulacion.satelite_df['y (km)'].iloc[future_step],
                                                   self.satelite_simulacion.satelite_df['z (km)'].iloc[future_step]]
                            distancia_nodo_future = self.satelite_simulacion.calcular_distancia(satelite_pos_future, self.satelite_simulacion.nodo_tierra)
                            delay_satelite_nodo = self.satelite_simulacion.calcular_latencia(distancia_nodo_future) + self.processing_delay + self.time_on_air
                            transmisiones['pkt_satellite_to_node'].append(delay_satelite_nodo)
                            tiempo_final = self.satelite_simulacion.satelite_df['Time'].iloc[future_step]
                            tiempo_total_recorrido = (tiempo_final - tiempo_inicio).total_seconds() / 3600
                            tiempos_recorrido.append(tiempo_total_recorrido)
                            print(f'{self.satelite_simulacion.satelite_df["Time"].iloc[future_step].time()} | Paquete enviado del satélite al nodo, respuesta de {estacion.nombre}. Delay: {delay_satelite_nodo:.8f} segundos. Distancia: {distancia_nodo_future:.2f} km. Total de envíos: {len(transmisiones["pkt_satellite_to_node"])}. Tiempo total del recorrido: {tiempo_total_recorrido:.2f} horas')
                            nodo_puede_transmitir = True
                            ultimo_tiempo_recepcion = self.satelite_simulacion.satelite_df['Time'].iloc[future_step]
                            break

        self.resultados[estacion.nombre] = {
            'pkt_node_to_satellite': np.mean(transmisiones['pkt_node_to_satellite']) if transmisiones['pkt_node_to_satellite'] else None,
            'pkt_satellite_to_ground': np.mean(transmisiones['pkt_satellite_to_ground']) if transmisiones['pkt_satellite_to_ground'] else None,
            'pkt_ground_to_satellite': np.mean(transmisiones['pkt_ground_to_satellite']) if transmisiones['pkt_ground_to_satellite'] else None,
            'pkt_satellite_to_node': np.mean(transmisiones['pkt_satellite_to_node']) if transmisiones['pkt_satellite_to_node'] else None,
            'tiempo_total_recorrido': np.mean(tiempos_recorrido) if tiempos_recorrido else None
        }

    def ejecutar_simulacion(self):
        self.satelite_simulacion.preparar_datos()
        for idx, estacion in self.satelite_simulacion.estaciones_terrenas_df.iterrows():
            nombre_estacion = estacion['Name_of_Ground_Station']
            coordenadas_estacion = [estacion['x (km)'], estacion['y (km)'], estacion['z (km)']]
            estacion_terrena = EstacionTerrena(nombre_estacion, coordenadas_estacion)
            print(f'\nSimulando para la estación terrestre: {nombre_estacion}')
            self.simular_comunicacion(estacion_terrena)

        for estacion, datos in self.resultados.items():
            print(f'\nResultados para {estacion}:')
            print(f'Promedio delay Nodo-Satélite: {datos["pkt_node_to_satellite"]:.8f} segundos')
            print(f'Promedio delay Satélite-Ground Station: {datos["pkt_satellite_to_ground"]:.8f} segundos')
            print(f'Promedio delay Ground Station-Satélite: {datos["pkt_ground_to_satellite"]:.8f} segundos')
            print(f'Promedio delay Satélite-Nodo: {datos["pkt_satellite_to_node"]:.8f} segundos')
            print(f'Promedio tiempo total del recorrido: {datos["tiempo_total_recorrido"]:.2f} horas')

# Crear la instancia de la simulación
satelite_simulacion = SateliteSimulacion('Satellite1_130_10sec.csv', 'nodo_tierra.csv', 'ksat_ground_stations.csv')
simulacion_comunicacion = SimulacionComunicacion(satelite_simulacion)

# Ejecutar la simulación
simulacion_comunicacion.ejecutar_simulacion()
