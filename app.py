from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
from datetime import date
import openpyxl
from io import BytesIO
from flask import send_file

app = Flask(__name__)

# Configuracion de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'DavidSantiago2005**'
app.config['MYSQL_DB'] = 'asisttrack'

mysql = MySQL(app)

@app.route('/')
def inicio():
    return redirect('/login')

@app.route('/empleados')
def empleados():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM empleados")
    empleados = cur.fetchall()
    cur.close()
    return render_template('empleados.html', empleados=empleados)

@app.route('/agregar_empleado', methods=['GET', 'POST'])
def agregar_empleado():
    if request.method == 'POST':
        nombre = request.form['nombre']
        cedula = request.form['cedula']
        cargo = request.form['cargo']
        valor_dia = request.form['valor_dia']
        numero_emergencia = request.form['numero_emergencia']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO empleados (nombre, cedula, cargo, valor_dia, numero_emergencia) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, cedula, cargo, valor_dia, numero_emergencia))
        mysql.connection.commit()
        cur.close()
        return redirect('/empleados')
    return render_template('agregar_empleado.html')

@app.route('/asistencia', methods=['GET', 'POST'])
def asistencia():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM empleados WHERE activo = TRUE")
    empleados = cur.fetchall()
    cur.close()
    
    if request.method == 'POST':
        fecha_hoy = date.today()
        cur = mysql.connection.cursor()
        for empleado in empleados:
            estado = request.form.get(f'asistencia_{empleado[0]}')
            cur.execute("INSERT INTO asistencia (empleado_id, fecha, estado) VALUES (%s, %s, %s)",
                       (empleado[0], fecha_hoy, estado))
        mysql.connection.commit()
        cur.close()
        return redirect('/asistencia')
    
    return render_template('asistencia.html', empleados=empleados, fecha=date.today())

@app.route('/reporte')
def reporte():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.nombre, e.cargo, a.fecha, a.estado
        FROM asistencia a
        JOIN empleados e ON a.empleado_id = e.id
        ORDER BY a.fecha, e.nombre
    """)
    datos = cur.fetchall()
    cur.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Asistencia"

    ws.append(["Nombre", "Cargo", "Fecha", "Estado"])

    for fila in datos:
        ws.append([fila[0], fila[1], str(fila[2]), fila[3]])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return send_file(output,
                     download_name="reporte_asistencia.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE usuario=%s AND contrasena=%s", (usuario, contrasena))
        user = cur.fetchone()
        cur.close()
        if user:
            return redirect('/dashboard') ###cambio de redirección de login
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/reporte_pago')
def reporte_pago():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.nombre, e.cargo,
               SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) as dias_trabajados,
               e.valor_dia,
               SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) * e.valor_dia as total
        FROM empleados e
        LEFT JOIN asistencia a ON e.id = a.empleado_id
        GROUP BY e.id, e.nombre, e.cargo, e.valor_dia
    """)
    pagos = cur.fetchall()
    cur.close()
    return render_template('reporte_pago.html', pagos=pagos)

@app.route('/reporte_pago_excel')
def reporte_pago_excel():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT e.nombre, e.cargo,
               SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) as dias_trabajados,
               e.valor_dia,
               SUM(CASE WHEN a.estado = 'presente' THEN 1 ELSE 0 END) * e.valor_dia as total
        FROM empleados e
        LEFT JOIN asistencia a ON e.id = a.empleado_id
        GROUP BY e.id, e.nombre, e.cargo, e.valor_dia
    """)
    pagos = cur.fetchall()
    cur.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Pago Quincenal"
    ws.append(["Nombre", "Cargo", "Dias Trabajados", "Valor Dia", "Total a Pagar"])
    for p in pagos:
        ws.append([p[0], p[1], p[2], float(p[3]), float(p[4])])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output,
                     download_name="pago_quincenal.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route('/dashboard')
def dashboard():
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT COUNT(*) FROM empleados WHERE activo = TRUE")
    total_empleados = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM asistencia WHERE fecha = CURDATE() AND estado = 'presente'")
    presentes_hoy = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM asistencia WHERE fecha = CURDATE() AND estado = 'ausente'")
    ausentes_hoy = cur.fetchone()[0]
    
    cur.execute("""
        SELECT SUM(CASE WHEN a.estado = 'presente' THEN e.valor_dia ELSE 0 END)
        FROM asistencia a
        JOIN empleados e ON a.empleado_id = e.id
    """)
    total_pagar = cur.fetchone()[0] or 0
    cur.close()
    
    return render_template('dashboard.html',
                         total_empleados=total_empleados,
                         presentes_hoy=presentes_hoy,
                         ausentes_hoy=ausentes_hoy,
                         total_pagar=total_pagar)

if __name__ == '__main__':
    app.run(debug=True)