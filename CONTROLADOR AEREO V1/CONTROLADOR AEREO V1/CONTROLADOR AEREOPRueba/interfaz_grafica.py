import csv
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any
import math
import random

class SistemaAeropuertoMejorado:
    def __init__(self):
        # Inicializar sistema
        self.reloj_virtual = 0
        self.en_ejecucion = False
        self.eventos_log = []
        self.vuelos = []
        self.pistas = []
        self.pistas_ocupadas = []
        self.flujo_aterrizaje = []
        self.flujo_despegue = []
        self.vuelos_completados = []
        self.aviones_animados = {}
        self.hilo_simulacion = None
        
        # Crear archivos de ejemplo
        self.crear_archivos_ejemplo()
        
        # Cargar datos iniciales
        self.cargar_datos_iniciales()
        
        # Crear interfaz
        self.crear_interfaz()
        
        # Iniciar simulación automáticamente
        self.iniciar_simulacion_auto()
    
    def crear_archivos_ejemplo(self):
        """Crea archivos CSV de ejemplo"""
        try:
            with open("vuelos.csv", "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'tipo', 'eta', 'etd', 'prioridad', 'combustible', 'estado'])
                writer.writerow(['IB101', 'ATERRIZAJE', '1', '', '0', '30', 'PENDIENTE'])
                writer.writerow(['IB202', 'ATERRIZAJE', '2', '', '0', '25', 'PENDIENTE'])
                writer.writerow(['UX303', 'DESPEGUE', '', '3', '0', '', 'PENDIENTE'])
                writer.writerow(['VY404', 'DESPEGUE', '', '4', '0', '', 'PENDIENTE'])
                writer.writerow(['AF505', 'ATERRIZAJE', '5', '', '0', '15', 'PENDIENTE'])
                writer.writerow(['BA606', 'ATERRIZAJE', '6', '', '1', '35', 'PENDIENTE'])
                writer.writerow(['LH707', 'DESPEGUE', '', '7', '0', '', 'PENDIENTE'])
            
            with open("pistas.csv", "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id_pista', 'categoria', 'tiempo_uso', 'habilitada'])
                writer.writerow(['R1', 'larga', '4', '1'])
                writer.writerow(['R2', 'estandar', '3', '1'])
                writer.writerow(['R3', 'corta', '2', '1'])
        except Exception as e:
            print(f"Error creando archivos: {e}")

    def cargar_datos_iniciales(self):
        """Carga todos los datos iniciales"""
        self.cargar_pistas_desde_csv()
        self.cargar_vuelos_desde_csv()

    def cargar_vuelos_desde_csv(self, archivo: str = "vuelos.csv"):
        """Carga los vuelos desde CSV"""
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
                        'estado': 'PENDIENTE',
                        'minuto_entrada_cola': None,
                        'minuto_asignacion': None,
                        'minuto_completado': None,
                        'posicion_animacion': 0  # Para controlar animación
                    }
                    self.vuelos.append(vuelo)
            self.registrar_evento("CARGA_INICIAL", f"vuelos={len(self.vuelos)}")
        except Exception as e:
            print(f"Error cargando vuelos: {e}")

    def cargar_pistas_desde_csv(self, archivo: str = "pistas.csv"):
        """Carga las pistas desde CSV"""
        try:
            with open(archivo, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    pista = {
                        'id_pista': row['id_pista'],
                        'categoria': row['categoria'],
                        'tiempo_uso': int(row['tiempo_uso']),
                        'habilitada': row['habilitada'] == '1',
                        'estado': 'LIBRE'
                    }
                    self.pistas.append(pista)
            self.registrar_evento("CARGA_INICIAL", f"pistas={len(self.pistas)}")
        except Exception as e:
            print(f"Error cargando pistas: {e}")

    def crear_interfaz(self):
        """Crea la interfaz gráfica completa con dibujos mejorados"""
        self.root = tk.Tk()
        self.root.title("🏢 Sistema de Control de Tráfico Aéreo - Simulación Visual")
        self.root.geometry("1400x950")
        self.root.configure(bg='#1a1a2e')
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== HEADER CON RELOJ PRINCIPAL =====
        header_frame = tk.Frame(main_frame, bg='#16213e', relief=tk.RAISED, bd=3)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Reloj virtual grande y visible
        self.reloj_label = tk.Label(header_frame, 
                                   text="⏰ MINUTO SIMULADO: 0", 
                                   font=("Arial", 20, "bold"), 
                                   fg="white", 
                                   bg="#e94560",
                                   padx=25,
                                   pady=12)
        self.reloj_label.pack(side=tk.LEFT, padx=(20, 30))
        
        # Contador de tiempo real
        self.tiempo_real_label = tk.Label(header_frame,
                                         text="🕐 TIEMPO REAL: 0s",
                                         font=("Arial", 12),
                                         fg="white",
                                         bg="#0f3460",
                                         padx=15,
                                         pady=8)
        self.tiempo_real_label.pack(side=tk.LEFT)
        
        # Botones de control
        control_frame = tk.Frame(header_frame, bg='#16213e')
        control_frame.pack(side=tk.RIGHT, padx=15, pady=10)
        
        self.btn_iniciar = tk.Button(control_frame, text="▶️ INICIAR", font=("Arial", 10, "bold"),
                  command=self.iniciar_simulacion_auto, bg='#27ae60', fg='white', width=12)
        self.btn_iniciar.pack(side=tk.LEFT, padx=3)
        
        self.btn_pausar = tk.Button(control_frame, text="⏸️ PAUSAR", font=("Arial", 10, "bold"),
                  command=self.detener_simulacion, bg='#e67e22', fg='white', width=12)
        self.btn_pausar.pack(side=tk.LEFT, padx=3)
        
        tk.Button(control_frame, text="📊 INFORME", font=("Arial", 10, "bold"),
                  command=self.generar_informe, bg='#3498db', fg='white', width=12).pack(side=tk.LEFT, padx=3)
        
        tk.Button(control_frame, text="🔄 REINICIAR", font=("Arial", 10, "bold"),
                  command=self.reiniciar_sistema, bg='#9b59b6', fg='white', width=12).pack(side=tk.LEFT, padx=3)
        
        # ===== PANEL DE ESTADO GENERAL =====
        estado_frame = tk.LabelFrame(main_frame, text="📊 PANEL DE CONTROL - ESTADO GENERAL", 
                                   font=("Arial", 11, "bold"), bg='#16213e', fg='white', bd=2)
        estado_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Métricas principales
        metricas_frame = tk.Frame(estado_frame, bg='#16213e')
        metricas_frame.pack(fill=tk.X, padx=15, pady=12)
        
        self.metricas = {}
        metricas_info = [
            ("🛬 ATERRIZAJE", "aterrizaje_cola", "#e74c3c"),
            ("🛫 DESPEGUE", "despegue_cola", "#3498db"),
            ("✅ ASIGNADOS", "asignados", "#2ecc71"),
            ("🏁 COMPLETADOS", "completados", "#27ae60"),
            ("🚨 EMERGENCIAS", "emergencias", "#f39c12"),
            ("🛣️ PISTAS OCUP", "pistas_ocupadas", "#9b59b6")
        ]
        
        for i, (texto, key, color) in enumerate(metricas_info):
            frame = tk.Frame(metricas_frame, bg=color, relief=tk.RAISED, bd=2)
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
            
            tk.Label(frame, text=texto, bg=color, fg="white", 
                    font=("Arial", 9, "bold"), pady=6).pack()
            
            self.metricas[key] = tk.Label(frame, text="0", bg="white", fg=color,
                                        font=("Arial", 14, "bold"), 
                                        width=6, height=1, relief=tk.SUNKEN, bd=2)
            self.metricas[key].pack(pady=6)
        
        # ===== ÁREA DE VISUALIZACIÓN CON PISTAS Y AVIONES =====
        visualizacion_frame = tk.LabelFrame(main_frame, text="🎯 SIMULACIÓN VISUAL - AEROPUERTO EN TIEMPO REAL", 
                                          font=("Arial", 11, "bold"), bg='#16213e', fg='white', bd=2)
        visualizacion_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Canvas para dibujar el aeropuerto
        self.canvas = tk.Canvas(visualizacion_frame, bg='#87CEEB', width=1200, height=450,
                               highlightthickness=3, highlightbackground='#e94560')
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # ===== PANEL DE INFORMACIÓN DE VUELOS =====
        info_frame = tk.Frame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Vuelos en espera de aterrizaje
        aterrizaje_frame = tk.LabelFrame(info_frame, text="🛬 COLA DE ATERRIZAJE - AVIONES EN ESPERA", 
                                       font=("Arial", 10, "bold"), bg='#16213e', fg='white')
        aterrizaje_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Frame para árbol y scrollbar
        aterrizaje_container = tk.Frame(aterrizaje_frame, bg='#16213e')
        aterrizaje_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.aterrizaje_tree = ttk.Treeview(aterrizaje_container, 
                                          columns=('id', 'combustible', 'prioridad', 'eta', 'estado'), 
                                          show='headings', height=6)
        
        # Configurar scrollbar
        scroll_aterrizaje = ttk.Scrollbar(aterrizaje_container, orient="vertical", command=self.aterrizaje_tree.yview)
        self.aterrizaje_tree.configure(yscrollcommand=scroll_aterrizaje.set)
        
        self.aterrizaje_tree.heading('id', text='✈️ VUELO')
        self.aterrizaje_tree.heading('combustible', text='⛽ COMBUSTIBLE')
        self.aterrizaje_tree.heading('prioridad', text='🚨 PRIORIDAD')
        self.aterrizaje_tree.heading('eta', text='🕐 ETA')
        self.aterrizaje_tree.heading('estado', text='📊 ESTADO')
        
        self.aterrizaje_tree.column('id', width=70)
        self.aterrizaje_tree.column('combustible', width=85)
        self.aterrizaje_tree.column('prioridad', width=80)
        self.aterrizaje_tree.column('eta', width=60)
        self.aterrizaje_tree.column('estado', width=80)
        
        self.aterrizaje_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_aterrizaje.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Vuelos en espera de despegue
        despegue_frame = tk.LabelFrame(info_frame, text="🛫 COLA DE DESPEGUE - AVIONES EN PLATAFORMA", 
                                     font=("Arial", 10, "bold"), bg='#16213e', fg='white')
        despegue_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        despegue_container = tk.Frame(despegue_frame, bg='#16213e')
        despegue_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.despegue_tree = ttk.Treeview(despegue_container, 
                                        columns=('id', 'etd', 'prioridad', 'estado'), 
                                        show='headings', height=6)
        
        scroll_despegue = ttk.Scrollbar(despegue_container, orient="vertical", command=self.despegue_tree.yview)
        self.despegue_tree.configure(yscrollcommand=scroll_despegue.set)
        
        self.despegue_tree.heading('id', text='✈️ VUELO')
        self.despegue_tree.heading('etd', text='🕐 ETD')
        self.despegue_tree.heading('prioridad', text='🚨 PRIORIDAD')
        self.despegue_tree.heading('estado', text='📊 ESTADO')
        
        self.despegue_tree.column('id', width=80)
        self.despegue_tree.column('etd', width=80)
        self.despegue_tree.column('prioridad', width=80)
        self.despegue_tree.column('estado', width=80)
        
        self.despegue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_despegue.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ===== LOG DE EVENTOS =====
        log_frame = tk.LabelFrame(main_frame, text="📝 REGISTRO DE EVENTOS - BITÁCORA DE OPERACIONES", 
                                font=("Arial", 11, "bold"), bg='#16213e', fg='white', bd=2)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=6, width=100, 
                               font=("Consolas", 9), bg='#1a1a2e', fg='#00ff88',
                               relief=tk.SUNKEN, bd=2)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 8), pady=8)
        
        # Iniciar contador de tiempo real
        self.tiempo_inicio = time.time()
        self.actualizar_tiempo_real()
        
        # Dibujar aeropuerto inicial
        self.dibujar_aeropuerto()
    
    def dibujar_aeropuerto(self):
        """Dibuja el aeropuerto con pistas y aviones"""
        self.canvas.delete("all")
        
        # Dibujar cielo con gradiente
        self.canvas.create_rectangle(0, 0, 1400, 450, fill='#4682b4', outline='')
        
        # Dibujar suelo del aeropuerto
        self.canvas.create_rectangle(0, 300, 1400, 450, fill='#708090', outline='')
        
        # Dibujar pistas
        pista_positions = [
            {'x1': 100, 'y1': 200, 'x2': 1300, 'y2': 230, 'id': 'R1'},
            {'x1': 100, 'y1': 250, 'x2': 1300, 'y2': 280, 'id': 'R2'},
            {'x1': 100, 'y1': 300, 'x2': 1300, 'y2': 330, 'id': 'R3'}
        ]
        
        for i, pos in enumerate(pista_positions):
            if i < len(self.pistas):
                pista = self.pistas[i]
                pista_ocupada = any(po['id_pista'] == pista['id_pista'] for po in self.pistas_ocupadas)
                
                # Color de pista según estado
                color_pista = '#ff4444' if pista_ocupada else '#2ecc71'
                
                # Dibujar pista principal
                self.canvas.create_rectangle(pos['x1'], pos['y1'], pos['x2'], pos['y2'], 
                                           fill=color_pista, outline='black', width=3)
                
                # Marcas de pista (líneas discontinuas)
                for x in range(pos['x1'] + 20, pos['x2'], 40):
                    self.canvas.create_line(x, pos['y1']+5, x, pos['y2']-5, fill='white', width=2)
                
                # Texto de la pista
                estado_text = "OCUPADA" if pista_ocupada else "LIBRE"
                color_text = "white" if pista_ocupada else "black"
                self.canvas.create_text(pos['x1'] - 40, (pos['y1'] + pos['y2']) // 2, 
                                      text=f"PISTA\n{pista['id_pista']}\n{estado_text}", 
                                      font=("Arial", 9, "bold"), fill=color_text,
                                      justify=tk.CENTER)
        
        # Dibujar terminal
        self.canvas.create_rectangle(50, 350, 350, 430, fill='#34495e', outline='black', width=2)
        self.canvas.create_text(200, 390, text="TERMINAL\nPRINCIPAL", 
                              font=("Arial", 10, "bold"), fill='white')
        
        # Dibujar torre de control
        self.canvas.create_rectangle(400, 330, 450, 430, fill='#e74c3c', outline='black', width=2)
        self.canvas.create_rectangle(420, 300, 430, 330, fill='#f39c12', outline='black', width=1)
        self.canvas.create_text(425, 380, text="TORRE", font=("Arial", 7, "bold"), fill='white')
        
        # Dibujar aviones según su estado
        self.dibujar_aviones()
    
    def dibujar_aviones(self):
        """Dibuja todos los aviones según su estado actual"""
        # Aviones en pistas (asignados)
        for pista_ocupada in self.pistas_ocupadas:
            vuelo = next((v for v in self.vuelos if v['id'] == pista_ocupada['vuelo_id']), None)
            if vuelo:
                pista_idx = next(i for i, p in enumerate(self.pistas) if p['id_pista'] == pista_ocupada['id_pista'])
                pos = self.obtener_posicion_pista(pista_idx)
                
                # Calcular progreso de la animación
                tiempo_total = next(p['tiempo_uso'] for p in self.pistas if p['id_pista'] == pista_ocupada['id_pista'])
                tiempo_transcurrido = self.reloj_virtual - (pista_ocupada['tiempo_fin'] - tiempo_total)
                progreso = min(max(tiempo_transcurrido / tiempo_total, 0), 1)
                
                # Posición X basada en el progreso
                avion_x = pos['x1'] + (pos['x2'] - pos['x1']) * progreso
                avion_y = (pos['y1'] + pos['y2']) // 2
                
                # Dibujar avión
                self.dibujar_avion_detallado(avion_x, avion_y, vuelo['id'], 
                                           'rojo' if vuelo['tipo'] == 'ATERRIZAJE' else 'azul')
        
        # Aviones esperando aterrizar (volando en círculo)
        for i, vuelo in enumerate([v for v in self.flujo_aterrizaje if v['estado'] == 'EN_COLA']):
            angle = (self.reloj_virtual * 15 + i * 90) % 360
            radius = 60
            center_x, center_y = 500, 100 + i * 30
            
            avion_x = center_x + radius * math.cos(math.radians(angle))
            avion_y = center_y + radius * math.sin(math.radians(angle))
            
            color = 'naranja' if vuelo['prioridad'] == 2 else 'rojo'
            self.dibujar_avion_detallado(avion_x, avion_y, vuelo['id'], color)
            
            # Dibujar círculo de espera
            self.canvas.create_oval(center_x - radius, center_y - radius,
                                  center_x + radius, center_y + radius,
                                  outline='yellow', dash=(4, 2), width=1)
        
        # Aviones esperando despegar (en plataforma)
        for i, vuelo in enumerate([v for v in self.flujo_despegue if v['estado'] == 'EN_COLA']):
            avion_x = 1200
            avion_y = 380 - i * 25
            self.dibujar_avion_detallado(avion_x, avion_y, vuelo['id'], 'azul')
    
    def obtener_posicion_pista(self, pista_idx):
        """Obtiene las coordenadas de una pista específica"""
        posiciones = [
            {'x1': 100, 'y1': 200, 'x2': 1300, 'y2': 230},
            {'x1': 100, 'y1': 250, 'x2': 1300, 'y2': 280},
            {'x1': 100, 'y1': 300, 'x2': 1300, 'y2': 330}
        ]
        return posiciones[pista_idx] if pista_idx < len(posiciones) else posiciones[0]
    
    def dibujar_avion_detallado(self, x, y, texto, tipo):
        """Dibuja un avión detallado en la posición especificada"""
        if tipo == 'rojo':
            color_cuerpo = '#e74c3c'
        elif tipo == 'azul':
            color_cuerpo = '#3498db'
        elif tipo == 'naranja':
            color_cuerpo = '#e67e22'
        else:
            color_cuerpo = '#95a5a6'
        
        # Cuerpo del avión
        self.canvas.create_oval(x-12, y-6, x+12, y+6, fill=color_cuerpo, outline='black', width=2)
        
        # Alas
        self.canvas.create_polygon(x-8, y-6, x-8, y-20, x+8, y-20, x+8, y-6, 
                                 fill=color_cuerpo, outline='black', width=1)
        self.canvas.create_polygon(x-8, y+6, x-8, y+20, x+8, y+20, x+8, y+6, 
                                 fill=color_cuerpo, outline='black', width=1)
        
        # Cola
        self.canvas.create_polygon(x+8, y-4, x+20, y, x+8, y+4, 
                                 fill=color_cuerpo, outline='black', width=1)
        
        # Ventanas
        for dx in [-6, 0, 6]:
            self.canvas.create_oval(x+dx-2, y-2, x+dx+2, y+2, fill='white', outline='black', width=1)
        
        # Texto del vuelo con fondo
        self.canvas.create_rectangle(x-25, y-35, x+25, y-20, fill='white', outline='black', width=1)
        self.canvas.create_text(x, y-27, text=texto, font=("Arial", 8, "bold"), fill='black')
    
    def actualizar_tiempo_real(self):
        """Actualiza el contador de tiempo real"""
        if hasattr(self, 'tiempo_inicio'):
            tiempo_transcurrido = int(time.time() - self.tiempo_inicio)
            self.tiempo_real_label.config(text=f"🕐 TIEMPO REAL: {tiempo_transcurrido}s")
        self.root.after(1000, self.actualizar_tiempo_real)
    
    def iniciar_simulacion_auto(self):
        """Inicia la simulación automática"""
        if not self.en_ejecucion:
            self.en_ejecucion = True
            self.btn_iniciar.config(state='disabled', bg='#7f8c8d')
            self.btn_pausar.config(state='normal', bg='#e67e22')
            self.hilo_simulacion = threading.Thread(target=self.ejecutar_simulacion_auto, daemon=True)
            self.hilo_simulacion.start()
            self.registrar_evento("SISTEMA", "Simulación INICIADA")
    
    def ejecutar_simulacion_auto(self):
        """Ejecuta la simulación automática"""
        while self.en_ejecucion:
            try:
                # Avanzar minuto
                self.avanzar_minuto()
                
                # Actualizar interfaz en el hilo principal
                self.root.after(0, self.actualizar_interfaz)
                
                # Esperar 3 segundos para mejor visualización
                time.sleep(3)
                
            except Exception as e:
                self.registrar_evento("ERROR", f"Error en simulación: {str(e)}")
                time.sleep(1)
    
    def avanzar_minuto(self):
        """Avanza un minuto en la simulación"""
        self.reloj_virtual += 1
        
        # 1. Actualizar combustible
        self.actualizar_combustible()
        
        # 2. Gestionar entrada a colas
        self.gestionar_entrada_colas()
        
        # 3. Liberar pistas
        self.liberar_pistas()
        
        # 4. Asignar pistas
        self.asignar_pistas()
        
        # 5. Registrar ciclo
        if self.reloj_virtual % 5 == 0:  # Cada 5 minutos
            self.registrar_evento("ESTADO", f"Reporte de sistema - Minuto {self.reloj_virtual}")
    
    def actualizar_combustible(self):
        """Actualiza el combustible de vuelos de aterrizaje"""
        for vuelo in self.vuelos:
            if (vuelo['tipo'] == "ATERRIZAJE" and 
                vuelo['estado'] == "EN_COLA" and 
                vuelo['combustible'] is not None):
                
                vuelo['combustible'] -= 1
                
                if vuelo['combustible'] <= 0:
                    vuelo['estado'] = "CANCELADO"
                    self.registrar_evento("CANCELADO", f"Vuelo {vuelo['id']} - SIN COMBUSTIBLE")
                    if vuelo in self.flujo_aterrizaje:
                        self.flujo_aterrizaje.remove(vuelo)
                
                elif vuelo['combustible'] <= 5 and vuelo['prioridad'] != 2:
                    vuelo['prioridad'] = 2
                    self.registrar_evento("EMERGENCIA", 
                                        f"Vuelo {vuelo['id']} - COMBUSTIBLE CRÍTICO: {vuelo['combustible']}min")

    def gestionar_entrada_colas(self):
        """Gestiona la entrada de vuelos a las colas"""
        for vuelo in self.vuelos:
            if vuelo['estado'] == "PENDIENTE":
                hora_prevista = vuelo['eta'] if vuelo['tipo'] == "ATERRIZAJE" else vuelo['etd']
                
                if hora_prevista <= self.reloj_virtual:
                    vuelo['estado'] = "EN_COLA"
                    vuelo['minuto_entrada_cola'] = self.reloj_virtual
                    
                    if vuelo['tipo'] == "ATERRIZAJE":
                        self.flujo_aterrizaje.append(vuelo)
                    else:
                        self.flujo_despegue.append(vuelo)
                    
                    self.registrar_evento("EN_COLA", f"Vuelo {vuelo['id']} ({vuelo['tipo']})")

    def liberar_pistas(self):
        """Libera pistas que han completado su tiempo"""
        pistas_a_liberar = []
        for pista_ocupada in self.pistas_ocupadas[:]:
            if pista_ocupada['tiempo_fin'] <= self.reloj_virtual:
                vuelo = next((v for v in self.vuelos if v['id'] == pista_ocupada['vuelo_id']), None)
                if vuelo:
                    vuelo['estado'] = "COMPLETADO"
                    vuelo['minuto_completado'] = self.reloj_virtual
                    self.vuelos_completados.append(vuelo)
                    self.registrar_evento("COMPLETADO", 
                                        f"Vuelo {vuelo['id']} - Pista {pista_ocupada['id_pista']}")
                
                pistas_a_liberar.append(pista_ocupada)
                self.pistas_ocupadas.remove(pista_ocupada)
    
    def asignar_pistas(self):
        """Asigna pistas disponibles a vuelos"""
        pistas_disponibles = [p for p in self.pistas 
                            if p['habilitada'] and 
                            p['id_pista'] not in [po['id_pista'] for po in self.pistas_ocupadas]]
        
        for pista in pistas_disponibles:
            vuelo = self.seleccionar_proximo_vuelo()
            if vuelo:
                self.asignar_pista_a_vuelo(vuelo, pista)

    def seleccionar_proximo_vuelo(self):
        """Selecciona el próximo vuelo según prioridad"""
        # Combinar y filtrar vuelos en cola
        todos_vuelos_en_cola = [v for v in self.flujo_aterrizaje + self.flujo_despegue 
                               if v['estado'] == 'EN_COLA']
        
        if not todos_vuelos_en_cola:
            return None
        
        # Ordenar por prioridad (emergencias primero)
        vuelos_prioridad_2 = [v for v in todos_vuelos_en_cola if v['prioridad'] == 2]
        vuelos_prioridad_1 = [v for v in todos_vuelos_en_cola if v['prioridad'] == 1]
        vuelos_prioridad_0 = [v for v in todos_vuelos_en_cola if v['prioridad'] == 0]
        
        # Procesar emergencias primero (prioridad 2)
        if vuelos_prioridad_2:
            # Para emergencias: aterrizajes con menos combustible primero
            aterrizajes_emergencia = [v for v in vuelos_prioridad_2 if v['tipo'] == "ATERRIZAJE"]
            despegues_emergencia = [v for v in vuelos_prioridad_2 if v['tipo'] == "DESPEGUE"]
            
            if aterrizajes_emergencia:
                aterrizajes_emergencia.sort(key=lambda x: x['combustible'])
                return aterrizajes_emergencia[0]
            elif despegues_emergencia:
                despegues_emergencia.sort(key=lambda x: x['etd'])
                return despegues_emergencia[0]
        
        # Combinar prioridad 1 y 0
        candidatos = vuelos_prioridad_1 + vuelos_prioridad_0
        
        if candidatos:
            # Ordenar por tipo (aterrizaje primero) y luego por tiempo de espera
            candidatos.sort(key=lambda x: (
                0 if x['tipo'] == 'ATERRIZAJE' else 1,  # Aterrizajes primero
                x['eta'] if x['tipo'] == 'ATERRIZAJE' else x['etd']  # Menor ETA/ETD primero
            ))
            return candidatos[0]
        
        return None

    def asignar_pista_a_vuelo(self, vuelo: Dict, pista: Dict):
        """Asigna una pista a un vuelo"""
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
                            f"Vuelo {vuelo['id']} - Pista {pista['id_pista']} ({vuelo['tipo']})")

    def registrar_evento(self, tipo: str, mensaje: str):
        """Registra un evento en el log"""
        evento = f"[Min {self.reloj_virtual:03d}] {tipo:12} {mensaje}"
        self.eventos_log.append(evento)
        
        # Guardar en archivo
        with open("eventos.log", "a", encoding="utf-8") as f:
            f.write(evento + "\n")

    def actualizar_interfaz(self):
        """Actualiza toda la interfaz gráfica"""
        try:
            # Actualizar reloj principal
            self.reloj_label.config(text=f"⏰ MINUTO SIMULADO: {self.reloj_virtual}")
            
            # Actualizar métricas
            estado = self.obtener_estado_actual()
            
            self.metricas['aterrizaje_cola'].config(text=str(estado['vuelos_en_cola_aterrizaje']))
            self.metricas['despegue_cola'].config(text=str(estado['vuelos_en_cola_despegue']))
            self.metricas['asignados'].config(text=str(estado['vuelos_asignados']))
            self.metricas['completados'].config(text=str(estado['vuelos_completados']))
            self.metricas['pistas_ocupadas'].config(text=f"{estado['pistas_ocupadas']}/{estado['pistas_totales']}")
            
            # Contar emergencias
            emergencias = len([v for v in estado['flujo_aterrizaje'] + estado['flujo_despegue'] 
                             if v['prioridad'] == 2 and v['estado'] == 'EN_COLA'])
            self.metricas['emergencias'].config(text=str(emergencias))
            
            # Redibujar el aeropuerto con aviones
            self.dibujar_aeropuerto()
            
            # Actualizar árboles de vuelos
            self.actualizar_arbol_vuelos()
            
            # Actualizar log
            self.actualizar_log()
            
        except Exception as e:
            print(f"Error actualizando interfaz: {e}")
    
    def actualizar_arbol_vuelos(self):
        """Actualiza los árboles de vuelos en cola"""
        try:
            # Limpiar árboles
            for item in self.aterrizaje_tree.get_children():
                self.aterrizaje_tree.delete(item)
            for item in self.despegue_tree.get_children():
                self.despegue_tree.delete(item)
            
            # Añadir vuelos de aterrizaje
            for vuelo in self.flujo_aterrizaje:
                if vuelo['estado'] == 'EN_COLA':
                    prioridad_text = {0: 'Normal', 1: 'Alta', 2: 'EMERGENCIA'}[vuelo['prioridad']]
                    estado_text = 'En Espera'
                    tags = ('emergencia',) if vuelo['prioridad'] == 2 else ('normal',)
                    if vuelo['combustible'] <= 5:
                        tags = ('emergencia',)
                    
                    self.aterrizaje_tree.insert('', 'end', values=(
                        vuelo['id'], 
                        f"{vuelo['combustible']} min", 
                        prioridad_text,
                        vuelo['eta'],
                        estado_text
                    ), tags=tags)
            
            # Añadir vuelos de despegue
            for vuelo in self.flujo_despegue:
                if vuelo['estado'] == 'EN_COLA':
                    prioridad_text = {0: 'Normal', 1: 'Alta', 2: 'EMERGENCIA'}[vuelo['prioridad']]
                    estado_text = 'En Espera'
                    tags = ('emergencia',) if vuelo['prioridad'] == 2 else ('normal',)
                    
                    self.despegue_tree.insert('', 'end', values=(
                        vuelo['id'], 
                        vuelo['etd'], 
                        prioridad_text,
                        estado_text
                    ), tags=tags)
            
            # Configurar colores para emergencias
            self.aterrizaje_tree.tag_configure('emergencia', background='#ffcccc')
            self.despegue_tree.tag_configure('emergencia', background='#ffcccc')
            
        except Exception as e:
            print(f"Error actualizando árboles: {e}")
    
    def actualizar_log(self):
        """Actualiza el área de log"""
        try:
            self.log_text.delete(1.0, tk.END)
            eventos_recientes = self.eventos_log[-20:]  # Últimos 20 eventos
            for evento in eventos_recientes:
                # Color coding basado en tipo de evento
                if "EMERGENCIA" in evento or "CANCELADO" in evento:
                    self.log_text.insert(tk.END, evento + '\n', 'alerta')
                elif "ASIGNACION" in evento or "COMPLETADO" in evento:
                    self.log_text.insert(tk.END, evento + '\n', 'exito')
                else:
                    self.log_text.insert(tk.END, evento + '\n')
            
            self.log_text.see(tk.END)
            
            # Configurar tags para colores
            self.log_text.tag_configure('alerta', foreground='#ff4444')
            self.log_text.tag_configure('exito', foreground='#00ff88')
            
        except Exception as e:
            print(f"Error actualizando log: {e}")
    
    def obtener_estado_actual(self):
        """Retorna el estado actual del sistema"""
        return {
            'reloj': self.reloj_virtual,
            'vuelos_en_cola_aterrizaje': len([v for v in self.flujo_aterrizaje if v['estado'] == 'EN_COLA']),
            'vuelos_en_cola_despegue': len([v for v in self.flujo_despegue if v['estado'] == 'EN_COLA']),
            'vuelos_asignados': len([v for v in self.vuelos if v['estado'] == 'ASIGNADO']),
            'vuelos_completados': len(self.vuelos_completados),
            'pistas_ocupadas': len(self.pistas_ocupadas),
            'pistas_totales': len(self.pistas),
            'detalle_pistas': self.pistas_ocupadas
        }
    
    def detener_simulacion(self):
        """Detiene la simulación"""
        self.en_ejecucion = False
        self.btn_iniciar.config(state='normal', bg='#27ae60')
        self.btn_pausar.config(state='disabled', bg='#7f8c8d')
        self.registrar_evento("SISTEMA", "Simulación PAUSADA")
    
    def generar_informe(self):
        """Genera el informe final"""
        try:
            with open("informe.log", "w", encoding="utf-8") as f:
                f.write("📊 INFORME DETALLADO - SISTEMA DE CONTROL AÉREO\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"⏰ Tiempo total simulado: {self.reloj_virtual} minutos\n")
                f.write(f"✈️  Vuelos totales procesados: {len(self.vuelos_completados)}/{len(self.vuelos)}\n")
                
                # Estadísticas de vuelos
                aterrizajes_completados = len([v for v in self.vuelos_completados if v['tipo'] == 'ATERRIZAJE'])
                despegues_completados = len([v for v in self.vuelos_completados if v['tipo'] == 'DESPEGUE'])
                f.write(f"🛬 Aterrizajes completados: {aterrizajes_completados}\n")
                f.write(f"🛫 Despegues completados: {despegues_completados}\n")
                
                # Tiempos de espera
                if self.vuelos_completados:
                    tiempos_espera = [v['minuto_asignacion'] - (v['eta'] if v['tipo'] == 'ATERRIZAJE' else v['etd']) 
                                    for v in self.vuelos_completados]
                    tiempo_medio = sum(tiempos_espera) / len(tiempos_espera)
                    f.write(f"⏱️  Tiempo medio de espera: {tiempo_medio:.1f} minutos\n")
                
                # Uso de pistas
                f.write(f"\n🛣️  USO DE PISTAS:\n")
                for pista in self.pistas:
                    count = len([po for po in self.pistas_ocupadas if po['id_pista'] == pista['id_pista']])
                    f.write(f"   - Pista {pista['id_pista']} ({pista['categoria']}): {count} operaciones\n")
                
                # Emergencias
                emergencias = len([v for v in self.vuelos_completados if v['prioridad'] == 2])
                f.write(f"\n🚨 Emergencias gestionadas: {emergencias}\n")
                
                # Detalle de vuelos completados
                f.write(f"\n📋 DETALLE DE OPERACIONES COMPLETADAS:\n")
                for vuelo in self.vuelos_completados:
                    tipo_extra = " (EMERGENCIA)" if vuelo['prioridad'] == 2 else ""
                    tiempo_espera = vuelo['minuto_asignacion'] - (vuelo['eta'] if vuelo['tipo'] == 'ATERRIZAJE' else vuelo['etd'])
                    f.write(f"   • {vuelo['id']} ({vuelo['tipo']}{tipo_extra}) | "
                           f"Espera: {tiempo_espera}min | "
                           f"Operación: {vuelo['minuto_asignacion']}-{vuelo['minuto_completado']}\n")
            
            messagebox.showinfo("Informe Generado", 
                              "📊 El informe detallado se ha guardado en 'informe.log'")
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error generando informe: {e}")
    
    def reiniciar_sistema(self):
        """Reinicia el sistema completo"""
        self.detener_simulacion()
        time.sleep(0.5)  # Esperar a que el hilo se detenga
        
        # Reiniciar variables
        self.reloj_virtual = 0
        self.vuelos = []
        self.pistas_ocupadas = []
        self.flujo_aterrizaje = []
        self.flujo_despegue = []
        self.vuelos_completados = []
        self.eventos_log = []
        self.aviones_animados = {}
        
        # Recargar datos
        self.cargar_datos_iniciales()
        
        # Reiniciar interfaz
        self.actualizar_interfaz()
        
        # Reiniciar botones
        self.btn_iniciar.config(state='normal', bg='#27ae60')
        self.btn_pausar.config(state='normal', bg='#e67e22')
        
        messagebox.showinfo("Sistema Reiniciado", "🔄 Sistema reiniciado correctamente")
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error ejecutando aplicación: {e}")

# Ejecutar la aplicación
if __name__ == "__main__":
    print("🚀 Iniciando Sistema de Control de Tráfico Aéreo...")
    app = SistemaAeropuertoMejorado()
    app.ejecutar()