#LIBRERIAS
from flask import Flask, render_template, redirect, request, session,url_for    #Importo Flask y la estructra HTML, para las sessiones
from flask_mysqldb import MySQL                                         #Libreria de SQL
from datetime import datetime                                           #Libreria de fecha y hora
from flask import send_from_directory                                   #Libreria para obtener imagenes de una carpeta
import os 
from werkzeug.security import check_password_hash, generate_password_hash#Seguridad de la contraseña

#CREACION DE LA APLICACION
app=Flask(__name__)

#LLAVE SECRETA
app.secret_key = 'una_clave_secreta_muy_larga_y_aleatoria'

#CONEXION A BASE DE DATOS
mysql=MySQL()

# Configuración de la conexión a la base de datos
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'desarrollodesoftware'

# Inicializa MySQL
mysql = MySQL(app)

#RUTAS
@app.route('/')
def index():
    return redirect(url_for('login'))

#Login
@app.route('/login')
def login():
    return render_template('login.html')

#Buscar usuario y logearse
@app.route('/admin/login/iniciar', methods=['POST'])
def buscarUsuario():
    usuario = request.form['usuario']
    contraseña = request.form['contraseña']
 
    sql = "SELECT * FROM usuarios WHERE usuario = %s AND contraseña = %s"
    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute(sql, (usuario,contraseña))
    resultado = cursor.fetchone()
    if resultado:
        session["login"] = True
        session['id'] = resultado[0]
        session['nombre'] = resultado[3]
        session['idRol'] = resultado[4]
        if session['idRol'] == 1:
            session['idRol'] = "Administrador"
            return redirect(url_for('indexAdmin'))
        elif session['idRol'] == 2:
            session['idRol'] = "Repositor"
            return redirect(url_for('repositor'))
        elif session['idRol'] == 3:
            session['idRol'] = "Vendedor"
            return redirect(url_for('vendedor'))
    else:
        return redirect(url_for('login'))

#Cerrar Session
@app.route('/cerrarSession')
def logout():
    # Eliminar todas las claves de la sesión
    session.clear()
    # Redirigir al usuario a la página de inicio de sesión
    return redirect(url_for('login'))

#Cambiar contraseña
@app.route('/cambiarContraseña')
def cambiarContraseña():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login"):
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    return render_template("/admin/usuarios/cambiarContraseña.html", usuario=nombre_usuario)

#Modificar contraseña
@app.route('/cambiarContraseña/cambiar', methods=['POST'])
def actualizarContraseña():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login"):
        return redirect(url_for('login'))
    legajo = session.get('id')
    contraseña = request.form['contraseña']
    nuevaContraseña = request.form['nuevaContraseña']
    #Actualizo contraseña en base de datos
    sql = "UPDATE usuarios SET contraseña = %s WHERE contraseña = %s AND legajo = %s "
    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute(sql, (nuevaContraseña, contraseña, legajo))
    conexion.commit()
    # Verificar si se ha actualizado alguna fila
    if cursor.rowcount > 0:
        # Si se ha actualizado al menos una fila, redirige a la página de éxito
        return redirect(url_for('login'))
    else:
        # Si no se ha actualizado ninguna fila, redirige a la página de cambio de contraseña con un mensaje de error
        
        return redirect(url_for('cambiarContraseña'))

#ADMIN - Incio
@app.route('/admin')
def indexAdmin():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtiene el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    # Obtener la cantidad de ventas y ganancias diarias y mensuales
    fyh = datetime.now()
    fecha = fyh.strftime('%Y-%m-%d')
    año = fyh.year
    mes = fyh.month
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM ventas')
    ventas= cursor.fetchall()
    cantVentasDiario = 0
    recaudadoDiario = 0
    cantVentasMensuales = 0
    recaudadoMensual = 0
    gananciasDiarias = 0
    gananciasMensuales = 0
    for venta in ventas:
        fechaVenta = datetime.strptime(venta[2], '%Y-%m-%d')
        añoVenta = fechaVenta.year
        mesVenta = fechaVenta.month
        # Obtener cantidad de ventas diarias
        if venta[2] == fecha:
            cantVentasDiario += 1
            recaudadoDiario += venta[4]
            numVenta = venta[0]
            #Obtengo ganancias diarias
            cursor.execute('SELECT * FROM detalle_venta')
            detalleVenta= cursor.fetchall()
            cursor.execute('SELECT * FROM productos')
            productos= cursor.fetchall()
            for detalleVen in detalleVenta:
                if numVenta == detalleVen[0]:
                    cod = detalleVen[1]
                    cantidadVendida = detalleVen[2]
                    for producto in productos:
                        if producto[0] == cod:
                            x = (producto[5] - producto[4]) * cantidadVendida
                            gananciasDiarias += x  
        # Obtener cantidad de ventas mensuales
        if añoVenta == año and mesVenta== mes:
            cantVentasMensuales+= venta[4]
            recaudadoMensual += venta[4]
            numVenta = venta[0]
            #Obtengo ganancias mensuales
            cursor.execute('SELECT * FROM detalle_venta')
            detalleVenta= cursor.fetchall()
            cursor.execute('SELECT * FROM productos')
            productos= cursor.fetchall()
            for detalleVen in detalleVenta:
                if numVenta == detalleVen[0]:
                    cod = detalleVen[1]
                    cantidadVendida = detalleVen[2]
                    for producto in productos:
                        if producto[0] == cod:
                            x = (producto[5] - producto[4]) * cantidadVendida
                            gananciasMensuales += x
    # Obtener productos con poco stock 
    pocoStock = []
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    for producto in productos:
        if producto[6] <= producto[7]:
            pocoStock.append(producto)
    # Cantidad de ventas y recaudado por vendedor
    cursor.execute('SELECT * FROM usuarios WHERE idRol = 3')
    usuarios = cursor.fetchall()
    cursor.execute('SELECT * FROM ventas WHERE fecha = %s',(fecha,))
    ventas= cursor.fetchall()
    vendedores = []
    for usuario in usuarios:
        cantVentas = 0
        recaudado = 0
        for venta in ventas:
            if usuario[0] == venta[1]:
                recaudado += venta[4]
                cantVentas += 1
        vendedor = [usuario[0], usuario[3], cantVentas, recaudado]
        vendedores.append(vendedor)
    return render_template('admin/index.html', nombre_usuario = nombre_usuario, cantVentasDiario=cantVentasDiario, recaudadoDiario=recaudadoDiario, gananciasDiarias=gananciasDiarias, cantVentasMensuales=cantVentasMensuales, recaudadoMensual=recaudadoMensual, gananciasMensuales=gananciasMensuales, fecha=fecha, mes=mes, pocoStock=pocoStock, vendedores=vendedores)

#ADMIN - Usuarios
@app.route('/admin/usuarios')
def adminUsuarios():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    #Obtengo los datos
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios= cursor.fetchall()
    cursor.execute('SELECT * FROM roles')
    roles= cursor.fetchall()
    #print(usuarios)
    return render_template('admin/usuarios/usuarios.html',roles=roles, usuarios = usuarios, nombre_usuario=nombre_usuario)

#ADMIN - Registrar usuario
@app.route('/admin/usuarios/registrar', methods=['POST'])
def adminUsuariosRegistrar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtener los datos del formulario
    nombre = request.form['nombre']
    usuario = request.form['usuario']
    contraseña = request.form['contraseña']
    rol = request.form.get('rol')
    legajo = "NULL"
    if rol == "Administrador":
        rol = 1
    elif rol == "Repositor":
        rol = 2
    elif rol == "Vendedor":
        rol = 3
    #Hago consulta SQL y ejecuto
    sql = "INSERT INTO usuarios (`legajo`, `usuario`, `contraseña`, `nombre`, `idRol`) VALUES (%s, %s, %s, %s, %s)"
    conexion = mysql.connection
    cursor = conexion.cursor()
    cursor.execute(sql, (legajo, usuario, contraseña, nombre, rol))   
    conexion.commit()
    return redirect(url_for('adminUsuarios'))
   
#ADMIN - Borrar usuario
@app.route('/admin/usuarios/borrar', methods=['POST'])
def adminUsuariosBorrar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    #Obtengo el id del usuario a eliminar
    numLeg = request.form['legajo']
    cursor = mysql.connection.cursor()
    sql = "DELETE FROM usuarios WHERE legajo = %s"
    cursor.execute(sql, (numLeg,))
    mysql.connection.commit()
    return redirect(url_for('adminUsuarios'))

#ADMIN - Modificar usuario
@app.route('/admin/usuarios/modificar', methods=['POST'])
def adminUsuariosModificar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
   # Obtener los datos del formulario
    legajo = request.form['legajo']
    usuario = request.form['usuario']
    contraseña = request.form['contraseña']
    idRol= request.form['rol']
    # Conectar a la base de datos y obtener el cursor
    conexion = mysql.connection
    cursor = conexion.cursor()
    # Actualizar en la base de datos
    sql = "UPDATE usuarios SET usuario = %s, contraseña = %s, idRol = %s WHERE legajo = %s"
    cursor.execute(sql, (usuario, contraseña, idRol, legajo))
    conexion.commit()
    return redirect(url_for('adminUsuarios'))

#ADMIN - Productos
@app.route('/admin/productos')
def AdminProductos():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categorias')
    categorias= cursor.fetchall()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    return render_template('/admin/productos/productos.html', categorias=categorias, productos = productos, nombre_usuario = nombre_usuario)

#ADMIN - Registrar producto
@app.route('/admin/productos/registrar', methods=['POST'])
def adminProductoRegistrar():
     # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtener los datos del formulario
    nombre = request.form['nombre'].strip()
    descripcion = request.form['descripcion'].strip()
    precioCompra = int(request.form['precioCompra'])
    precioVenta = int(request.form['precioVenta'])
    stock = int(request.form['stock'])
    stockMin = int(request.form['stockMin'])
    categoria = request.form['categoria']
    # Verifico si está el producto en la base de datos
    cursor = mysql.connection.cursor()
    sql_select = "SELECT * FROM productos WHERE nombre = %s AND descripcion = %s AND idCategoria = %s"
    cursor.execute(sql_select, (nombre, descripcion, categoria))
    producto = cursor.fetchone()
    if producto:
        # Producto existente
        stock = producto[6] + stock
        codigo = producto[0]
        sql_update = "UPDATE productos SET precioCompra = %s, precioVenta = %s, stock = %s, stockMin = %s WHERE cod = %s"
        cursor.execute(sql_update, (precioCompra, precioVenta, stock, stockMin, codigo))
        mysql.connection.commit()
    else:
        # En caso de que no esté el producto, se registra
        sql = "INSERT INTO productos (nombre, descripcion, idCategoria, precioCompra, precioVenta, stock, stockMin) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(sql, (nombre, descripcion, categoria, precioCompra, precioVenta, stock, stockMin))
        mysql.connection.commit()
    return redirect(url_for('AdminProductos'))

#ADMIN - Modificar producto
@app.route('/admin/productos/modificar', methods=['POST'])
def adminProductoActualizar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtener los datos del formulario
    codigo = request.form['codigo']
    stock = request.form['stock']
    stockMin = request.form['stockMin']
    precioCompra = request.form['precioCompra']
    precioVenta = request.form['precioVenta']

    # Actualizar el producto en la base de datos
    sql = "UPDATE productos SET precioCompra=%s, precioVenta=%s, stock=%s, stockMin=%s WHERE cod=%s"
    # Obtener la conexión y el cursor
    conexion = mysql.connection
    cursor = conexion.cursor()

    # Ejecutar la consulta SQL
    cursor.execute(sql, ( precioCompra, precioVenta, stock, stockMin, codigo))

    # Confirmar los cambios
    conexion.commit()

    # Redirigir de nuevo a la página de productos
    return redirect('/admin/productos')

#ADMIN - Eliminar producto
@app.route('/admin/productos/eliminar', methods=['POST'])
def adminProductoEliminar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    #Obtengo el codigo del producto a eliminar
    codigo = request.form['codigo']
    cursor = mysql.connection.cursor()
    sql = "DELETE FROM productos WHERE cod = %s"
    cursor.execute(sql, (codigo,))
    mysql.connection.commit()
    return redirect(url_for('AdminProductos'))

#ADMIN - Categorias de productos
@app.route('/admin/categorias')
def adminCategorias():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categorias')
    categorias= cursor.fetchall()
    return render_template('/admin/productos/categorias.html', categorias=categorias, nombre_usuario = nombre_usuario)

#ADMIN - Registrar categoria de productos
@app.route('/admin/categorias/registrar', methods=['POST'])
def adminCategoriaRegistrar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    #Obtengo los datos del formulario
    nombre = request.form['nombre']

    #Preparo la secuencia
    sql = "INSERT INTO categorias (nombre) VALUES (%s)"

    # Obtengo la conexión y el cursor
    conexion = mysql.connection
    cursor = conexion.cursor()

    # Ejecuto la consulta SQL
    cursor.execute(sql, (nombre,))
    
    # Confirmar los cambios
    conexion.commit()

    return redirect(url_for('adminCategorias'))

#ADMIN - Eliminar categoria producto
@app.route('/admin/categorias/eliminar', methods=['POST'])
def adminCategoriaEliminar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    #Obtengo el codigo del producto a eliminar
    id = request.form['id']
    cursor = mysql.connection.cursor()
    sql = "DELETE FROM categorias WHERE id = %s"
    cursor.execute(sql, (id,))
    mysql.connection.commit()
    return redirect(url_for('adminCategorias'))

#ADMIN - Venta
@app.route('/admin/ventas')
def adminVenta():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    # Elimino productos sin stock
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM productos WHERE stock = 0')
    productos= cursor.fetchall()
    for producto in productos:
        sql = "DELETE FROM productos WHERE cod = %s"
        cod = int(producto[0])
        cursor.execute(sql, (cod,))
        mysql.connection.commit() 
    # Calculo total de la compra
    total = 0
    cantProductos=0
    cursor.execute('SELECT * FROM detalle_venta WHERE numVenta = 0')
    productosCarrito = cursor.fetchall()
    for productoCarrito in productosCarrito:
        cantProductos += 1 * productoCarrito[2]
        codProducto = productoCarrito[1]
        cursor.execute('SELECT * FROM productos WHERE cod = %s', (codProducto,))
        producto = cursor.fetchone()
        if producto:
            total += producto[5] * productoCarrito[2]
    #Muestro productos con stock
    cursor.execute('SELECT * FROM categorias')
    categorias= cursor.fetchall()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    return render_template('/admin/ventas/index.html', categorias=categorias, productos = productos, nombre_usuario = nombre_usuario, total=total, cantProductos=cantProductos)

#ADMIN - Venta - Agregar producto al carrito
@app.route('/admin/venta/agregarProducto', methods=['POST'])
def adminAgregarProductoVenta():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    codigo = int(request.form['codigo'])
    cantidad = int(request.form['cantidad'])
    for producto in productos:
        codProd=int(producto[0])
        if codProd == codigo:
            #Si alcanza el stock
            if cantidad <= producto[6]:
                sql = "INSERT INTO detalle_venta (numVenta,codProducto,cantidad) VALUES (%s,%s,%s)"
                conexion = mysql.connection
                cursor.execute(sql, (0,codigo,cantidad))
                conexion.commit()
                # Actualizar el stock del producto
                nuevoStock = producto[6] - cantidad
                sql = "UPDATE productos SET  stock=%s WHERE cod=%s"
                cursor.execute(sql, ( nuevoStock, codigo))
                conexion.commit()
                return redirect(url_for('adminVenta'))
    return "No alcanza el stock"

#ADMIN - Venta - Comprar
@app.route('/admin/ventas/comprar', methods=['POST'])
def adminComprar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login')) 
    legajo_usuario = session.get('id')
    fyh = datetime.now()
    fecha = fyh.strftime('%Y-%m-%d')
    hora = fyh.strftime('%H:%M:%S')
    cursor = mysql.connection.cursor()
    # Obtener detalles de venta
    cursor.execute("SELECT * FROM detalle_venta WHERE numVenta = 0")
    detalles = cursor.fetchall() 
    # Calcular el precioTotal y la cantidad total
    cantidad = 0
    total = 0
    for detalle in detalles:
        codigo = int(detalle[1])
        cantidad += detalle[2]
        cursor.execute("SELECT * FROM productos WHERE cod = %s", (codigo,))
        productos = cursor.fetchall()
        for producto in productos:
            total += producto[5] * detalle[2]
    # Crear la venta
    sql = "INSERT INTO ventas (legVendedor,fecha, hora, precioTotal) VALUES (%s,%s, %s, %s)"
    cursor.execute(sql, (legajo_usuario,fecha, hora, total))
    mysql.connection.commit()
    # Obtener el numVenta recién insertado
    cursor.execute("SELECT numVenta FROM ventas WHERE fecha = %s AND hora = %s", (fecha, hora))
    numVenta_row = cursor.fetchone()
    if numVenta_row:
        numVenta = numVenta_row[0]  # Obtener el primer elemento de la tupla
        # Actualizar detalle_venta con numVenta
        sql = "UPDATE detalle_venta SET numVenta = %s WHERE numVenta = 0"
        cursor.execute(sql, (numVenta,))
        mysql.connection.commit()
    cursor.close()
    return redirect(url_for('adminVenta'))

#ADMIN - Venta - Cancelar compra
@app.route('/admin/ventas/cancelar')
def adminCompraCancelar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de vendedor (idRol == "Administrador")
    if not session.get("login") or session.get("idRol") != "Administrador":
        return redirect(url_for('login'))
    # Obtengo la conexión
    cursor = mysql.connection.cursor()
    # Actualizo el stock a como estaba antes de agregar al carrito
    cursor.execute("SELECT * FROM detalle_venta WHERE numVenta = 0")
    detalle_ventas = cursor.fetchall()
    for detalle_venta in detalle_ventas:
        codigo = detalle_venta[1]
        cantidad = detalle_venta[2]
        # Selecciona todos los productos con el código
        cursor.execute("SELECT * FROM productos WHERE cod = %s", (codigo,))
        productos = cursor.fetchall()
        # Actualizo el stock
        for producto in productos:
            stock = producto[6]
            stockActualizado = stock + cantidad
            cursor.execute("UPDATE productos SET stock = %s WHERE cod = %s", (stockActualizado, codigo))
            mysql.connection.commit()
    # Elimino el detalle_venta con numVenta = 0
    sql_delete = "DELETE FROM detalle_venta WHERE numVenta = 0"
    cursor.execute(sql_delete)
    mysql.connection.commit()
    return redirect(url_for('adminVenta'))

#REPOSITOR - Inicio
@app.route('/repositor')
def repositor():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de repositor
    if not session.get("login") or session.get("idRol") != "Repositor":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    #Obtengo los datos para mostrar en la pagina
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categorias')
    categorias= cursor.fetchall()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    return render_template('/sitio/repositor/index.html', categorias=categorias, productos = productos, nombre_usuario = nombre_usuario)

#REPOSITOR - Registrar producto
@app.route('/repositor/producto/registrar', methods=['POST'])
def RepositorProductoAgregar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Repositor":
        return redirect(url_for('login'))
    # Obtener los datos del formulario
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    categoria = request.form['categoria']
    stock = int(request.form['stock'])
    stockMin = int(request.form['stockMin'])
    precioCompra = int(request.form['precioCompra'])
    precioVenta = int(request.form['precioVenta'])
    #Registro producto
    conexion = mysql.connection
    cursor = conexion.cursor()
    sql = "INSERT INTO productos (nombre, descripcion, idCategoria, precioCompra, precioVenta, stock, stockMin) VALUES (%s,%s,%s,%s,%s,%s,%s)"            
    cursor.execute(sql, (nombre, descripcion, categoria, precioCompra, precioVenta, stock, stockMin))
    conexion.commit()
    return redirect(url_for('repositor'))

#REPOSITOR - Actualizar producto
@app.route('/repositor/producto/actualizar', methods=['POST'])
def RepositorProductoActualizar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Repositor":
        return redirect(url_for('login'))
    # Obtener los datos del formulario
    codigo = int(request.form['codigo'])
    precioCompra = int(request.form['precioCompra'])
    precioVenta = int(request.form['precioVenta'])
    stock = int(request.form['stock'])
    stockMin = int(request.form['stockMin'])
    
    #Actualizo el stock
    conexion = mysql.connection
    cursor = conexion.cursor()
    sql = "UPDATE productos SET precioCompra = %s, precioVenta = %s, stock = %s, stockMin = %s WHERE cod = %s"
    cursor.execute(sql, (precioCompra, precioVenta, stock, stockMin, codigo))
    mysql.connection.commit()
    return redirect(url_for('repositor'))

#REPOSITOR - Eliminar producto
@app.route('/repositor/producto/eliminar', methods=['POST'])
def repositorProductoEliminar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Repositor":
        return redirect(url_for('login'))
    #Elimino el producto
    codigo = request.form['codigo']
    cursor = mysql.connection.cursor()
    sql = "DELETE FROM productos WHERE cod = %s"
    cursor.execute(sql, (codigo,))
    mysql.connection.commit()
    return redirect(url_for('repositor'))

#VENDEDOR - Inicio
@app.route('/vendedor')
def vendedor():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Vendedor":
        return redirect(url_for('login'))
    # Obtengo el nombre del usuario desde la sesión
    nombre_usuario = session.get('nombre')
    cursor = mysql.connection.cursor()
    # Elimino productos sin stock
    cursor.execute('SELECT * FROM productos WHERE stock = 0')
    productos= cursor.fetchall()
    for producto in productos:
        sql = "DELETE FROM productos WHERE cod = %s"
        cod = int(producto[0])
        cursor.execute(sql, (cod,))
        mysql.connection.commit()
    # Calculo total de la compra
    total = 0
    cantProductos=0
    cursor.execute('SELECT * FROM detalle_venta WHERE numVenta = 0')
    productosCarrito = cursor.fetchall()
    for productoCarrito in productosCarrito:
        cantProductos += 1 * productoCarrito[2]
        codProducto = productoCarrito[1]
        cursor.execute('SELECT * FROM productos WHERE cod = %s', (codProducto,))
        producto = cursor.fetchone()
        if producto:
            total += producto[5] * productoCarrito[2]
    #Muesto productos y categorias en la lista
    cursor.execute('SELECT * FROM categorias')
    categorias= cursor.fetchall()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    return render_template('/sitio/vendedor/index.html', categorias=categorias, productos = productos, nombre_usuario = nombre_usuario, total=total, cantProductos=cantProductos)

#VENDEDOR - Agregar producto al carrito
@app.route('/vendedor/producto/agregar', methods=['POST'])
def vendedorAgregarProductoVenta():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Vendedor":
       return redirect(url_for('login'))
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM productos')
    productos= cursor.fetchall()
    codigo = int(request.form['codigo'])
    cantidad = int(request.form['cantidad'])
    for producto in productos:
        codProd=int(producto[0])
        if codProd == codigo:
            #Si alcanza el stock
            if cantidad <= producto[6]:
                print("Enttre al segundo if")
                sql = "INSERT INTO detalle_venta (numVenta,codProducto,cantidad) VALUES (%s,%s,%s)"
                conexion = mysql.connection
                cursor.execute(sql, (0,codigo,cantidad))
                conexion.commit()
                # Actualizar el stock del producto
                nuevoStock = producto[6] - cantidad
                sql = "UPDATE productos SET  stock=%s WHERE cod=%s"
                cursor.execute(sql, ( nuevoStock, codigo))
                conexion.commit()
                return redirect(url_for('vendedor'))
    return "No alcanza el stock"

#VENDEDOR - Comprar
@app.route('/vendedor/comprar', methods=['POST'])
def VendedorComprar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de administrador (idRol == 1)
    if not session.get("login") or session.get("idRol") != "Vendedor":
        return redirect(url_for('login'))
    legajo_usuario = session.get('id')
    fyh = datetime.now()
    fecha = fyh.strftime('%Y-%m-%d')
    hora = fyh.strftime('%H:%M:%S')
    cursor = mysql.connection.cursor()
    # Obtener detalles de venta
    cursor.execute("SELECT * FROM detalle_venta WHERE numVenta = 0")
    detalles = cursor.fetchall() 
    # Calcular el precioTotal y la cantidad total
    cantidad = 0
    total = 0
    for detalle in detalles:
        codigo = int(detalle[1])
        cantidad += detalle[2]
        cursor.execute("SELECT * FROM productos WHERE cod = %s", (codigo,))
        productos = cursor.fetchall()
        for producto in productos:
            total += producto[5] * detalle[2]
    # Crear la venta
    sql = "INSERT INTO ventas (legVendedor,fecha, hora, precioTotal) VALUES (%s,%s, %s, %s)"
    cursor.execute(sql, (legajo_usuario, fecha, hora, total))
    mysql.connection.commit()
    # Obtener el numVenta recién insertado
    cursor.execute("SELECT numVenta FROM ventas WHERE fecha = %s AND hora = %s", (fecha, hora))
    numVenta_row = cursor.fetchone()
    if numVenta_row:
        numVenta = numVenta_row[0]  # Obtener el primer elemento de la tupla
        # Actualizar detalle_venta con numVenta
        sql = "UPDATE detalle_venta SET numVenta = %s WHERE numVenta = 0"
        cursor.execute(sql, (numVenta,))
        mysql.connection.commit()
    cursor.close()
    return redirect(url_for('vendedor'))

#VENDEDOR - Cancelar compra
@app.route('/vendedor/cancelarCompra')
def vendedorCompraCancelar():
    # Verifica si el usuario ha iniciado sesión y si tiene el rol de vendedor (idRol == "Vendedor")
    if not session.get("login") or session.get("idRol") != "Vendedor":
        return redirect(url_for('login'))
    # Obtengo la conexión
    cursor = mysql.connection.cursor()
    # Actualizo el stock a como estaba antes de agregar al carrito
    cursor.execute("SELECT * FROM detalle_venta WHERE numVenta = 0")
    detalle_ventas = cursor.fetchall()
    for detalle_venta in detalle_ventas:
        codigo = detalle_venta[1]
        cantidad = detalle_venta[2]
        # Selecciona todos los productos con el código
        cursor.execute("SELECT * FROM productos WHERE cod = %s", (codigo,))
        productos = cursor.fetchall()
        # Actualizo el stock
        for producto in productos:
            stock = producto[6]
            stockActualizado = stock + cantidad
            cursor.execute("UPDATE productos SET stock = %s WHERE cod = %s", (stockActualizado, codigo))
            mysql.connection.commit()
    # Elimino el detalle_venta con numVenta = 0
    sql_delete = "DELETE FROM detalle_venta WHERE numVenta = 0"
    cursor.execute(sql_delete)
    mysql.connection.commit()
    return redirect(url_for('vendedor'))

@app.route('/prueba')
def prueba():
    return render_template('/sitio/prueba.html')
#EJECUCION DE APP
if __name__=='__main__':
    app.run(debug=True)