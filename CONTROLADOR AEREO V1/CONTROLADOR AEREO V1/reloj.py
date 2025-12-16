import time
import threading
from datetime import datetime, timedelta
import csv
from typing import List, Dict, Any

class SistemaAeropuerto:
    def __init__(self):
        self.reloj_virtual = 0  # Minutos simulados desde el inicio
        self.en_ejecucion = False
        self.eventos_log = []
        self.vuelos = []  # Todos los vuelos cargados desde CSV
        self.pistas = []  # Pistas cargadas desde CSV
        self.pistas_ocupadas = []  # Pistas actualmente ocupadas
        
    def cargar_vuelos_desde_csv(self, archivo: str = "vuelos.csv"):
        """Carga los vuelos desde el archivo CSV al iniciar el programa"""
        try:
            with open(archivo, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    # Convertir tipos de datos
                    vuelo = {
                        'id': row['id'],
                        'tipo': row['tipo'],
                        'eta': int(row['eta']) if row.get('eta') else None,
                        'etd': int(row['etd']) if row.get('etd') else None,
                        'prioridad': int(row['prioridad']),
                        'combustible': int(row['combustible']) if row.get('combustible') else None,
                        'estado': row['estado']
                    }
                    self.vuelos.append(vuelo)
            self.registrar_evento("SISTEMA", f"Vuelos cargados: {len(self.vuelos)} vuelos desde {archivo}")
        except FileNotFoundError:
            self.registrar_evento("ERROR", f"Archivo {archivo} no encontrado")
        except Exception as e:
            self.registrar_evento("ERROR", f"Error cargando vuelos: {str(e)}")
    
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
            self.registrar_evento("SISTEMA", f"Pistas cargadas: {len(self.pistas)} pistas desde {archivo}")
        except FileNotFoundError:
            self.registrar_evento("ERROR", f"Archivo {archivo} no encontrado")
        except Exception as e:
            self.registrar_evento("ERROR", f"Error cargando pistas: {str(e)}")
    
    def iniciar_simulacion(self):
        """Inicia la simulación del sistema con el reloj virtual"""
        # Cargar datos iniciales
        self.cargar_vuelos_desde_csv()
        self.cargar_pistas_desde_csv()
        
        self.en_ejecucion = True
        self.registrar_evento("SISTEMA", "Simulación iniciada")
        print(f"Simulación iniciada. Reloj virtual: {self.reloj_virtual} minutos")
        
        # Hilo principal de simulación
        while self.en_ejecucion:
            # Esperar 5 segundos reales = 1 minuto simulado
            time.sleep(5)
            
            # Avanzar reloj virtual en 1 minuto
            self.reloj_virtual += 1
            
            # Ejecutar todas las rutinas de actualización
            self.ejecutar_actualizaciones()
            
    def ejecutar_actualizaciones(self):
        """Ejecuta todas las rutinas de actualización del sistema por cada incremento del reloj"""
        try:
            # 1. Actualizar consumo de combustible de vuelos en espera
            self.actualizar_combustible()
            
            # 2. Liberar pistas que han completado su tiempo de uso
            self.liberar_pistas()
            
            # 3. Gestionar entrada/salida de vuelos en cola
            self.gestionar_colas_vuelos()
            
            # 4. Asignar pistas disponibles a vuelos en cola
            self.asignar_pistas_disponibles()
            
            # 5. Mostrar estado actual del sistema
            self.mostrar_estado_actual()
            
            # 6. Registrar evento de ciclo completado
            self.registrar_evento("RELÓJ", f"Ciclo completado - Minuto {self.reloj_virtual}")
            
        except Exception as e:
            self.registrar_evento("ERROR", f"Error en actualización minuto {self.reloj_virtual}: {str(e)}")
    
    def actualizar_combustible(self):
        """Actualiza el consumo de combustible de vuelos de aterrizaje en espera"""
        for vuelo in self.vuelos:
            if (vuelo['tipo'] == "ATERRIZAJE" and 
                vuelo['estado'] == "EN_COLA" and 
                vuelo['combustible'] is not None and 
                vuelo['combustible'] > 0):
                
                vuelo['combustible'] -= 1
                
                # Verificar emergencias por combustible
                if vuelo['combustible'] <= 0:
                    vuelo['estado'] = "CANCELADO"
                    self.registrar_evento("EMERGENCIA", 
                                        f"Vuelo {vuelo['id']} SIN COMBUSTIBLE - Cancelado")
                elif vuelo['combustible'] <= 5:
                    # Elevar prioridad por combustible bajo
                    vuelo['prioridad'] = 2  # Emergencia
                    self.registrar_evento("COMBUSTIBLE", 
                                        f"Vuelo {vuelo['id']} - Combustible bajo: {vuelo['combustible']} min")
    
    def liberar_pistas(self):
        """Libera pistas que han completado su tiempo de uso"""
        pistas_a_liberar = []
        
        for pista_ocupada in self.pistas_ocupadas[:]:
            if pista_ocupada['tiempo_fin'] <= self.reloj_virtual:
                # Liberar pista
                self.pistas_ocupadas.remove(pista_ocupada)
                pistas_a_liberar.append(pista_ocupada['id_pista'])
                
                # Actualizar estado del vuelo
                vuelo = self.buscar_vuelo_por_id(pista_ocupada['vuelo_id'])
                if vuelo:
                    vuelo['estado'] = "COMPLETADO"
                
                self.registrar_evento("PISTA", 
                                    f"Pista {pista_ocupada['id_pista']} liberada - Vuelo {pista_ocupada['vuelo_id']} completado")
        
        return pistas_a_liberar
    
    def gestionar_colas_vuelos(self):
        """Gestiona la entrada de vuelos a cola según su ETA/ETD"""
        vuelos_entraron_cola = []
        
        for vuelo in self.vuelos:
            # Verificar si el vuelo debe entrar en cola según el reloj actual
            if (vuelo['estado'] not in ["EN_COLA", "ASIGNADO", "COMPLETADO", "CANCELADO"] and
                ((vuelo['tipo'] == "ATERRIZAJE" and vuelo['eta'] <= self.reloj_virtual) or
                 (vuelo['tipo'] == "DESPEGUE" and vuelo['etd'] <= self.reloj_virtual))):
                
                vuelo['estado'] = "EN_COLA"
                vuelos_entraron_cola.append(vuelo['id'])
                self.registrar_evento("VUELO", 
                                    f"Vuelo {vuelo['id']} ({vuelo['tipo']}) entró en cola de espera")
        
        return vuelos_entraron_cola
    
    def asignar_pistas_disponibles(self):
        """Asigna pistas disponibles a vuelos en cola según prioridad"""
        # Obtener pistas disponibles (habilitadas y no ocupadas)
        pistas_disponibles = [
            pista for pista in self.pistas 
            if pista['habilitada'] and 
            pista['id_pista'] not in [po['id_pista'] for po in self.pistas_ocupadas]
        ]
        
        # Obtener vuelos en cola ordenados por prioridad (emergencia primero)
        vuelos_en_cola = [
            vuelo for vuelo in self.vuelos 
            if vuelo['estado'] == "EN_COLA"
        ]
        vuelos_en_cola.sort(key=lambda x: (-x['prioridad'], x['eta'] if x['tipo'] == 'ATERRIZAJE' else x['etd']))
        
        # Asignar pistas a vuelos
        for pista in pistas_disponibles:
            if vuelos_en_cola:
                vuelo = vuelos_en_cola.pop(0)
                self.asignar_pista_a_vuelo(vuelo, pista)
    
    def asignar_pista_a_vuelo(self, vuelo: Dict, pista: Dict):
        """Asigna una pista específica a un vuelo"""
        tiempo_fin = self.reloj_virtual + pista['tiempo_uso']
        
        # Registrar ocupación de pista
        self.pistas_ocupadas.append({
            'id_pista': pista['id_pista'],
            'vuelo_id': vuelo['id'],
            'tiempo_fin': tiempo_fin
        })
        
        # Actualizar estado del vuelo
        vuelo['estado'] = "ASIGNADO"
        
        self.registrar_evento("ASIGNACION", 
                            f"Pista {pista['id_pista']} asignada a vuelo {vuelo['id']} hasta minuto {tiempo_fin}")
    
    def buscar_vuelo_por_id(self, vuelo_id: str) -> Dict:
        """Busca un vuelo por su ID"""
        for vuelo in self.vuelos:
            if vuelo['id'] == vuelo_id:
                return vuelo
        return None
    
    def registrar_evento(self, tipo: str, mensaje: str):
        """Registra un evento en el log del sistema"""
        evento = {
            'minuto': self.reloj_virtual,
            'tipo': tipo,
            'mensaje': mensaje
        }
        self.eventos_log.append(evento)
        
        # Mostrar en consola y guardar en archivo
        print(f"[Min {self.reloj_virtual:04d}] [{tipo}] {mensaje}")
        self.guardar_log_archivo()
    
    def guardar_log_archivo(self):
        """Guarda el log completo en un archivo .log"""
        try:
            with open("simulacion.log", "w", encoding="utf-8") as file:
                file.write("LOG DE SIMULACIÓN - SISTEMA AEROPUERTO\n")
                file.write("=" * 50 + "\n")
                for evento in self.eventos_log:
                    file.write(f"[Min {evento['minuto']:04d}] [{evento['tipo']}] {evento['mensaje']}\n")
        except Exception as e:
            print(f"Error guardando log: {e}")
    
    def mostrar_estado_actual(self):
        """Muestra el estado actual del sistema"""
        vuelos_en_cola = len([v for v in self.vuelos if v['estado'] == "EN_COLA"])
        vuelos_asignados = len([v for v in self.vuelos if v['estado'] == "ASIGNADO"])
        pistas_ocupadas = len(self.pistas_ocupadas)
        pistas_habilitadas = len([p for p in self.pistas if p['habilitada']])
        
        print(f"\n--- Estado del Sistema [Min {self.reloj_virtual:04d}] ---")
        print(f"Vuelos en cola: {vuelos_en_cola}")
        print(f"Vuelos asignados: {vuelos_asignados}")
        print(f"Pistas ocupadas: {pistas_ocupadas}/{pistas_habilitadas}")
        print(f"Total eventos: {len(self.eventos_log)}")
        print("-" * 50)
    
    def detener_simulacion(self):
        """Detiene la simulación"""
        self.en_ejecucion = False
        self.registrar_evento("SISTEMA", "Simulación detenida")
        print("Simulación detenida")

# Función principal
def main():
    sistema = SistemaAeropuerto()
    
    print("Sistema de Simulación de Aeropuerto")
    print("Reloj virtual: 1 minuto simulado = 5 segundos reales")
    print("Presiona Ctrl+C para detener la simulación\n")
    
    # Iniciar simulación en un hilo separado
    hilo_simulacion = threading.Thread(target=sistema.iniciar_simulacion)
    hilo_simulacion.daemon = True
    hilo_simulacion.start()
    
    try:
        # Mantener el programa principal en ejecución
        while sistema.en_ejecucion:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo simulación...")
    finally:
        sistema.detener_simulacion()

if __name__ == "__main__":
    main()
