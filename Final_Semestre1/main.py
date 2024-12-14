import mysql.connector
import tkinter as tk
from tkinter import ttk, messagebox
from tabulate import tabulate

class DatabaseConnector:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            print("Conectado a la base de datos")
        except mysql.connector.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            messagebox.showerror("Error de conexión", f"Error al conectar a la base de datos: {e}")

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Conexión cerrada")

    def display_results(self, results):
        self.result_text.delete(1.0, tk.END)
        for headers, rows in results:
            table = tabulate(rows, headers=headers, tablefmt="grid")
            self.result_text.insert(tk.END, table + "\n\n")

    def execute_procedure(self, procedure_name, *args):
        try:
            # Llamar al procedimiento almacenado
            self.cursor.callproc(procedure_name, args)
            results = []
            # Obtener los resultados del procedimiento
            for result in self.cursor.stored_results():
                rows = result.fetchall()
                if rows:
                    headers = [i[0] for i in result.description]  # Obtener los encabezados de columna
                    results.append((headers, rows))  # Añadir los resultados a la lista
            self.connection.commit()  # Confirmar los cambios
            return results
        except mysql.connector.Error as e:
            self.connection.rollback()  # Hacer rollback en caso de error
            print(f"Error al ejecutar el procedimiento {procedure_name}: {e}")
            messagebox.showerror("Error", f"Error al ejecutar el procedimiento {procedure_name}: {e}")
            return None

class ClientApp(tk.Tk):
    def __init__(self, db_connector):
        super().__init__()
        self.db_connector = db_connector
        self.title("Gestión de Clientes")
        self.geometry("900x700")
        self.create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Campos de entrada
        self.fields = ['ClienteID', 'Nombre', 'Apellido', 'Email', 'Telefono', 'Direccion']
        self.entries = {}

        for i, field in enumerate(self.fields):
            ttk.Label(main_frame, text=field).grid(row=i, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(main_frame, width=50)
            entry.grid(row=i, column=1, sticky=tk.W, padx=5, pady=2)
            self.entries[field] = entry

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(self.fields), column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Buscar", command=self.search_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Insertar", command=self.insert_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Actualizar", command=self.update_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Eliminar", command=self.delete_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Mostrar Todos", command=self.show_all_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpiar", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        # Área de resultados
        self.result_text = tk.Text(main_frame, height=20, width=80)
        self.result_text.grid(row=len(self.fields)+1, column=0, columnspan=2, pady=10)

    def search_client(self):
        client_id = self.entries['ClienteID'].get()
        if not client_id:
            messagebox.showwarning("Advertencia", "Por favor, ingrese un ID de cliente")
            return

        results = self.db_connector.execute_procedure('BuscarCliente', client_id)
        if results:
            self.display_results(results)
        else:
            messagebox.showinfo("Información", "No se encontró el cliente")

    def insert_client(self):
        values = [self.entries[field].get() for field in self.fields[1:]]
        results = self.db_connector.execute_procedure('RegistrarCliente', *values)
        if results is not None:
            messagebox.showinfo("Éxito", "Cliente insertado correctamente")
            self.clear_fields()
            self.show_all_clients()

    def update_client(self):
        values = [self.entries[field].get() for field in self.fields]
        results = self.db_connector.execute_procedure('ActualizarCliente', *values)
        if results is not None:
            messagebox.showinfo("Éxito", "Cliente actualizado correctamente")
            self.show_all_clients()

    def delete_client(self):
        client_id = self.entries['ClienteID'].get()
        if not client_id:
            messagebox.showwarning("Advertencia", "Por favor, ingrese un ID de cliente")
            return

        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar este cliente?"):
            results = self.db_connector.execute_procedure('EliminarCliente', client_id)
            if results is not None:
                messagebox.showinfo("Éxito", "Cliente eliminado correctamente")
                self.clear_fields()
                self.show_all_clients()


    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)

    def show_all_clients(self):
        results = self.db_connector.execute_procedure('MostrarTodosClientes	')  # Llamada al procedimiento
        if results:
            self.display_results(results)  # Mostrar resultados

    def display_results(self, results):
        self.result_text.delete(1.0, tk.END)
        for headers, rows in results:
            table = tabulate(rows, headers=headers, tablefmt="grid")  # Formatear la tabla
            self.result_text.insert(tk.END, table + "\n\n")

    def on_close(self):
        self.db_connector.disconnect()
        self.quit()

# Configuración de la base de datos
user = 'root'
password = ''
host = 'localhost'
database = 'GestionClientesDB'

db_connector = DatabaseConnector(host, user, password, database)
db_connector.connect()

app = ClientApp(db_connector)
app.mainloop()

