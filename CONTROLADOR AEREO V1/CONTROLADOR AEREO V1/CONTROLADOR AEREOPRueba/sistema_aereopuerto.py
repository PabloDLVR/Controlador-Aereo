import csv
import time
import threading
from typing import List, Dict, Any

class SistemaAeropuerto:
    def __init__(self):
        self.reloj_virtual = 0
        self.en_ejecucion = False
        self.eventos_log = []
        self.vuelos = []
        self.pistas = []
        self.pistas_ocupadas = []
        self.flujo_aterrizaje = []
        self.flujo_despegue = []
        self.vuelos_completados = []
        
    def cargar_vuelos_desde_csv(self, archivo: str = "vuelos.csv"):
        """Carga los vuelos desde el archivo CSV"""
        try:
            with open(archivo, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    vuelo = {
                        'id': row['id'],
                        'tipo': row['tipo'],
                        'eta': int(row['eta']) if row.get('eta') else None,
                        'etd': int(row['etd']) if row.get('etd') else None,
                        'prioridad': int(row['prioridad']),
                        'combustible': int(row['combustible']) if row.get('combustible') else None,
                        'estado': row['estado'],
                        'minuto_entrada_cola': None,
                        'minuto_asignacion': None,
                        'minuto_completado': None
                    }
                    self.vuelos.append(vuelo)
            self.registrar_evento("CARGA_INICIAL", f"vuelos={len(self.vuelos)}")
        except FileNotFoundError:
            print(f"Error: Archivo {archivo} no encontrado")
        except Exception as e:
            print(f"Error cargando vuelos: {e}")

    def cargar_pistas_desde_csv(self, archivo: str = "pistas.csv"):
        """Carga las pistas desde el archivo CSV"""
        try:
            with open(archivo, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    pista = {
                        'id_pista': row['id_pista'],
                        'categoria': row['categoria'],
                        'tiempo_uso': int(row['tiempo_uso']),
                        'habilitada': row['habilitada'] == '1'
                    }
                    self.pistas.append(pista)
            self.registrar_evento("CARGA_INICIAL", f"pistas={len(self.pistas)}")
        except FileNotFoundError:
            print(f"Error: Archivo {archivo} no encontrado")
        except Exception as e:
            print(f"Error cargando pistas: {e}")

    def iniciar_simulacion_automatica(self):
        """Inicia la simulación automática con reloj virtual"""
        self.cargar_datos_iniciales()
        self.en_ejecucion = True
        
        while self.en_ejecucion:
            time.sleep(5)  # 5 segundos reales = 1 minuto simulado
            self.reloj_virtual += 1
            self.ejecutar_ciclo_simulacion()

    def ejecutar_ciclo_simulacion(self):
        """Ejecuta un ciclo completo de simulación"""
        # 1. Actualizar combustible
        self.actualizar_combustible()
        
        # 2. Gestionar entrada a colas
        self.gestionar_entrada_colas()
        
        # 3. Liberar pistas
        self.liberar_pistas()
        
        # 4. Asignar pistas
        self.asignar_pistas()
        
        # 5. Registrar estado
        self.registrar_evento("CICLO", f"Minuto {self.reloj_virtual} completado")

    def actualizar_combustible(self):
        """Actualiza el combustible de vuelos de aterrizaje en cola"""
        for vuelo in self.vuelos:
            if (vuelo['tipo'] == "ATERRIZAJE" and 
                vuelo['estado'] == "EN_COLA" and 
                vuelo['combustible'] is not None):
                
                vuelo['combustible'] -= 1
                
                # Verificar emergencia por combustible bajo
                if vuelo['combustible'] <= 5 and vuelo['prioridad'] != 2:
                    vuelo['prioridad'] = 2
                    self.registrar_evento("EMERGENCIA", 
                                        f"id_vuelo={vuelo['id']} prioridad=2 motivo=combustible<={vuelo['combustible']}")

    def gestionar_entrada_colas(self):
        """Gestiona la entrada de vuelos a las colas según ETA/ETD"""
        for vuelo in self.vuelos:
            if vuelo['estado'] not in ["EN_COLA", "ASIGNADO", "COMPLETADO", "CANCELADO"]:
                hora_prevista = vuelo['eta'] if vuelo['tipo'] == "ATERRIZAJE" else vuelo['etd']
                
                if hora_prevista <= self.reloj_virtual:
                    vuelo['estado'] = "EN_COLA"
                    vuelo['minuto_entrada_cola'] = self.reloj_virtual
                    
                    if vuelo['tipo'] == "ATERRIZAJE":
                        self.flujo_aterrizaje.append(vuelo)
                    else:
                        self.flujo_despegue.append(vuelo)
                    
                    self.registrar_evento("EN_COLA", 
                                        f"id_vuelo={vuelo['id']} tipo={vuelo['tipo']}")

    def liberar_pistas(self):
        """Libera pistas que han completado su tiempo de uso"""
        pistas_liberar = []
        for pista_ocupada in self.pistas_ocupadas[:]:
            if pista_ocupada['tiempo_fin'] <= self.reloj_virtual:
                # Encontrar el vuelo y marcarlo como completado
                vuelo = next((v for v in self.vuelos if v['id'] == pista_ocupada['vuelo_id']), None)
                if vuelo:
                    vuelo['estado'] = "COMPLETADO"
                    vuelo['minuto_completado'] = self.reloj_virtual
                    self.vuelos_completados.append(vuelo)
                
                self.pistas_ocupadas.remove(pista_ocupada)
                pistas_liberar.append(pista_ocupada['id_pista'])
                
                self.registrar_evento("COMPLETADO", 
                                    f"id_vuelo={pista_ocupada['vuelo_id']} pista={pista_ocupada['id_pista']}")

    def asignar_pistas(self):
        """Asigna pistas disponibles a vuelos según política de prioridad"""
        pistas_disponibles = [p for p in self.pistas 
                            if p['habilitada'] and 
                            p['id_pista'] not in [po['id_pista'] for po in self.pistas_ocupadas]]
        
        for pista in pistas_disponibles:
            vuelo = self.seleccionar_proximo_vuelo()
            if vuelo:
                self.asignar_pista_a_vuelo(vuelo, pista)

    def seleccionar_proximo_vuelo(self):
        """Selecciona el próximo vuelo según política de prioridad"""
        todos_vuelos = self.flujo_aterrizaje + self.flujo_despegue
        vuelos_en_cola = [v for v in todos_vuelos if v['estado'] == "EN_COLA"]
        
        if not vuelos_en_cola:
            return None
        
        # Ordenar por prioridad (emergencias primero)
        vuelos_prioridad_2 = [v for v in vuelos_en_cola if v['prioridad'] == 2]
        vuelos_prioridad_1 = [v for v in vuelos_en_cola if v['prioridad'] == 1]
        vuelos_prioridad_0 = [v for v in vuelos_en_cola if v['prioridad'] == 0]
        
        # Para emergencias: aterrizajes con menos combustible primero
        if vuelos_prioridad_2:
            aterrizajes = [v for v in vuelos_prioridad_2 if v['tipo'] == "ATERRIZAJE"]
            despegues = [v for v in vuelos_prioridad_2 if v['tipo'] == "DESPEGUE"]
            
            if aterrizajes:
                aterrizajes.sort(key=lambda x: x['combustible'])
                return aterrizajes[0]
            elif despegues:
                despegues.sort(key=lambda x: x['etd'])
                return despegues[0]
        
        # Para prioridad 1 y 0: mayor atraso primero
        candidatos = vuelos_prioridad_1 + vuelos_prioridad_0
        if candidatos:
            candidatos.sort(key=lambda x: (
                x['eta'] if x['tipo'] == 'ATERRIZAJE' else x['etd']
            ))
            return candidatos[0]
        
        return None

    def asignar_pista_a_vuelo(self, vuelo: Dict, pista: Dict):
        """Asigna una pista a un vuelo específico"""
        tiempo_fin = self.reloj_virtual + pista['tiempo_uso']
        
        self.pistas_ocupadas.append({
            'id_pista': pista['id_pista'],
            'vuelo_id': vuelo['id'],
            'tiempo_fin': tiempo_fin
        })
        
        vuelo['estado'] = "ASIGNADO"
        vuelo['minuto_asignacion'] = self.reloj_virtual
        
        # Remover de la cola correspondiente
        if vuelo in self.flujo_aterrizaje:
            self.flujo_aterrizaje.remove(vuelo)
        elif vuelo in self.flujo_despegue:
            self.flujo_despegue.remove(vuelo)
        
        self.registrar_evento("ASIGNACION", 
                            f"id_vuelo={vuelo['id']} pista={pista['id_pista']} tipo={vuelo['tipo']}")

    def registrar_evento(self, tipo: str, mensaje: str):
        """Registra un evento en el log"""
        evento = f"[t={self.reloj_virtual}] {tipo} {mensaje}"
        self.eventos_log.append(evento)
        print(evento)
        
        # Guardar en archivo
        with open("eventos.log", "a", encoding="utf-8") as f:
            f.write(evento + "\n")

    def generar_informe(self):
        """Genera el informe final de la simulación"""
        with open("informe.log", "w", encoding="utf-8") as f:
            f.write("RESUMEN\n")
            f.write(f"- Tiempo simulado (min): {self.reloj_virtual}\n")
            f.write(f"- Vuelos atendidos: {len(self.vuelos_completados)}\n")
            
            # Calcular tiempo medio de espera
            if self.vuelos_completados:
                tiempos_espera = [v['minuto_asignacion'] - (v['eta'] if v['tipo'] == 'ATERRIZAJE' else v['etd']) 
                                for v in self.vuelos_completados]
                tiempo_medio = sum(tiempos_espera) / len(tiempos_espera)
                f.write(f"- Tiempo medio de espera (min): {tiempo_medio:.1f}\n")
            
            # Uso de pistas
            operaciones_por_pista = {}
            for pista in self.pistas:
                count = len([po for po in self.pistas_ocupadas if po['id_pista'] == pista['id_pista']])
                operaciones_por_pista[pista['id_pista']] = count
            
            for pista_id, count in operaciones_por_pista.items():
                f.write(f"- Uso de pistas: {pista_id}={count} operaciones\n")
            
            # Emergencias
            emergencias = len([v for v in self.vuelos_completados if v['prioridad'] == 2])
            f.write(f"- Emergencias gestionadas: {emergencias}\n")
            
            # Detalle de vuelos
            f.write("- Detalle de vuelos completados:\n")
            for vuelo in self.vuelos_completados:
                tipo_extra = " (EMERGENCIA)" if vuelo['prioridad'] == 2 else ""
                f.write(f"• {vuelo['id']} ({vuelo['tipo']}{tipo_extra}) t_inicio={vuelo['minuto_asignacion']} t_fin={vuelo['minuto_completado']}\n")

    def cargar_datos_iniciales(self):
        """Carga todos los datos iniciales"""
        self.cargar_pistas_desde_csv()
        self.cargar_vuelos_desde_csv()

    def avanzar_minuto(self):
        """Avanza un minuto en la simulación (para modo manual)"""
        self.reloj_virtual += 1
        self.ejecutar_ciclo_simulacion()
        return self.obtener_estado_actual()

    def obtener_estado_actual(self):
        """Retorna el estado actual para la interfaz gráfica"""
        return {
            'reloj': self.reloj_virtual,
            'vuelos_en_cola_aterrizaje': len(self.flujo_aterrizaje),
            'vuelos_en_cola_despegue': len(self.flujo_despegue),
            'vuelos_asignados': len([v for v in self.vuelos if v['estado'] == 'ASIGNADO']),
            'vuelos_completados': len(self.vuelos_completados),
            'pistas_ocupadas': len(self.pistas_ocupadas),
            'pistas_totales': len(self.pistas),
            'detalle_vuelos': self.vuelos,
            'detalle_pistas': self.pistas_ocupadas,
            'flujo_aterrizaje': self.flujo_aterrizaje,
            'flujo_despegue': self.flujo_despegue
        }

    def detener_simulacion(self):
        """Detiene la simulación"""
        self.en_ejecucion = False

# Función para crear archivos de ejemplo
def crear_archivos_ejemplo():
    """Crea archivos CSV de ejemplo si no existen"""
    try:
        with open("vuelos.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'tipo', 'eta', 'etd', 'prioridad', 'combustible', 'estado'])
            writer.writerow(['IB101', 'ATERRIZAJE', '0', '', '0', '20', 'PENDIENTE'])
            writer.writerow(['IB202', 'ATERRIZAJE', '0', '', '0', '15', 'PENDIENTE'])
            writer.writerow(['UX303', 'DESPEGUE', '', '0', '0', '', 'PENDIENTE'])
            writer.writerow(['VY404', 'DESPEGUE', '', '0', '0', '', 'PENDIENTE'])
            writer.writerow(['AF505', 'ATERRIZAJE', '0', '', '0', '8', 'PENDIENTE'])
        
        with open("pistas.csv", "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id_pista', 'categoria', 'tiempo_uso', 'habilitada'])
            writer.writerow(['R1', 'larga', '3', '1'])
            writer.writerow(['R2', 'estandar', '3', '1'])
        print("Archivos de ejemplo creados: vuelos.csv y pistas.csv")
    except Exception as e:
        print(f"Error creando archivos ejemplo: {e}")

if __name__ == "__main__":
    # Para uso en consola
    crear_archivos_ejemplo()
    sistema = SistemaAeropuerto()
    sistema.cargar_datos_iniciales()
    
    print("Sistema de Simulación de Aeropuerto")
    print("Modo automático: 5 segundos = 1 minuto simulado")
    print("Presiona Ctrl+C para detener")
    
    try:
        sistema.iniciar_simulacion_automatica()
    except KeyboardInterrupt:
        sistema.generar_informe()
        print("\nSimulación detenida. Informe generado en informe.log")