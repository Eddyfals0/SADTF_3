"""
Interfaz gráfica del cliente del sistema distribuido
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import socket
import threading
import base64
import os
from datetime import datetime
from typing import Optional, Dict, List

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import COORDINATOR_HOST, COORDINATOR_PORT, GUI_UPDATE_INTERVAL
from common.protocol import MessageType, receive_message, send_message
from common.utils import format_size, combine_blocks_into_file

class DistributedFileSystemGUI:
    """Interfaz gráfica del sistema de archivos distribuido"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Archivos Distribuido - Tolerante a Fallas")
        self.root.geometry("1200x800")
        
        # Conexión con coordinador
        self.coordinator_socket: Optional[socket.socket] = None
        self.connected = False
        
        # Datos
        self.files: Dict[str, Dict] = {}
        self.active_nodes: List[Dict] = []
        self.block_table_data: Optional[Dict] = None
        
        # Crear interfaz
        self.create_widgets()
        
        # Conectar con coordinador
        self.connect_to_coordinator()
        
        # Iniciar actualización periódica
        self.update_data()
    
    def create_widgets(self):
        """Crea los widgets de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Panel izquierdo - Nodos activos
        left_panel = ttk.LabelFrame(main_frame, text="Nodos Activos", padding="10")
        left_panel.grid(row=0, column=0, rowspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)
        
        ttk.Label(left_panel, text="Estado del Sistema", font=("Arial", 10, "bold")).grid(row=0, column=0, pady=(0, 10))
        
        # Treeview para nodos
        nodes_tree = ttk.Treeview(left_panel, columns=("Espacio", "Estado"), show="tree headings", height=10)
        nodes_tree.heading("#0", text="Nodo ID")
        nodes_tree.heading("Espacio", text="Espacio")
        nodes_tree.heading("Estado", text="Estado")
        nodes_tree.column("#0", width=150)
        nodes_tree.column("Espacio", width=100)
        nodes_tree.column("Estado", width=80)
        nodes_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar_nodes = ttk.Scrollbar(left_panel, orient="vertical", command=nodes_tree.yview)
        scrollbar_nodes.grid(row=1, column=1, sticky=(tk.N, tk.S))
        nodes_tree.configure(yscrollcommand=scrollbar_nodes.set)
        
        self.nodes_tree = nodes_tree
        
        # Panel central - Archivos y operaciones
        center_panel = ttk.LabelFrame(main_frame, text="Archivos", padding="10")
        center_panel.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        center_panel.columnconfigure(0, weight=1)
        center_panel.rowconfigure(1, weight=1)
        
        # Botones de operaciones
        buttons_frame = ttk.Frame(center_panel)
        buttons_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(buttons_frame, text="Subir Archivo", command=self.upload_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Descargar", command=self.download_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Eliminar", command=self.delete_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Ver Atributos", command=self.view_file_attributes).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Actualizar", command=self.refresh_files).pack(side=tk.LEFT, padx=5)
        
        # Treeview para archivos
        files_tree = ttk.Treeview(center_panel, columns=("Tamaño", "Bloques", "Fecha"), show="tree headings", height=10)
        files_tree.heading("#0", text="Nombre del Archivo")
        files_tree.heading("Tamaño", text="Tamaño")
        files_tree.heading("Bloques", text="Bloques")
        files_tree.heading("Fecha", text="Fecha Subida")
        files_tree.column("#0", width=250)
        files_tree.column("Tamaño", width=100)
        files_tree.column("Bloques", width=80)
        files_tree.column("Fecha", width=150)
        files_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar_files = ttk.Scrollbar(center_panel, orient="vertical", command=files_tree.yview)
        scrollbar_files.grid(row=1, column=1, sticky=(tk.N, tk.S))
        files_tree.configure(yscrollcommand=scrollbar_files.set)
        
        self.files_tree = files_tree
        
        # Panel derecho - Tabla de bloques
        right_panel = ttk.LabelFrame(main_frame, text="Tabla de Bloques", padding="10")
        right_panel.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        
        ttk.Button(right_panel, text="Actualizar Tabla", command=self.refresh_block_table).grid(row=0, column=0, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Treeview para tabla de bloques
        blocks_tree = ttk.Treeview(right_panel, columns=("Estado", "Archivo", "Nodo", "Réplica"), show="tree headings", height=10)
        blocks_tree.heading("#0", text="Bloque ID")
        blocks_tree.heading("Estado", text="Estado")
        blocks_tree.heading("Archivo", text="Archivo")
        blocks_tree.heading("Nodo", text="Nodo")
        blocks_tree.heading("Réplica", text="Nodo Réplica")
        blocks_tree.column("#0", width=80)
        blocks_tree.column("Estado", width=80)
        blocks_tree.column("Archivo", width=150)
        blocks_tree.column("Nodo", width=100)
        blocks_tree.column("Réplica", width=100)
        blocks_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar_blocks = ttk.Scrollbar(right_panel, orient="vertical", command=blocks_tree.yview)
        scrollbar_blocks.grid(row=1, column=1, sticky=(tk.N, tk.S))
        blocks_tree.configure(yscrollcommand=scrollbar_blocks.set)
        
        self.blocks_tree = blocks_tree
        
        # Consola en la parte inferior
        console_frame = ttk.LabelFrame(main_frame, text="Consola", padding="10")
        console_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        
        self.console = scrolledtext.ScrolledText(console_frame, height=8, wrap=tk.WORD)
        self.console.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.console.config(state=tk.DISABLED)
        
        # Barra de estado
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Desconectado", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
    
    def log(self, message: str):
        """Añade mensaje a la consola"""
        self.console.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console.see(tk.END)
        self.console.config(state=tk.DISABLED)
    
    def connect_to_coordinator(self):
        """Conecta con el coordinador"""
        try:
            self.coordinator_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.coordinator_socket.connect((COORDINATOR_HOST, COORDINATOR_PORT))
            self.connected = True
            self.status_label.config(text="Conectado", foreground="green")
            self.log("Conectado al coordinador")
        except Exception as e:
            self.connected = False
            self.status_label.config(text="Desconectado", foreground="red")
            self.log(f"Error conectando al coordinador: {e}")
            messagebox.showerror("Error", f"No se pudo conectar al coordinador: {e}")
    
    def send_request(self, msg_type: MessageType, data: dict = None) -> Optional[dict]:
        """Envía una solicitud al coordinador y espera respuesta"""
        if not self.connected or not self.coordinator_socket:
            messagebox.showerror("Error", "No conectado al coordinador")
            return None
        
        try:
            send_message(self.coordinator_socket, msg_type, data)
            response = receive_message(self.coordinator_socket)
            return response
        except Exception as e:
            self.log(f"Error en comunicación: {e}")
            self.connected = False
            self.status_label.config(text="Desconectado", foreground="red")
            return None
    
    def upload_file(self):
        """Sube un archivo al sistema"""
        file_path = filedialog.askopenfilename(title="Seleccionar archivo para subir")
        if not file_path:
            return
        
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            self.log(f"Subiendo archivo: {filename} ({format_size(file_size)})")
            
            # Leer archivo y codificar en base64
            with open(file_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Enviar solicitud
            response = self.send_request(MessageType.UPLOAD_FILE, {
                "filename": filename,
                "size": file_size,
                "file_data": file_data
            })
            
            if response and response.get("type") == MessageType.UPLOAD_RESPONSE.value:
                data = response.get("data", {})
                if data.get("success"):
                    self.log(f"Archivo subido exitosamente: {filename}")
                    messagebox.showinfo("Éxito", f"Archivo {filename} subido exitosamente")
                    self.refresh_files()
                else:
                    error_msg = data.get("message", "Error desconocido")
                    self.log(f"Error subiendo archivo: {error_msg}")
                    messagebox.showerror("Error", error_msg)
            elif response and response.get("type") == MessageType.ERROR.value:
                error_msg = response.get("data", {}).get("message", "Error desconocido")
                self.log(f"Error: {error_msg}")
                messagebox.showerror("Error", error_msg)
        except Exception as e:
            self.log(f"Error subiendo archivo: {e}")
            messagebox.showerror("Error", f"Error subiendo archivo: {e}")
    
    def download_file(self):
        """Descarga un archivo seleccionado"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un archivo para descargar")
            return
        
        item = self.files_tree.item(selection[0])
        file_id = item.get("tags", [None])[0] if item.get("tags") else None
        
        if not file_id or file_id not in self.files:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        file_info = self.files[file_id]
        filename = file_info["filename"]
        
        # Seleccionar destino
        dest_path = filedialog.asksaveasfilename(
            title="Guardar archivo como",
            initialfile=filename,
            defaultextension=".*"
        )
        
        if not dest_path:
            return
        
        try:
            self.log(f"Descargando archivo: {filename}")
            
            # Solicitar descarga
            response = self.send_request(MessageType.DOWNLOAD_FILE, {
                "file_id": file_id
            })
            
            if response and response.get("type") == MessageType.DOWNLOAD_RESPONSE.value:
                data = response.get("data", {})
                if data.get("success"):
                    blocks_data = data.get("blocks", {})
                    
                    # Combinar bloques
                    blocks = [(int(k), base64.b64decode(v)) for k, v in blocks_data.items()]
                    combine_blocks_into_file(blocks, dest_path)
                    
                    self.log(f"Archivo descargado exitosamente: {filename}")
                    messagebox.showinfo("Éxito", f"Archivo {filename} descargado exitosamente")
                else:
                    error_msg = data.get("message", "Error desconocido")
                    self.log(f"Error descargando archivo: {error_msg}")
                    messagebox.showerror("Error", error_msg)
            else:
                error_msg = response.get("data", {}).get("message", "Error desconocido") if response else "Sin respuesta"
                self.log(f"Error: {error_msg}")
                messagebox.showerror("Error", error_msg)
        except Exception as e:
            self.log(f"Error descargando archivo: {e}")
            messagebox.showerror("Error", f"Error descargando archivo: {e}")
    
    def delete_file(self):
        """Elimina un archivo seleccionado"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un archivo para eliminar")
            return
        
        item = self.files_tree.item(selection[0])
        file_id = item.get("tags", [None])[0] if item.get("tags") else None
        
        if not file_id or file_id not in self.files:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        file_info = self.files[file_id]
        filename = file_info["filename"]
        
        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar {filename}?"):
            return
        
        try:
            self.log(f"Eliminando archivo: {filename}")
            
            response = self.send_request(MessageType.DELETE_FILE, {
                "file_id": file_id
            })
            
            if response and response.get("type") == MessageType.DELETE_RESPONSE.value:
                data = response.get("data", {})
                if data.get("success"):
                    self.log(f"Archivo eliminado exitosamente: {filename}")
                    messagebox.showinfo("Éxito", f"Archivo {filename} eliminado exitosamente")
                    self.refresh_files()
                    self.refresh_block_table()
                else:
                    error_msg = data.get("message", "Error desconocido")
                    self.log(f"Error eliminando archivo: {error_msg}")
                    messagebox.showerror("Error", error_msg)
            else:
                error_msg = response.get("data", {}).get("message", "Error desconocido") if response else "Sin respuesta"
                self.log(f"Error: {error_msg}")
                messagebox.showerror("Error", error_msg)
        except Exception as e:
            self.log(f"Error eliminando archivo: {e}")
            messagebox.showerror("Error", f"Error eliminando archivo: {e}")
    
    def view_file_attributes(self):
        """Muestra los atributos de un archivo"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un archivo para ver sus atributos")
            return
        
        item = self.files_tree.item(selection[0])
        file_id = item.get("tags", [None])[0] if item.get("tags") else None
        
        if not file_id:
            messagebox.showerror("Error", "Archivo no encontrado")
            return
        
        try:
            response = self.send_request(MessageType.GET_FILE_INFO, {
                "file_id": file_id
            })
            
            if response and response.get("type") == MessageType.FILE_INFO.value:
                data = response.get("data", {})
                file_info = data.get("file", {})
                blocks = data.get("blocks", [])
                
                # Crear ventana de atributos
                attr_window = tk.Toplevel(self.root)
                attr_window.title(f"Atributos: {file_info.get('filename', 'N/A')}")
                attr_window.geometry("600x400")
                
                # Información del archivo
                info_frame = ttk.LabelFrame(attr_window, text="Información del Archivo", padding="10")
                info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                info_text = f"""
Nombre: {file_info.get('filename', 'N/A')}
Tamaño: {format_size(file_info.get('size', 0))}
Bloques: {file_info.get('num_blocks', 0)}
Fecha de Subida: {file_info.get('upload_date', 'N/A')}
                """
                
                ttk.Label(info_frame, text=info_text.strip(), justify=tk.LEFT).pack(anchor=tk.W)
                
                # Información de bloques
                blocks_frame = ttk.LabelFrame(attr_window, text="Distribución de Bloques", padding="10")
                blocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                blocks_tree = ttk.Treeview(blocks_frame, columns=("Nodo", "Réplica"), show="tree headings")
                blocks_tree.heading("#0", text="Bloque #")
                blocks_tree.heading("Nodo", text="Nodo Principal")
                blocks_tree.heading("Réplica", text="Nodo Réplica")
                blocks_tree.pack(fill=tk.BOTH, expand=True)
                
                for block in blocks:
                    blocks_tree.insert("", tk.END, text=f"Bloque {block.get('block_number', 'N/A')}",
                                     values=(block.get('node_id', 'N/A'), 
                                            block.get('replica_node_id', 'N/A')))
            else:
                error_msg = response.get("data", {}).get("message", "Error desconocido") if response else "Sin respuesta"
                messagebox.showerror("Error", error_msg)
        except Exception as e:
            messagebox.showerror("Error", f"Error obteniendo atributos: {e}")
    
    def refresh_files(self):
        """Actualiza la lista de archivos"""
        response = self.send_request(MessageType.LIST_FILES)
        
        if response and response.get("type") == MessageType.FILE_LIST.value:
            data = response.get("data", {})
            files_list = data.get("files", [])
            
            # Limpiar treeview
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            # Actualizar datos
            self.files = {}
            for file_info in files_list:
                file_id = file_info.get("file_id")
                self.files[file_id] = file_info
                
                self.files_tree.insert("", tk.END, 
                                      text=file_info.get("filename", "N/A"),
                                      values=(
                                          format_size(file_info.get("size", 0)),
                                          file_info.get("num_blocks", 0),
                                          file_info.get("upload_date", "N/A")[:19] if file_info.get("upload_date") else "N/A"
                                      ),
                                      tags=(file_id,))
    
    def refresh_block_table(self):
        """Actualiza la tabla de bloques"""
        response = self.send_request(MessageType.GET_BLOCK_TABLE)
        
        if response and response.get("type") == MessageType.BLOCK_TABLE_DATA.value:
            data = response.get("data", {})
            table = data.get("table", {})
            self.block_table_data = table
            
            # Limpiar treeview
            for item in self.blocks_tree.get_children():
                self.blocks_tree.delete(item)
            
            # Mostrar información resumida
            blocks = table.get("blocks", [])
            total = table.get("total_blocks", 0)
            free = table.get("free_blocks", 0)
            used = table.get("used_blocks", 0)
            
            # Insertar resumen
            summary = self.blocks_tree.insert("", tk.END, 
                                             text="RESUMEN",
                                             values=(f"Libres: {free}", f"Usados: {used}", f"Total: {total}", ""))
            
            # Insertar bloques (solo los usados para no saturar)
            for block in blocks[:100]:  # Limitar a 100 para rendimiento
                if block.get("status") != "FREE":
                    self.blocks_tree.insert("", tk.END,
                                           text=str(block.get("block_id", "N/A")),
                                           values=(
                                               block.get("status", "N/A"),
                                               block.get("file_id", "N/A")[:20] + "..." if len(block.get("file_id", "")) > 20 else block.get("file_id", "N/A"),
                                               block.get("node_id", "N/A"),
                                               block.get("replica_node_id", "N/A")
                                           ))
    
    def refresh_nodes(self):
        """Actualiza la lista de nodos activos"""
        response = self.send_request(MessageType.GET_ACTIVE_NODES)
        
        if response and response.get("type") == MessageType.ACTIVE_NODES_DATA.value:
            data = response.get("data", {})
            nodes_list = data.get("nodes", [])
            self.active_nodes = nodes_list
            
            # Limpiar treeview
            for item in self.nodes_tree.get_children():
                self.nodes_tree.delete(item)
            
            # Insertar nodos
            for node in nodes_list:
                status = "Activo" if node.get("is_alive") else "Inactivo"
                space = format_size(node.get("shared_space_size", 0))
                
                self.nodes_tree.insert("", tk.END,
                                      text=node.get("node_id", "N/A"),
                                      values=(space, status))
    
    def update_data(self):
        """Actualiza todos los datos periódicamente"""
        if self.connected:
            self.refresh_files()
            self.refresh_nodes()
            self.refresh_block_table()
        
        # Programar próxima actualización
        self.root.after(GUI_UPDATE_INTERVAL, self.update_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = DistributedFileSystemGUI(root)
    root.mainloop()

