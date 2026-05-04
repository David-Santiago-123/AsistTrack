from flask import Flask, render_template, request, redirect
from flask_mysqldb import MySQL
from datetime import date

app = Flask(__name__)

# Configuracion de la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'DavidSantiago2005**'
app.config['MYSQL_DB'] = 'asisttrack'

mysql = MySQL(app)

@app.route('/')
def inicio():
    return render_template('login.html')

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

if __name__ == '__main__':
    app.run(debug=True)