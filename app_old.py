#----------------------------------
#------------ RECURSOS ------------
#----------------------------------
# pip install MySQL-python
# pip install Flask
# pip install Flask-MySQLdb
# pip install Flask-Cors==1.1.2
# pip install tabulate
# pip install tabula-py
# pip install waitress
#   pip install googletrans         (Insalar en el servidor contabo) 14-07-2022...

from platform import processor
from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from tabula import read_pdf 
from tabulate import tabulate 
import numpy as np
import pandas as pd 
import datetime
import sys
from waitress import serve
from flask_cors import CORS, cross_origin
# from flask_cors import CORS
from googletrans import Translator




#-------------------------------
# initializations
#-------------------------------
app = Flask(__name__)
CORS(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})





#---------------------------------------
#------------ BASE DE DATOS ------------
#---------------------------------------
app.config['MYSQL_HOST']        = 'localhost' 
app.config['MYSQL_USER']        = 'db_user'
app.config['MYSQL_PASSWORD']    = 'Lupa-12312423$$**12'
app.config['MYSQL_DB']          = 'db_lupajuridica'
mysql = MySQL(app)
# settings A partir de ese momento Flask utilizará esta clave para poder cifrar la información de la cookie
app.secret_key = "mysecretkey"






#-----------------------------------
#------------ FUNCIONES ------------
#-----------------------------------
#Convierte string a float
def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False    
    
#Convierte string a int
def isint(num):
    try:
        int(num)
        return True
    except ValueError:
        return False   

#Cambia el formato de la fecha a Y-m-d (la fecha llega en formato d/m/Y)
def convertidor_formato_fecha(fecha):
    date_sr_aux       = pd.to_datetime(pd.Series(fecha), infer_datetime_format=True) 
    change_format     = date_sr_aux.dt.strftime('%Y-%m-%d') 
    fecha_new_format  = change_format[0] 
    
    return fecha_new_format

#Para el formato #2 convierte la cadena de texto a una fecha
def convertidor_string_fecha(cadena_fecha):  
    try:
        dia  = str(cadena_fecha).replace("\n", " ").replace("\r", " ").replace("(", "").replace(")", "").split()[1]
        mes  = str(cadena_fecha).replace("\n", " ").replace("\r", " ").replace("(", "").replace(")", "").split()[3]
        anio = str(cadena_fecha).replace("\n", " ").replace("\r", " ").replace("(", "").replace(")", "").split()[8]
        
        translator       = Translator(service_urls=['translate.googleapis.com']) #API Googletranslator
        mes_traducido    = translator.translate( mes, src='es', dest='en' )     #De español a ingles
        fecha_convertida = convertidor_formato_fecha( dia + mes_traducido.text[0:3] + anio ) #dd/month/yyyy: month es un texto. Ej: Mayo --> May (16/may/2002) => (2002-06-16).
        
    except (ValueError, TypeError, IndexError) as e:
        print("Ocurrió un error en el formato #2 de Fijaciones en la columna de fecha: \nError:", e)
        exit() 
        
    return fecha_convertida
   
  





#--------------------------------------------------------
#------------ PARA LOS DOCUMENTOS DE ESTADOS ------------
#--------------------------------------------------------
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
        if isfloat(key[0]) and isint(key[0]):   #and key[0].isnumeric()
            #SE ELIMINA LOS ITEMS DEL ARRAY QUE DICEN "Nan" QUE EL EXTRACTOR ENTENDIÓ "MAL"
            # key = np.delete(key, [8,9,10,11,12,13,14,15,16,17,18,19,20, 21, 22])
            data.append(key)       
            
    return data


def insertar_texto_estado(data, json_post):
    
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
        
        
        
        
        
         
        if (json_post['tablaRegistros'] == "lupa_texto_estado_diario_entidades"):
            query = "INSERT IGNORE INTO lupa_texto_estado_diario_entidades (estado_id, texto_estado, entidad_id, texto_departamento, texto_municipio, texto_imagen, texto_radicacion, texto_radicacion_ano, texto_tipo_proceso, texto_demandante, texto_demandado, texto_cuaderno, texto_fecha_auto, texto_fecha_texto, texto_fecha_grabacion, texto_hora_grabacion, texto_cod_operador) "
            query += "VALUES ( "  
            query += " '"+json_post['estado_id_imagen']  +"' , '"+json_post['est_imagen']  +"' , '"+json_post['entidad_id']  +"' , '"+json_post['dep_imagen']+"' , '"+json_post['mun_imagen']+"' , '"+json_post['img_url_imagen']+"' , '"+radicacion_aux+"' , '"+radicacion_anio+"' , '"+clase_proceso+"' , '"+demandante+"' , '"+demandado+"' , '"+providencia+"' , '"+fecha_auto+"' , '"+json_post['fecha_estado']+"' , CURDATE() , CURTIME() , '"+json_post['ced_usuario']  +"' "
            query += ")"
            
        elif (json_post['tablaRegistros']=="lupa_texto_estado_diario"):
            
            proceso = ""                                                   
            proceso = json_post["dep_imagen"]+json_post["mun_imagen"]+ json_post["ent_imagen"]+json_post["esp_imagen"]+json_post["desp_imagen"]+radicacion_anio+radicacion_aux
            
            query = "INSERT IGNORE INTO lupa_texto_estado_diario (estado_id, texto_estado, texto_departamento, texto_municipio, texto_entidad, texto_especialidad,texto_despacho, texto_proceso, texto_imagen, texto_radicacion, texto_radicacion_ano, texto_tipo_proceso, texto_demandante, texto_demandado, texto_cuaderno, texto_fecha_auto, texto_fecha_texto, texto_fecha_grabacion, texto_hora_grabacion, texto_cod_operador) "
            query += "VALUES ( "  
            query += " '"+json_post['estado_id_imagen']  +"' , '"+json_post['est_imagen']  +"' , '"+json_post['dep_imagen']+"' , '"+json_post['mun_imagen']+"', '"+json_post['ent_imagen']+"' , '"+json_post['esp_imagen']+"' , '"+json_post['desp_imagen']+"' , '"+proceso+"' , '"+json_post['img_url_imagen']+"' , '"+radicacion_aux+"' , '"+radicacion_anio+"' , '"+clase_proceso+"' , '"+demandante+"' , '"+demandado+"' , '"+providencia+"' , '"+fecha_auto+"' , '"+json_post['fecha_estado']+"' , CURDATE() , CURTIME() , '"+json_post['ced_usuario']  +"' "
            query += ")"
        
        
        
        # print("Registro N°:" + str(total_registros))
        rstInsert = cur.execute(query)
        mysql.connection.commit() 
        
        # print( "Rst --> "+rstInsert )
        # print( "" )
        # print( "Query --> "+query )
        # print( "" )
        # print( "" )
        # print( "" )
        
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





#-----------------------------------------------------------
#------------ PARA LOS DOCUMENTOS DE FIJACIONES ------------
#-----------------------------------------------------------
def obtieneTipoFormatoFijacion(dataframe):
    #COLUMNAS:
    #VALIDA SI ES FORMATO 1 O FORMATO 2: 
    #LA DIFERENCIA DE AMBOS FORMATOS ES QUE EL FORMATO 2 TRAE EL NOMBRE DE COLUMNA "EXPEDIENTE" Y NO TRAE LA COLUMNA "No."
    columnas = dataframe[0].columns.values.tolist()            # print(columnas)
    formato="0" #SIN FORMATO
    for col in columnas:    
        if col in ["RADICACIÓN", "No."]:     #FORMATO 1
            formato="1"
        elif col in ["EXPEDIENTE"]:          #FORMATO 2
            formato="2"   
            
    return formato


def armar_data_fijaciones(dataframe, formato):
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
        # if isfloat(key[0]) and isint(key[0]):            
        #     #SE ELIMINA LOS ITEMS DEL ARRAY QUE DICEN "Nan" QUE EL EXTRACTOR ENTENDIÓ "MAL"
        #     key = np.delete(key, [8,9,10,11,12,13,14,15,16,17,18,19,20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30])
        #     data.append(key)       
        if formato=="1":  
            if isfloat(key[0]) and isint(key[0]):              
                data.append(key)       
            
        elif formato=="2":  
            if key[4]!="" and key[4]!=None and key[5]!="" and key[4]!=None:                 
                key[4] = convertidor_string_fecha(key[4])                      
                key[5] = convertidor_string_fecha(key[5])                      
                data.append(key) 
            else:
                print("Ocurrió un error en el formato #2 de Fijaciones, la columna de fecha esta vacia")
                exit()
            
    return data


def insertar_data_fijaciones(data, json_post, formato):
    
    status=True
    cnt_insertados    = 0
    cnt_no_insertados = 0
    total_registros   = 0
    respuesta         = {}
    
    
    cur = mysql.connection.cursor()
    for registros_aux in data:  
        total_registros=total_registros+1
        
        indice=0
        if (formato=="1"):
            indice+=1

        radicacion          = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        clase_proceso       = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        demandante          = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        demandado           = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        fecha_inicio        = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        fecha_vencimiento   = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        tipo_traslado       = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        
        # fecha_inicio_aux      = convertidor_formato_fecha(fecha_inicio)
        # fecha_vencimiento_aux = convertidor_formato_fecha(fecha_vencimiento)
        # radicacion_aux  = str(radicacion[3:len(radicacion)])   
        # if len(radicacion_aux)<5:    
        #     radicacion_aux = radicacion_aux.zfill(5) 
        # radicacion_anio = "20"+radicacion[0:2]  
        
        if ( formato=="1" ):
            #Formato #1
            fecha_inicio      = convertidor_formato_fecha(fecha_inicio)
            fecha_vencimiento = convertidor_formato_fecha(fecha_vencimiento)
            radicacion_aux        = str(radicacion[3:len(radicacion)])   
            if len(radicacion_aux)<5:    
                radicacion_aux = radicacion_aux.zfill(5) 
            radicacion_anio = "20"+radicacion[0:2]     
                    
        elif( formato=="2" ):
            #Formato #2
            radicacion_aux  = str(radicacion[5:len(radicacion)])   
            if len(radicacion_aux)<5:    
                radicacion_aux = radicacion_aux.zfill(5) 
            radicacion_anio = radicacion[0:4]  
                 
                
        if (json_post['tablaRegistros'] == "lupa_texto_fijalista_entidades"):
            
            query = "INSERT IGNORE INTO lupa_texto_fijalista_entidades ( "            
            query += " fijacion_id, "
            query += " entidad_id, "
            query += " `texto_fijalista_departamento`, "
            query += " `texto_fijalista_municipio`, "
            query += " `texto_fijalista_entidad`, "
            query += " `texto_fijalista_especialidad`, "
            query += " `texto_fijalista_despacho`, "
            query += " `texto_fijalista_ano`, "
            query += " `texto_fijalista_radicacion`, "
            query += " texto_fijalista_sociedad, "
            query += " `texto_fijalista_consecutivo`, "
            query += " `texto_fijalista_imagen`, "        
            query += " `texto_fijalista_fecha`, "
            query += " `texto_fijalista_fecha_fijalista`, "
            query += " `texto_fijalista_fecha_vencimiento`, "        
            query += " `texto_fijalista_demandante`, "
            query += " `texto_fijalista_demandado`, "
            query += " `texto_fijalista_motivo`, "
            query += " `texto_fijalista_fecha_grabacion`, "
            query += " `texto_fijalista_hora_grabacion`, "
            query += " `texto_fijalista_cod_operador` "            
            query += " ) VALUES ( "      
            query += " '" + json_post['fijacion_id'] + "' "
            query += " , '" + json_post['entidad_id'] + "' "
            query += " , '" + json_post['dep_imagen'] + "' "
            query += " , '" + json_post['mun_imagen'] + "' "
            query += " , '' "
            query += " , '' "
            query += " , '' "
            query += " , '" + radicacion_anio + "' "
            query += " , '" + radicacion_aux + "' "
            query += " , '' "
            query += " , '" + json_post['txtconsecutivo'] + "' "
            query += " , '" + json_post['img_url_imagen'] + "' "
            query += " , '" + fecha_inicio + "' "
            query += " , '" + fecha_inicio + "' "
            query += " , '" + fecha_vencimiento + "' "        
            query += " , '" + demandante + "' "
            query += " , '" + demandado + "' "        
            query += " , '" + tipo_traslado + "' "        
            query += " , CURDATE() "
            query += " , CURTIME() "
            query += " , '" + json_post['ced_usuario'] + "' "            
            query += ")";
            
        elif (json_post['tablaRegistros']=="lupa_texto_fijalista"):  
            proceso = ""                                                   
            proceso = json_post["dep_imagen"]+json_post["mun_imagen"]+ json_post["ent_imagen"]+json_post["esp_imagen"]+json_post["desp_imagen"]+radicacion_anio+radicacion_aux
                      
            query = "INSERT IGNORE INTO lupa_texto_fijalista ( "            
            # query += " fijacion_id, "
            query += " `texto_fijalista_proceso`, "
            query += " `texto_fijalista_departamento`, "
            query += " `texto_fijalista_municipio`, "
            query += " `texto_fijalista_entidad`, "
            query += " `texto_fijalista_especialidad`, "
            query += " `texto_fijalista_despacho`, "
            query += " `texto_fijalista_ano`, "
            query += " `texto_fijalista_radicacion`, "
            
            query += " `texto_fijalista_imagen`, "        
            query += " `texto_fijalista_fecha`, "
            query += " `texto_fijalista_fecha_fijalista`, "
            query += " `texto_fijalista_fecha_vencimiento`, "        
            query += " `texto_fijalista_demandante`, "
            query += " `texto_fijalista_demandado`, "
            query += " `texto_fijalista_motivo`, "
            query += " `texto_fijalista_fecha_grabacion`, "
            query += " `texto_fijalista_hora_grabacion`, "
            query += " `texto_fijalista_cod_operador` "            
            query += " ) VALUES ( "      
            # query += " '" + json_post['fijacion_id'] + "' "
            query += "  '" + proceso + "' "
            query += " , '" + json_post['dep_imagen'] + "' "
            query += " , '" + json_post['mun_imagen'] + "' "
            query += " , '" + json_post['ent_imagen'] + "' "
            query += " , '" + json_post['esp_imagen'] + "' "
            query += " , '" + json_post['desp_imagen'] + "' "
            query += " , '" + radicacion_anio + "' "
            query += " , '" + radicacion_aux + "' "
            
            query += " , '" + json_post['img_url_imagen'] + "' "
            query += " , CURDATE() "
            # query += " , '" + fecha_inicio_aux + "' "
            query += " , '" + fecha_inicio + "' "
            query += " , '" + fecha_vencimiento + "' "        
            query += " , '" + demandante + "' "
            query += " , '" + demandado + "' "        
            query += " , '" + tipo_traslado + "' "        
            query += " , CURDATE() "
            query += " , CURTIME() "
            query += " , '" + json_post['ced_usuario'] + "' "            
            query += ")";

        
        
        
        # print("Query Insert: " + query )
        rstInsert = cur.execute(query)
        mysql.connection.commit() 
        # print("Respuesta Insert: " + rstInsert )
        
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
        "cnt_total_registros":total_registros,
        "msg":"Cantidad insertados: " + str(cnt_insertados) + " | Cantidad No insertados: " + str(cnt_no_insertados) + " | Cantidad Total registros encontrados: "+str(total_registros)
    }        
        
    return respuesta






#-------------------------------
#------------ RUTAS ------------
#-------------------------------
@app.errorhandler(500)
def special_exception_handler(error):
	return {"status": False, "msg":"conexion fallida [ERROR 500]"},500


@app.errorhandler(404)
def page_not_found(error):
	return {"status": False, "msg":"El endpoint no existe. [ERROR 404]"},404


@app.route('/', methods=['GET'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def ruta():
    respuesta = {
        "Hora":format(datetime.datetime.now().strftime("%X")),
        "msg":"[API]: Bienvenido.",
        "OS": sys.platform,
        "Author":"Alexander Beleno Mackenzie"
    } 
    
    return respuesta


# Ruta para extraer la tabla del pdf (ESTADOS) - method (POST) - JSON
@app.route('/extraer/estado', methods=['POST'])
@cross_origin(origin='localhost',headers=['Content- Type','Authorization'])
def getextraerestado_json():
    try:
        if request.method == 'POST':
            print(request)            
            #DATA RECIBIDA
            path_archivo        = request.json['path_pdf']   
            
            #Nota: Stream busca espacios en blanco entre columnas, mientras que Lattice busca líneas de límite entre columnas.    
            #PRUEBA 1:  
            columns = ["1", "2", "3", "4", "5", "6", "7", "8"]  
            dataframe  = read_pdf("../../../.."+path_archivo, multiple_tables=True, columns= columns,pages="all", stream=True, lattice=False, output_format="dataframe")    
            
            #PRUEBA 1:                          
            # dataframe  = read_pdf("../../../.."+path_archivo, pages="all", area=(182.07, 9.45, 602.91, 998.55), stream=False, lattice=True, output_format="dataframe")    
            
            #PRUEBA 2:                      
            # dataframe   = read_pdf("../../../.."+path_archivo, pages="all", area=(160.65, 38.43, 586.53, 972.09), output_format="dataframe")     #type<Dataframe>  
            
            #ORIGINAL:
            # dataframe   = read_pdf("../../../.."+path_archivo, pages="all", area=(86.31, 19.53, 599.13, 989.73), stream=False, lattice=True, output_format="dataframe")       #type<Dataframe>  
            
            data        = armar_data_estado(dataframe)    #type<Array>    
            
            
            # IMPRIME LA TABLA CON LA DATA "ORGANIZADA Y LIMPIA"
            # print( tabulate(data, tablefmt="pretty") )
            
            print('\nSe empieza a insertar los datos a la Base de datos...')
            print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
            
            rstInsert   = insertar_texto_estado(data, request.json)
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


# Ruta para extraer la tabla del pdf (FIJACION) - method (POST) - JSON
@app.route('/extraer/fijacion', methods=['POST'])
def getextraerfijacion_json():
    try:
        if request.method == 'POST':
            #DATA RECIBIDA
            path_archivo        = request.json['path_pdf']    
            # print(request.json)
            
                                      
            #PRUEBA 1:                          
            # dataframe  = read_pdf("../../../.."+path_archivo, pages="all", stream=False, lattice=True, output_format="dataframe")    
            
            #borrar
            columns = ["1", "2", "3", "4", "5", "6", "7", "8"] 
            dataframe  = read_pdf("../../../.."+path_archivo, multiple_tables=True, columns=columns, pages="all",  stream=True, lattice=False, output_format="dataframe")   
            
            #PRUEBA 2:                              
            # dataframe   = read_pdf("../../../"+path_archivo, pages="all", area=(106.47, 14.49, 582.75, 997.29), stream=False, lattice=True, output_format="dataframe")     #type<Dataframe>  
            
            #ORIGINAL:
            # dataframe  = read_pdf("../../../.."+path_archivo, pages="all", area=(106.47, 14.49, 582.75, 997.29), stream=False, lattice=True, output_format="dataframe")     
            
            #SE OBTIENE EL FORMATO DEL DOCUMENTO
            formato    = obtieneTipoFormatoFijacion(dataframe)#type<Dataframe>  
            #ARMA LA DATA QUE SE VA A INSERTAR EN LA EN BD
            data       = armar_data_fijaciones(dataframe, formato)    #type<Array>    
            
            # IMPRIME LA TABLA CON LA DATA "ORGANIZADA Y LIMPIA"
            # print( tabulate(data, tablefmt="pretty") )
            
            print('\nSe empieza a insertar los datos a la Base de datos...')
            print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
            
            rstInsert   = insertar_data_fijaciones(data, request.json, formato)
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






#-------------------------------
# starting the app
#-------------------------------
if __name__ == "__main__":
    #SERVER DE DESARROLLO LOCAL:
    app.run(host="localhost", port=9000, debug=False)
    
    #REMOTO - LOCAL:
    # serve(app, host="localhost", port=9000 )