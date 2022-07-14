from pyxlsb import open_workbook as open_xlsb
from pyxlsb import convert_date
import sys, datetime, pymysql

# ------ PIP ------
# pip install pyxlsb https://pypi.org/project/pyxlsb/

class Convertidor:
    
    def __init__(self, tabla):
        #--------BASE DE DATOS---------
        #self.BD     = "db_lupajuridica"
        #self.BD     = "jurix_cali"
        self.BD     = "control_mineducacion"
        #------------TABLA--------------
        self.tabla  = tabla

    def extraerColumnasFechas(self,Row):
        columnas_fecha = []
        columna = 0
        for r in Row:
            if ( 'FECHA' in str(r).encode(encoding="utf-8",errors="xmlcharrefreplace").decode("utf-8").upper()):
                columnas_fecha.append(columna)
                
            columna += 1
        # print(columnas_fecha)
        return columnas_fecha

    def convertirXLSB(self,nombre_excelXLSB, extraer_campos = 0):
        with open_xlsb(nombre_excelXLSB) as wb:
            with wb.get_sheet(1) as sheet:
                fila = 0
                columnas_fecha = []
                for row in sheet.rows():
                    row_aux = [None if item.v == None else str(item.v).replace('', ' ').encode(encoding="utf-8",errors="xmlcharrefreplace") for item in row]
                    
                    if(fila==0):
                        campos_tabla = [None if item.v == None else str(item.v).replace('', ' ').encode(encoding="utf-8",errors="xmlcharrefreplace").decode("utf-8") for item in row]
                        if(extraer_campos == 1):                  
                            self.crear_tabla(campos_tabla)
                            break
                        else:
                            campos_tabla_insert = campos_tabla
                        columnas_fecha = self.extraerColumnasFechas(row_aux)
                    if(fila==1):
                        print('Empieza lectura...')
                        print("Tiempo de inicio: {}".format(datetime.datetime.now().strftime("%X")))
                    try:
                        if(fila>0):
                            row_aux = [None if item.v == None else str(item.v).replace('', ' ').encode("utf-8").decode("utf-8") for item in row]
                            self.conversionFechasFila(columnas_fecha, row_aux)
                            # print(row_aux)
                            self.insertar_registros_tabla(campos_tabla_insert, row_aux)
                    except ValueError as error:
                        print(f'error de escritura para la fila: {fila}, \n error: {error}')
                        quit()
                    
                    fila+=1
        if extraer_campos == 0:
            print('Termina lectura...')
            print("Tiempo de fin: {}".format(datetime.datetime.now().strftime("%X")))
         
    def conversionFechasFila(self,columnafecha=[], row=[]):
        if(len(columnafecha) > 0):
            for cf in columnafecha:                      
                if( row[cf] != None and row[cf].replace('.', '').isnumeric() and len(row[cf]) <= 8):
                    
                    row[cf]=convert_date(float(row[cf])).strftime("%Y-%m-%d").encode(encoding="utf-8").decode("utf-8") 
            # exit()
        
    def conexion(self):
        try:
            conexion = pymysql.connect(
                                        host='localhost',
                                        user='db_user',
                                        password='Lupa-12312423$$**12',
                                        db= self.BD
                                    )
            # print("Conexión correcta")
        except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
            print("Ocurrió un error al conectar: ", e)
            exit()

        return conexion

    def existe_tabla(self):
        conx = self.conexion()
        with conx.cursor() as cursor:
            sql = "SELECT COUNT(*) AS cantidad FROM information_schema.tables WHERE 1 AND table_schema = '"+str(self.BD)+"' AND table_name = '"+str(self.tabla)+"' ;"
            cursor.execute(sql)
            fila = cursor.fetchone()
            
            if(fila[0] > 0):
                print("La tabla '"+self.tabla+"' se encuentra registrada, se empezará a convertir e insertar los datos del arhivo a la Base de Datos...\n")
                self.convertirXLSB(sys.argv[1])
            else:
                print(f"\nCreando la tabla {self.tabla}...")
                self.convertirXLSB(sys.argv[1], 1)
                self.existe_tabla()
                
    def crear_tabla(self,campos_tabla):
        conx = self.conexion()
        with conx.cursor() as cursor:
            # print(campos_tabla)
            sql = "CREATE TABLE "+self.BD+"."+self.tabla+" (`id` INT(10) UNSIGNED NOT NULL AUTO_INCREMENT ";

            if len(campos_tabla) > 0:        
                for campo in campos_tabla:
                    campo_aux = str(campo).replace(' ','_').lower()[0:64]
                    
                    
                    sql += ", `"+campo_aux+"` TEXT DEFAULT NULL "
                       
            sql += ', PRIMARY KEY (`id`) '
            sql += ') ENGINE=MYISAM DEFAULT CHARSET=utf8 '
            # print(sql)
            # exit()
            cursor.execute(sql)
            conx.commit()
            print("La tabla '"+self.tabla+"' fue creada con exito!")
    
    def insertar_registros_tabla(self,campos_tabla, registros):
        conx = self.conexion()
          
        with conx.cursor() as cursor:
            
            sql = "INSERT IGNORE INTO "+self.BD+"."+self.tabla+" (id" 
            if (campos_tabla and registros):
                for campos_tabla_aux in campos_tabla:
                    if campos_tabla_aux != None:
                        campos_tabla_aux = str(campos_tabla_aux).replace(' ','_').lower()[0:64]
                        sql += ", `"+campos_tabla_aux+"`"
                    # print(campos_tabla_aux)
                # print("\n"+sql)
                # exit()
            sql += ") "
            sql += "VALUES (NULL"
            
            if (campos_tabla and registros):
                for registros_aux in registros:                
                    if registros_aux:                 
                        registros_aux = str(registros_aux).replace("'",'').replace('"','').replace("´",'').replace('\\','')
                        sql += ", '"+registros_aux+"'"
                    else:
                        sql += ", ''"
                        
            sql += ")";
            # print("\n"+sql)
            # exit()
            try:
                cursor.execute(sql)
                conx.commit()
            except pymysql.err.ProgrammingError as error:
                raise ValueError(f'error de consulta: {sql} \n error: {error}')

