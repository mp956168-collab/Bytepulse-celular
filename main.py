from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os
import threading
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.progressbar import MDProgressBar
from kivy.uix.image import Image
from plyer import notification
from fpdf import FPDF

DB_FILE = "usuarios_data.json"
LOGO_FILE = "bytepulse-logo.png"

class AppCelular(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Blue"
        
        self.sm = MDScreenManager()
        
        # Pantalla Principal / Metas y Registro[cite: 2]
        self.screen_principal = MDScreen(name="principal")
        self.setup_pantalla_principal()
        
        # Pantalla Dashboard y Gráficas[cite: 2]
        self.screen_dashboard = MDScreen(name="dashboard")
        self.setup_pantalla_dashboard()
        
        self.sm.add_widget(self.screen_principal)
        self.sm.add_widget(self.screen_dashboard)
        
        # Iniciar el sistema de notificaciones automáticas (con logo de Bytepulse)
        self.iniciar_sistema_notificaciones_automaticas()
        
        return self.sm

    def setup_pantalla_principal(self):
        scroll = MDScrollView()
        layout = MDBoxLayout(orientation="vertical", spacing="12dp", padding="16dp", size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        if os.path.exists(LOGO_FILE):
            logo = Image(source=LOGO_FILE, size_hint=(None, None), size=("70dp", "70dp"), pos_hint={"center_x": 0.5})
            layout.add_widget(logo)
            
        layout.add_widget(MDLabel(text="Bytepulse - Finanzas y Metas", halign="center", font_style="H5", size_hint_y=None, height="35dp"))
        
        self.nombre_meta = MDTextField(hint_text="Nombre de la meta", size_hint_y=None, height="48dp")
        self.monto_meta = MDTextField(hint_text="Monto total deseado ($)", input_filter="float", size_hint_y=None, height="48dp")
        self.fecha_inicio = MDTextField(hint_text="Fecha inicio (YYYY-MM-DD)", text=datetime.now().strftime("%Y-%m-%d"), size_hint_y=None, height="48dp")
        self.fecha_fin = MDTextField(hint_text="Fecha finalización (YYYY-MM-DD)", size_hint_y=None, height="48dp")
        
        layout.add_widget(self.nombre_meta)
        layout.add_widget(self.monto_meta)
        layout.add_widget(self.fecha_inicio)
        layout.add_widget(self.fecha_fin)
        
        btn_calcular = MDRaisedButton(text="Guardar y Calcular Ahorro", pos_hint={"center_x": 0.5}, on_release=self.calcular_meta)
        layout.add_widget(btn_calcular)
        
        self.lbl_resultados = MDLabel(text="Ingrese su meta para ver el desglose diario, semanal y mensual.", halign="center", size_hint_y=None, height="60dp")
        layout.add_widget(self.lbl_resultados)
        
        layout.add_widget(MDLabel(text="Progreso de Ahorro:", size_hint_y=None, height="20dp"))
        self.progress_bar = MDProgressBar(value=0, size_hint_y=None, height="10dp")
        layout.add_widget(self.progress_bar)
        
        # Registro diario / Checklist con ingreso de valor[cite: 2]
        layout.add_widget(MDLabel(text="Registro de Ahorro Diario o Gasto", halign="center", font_style="Subtitle1", size_hint_y=None, height="30dp"))
        self.input_ahorro_hoy = MDTextField(hint_text="Valor ahorrado hoy ($)", input_filter="float", size_hint_y=None, height="48dp")
        layout.add_widget(self.input_ahorro_hoy)
        
        btn_registrar_hoy = MDRaisedButton(text="Registrar Ahorro de Hoy", pos_hint={"center_x": 0.5}, on_release=self.registrar_ahorro_diario)
        layout.add_widget(btn_registrar_hoy)
        
        btn_ir_dashboard = MDRaisedButton(text="Ver Dashboard y Gráficas", pos_hint={"center_x": 0.5}, on_release=lambda x: setattr(self.sm, 'current', 'dashboard'))
        layout.add_widget(btn_ir_dashboard)
        
        scroll.add_widget(layout)
        self.screen_principal.add_widget(scroll)
        
        # Variables de control
        self.meta_total = 0.0
        self.ahorro_acumulado = 0.0
        self.historial_diario = []

    def setup_pantalla_dashboard(self):
        scroll = MDScrollView()
        layout = MDBoxLayout(orientation="vertical", spacing="15dp", padding="16dp", size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        
        layout.add_widget(MDLabel(text="Dashboard y Análisis Financiero", halign="center", font_style="H5", size_hint_y=None, height="35dp"))
        
        self.lbl_estado_dash = MDLabel(text="Aún no hay datos suficientes para mostrar las gráficas.", halign="center", size_hint_y=None, height="40dp")
        layout.add_widget(self.lbl_estado_dash)
        
        btn_generar_graficas = MDRaisedButton(text="Generar Gráficas y Descargar PNG", pos_hint={"center_x": 0.5}, on_release=self.generar_y_guardar_graficas)
        layout.add_widget(btn_generar_graficas)
        
        btn_generar_pdf = MDRaisedButton(text="Exportar Reporte PDF (con Logo)", pos_hint={"center_x": 0.5}, on_release=self.exportar_reporte_pdf)
        layout.add_widget(btn_generar_pdf)
        
        btn_volver = MDRaisedButton(text="Volver a Metas", pos_hint={"center_x": 0.5}, on_release=lambda x: setattr(self.sm, 'current', 'principal'))
        layout.add_widget(btn_volver)
        
        scroll.add_widget(layout)
        self.screen_dashboard.add_widget(scroll)

    def calcular_meta(self, instance):
        try:
            self.meta_total = float(self.monto_meta.text)
            f_inicio = datetime.strptime(self.fecha_inicio.text, "%Y-%m-%d")
            f_fin = datetime.strptime(self.fecha_fin.text, "%Y-%m-%d")
            
            dias = (f_fin - f_inicio).days
            if dias <= 0:
                self.lbl_resultados.text = "La fecha final debe ser mayor a la inicial."
                return
            
            diario = self.meta_total / dias
            semanal = diario * 7
            mensual = diario * 30
            
            self.lbl_resultados.text = (
                f"Meta: {self.nombre_meta.text} | Total: ${self.meta_total}\n"
                f"Cuota Sugerida -> Diario: ${diario:.2f} | Semanal: ${semanal:.2f} | Mensual: ${mensual:.2f}"
            )
        except Exception as e:
            self.lbl_resultados.text = "Error en los datos ingresados. Verifique los formatos."

    def registrar_ahorro_diario(self, instance):
        try:
            valor = float(self.input_ahorro_hoy.text)
            self.ahorro_acumulado += valor
            self.historial_diario.append({"fecha": datetime.now().strftime("%Y-%m-%d"), "monto": valor})
            
            if self.meta_total > 0:
                porcentaje = (self.ahorro_acumulado / self.meta_total) * 100
                self.progress_bar.value = min(100, porcentaje)
            
            self.input_ahorro_hoy.text = ""
            self.lbl_resultados.text = f"¡Ahorro registrado! Acumulado actual: ${self.ahorro_acumulado:.2f}"
        except:
            self.lbl_resultados.text = "Ingrese un valor numérico válido para el ahorro de hoy."

    def generar_y_guardar_graficas(self, instance):
        if not self.historial_diario:
            self.lbl_estado_dash.text = "No hay registros diarios para graficar."
            return
            
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(6, 12))
        
        # 1. Gráfica de pastel (Progreso vs Falta)[cite: 2]
        faltante = max(0, self.meta_total - self.ahorro_acumulado)
        ax1.pie([self.ahorro_acumulado, faltante], labels=['Ahorrado', 'Faltante'], autopct='%1.1f%%', colors=['#2196F3', '#E0E0E0'])
        ax1.set_title("Progreso General de la Meta")
        
        # 2. Gráfica de barras (Ahorro acumulado vs Meta)[cite: 2]
        ax2.bar(['Ahorrado', 'Meta Total'], [self.ahorro_acumulado, self.meta_total], color=['#4CAF50', '#FF9800'])
        ax2.set_title("Comparativa de Ahorro")
        
        # 3. Gráfica lineal del checklist / historial diario[cite: 2]
        fechas = [h['fecha'] for h in self.historial_diario]
        montos = [h['monto'] for h in self.historial_diario]
        ax3.plot(fechas, montos, marker='o', color='#3F51B5', linestyle='-')
        ax3.set_title("Comportamiento Diario del Ahorro")
        ax3.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        output_png = "dashboard_bytepulse.png"
        plt.savefig(output_png)
        plt.close()
        
        self.lbl_estado_dash.text = f"¡Gráficas generadas y guardadas como {output_png}!"

    def exportar_reporte_pdf(self, instance):
        pdf = FPDF()
        pdf.add_page()
        
        # Cabecera con logo si existe[cite: 2]
        if os.path.exists(LOGO_FILE):
            pdf.image(LOGO_FILE, x=10, y=8, w=25)
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "Bytepulse - Reporte de Metas Financieras", 0, 1, 'C')
        pdf.ln(15)
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Meta: {self.nombre_meta.text or 'General'}", 0, 1)
        pdf.cell(0, 10, f"Monto Total Objetivo: ${self.meta_total}", 0, 1)
        pdf.cell(0, 10, f"Ahorro Total Acumulado: ${self.ahorro_acumulado}", 0, 1)
        pdf.ln(10)
        
        # Tabla detallada del checklist diario[cite: 2]
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(40, 10, "Fecha", 1, 0, 'C')
        pdf.cell(50, 10, "Monto Aportado", 1, 1, 'C')
        
        pdf.set_font("Arial", '', 11)
        for item in self.historial_diario:
            pdf.cell(40, 10, str(item['fecha']), 1, 0, 'C')
            pdf.cell(50, 10, f"${item['monto']}", 1, 1, 'C')
            
        output_pdf = "reporte_bytepulse.pdf"
        pdf.output(output_pdf)
        self.lbl_estado_dash.text = f"Reporte PDF exportado con éxito como {output_pdf}."

    def iniciar_sistema_notificaciones_automaticas(self):
        def bucle_notificaciones():
            while True:
                ahora = datetime.now(ZoneInfo("America/Bogota"))
                hora = ahora.hour
                minuto = ahora.minute
                
                # Envío programado a las 8:00, 14:00 y 20:00
                if minuto == 0:
                    if hora == 8:
                        self.enviar_notificacion("Bytepulse - Mañana", "¡Buenos días! Organiza tus finanzas y planifica tu ahorro de hoy.")
                    elif hora == 14:
                        self.enviar_notificacion("Bytepulse - Tarde", "Recordatorio de la tarde: ¿Has realizado algún gasto o ahorro hoy? Regístralo.")
                    elif hora == 20:
                        self.enviar_notificacion("Bytepulse - Noche", "Cierre del día: Ingresa el valor ahorrado para mantener al día tu meta.")
                
                time.sleep(60)

        hilo_notif = threading.Thread(target=bucle_notificaciones, daemon=True)
        hilo_notif.start()

    def enviar_notificacion(self, titulo, mensaje):
        try:
            # Se adjunta el logo corporativo de Bytepulse a la notificación del sistema
            icon_path = LOGO_FILE if os.path.exists(LOGO_FILE) else None
            notification.notify(
                title=titulo,
                message=mensaje,
                app_icon=icon_path,
                timeout=10
            )
        except Exception as e:
            print("No se pudo enviar la notificación del sistema:", e)

if __name__ == "__main__":
    AppCelular().run()