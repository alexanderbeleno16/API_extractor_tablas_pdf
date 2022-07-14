#------------ RECURSOS ------------

# pip install MySQL-python
# pip install Flask
# pip install Flask-MySQLdb
# pip install Flask-Cors==1.1.2
# pip install tabulate
# pip install tabula-py
# pip install waitress

from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from tabula import read_pdf 
from tabulate import tabulate 
import numpy as np
import pandas as pd 
import datetime
import sys
from waitress import serve



# from flask_cors import CORS, cross_origin
# from flask_cors import CORS


# initializations
app = Flask(__name__)
# CORS(app)



#------------ BASE DE DATOS ------------
app.config['MYSQL_HOST']        = 'localhost' 
app.config['MYSQL_USER']        = 'db_user'
app.config['MYSQL_PASSWORD']    = 'Lupa-12312423$$**12'
app.config['MYSQL_DB']          = 'db_lupajuridica'
mysql = MySQL(app)


# settings A partir de ese momento Flask utilizará esta clave para poder cifrar la información de la cookie
app.secret_key = "mysecretkey"





#------------ FUNCIONES ------------
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False    
    

def isint(num):
    try:
        int(num)
        return True
    except ValueError:
        return False   


def armar_data_estado(dataframe):
    # CONVERTIR DATAFRAME A LISTA
    # df_list = dataframe[0].to_numpy().tolist()    #type<List>
    
    # CONVERTIR DATAFRAME A ARRAY
    df_arr  = dataframe[0].to_numpy()   #type<Array>
    
    # EXTRAER COLUMNAS DEL DATAFRAME
    # columns_names = dataframe[0].columns.values
    
    # IMPRIME LA TABLA QUE ENTENDIÓ EL LECTOR PDF
    # print( tabulate(df_arr, tablefmt="pretty") )
    
    data=[]    
    for key in df_arr:    
        if isfloat(key[0]) and isint(key[0]) and key[0].isnumeric():            
            #SE ELIMINA LOS ITEMS DEL ARRAY QUE DICEN "Nan" QUE EL EXTRACTOR ENTENDIÓ "MAL"
            key = np.delete(key, [8,9,10,11,12,13,14,15,16,17,18,19,20, 21, 22])
            data.append(key)       
            
    return data


def insertar_data(data, json_post):
    
    status=True
    cnt_insertados    = 0
    cnt_no_insertados = 0
    total_registros   = 0
    respuesta         = {}
    
    
    cur = mysql.connection.cursor()
    for registros_aux in data:  
        total_registros=total_registros+1

        radicacion          = str(registros_aux[1]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        clase_proceso       = str(registros_aux[2]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        demandante          = str(registros_aux[3]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        demandado           = str(registros_aux[4]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        providencia         = str(registros_aux[5]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        fecha               = str(registros_aux[6]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        # vinculo_providencia = str(registros_aux[7]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
          
        #Cambia el formato de la fecha a Y-m-d (la fecha llega en formato d/m/Y)
        date_sr = pd.to_datetime(pd.Series(fecha), infer_datetime_format=True) 
        change_format = date_sr.dt.strftime('%Y-%m-%d') 
        fecha_auto = change_format[0] 
        
             
        radicacion_aux  = str(radicacion[3:len(radicacion)])   
        if len(radicacion_aux)<5:    
            radicacion_aux = radicacion_aux.zfill(5) 
        radicacion_anio = "20"+radicacion[0:2]   
        
        
        
        query = "INSERT IGNORE INTO lupa_texto_estado_diario_entidades (estado_id, texto_estado, entidad_id, texto_departamento, texto_municipio, texto_imagen, texto_radicacion, texto_radicacion_ano, texto_tipo_proceso, texto_demandante, texto_demandado, texto_cuaderno, texto_fecha_auto, texto_fecha_texto, texto_fecha_grabacion, texto_hora_grabacion, texto_cod_operador) "
        query += "VALUES ( "  
        query += " '"+json_post['estado_id_imagen']  +"' , '"+json_post['est_imagen']  +"' , '"+json_post['entidad_id']  +"' , '"+json_post['dep_imagen']+"' , '"+json_post['mun_imagen']+"' , '"+json_post['img_url_imagen']+"' , '"+radicacion_aux+"' , '"+radicacion_anio+"' , '"+clase_proceso+"' , '"+demandante+"' , '"+demandado+"' , '"+providencia+"' , '"+fecha_auto+"' , '"+json_post['fecha_estado']+"' , CURDATE() , CURTIME() , '"+json_post['ced_usuario']  +"' "
        query += ")";
        
        
        # print("Registro N°:" + str(total_registros))
        
        rstInsert = cur.execute(query)
        mysql.connection.commit() 
        
        if rstInsert:
            status=True
            cnt_insertados=cnt_insertados+1
        else:
            status=False
            cnt_no_insertados=cnt_no_insertados+1        
                 
    respuesta = {
        "status":status,
        "cnt_insertados":cnt_insertados,
        "cnt_no_insertados":cnt_no_insertados,
        "msg":"Cantidad insertados: " + str(cnt_insertados) + " | Cantidad No insertados: " + str(cnt_no_insertados) + " | Cantidad Total registros: "+str(total_registros)
    }        
        
    return respuesta






#------------ RUTAS ------------
@app.route('/', methods=['GET'])
def ruta():
    respuesta = {
        "Hora":format(datetime.datetime.now().strftime("%X")),
        "msg":"Bienvenido.",
        "OS": sys.platform,
        "Author":"Alexander Beleno Mackenzie"
    } 
    return respuesta



# Ruta para extraer la tabla del pdf (ESTADOS) - method (GET) - HTML
#POINT DESACTUALIADO
@app.route('/extraer/estado/<path_archivo>', methods=['GET'])
def getextraerestado(path_archivo):    
    try:
        if request.method == 'GET':
            dataframe   = read_pdf("carpeta_pdf/"+path_archivo, pages="all", area=(160.65, 38.43, 586.53, 972.09), output_format="dataframe")     #type<Dataframe>  
            data        = armar_data_estado(dataframe)    #type<Array>  
            
            # IMPRIME LA TABLA CON LA DATA "ORGANIZADA Y LIMPIA"
            # print( tabulate(data, tablefmt="pretty") )     
            
            print('Se empieza a insertar los datos a la Base de datos...')
            print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
                   
            rstInsert   = insertar_data(data)        
            status  =rstInsert['status']    
            msg     =rstInsert['msg']  
            
            print('Termina inserccion...')
            print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")))
        else:
            status    = False 
            msg       = 'Error, el request es invalido'
    except FileNotFoundError as error:
        status    = False 
        msg       = f'Error, el archivo especificado no se encuentra: {error}'
       
    respuesta = {
        "status":status,
        "msg":msg
    }  
    return jsonify(respuesta)



# Ruta para extraer la tabla del pdf (ESTADOS) - method (POST) - JSON
@app.route('/extraer/estado', methods=['POST'])
def getextraerestado_json():
    try:
        if request.method == 'POST':
            #DATA RECIBIDA
            path_archivo        = request.json['path_pdf']   
            # print(request.json)            
                                      
            dataframe   = read_pdf("../../../.."+path_archivo, pages="all", area=(160.65, 38.43, 586.53, 972.09), output_format="dataframe")     #type<Dataframe>  
            data        = armar_data_estado(dataframe)    #type<Array>    
            
            # IMPRIME LA TABLA CON LA DATA "ORGANIZADA Y LIMPIA"
            # print( tabulate(data, tablefmt="pretty") )
            
            print('\nSe empieza a insertar los datos a la Base de datos...')
            print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
            
            rstInsert   = insertar_data(data, request.json)
            status  =rstInsert['status']    
            msg     =rstInsert['msg']    
            
            print('\nTermina inserccion... \n' + msg)
            print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")) + "\n")
        else:
            status    = False 
            msg       = 'Error, el request es invalido'
        
    except FileNotFoundError as error:
        status    = False 
        msg       = f'Error, el archivo especificado no se encuentra: {error}'
       
    respuesta = {
        "status":status,
        "msg":msg
    }  
    return jsonify(respuesta)






# starting the app
if __name__ == "__main__":
    #LOCAL:
    # app.run(host="5.189.158.190", port=7000, debug=False)
    
    #REMOTO:
    serve(app, host="lupajuridica.com.co", port=8080)



