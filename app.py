from flask import Flask, render_template
from flask_mysqldb import MySQL

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

if __name__ == '__main__':
    app.run(debug=True)