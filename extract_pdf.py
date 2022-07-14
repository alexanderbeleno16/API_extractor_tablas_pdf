#------------ RECURSOS ------------

# pip install MySQL-python
# pip install Flask                 installed
# pip install Flask-MySQLdb         installed
# pip install Flask-Cors==1.1.2
# pip install tabulate              installed
# pip install tabula-py             installed
#   pip install googletrans         (Insalar en el servidor contabo) 14-07-2022...

from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
from tabula import read_pdf 
from tabulate import tabulate 
import numpy as np
import pandas as pd 
import datetime
from googletrans import Translator




# from flask_cors import CORS, cross_origin
# from flask_cors import CORS



# initializations
app = Flask(__name__)
# CORS(app)



#------------ BASE DE DATOS ------------
app.config['MYSQL_HOST']        = 'localhost' 
app.config['MYSQL_USER']        = 'root'
app.config['MYSQL_PASSWORD']    = ''
app.config['MYSQL_DB']          = 'extractordatapdf'
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
        
        translator       = Translator(service_urls=['translate.googleapis.com'])
        mes_traducido    = translator.translate( mes, src='es', dest='en' )
        fecha_convertida = convertidor_formato_fecha( dia + mes_traducido.text[0:3] + anio ) #dd/month/yyyy: month es un texto. Ej: Mayo --> May (En ingles).
        
    except (ValueError, TypeError, IndexError) as e:
        print("Ocurrió un error en el formato #2 de Fijaciones en la columna de fecha: \nError:", e)
        exit() 
        
    return fecha_convertida
   




#PARA ESTADOS:
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
        if isfloat(key[0]) and isint(key[0]):            
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



#PARA FIJACIONES:
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
            #SE ELIMINA LOS ITEMS DEL ARRAY QUE DICEN "Nan" QUE EL EXTRACTOR ENTENDIÓ "MAL"
            # key = np.delete(key, [8,9,10,11,12,13,14,15,16,17,18,19,20, 21, 22])
            # data.append(key)               
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
            
        
        if ( json_post['tablaRegistros'] == "lupa_texto_fijalista_entidades" ):
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
                query += " , '' "
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


#------------ RUTAS ------------
@app.errorhandler(500)
def special_exception_handler(error):
	return {"status":"500", "msg":"conexion fallida"},500

@app.errorhandler(404)
def page_not_found(error):
	return {"status":"404", "msg":"El endpoint no existe."},404

@app.route('/', methods=['GET'])
def ruta():
    respuesta = {
        "Hora":format(datetime.datetime.now().strftime("%X")),
        "msg":"[API]: Bienvenido.",
        "Author":"Alexander Beleno Mackenzie"
    } 
    
    return respuesta







# Ruta para extraer la tabla del pdf (ESTADOS) - method (POST) - JSON
@app.route('/extraer/estado', methods=['POST'])
def getextraerestado_json():
    try:
        if request.method == 'POST':
            #DATA RECIBIDA
            path_archivo        = request.json['path_pdf']   
            # nombre_pdf          = request.json['nombre_pdf']   
            # entidad_id          = request.json['entidad_id']   
            # dep_imagen          = request.json['dep_imagen']   
            # mun_imagen          = request.json['mun_imagen']   
            # est_imagen          = request.json['est_imagen'] 
            # img_url_imagen      = request.json['img_url_imagen']   
            # estado_id_imagen    = request.json['estado_id_imagen']   
            # ced_usuario         = request.json['ced_usuario']   
            # fecha_estado        = request.json['fecha_estado']   
              
            # registros           = request.json['registros']   
            # sociedad            = request.json['sociedad']   
            # tablaRegistros      = request.json['tablaRegistros']   
            # print(request.json)
            
                                      
            dataframe   = read_pdf("../../../"+path_archivo, pages="all", area=(86.31, 19.53, 599.13, 989.73), stream=False, lattice=True, output_format="dataframe")      #type<Dataframe>  
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



# Ruta para extraer la tabla del pdf (FIJACION) - method (POST) - JSON
@app.route('/extraer/fijacion', methods=['POST'])
def getextraerfijacion_json():
    try:
        if request.method == 'POST':
            #DATA RECIBIDA
            path_archivo        = request.json['path_pdf']    
            #LEE EL PDF
            dataframe   = read_pdf("carpeta_pdf/"+path_archivo, pages="all", area=(106.47, 14.49, 582.75, 997.29), stream=False, lattice=True, output_format="dataframe")     #type<Dataframe>  
            #SE OBTIENE EL FORMATO DEL DOCUMENTO
            formato = obtieneTipoFormatoFijacion(dataframe)
            #ARMA LA DATA QUE SE VA A INSERTAR EN LA EN BD
            data = armar_data_fijaciones(dataframe, formato)    #type<Array>    
            # IMPRIME LA TABLA CON LA DATA QUE SE ARMÓ "ORGANIZADA Y LIMPIA"
            # print( tabulate(data, tablefmt="pretty") )   
            
            print('\nSe empieza a insertar los datos a la Base de datos...')
            print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
            
            rstInsert   = insertar_data_fijaciones(data, request.json, formato)
            status      = rstInsert['status']    
            msg         = rstInsert['msg']    
            
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









# Ruta para extraer la tabla del pdf (ESTADOS) - method (GET) - HTML
# @app.route('/extraer/estado/<path_archivo>', methods=['GET'])
# def getextraerestado(path_archivo):    
#     try:
#         if request.method == 'GET':
#             dataframe   = read_pdf("carpeta_pdf/"+path_archivo, pages="all", area=(160.65, 38.43, 586.53, 972.09), output_format="dataframe")     #type<Dataframe>  
#             data        = armar_data_estado(dataframe)    #type<Array>  
            
#             # IMPRIME LA TABLA CON LA DATA "ORGANIZADA Y LIMPIA"
#             # print( tabulate(data, tablefmt="pretty") )     
            
#             print('Se empieza a insertar los datos a la Base de datos...')
#             print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
                   
#             rstInsert   = insertar_data(data)        
#             status  =rstInsert['status']    
#             msg     =rstInsert['msg']  
            
#             print('Termina inserccion...')
#             print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")))
#         else:
#             status    = False 
#             msg       = 'Error, el request es invalido'
#     except FileNotFoundError as error:
#         status    = False 
#         msg       = f'Error, el archivo especificado no se encuentra: {error}'
       
#     respuesta = {
#         "status":status,
#         "msg":msg
#     }  
#     return jsonify(respuesta)








# starting the app
if __name__ == "__main__":
    # try:
    app.run(port=3000, debug=False)
    # except (mysqldb._exceptions.OperationalError) as error:
    #     status    = "ERROR" 
    #     msg       = f'Error, la base de datos no se reconoce o no existe: {error}'







#NOTEBOOK JUPYTER
# from tabula import read_pdf 
# from tabulate import tabulate 

# df = read_pdf("carpeta_pdf/ESTADO 094.pdf", pages="all", area=(161, 38, 578, 973), output_format="dataframe") 
# # print( tabulate(df, tablefmt="pretty") )
# # df.to_numpy().tolist()
# print(df)
