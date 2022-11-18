############# importar librerias o recursos#####
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
# from flask_cors import CORS, cross_origin
# from flask_cors import CORS

# initializations
app = Flask(__name__)
# CORS(app)


# Mysql Connection
app.config['MYSQL_HOST'] = 'localhost' 
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskcrud'
mysql = MySQL(app)

# settings A partir de ese momento Flask utilizará esta clave para poder cifrar la información de la cookie
app.secret_key = "mysecretkey"


# ruta para consultar todos los registros
@app.route('/getAllasas/<table_name>/<id>', methods=['GET'])
def getAllasas(table_name, id):
    
    cur = mysql.connection.cursor()
    sql = 'SELECT * FROM '+table_name+' where id = {0}'.format(id)
    cur.execute(sql)
    rv = cur.fetchall()
    cur.close()
    payload = []
    content = {}

    if (table_name == 'contacts'):
        for result in rv:
            content = {'id': result[0], 'fullname': result[1], 'phone': result[2], 'email': result[3]}
            payload.append(content)
            content = {}
    elif (table_name == 'paciente'):
        for result in rv:
            content = {'id': result[0], 'nombre_cliente': result[1], 'apellido_cliente': result[2], 'telefono_cliente': result[3], 'ciudad_cliente': result[4]}
            payload.append(content)
            content = {}
            

    return jsonify(payload)


# ruta para consultar por parametro
@app.route('/getAll', methods=['GET'])
def getAll():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM contacts')
    rv = cur.fetchall()
    cur.close()
    payload = []
    content = {}
    for result in rv:
       content = {'id': result[0], 'fullname': result[1], 'phone': result[2], 'email': result[3]}
       payload.append(content)
       content = {}
    return jsonify(payload)

#### ruta para crear un registro########
@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        fullname = request.json['fullname']  ## nombre
        phone = request.json['phone']        ## telefono
        email = request.json['email']        ## email
        cur = mysql.connection.cursor()
        tabla = "contacts"
        cur.execute("INSERT INTO "+str(tabla)+" (fullname, phone, email) VALUES (%s,%s,%s)", (fullname, phone, email))
        mysql.connection.commit()
        return jsonify({"informacion":"Registro exitoso"})

######### ruta para actualizar################
@app.route('/update/<id>', methods=['PUT'])
def update_contact(id):
    if(ejemplo):
        fullname = request.json['fullname']
        phone = request.json['phone']
        email = request.json['email']
        cur = mysql.connection.cursor()
        cur.execute("""
                UPDATE contacts
                SET fullname = %s,
                    email = %s,
                    phone = %s
                WHERE id = %s
            """, (fullname, email, phone, id))
        mysql.connection.commit()
        return jsonify({"informacion":"Registro actualizado"})


@app.route('/delete/<id>', methods = ['DELETE'])
def delete_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM contacts WHERE id = %s', (id,))
    mysql.connection.commit()
    return jsonify({"informacion":"Registro eliminado"})

@app.route('/login',methods=['GET'])
def login():
    user = request.json['user']
    password = request.json['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM user WHERE user = %s and password =%s", (user,password))
    ###cur.execute('SELECT * FROM contacts')
    data = cur.fetchall()
    cur.close()
    print("enviado")
   
    if len(data)==0 :
        return jsonify({"data":0})
    else :
        return jsonify({"data":data})

# starting the app
if __name__ == "__main__":
    app.run(port=3000, debug=True)
