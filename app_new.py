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
import tabula
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
import re




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
app.config['MYSQL_USER']        = 'root'
app.config['MYSQL_PASSWORD']    = ''
app.config['MYSQL_DB']          = 'extractordatapdf'
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
    lista_enlaces_providencia = []
        
        
    cur = mysql.connection.cursor()
    for registros_aux in data:  
        total_registros=total_registros+1

        radicacion          = str(registros_aux[1]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        clase_proceso       = str(registros_aux[2]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        demandante          = str(registros_aux[3]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        demandado           = str(registros_aux[4]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        providencia         = str(registros_aux[5]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        fecha               = str(registros_aux[6]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        vinculo_providencia = str(registros_aux[7]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        
        #-----------------------------------NEW:-----------------------------------------
        providencia_digitos = providencia.zfill(6) 
        doc_url = ""; enlace_providencia="";
        if ( re.findall(r"entencia", vinculo_providencia) or re.findall(r"ENTENCIA", vinculo_providencia) ):
            doc_url = "SE" #Sentrencia
        elif ( re.findall(r"auto", vinculo_providencia) or re.findall(r"Auto", vinculo_providencia) or re.findall(r"AUTO", vinculo_providencia) ):
            doc_url = "AU" #auto
            
        if doc_url!="":
            enlace_providencia = "http://visordocs.sic.gov.co/documentos/Docs042/docs34/2022/2022"+str(providencia_digitos)+str(doc_url)+"/2022"+str(providencia_digitos)+str(doc_url)+"0000000001.PDF" 
            lista_enlaces_providencia.append(enlace_providencia)
        #---------------------------------------------------------------------------------
          
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
        
        
        cur.execute(query)
        mysql.connection.commit() 
        
        
        if cur.rowcount>0:
            status=True
            cnt_insertados=cnt_insertados+1
        else:
            status=False
            cnt_no_insertados=cnt_no_insertados+1        
                 
    
    #MANDAR A LLAMAR UNA FUNCION QUE ACTUALICE LA TABLA QUE CONTIENE EL ESTADO, INSERTANDO UN JSON EN UN CAMPO QUE CONTENGA LOS ENLACES(AUTOS/SENTENCIAS) DEL PDF DE LAS SIC (ESTADO, fijaciones no tiene enlaces...)
    #Ej: InsertarEnlacesSic(id_estado, ListaEnlaces);    
    # if len(lista_enlaces_providencia)>0:
    #     insertarArrayEnlacesEstado( json_post["estado_id"] , str(lista_enlaces_providencia) )
        
    
    respuesta = {
        "status":status,
        "cnt_insertados":cnt_insertados,
        "cnt_no_insertados":cnt_no_insertados,
        "lista_enlaces_providencia":lista_enlaces_providencia,
        "msg":"Cantidad Total registros encontrados: " + str(total_registros) + "\n - Cant. insertados: " + str(cnt_insertados) + "\n - Cant. No insertados: " + str(cnt_no_insertados) 
    }        
        
    return respuesta


def insertarArrayEnlacesEstado(id_estado, array_enlaces):
    # print( array_enlaces ) 
    
    cur = mysql.connection.cursor()
    cur.execute('UPDATE lupa_estado SET estado_enlaces_pdf = %s WHERE id = %s', (array_enlaces, id_estado) )
    mysql.connection.commit()
    
    return cur.rowcount  


def actualizarImagenesEstadoScadDigitadas(json_post):
    cur = mysql.connection.cursor()
    
    query = "UPDATE `lupa_imagenes_estado` "
    query += "SET scad = '11' "
    query += "WHERE 1 "
    
    query += "AND imagenes_departamento     = '"+json_post['dep_imagen']+"' "
    query += "AND imagenes_municipio        = '"+json_post['mun_imagen']+"' "
    query += "AND imagenes_entidad          = '"+json_post['ent_imagen']+"' "
    query += "AND imagenes_especialidad     = '"+json_post['esp_imagen']+"' "
    query += "AND imagenes_despacho         = '"+json_post['desp_imagen']+"' "
    
    query += "AND imagenes_operador         = '"+json_post['ced_usuario']+"' "
    query += "AND imagenes_fecha_grabacion = CURDATE() "
    
    cur.execute(query)
    mysql.connection.commit()
    
    return cur.rowcount  


def insertarImgenesEstadoRevisado(json_post):
    cur = mysql.connection.cursor()
    
    query = "INSERT ignore INTO lupa_imagenes_estado_revisado "
    query += "( "
    query += "id_imagen, "
    query += "estado, "
    query += "fecha_revision, "
    query += "hora_revision, "
    query += "operador "
    query += ") "
    query += "SELECT id, '2', CURDATE(), CURTIME() "
    query += " ,'"+json_post['ced_usuario']+"' "
    query += "FROM lupa_imagenes_estado "
    query += "WHERE 1 "
    query += "AND imagenes_departamento     = '"+json_post['dep_imagen']+"' "
    query += "AND imagenes_municipio        = '"+json_post['mun_imagen']+"' "
    query += "AND imagenes_entidad          = '"+json_post['ent_imagen']+"' "
    query += "AND imagenes_especialidad     = '"+json_post['esp_imagen']+"' "
    query += "AND imagenes_despacho         = '"+json_post['desp_imagen']+"' "
    query += "AND imagenes_operador         = '"+json_post['ced_usuario']+"' "
    query += "AND imagenes_fecha_grabacion = CURDATE() "
    
    cur.execute(query)
    mysql.connection.commit() 
    
    return cur.rowcount
    


def validarColumnasTabulaEstado(path_archivo, json_post, opcion=1, opc_stream=False, opc_lattice=True):
    respuesta = {
        "status":True,
        "statusImgDigitada":True,
        "statusImgRevisado":True,
        "msg":""
    }   
    if opcion==1:
        dataframe  = read_pdf(path_archivo, pages="all", stream=opc_stream, lattice=opc_lattice, output_format="dataframe", encoding='latin1') 
    elif opcion==2:
        columns = ["1", "2", "3", "4", "5", "6", "7", "8"]
        dataframe  = read_pdf(path_archivo, multiple_tables=True, columns = columns, pages="all", stream=opc_stream, lattice=opc_lattice, output_format="dataframe", encoding='latin1') 
        
    data        = armar_data_estado(dataframe)    #type<Array>    
    print('\nSe empieza a insertar los datos a la Base de datos...')
    print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
    rstInsert   = insertar_texto_estado(data, json_post)
    # status  = rstInsert['status']    
    # msg     = rstInsert['msg']   
    print('\nTermina inserccion... \n')
    print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")) + "\n") 
    
    if rstInsert['status']:
        respuesta = {
            "status":rstInsert['status'],
            "statusImgDigitada":True,
            "statusImgRevisado":True,
            "msg":rstInsert['msg']
        }   
        print('Se inicia la actualizacion de las imagenes de estado a scad 11 (digitadas)...')
        respActualizarImgEstado = actualizarImagenesEstadoScadDigitadas(json_post)
        if respActualizarImgEstado>0:
            print('Imagenes de estado digitadas...')
            print('Se inicia la insercion de las imagenes de estado a la tabla de revisados...')
            respInsertImgEstadoRevisado = insertarImgenesEstadoRevisado(json_post)
            
            if respInsertImgEstadoRevisado==0: 
                respuesta = {
                    "status":rstInsert['status'],
                    "statusImgDigitada":True,
                    "statusImgRevisado":False,
                    "msg":str(rstInsert['msg'])+"\nError, no se insertaron las imagenes de estado a la tabla de revisado - insertarImgenesEstadoRevisado()"
                }
                print( respuesta["msg"] )
                
        else:
            respuesta = {
                "status":rstInsert['status'],
                "statusImgDigitada":False,
                "statusImgRevisado":False,
                "msg": str(rstInsert['msg'])+"\nError, no se actualizó ninguna imagen de estado - actualizarImagenesEstadoScadDigitadas()"
            }
            print( respuesta["msg"] )
            
    else:
        respuesta = {
            "status":False,
            "statusImgDigitada":False,
            "statusImgRevisado":False,
            "msg":"No se insertaron todos los registros - insertar_texto_estado()"
        }
        print( respuesta["msg"] )
    
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


def armar_data_fijaciones(dataframe):
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
        if isfloat(key[0]) and isint(key[0]):              
            data.append(key)       
            
        # elif formato=="2":  
        #     if key[4]!="" and key[4]!=None and key[5]!="" and key[4]!=None:                 
        #         key[4] = convertidor_string_fecha(key[4])                      
        #         key[5] = convertidor_string_fecha(key[5])                      
        #         data.append(key) 
        #     else:
        #         print("Ocurrió un error en el formato #2 de Fijaciones, la columna de fecha esta vacia")
        #         exit()
            
    return data


def insertar_texto_fijacion(data, json_post):
    
    status=True
    cnt_insertados    = 0
    cnt_no_insertados = 0
    total_registros   = 0
    respuesta         = {}
    
    
    cur = mysql.connection.cursor()
    for registros_aux in data:  
        indice=0
        total_registros=total_registros+1
        
        # if (formato=="1"):
        indice+=1

        radicacion          = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        clase_proceso       = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        demandante          = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        demandado           = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        fecha_inicio        = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        fecha_vencimiento   = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");indice+=1
        tipo_traslado       = str(registros_aux[indice]).replace("'",'').replace('"','').replace("´",'').replace('\\','').replace(',','').replace("\n", " ").replace("\r", " ");
        
        
        if len(radicacion)==11 or re.findall(r"([0-9][0-9][0-9][0-9]-)", radicacion):
            if fecha_inicio!="" and fecha_inicio!=None and fecha_vencimiento!="" and fecha_vencimiento!=None:                 
                fecha_inicio      = convertidor_string_fecha(fecha_inicio)                      
                fecha_vencimiento = convertidor_string_fecha(fecha_vencimiento) 
                # fecha_inicio      = convertidor_formato_fecha(fecha_inicio)
                # fecha_vencimiento = convertidor_formato_fecha(fecha_vencimiento)
                    
            radicacion_aux  = str(radicacion[5:len(radicacion)])   
            if len(radicacion_aux)<5:    
                radicacion_aux = radicacion_aux.zfill(5) 
            radicacion_anio = radicacion[0:4]  
        else:
            fecha_inicio      = convertidor_formato_fecha(fecha_inicio)
            fecha_vencimiento = convertidor_formato_fecha(fecha_vencimiento)
            radicacion_aux        = str(radicacion[3:len(radicacion)])   
            if len(radicacion_aux)<5:    
                radicacion_aux = radicacion_aux.zfill(5) 
            radicacion_anio = "20"+radicacion[0:2]   
        
        
        
        # if ( formato=="1" ):
        #     #Formato #1
        #     fecha_inicio      = convertidor_formato_fecha(fecha_inicio)
        #     fecha_vencimiento = convertidor_formato_fecha(fecha_vencimiento)
        #     radicacion_aux        = str(radicacion[3:len(radicacion)])   
        #     if len(radicacion_aux)<5:    
        #         radicacion_aux = radicacion_aux.zfill(5) 
        #     radicacion_anio = "20"+radicacion[0:2]     
                    
        # elif( formato=="2" ):
        #     #Formato #2
        #     radicacion_aux  = str(radicacion[5:len(radicacion)])   
        #     if len(radicacion_aux)<5:    
        #         radicacion_aux = radicacion_aux.zfill(5) 
        #     radicacion_anio = radicacion[0:4]  
            
                
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
        cur.execute(query)
        mysql.connection.commit() 
        # print("Respuesta Insert: " + rstInsert )
        
        if cur.rowcount>0:
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
        "msg":"Cantidad Total registros encontrados: " + str(total_registros) + "\n - Cant. insertados: " + str(cnt_insertados) + "\n - Cant. No insertados: " + str(cnt_no_insertados) 
    }        
        
    return respuesta

  
def actualizarImagenesFijacionesScadDigitadas(json_post):
    cur = mysql.connection.cursor()
    
    query = "UPDATE `lupa_imagenes_fija` "
    query += "SET scad = '11' "
    query += "WHERE 1 "
    
    query += "AND imagenes_departamento     = '"+json_post['dep_imagen']+"' "
    query += "AND imagenes_municipio        = '"+json_post['mun_imagen']+"' "
    query += "AND imagenes_entidad          = '"+json_post['ent_imagen']+"' "
    query += "AND imagenes_especialidad     = '"+json_post['esp_imagen']+"' "
    query += "AND imagenes_despacho         = '"+json_post['desp_imagen']+"' "
    
    query += "AND imagenes_operador         = '"+json_post['ced_usuario']+"' "
    query += "AND imagenes_fecha_grabacion = CURDATE() "
    
    cur.execute(query)
    mysql.connection.commit()
    
    return cur.rowcount  

  
def insertarImgenesFijacionRevisado(json_post):
    cur = mysql.connection.cursor()
    
    query = "INSERT ignore INTO lupa_imagenes_revisado "
    query += "( "
    query += "id_imagen, "
    query += "estado, "
    query += "fecha_revision, "
    query += "hora_revision, "
    query += "operador "
    query += ") "
    query += "SELECT id, '2', CURDATE(), CURTIME() "
    query += " ,'"+json_post['ced_usuario']+"' "
    query += "FROM lupa_imagenes_fija "
    query += "WHERE 1 "
    query += "AND imagenes_departamento     = '"+json_post['dep_imagen']+"' "
    query += "AND imagenes_municipio        = '"+json_post['mun_imagen']+"' "
    query += "AND imagenes_entidad          = '"+json_post['ent_imagen']+"' "
    query += "AND imagenes_especialidad     = '"+json_post['esp_imagen']+"' "
    query += "AND imagenes_despacho         = '"+json_post['desp_imagen']+"' "
    query += "AND imagenes_operador         = '"+json_post['ced_usuario']+"' "
    query += "AND imagenes_fecha_grabacion = CURDATE() "
    
    cur.execute(query)
    mysql.connection.commit() 
    
    return cur.rowcount
    


def validarColumnasTabulaFijacion(path_archivo, json_post, opcion=1, opc_stream=False, opc_lattice=True):
    # print( path_archivo )
    if opcion==2:
        columns = ["1", "2", "3", "4", "5", "6", "7", "8"]
        dataframe  = read_pdf("carpeta_pdf/documentos_ent_SIC/"+path_archivo, multiple_tables=True, columns = columns, pages="all", stream=opc_stream, lattice=opc_lattice, output_format="dataframe") 
    else:
        dataframe  = read_pdf("carpeta_pdf/documentos_ent_SIC/"+path_archivo, pages="all", stream=opc_stream, lattice=opc_lattice, output_format="dataframe")   
        
    # formato    = obtieneTipoFormatoFijacion(dataframe) #type<Dataframe>  
    # data       = armar_data_fijaciones(dataframe, formato)    #type<Array>    
    data       = armar_data_fijaciones(dataframe)    #type<Array>    
    print('\nSe empieza a insertar los datos a la Base de datos...')
    print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
    rstInsert   = insertar_texto_fijacion(data, json_post)
    # rstInsert   = insertar_texto_fijacion(data, json_post, formato)
    # status  =rstInsert['status']    
    # msg     =rstInsert['msg'] 
    print('\nTermina inserccion... \n')
    print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")) + "\n")
    
    if rstInsert['status']:
        respuesta = {
            "status":rstInsert['status'],
            "statusImgDigitada":True,
            "statusImgRevisado":True,
            "msg":rstInsert['msg']
        }   
        print('Se inicia la actualizacion de las imagenes de fijaciones a scad 11 (digitadas)...')
        respActualizarImgFija = actualizarImagenesFijacionesScadDigitadas(json_post)
        if respActualizarImgFija>0:
            print('Imagenes de fijacion digitadas...')
            print('Se inicia la insercion de las imagenes de fijacion a la tabla de revisados...')
            respInsertImgFijaRevisado = insertarImgenesFijacionRevisado(json_post)
            
            if respInsertImgFijaRevisado==0: 
                respuesta = {
                    "status":rstInsert['status'],
                    "statusImgDigitada":True,
                    "statusImgRevisado":False,
                    "msg":str(rstInsert['msg'])+"\nError, no se insertaron las imagenes de fijacion a la tabla de revisado - insertarImgenesFijacionRevisado()"
                }
                print( respuesta["msg"] )
                
        else:
            respuesta = {
                "status":rstInsert['status'],
                "statusImgDigitada":False,
                "statusImgRevisado":False,
                "msg":str(rstInsert['msg'])+"\nError, no se actualizó ninguna imagen de fijacion - actualizarImagenesFijacionesScadDigitadas()"
            }
            print( respuesta["msg"] )
        
    else:
        respuesta = {
            "status":False,
            "statusImgDigitada":False,
            "statusImgRevisado":False,
            "msg":"No se insertaron todos los registros - insertar_texto_fijacion()"
        }
        print( respuesta["msg"] )
    
    
    
    return rstInsert
    
  





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
@cross_origin(origin='localhost',headers=['Content-Type','Authorization'])
def ruta():
    respuesta = {
        "Hora":format(datetime.datetime.now().strftime("%X")),
        "msg":"[API]: Bienvenido.",
        "OS": sys.platform,
        "Author":"Alexander Beleno Mackenzie..."
    } 
    
    return respuesta


# Ruta para extraer la tabla del pdf (ESTADOS) - method (POST) - JSON
@app.route('/extraer/estado', methods=['POST'])
@cross_origin(origin='localhost',headers=['Content-Type','Authorization'])
def getextraerestado_json():
    if request.method == 'POST':  
        #DATA RECIBIDA
        path_archivo        = request.json['path_pdf']   
        entidad             = request.json['ent_imagen']   
        especialidad        = request.json['esp_imagen']     
        if ( path_archivo ):
            if (entidad=="95" and especialidad=="01"):                
                #VALIDACION No.1
                try:           
                    resValidaRead = validarColumnasTabulaEstado(path_archivo, request.json, 1)    
                    status  = resValidaRead["status"]
                    msg     = resValidaRead["msg"] 
                except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                    status    = False 
                    msg       = f'Error interno ESTADO (1): {error}'
                    
                    
                #VALIDACION No.2
                if status==False: 
                    try:
                        resValidaRead = validarColumnasTabulaEstado(path_archivo, request.json, 2)   
                        status  = resValidaRead["status"]
                        msg     = resValidaRead["msg"]  
                    except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                        status    = False 
                        msg       = f'Error interno ESTADO (2): {error}'
                        
                        
                    #VALIDACION No.3
                    if status==False: 
                        opc_stream =True
                        opc_lattice=False
                        try:
                            resValidaRead = validarColumnasTabulaEstado(path_archivo, request.json, 1, opc_stream, opc_lattice)   
                            status  = resValidaRead["status"]
                            msg     = resValidaRead["msg"]  
                        except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                            status    = False 
                            msg       = f'Error interno ESTADO (3): {error}'
                        
                            
                        #VALIDACION No.4
                        if status==False: 
                            try:
                                resValidaRead = validarColumnasTabulaEstado(path_archivo, request.json, 2, opc_stream, opc_lattice)   
                                status  = resValidaRead["status"]
                                msg     = resValidaRead["msg"]  
                            except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                                status    = False 
                                msg       = f'Error interno ESTADO (4): {error}'

            else:
                status    = False 
                msg       = 'Error, solo se puede extraer textos a las SIC...'
        else:
            status    = False 
            msg       = 'Error de parametros, la API no recibió el archivo .PDF'
    else:
        status    = False 
        msg       = 'Error, el request de tipo {} es invalida'.format(request.method)
        
        
    respuesta = {
        "status":status,
        "msg":msg
    }  
    return jsonify(respuesta)


# Ruta para extraer la tabla del pdf (FIJACION) - method (POST) - JSON
@app.route('/extraer/fijacion', methods=['POST'])
def getextraerfijacion_json():
    if request.method == 'POST':
        #DATA RECIBIDA
        path_archivo        = request.json['path_pdf']   
        entidad             = request.json['ent_imagen']   
        especialidad        = request.json['esp_imagen']     
        # print( path_archivo ) 
        if ( path_archivo ):
            if (entidad=="95" and especialidad=="01"):   
                #VALIDACION No.1
                try:           
                    resValidaRead = validarColumnasTabulaFijacion(path_archivo, request.json, 1)    
                    status  = resValidaRead["status"]
                    msg     = resValidaRead["msg"] 
                except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                    status    = False 
                    msg       = f'Error interno FIJACION (1): {error}'
                    
                    
                #VALIDACION No.2
                if status==False: 
                    try:
                        resValidaRead = validarColumnasTabulaFijacion(path_archivo, request.json, 2)   
                        status  = resValidaRead["status"]
                        msg     = resValidaRead["msg"]  
                    except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                        status    = False 
                        msg       = f'Error interno FIJACION (2): {error}'
                        
                        
                    #VALIDACION No.3
                    if status==False: 
                        opc_stream =True
                        opc_lattice=False
                        try:
                            resValidaRead = validarColumnasTabulaFijacion(path_archivo, request.json, 1, opc_stream, opc_lattice)   
                            status  = resValidaRead["status"]
                            msg     = resValidaRead["msg"]  
                        except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                            status    = False 
                            msg       = f'Error interno FIJACION (3): {error}'
                        
                            
                        #VALIDACION No.4
                        if status==False: 
                            try:
                                resValidaRead = validarColumnasTabulaFijacion(path_archivo, request.json, 2, opc_stream, opc_lattice)   
                                status  = resValidaRead["status"]
                                msg     = resValidaRead["msg"]  
                            except (FileNotFoundError , tabula.errors.CSVParseError) as error:
                                status    = False 
                                msg       = f'Error interno FIJACION (4): {error}'
        
            else:
                status    = False 
                msg       = 'Error, solo se puede extraer textos a las SIC...'
        else:
            status    = False 
            msg       = 'Error de parametros, la API no recibió el archivo .PDF'
              
    else:
        status    = False 
        msg       = 'Error, el request es invalido'
       
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
    # app.run(host="localhost", port=9000, debug=False)
    
    #REMOTO - LOCAL:
    # serve(app, host="localhost", port=9000 )