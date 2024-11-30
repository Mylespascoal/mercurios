from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from datetime import datetime
import time
import mysql.connector
from mysql.connector import errorcode
from mysql.connector import pooling
import os

app = Flask(__name__)
app.secret_key = 'Mercurios'
db_config = {
	'user': 'root',
	'password': 'Mercurios',
	'host': 'localhost',
	'port': '3308',
	'database': 'WethCommerce',
}

db_pool = pooling.MySQLConnectionPool(
	pool_name="mypool",
	pool_size=5,
	**db_config
)

def get_db_connection():
	conn = db_pool.get_connection()
	return conn

@app.route('/')
def home():
	return (render_template('home.html'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute("SELECT * FROM vendedor WHERE name = %s AND password = %s", (username, password))
		user = cursor.fetchone()
		if user:
			session['id'] = user[0]
			return redirect('/loja_data')
		else:
			return "erro nas credenciais!"
	return render_template('login.html')
	cursor.close()
	conn.close

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		password = request.form['password']
		phone_number_1 = request.form['phone_number_1']
		phone_number_2 = request.form['phone_number_2']
		address = request.form['address']
		status = 'active'
		store_name = request.form['store_name']
		conn = mysql.connector.connect(**db_config)
		cursor = conn.cursor()
		cursor.execute("""INSERT INTO vendedor (name, email, password, phone_number_1, phone_number_2, address, status) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (name, email, password, phone_number_1, phone_number_2, address, status))
		conn.commit()
		vendedor_id = cursor.lastrowid
		cursor.execute("""INSERT INTO lojas (vendedor_id, nome) VALUES (%s, %s)""", (vendedor_id, store_name))
		conn.commit()
		return "usuario cadastrado com sucesso!"
	return render_template('cadastro.html')
	cursor.close()
	conn.close()
        	

@app.route('/perfil', methods=['GET'])
def perfil():
	vendedor_id = session['id']
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			cursor.execute("SELECT * FROM vendedor WHERE id = %s", (vendedor_id,))
			vendedor = cursor.fetchone()
			if vendedor:
				profile_data = {
				'id': vendedor[0],
				'name': vendedor[1],
				'email': vendedor[2],
				'phone_number_1': vendedor[4],
				'phone_number_2': vendedor[5],
				'address': vendedor[6]	
				}
				return render_template('perfil.html', profile_data=profile_data)
			else:
				return jsonify({'error': 'Vendedor não encontrado'}), 404
		finally:
			cursor.close()
			conn.close()
			
@app.route('/logout')
def logout():
	#session.pop('id', None)
	session.clear()
	return redirect('/')

@app.route('/perfil_data', methods=['GET', 'POST'])
def perfil_data():
	if 'id' not in session:
		flash("Por favor, faça login para acessar seu perfil.")	
		return redirect('/')
	vendedor_id = session['id']
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			cursor.execute("SELECT * FROM vendedor WHERE id = %s", (vendedor_id,))
			vendedor = cursor.fetchone()
			if vendedor:
				profile_data = {
				'name': vendedor[1],
				'email': vendedor[2],
				'phone_number_1': vendedor[4],
				'phone_number_2': vendedor[5],
				'address': vendedor[6]	
				}
				return render_template('perfil_data.html', profile_data=profile_data, active_page='perfil')
			else:
				return jsonify({'error': 'Vendedor não encontrado'}), 404
		finally:
			cursor.close()
			conn.close()

@app.route('/loja_data', methods=['GET', 'POST'])
def loja_data():
	if request.method == 'GET':
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		vendedor_id = session['id']
		print(type(vendedor_id))
		vendedor_id = session['id']
		print(f"vendedor_id: {vendedor_id}")  # Para verificar o valor do vendedor_id

		query = "SELECT * FROM produtos WHERE vendedor_id = %s"
		cursor.execute(query, (vendedor_id,))
		produtos = cursor.fetchall()
		query = "SELECT nome FROM lojas WHERE vendedor_id = %s"
		cursor.execute(query, (vendedor_id,))
		loja = cursor.fetchone()
		cursor.close()
		conn.close()
		loja_name = loja[0]
		return render_template('loja_data.html', produtos=produtos, loja=loja_name, active_page='loja')

@app.route('/adicionar_produto', methods=['GET', 'POST'])
def adicionar_produto():
	if request.method == 'POST':
		nome = request.form['nome']
		preco = request.form['preco']
		quantidade_estoque = request.form['quantidade_estoque']
		vendedor_id = session['id']
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		try:
			cursor.execute("SELECT id FROM lojas WHERE vendedor_id = %s", (vendedor_id,))
			loja = cursor.fetchone()
			if loja:
				loja_id = loja[0]
			else:
				print("ERROR: Loja nao encontrada para o vendedor.")
			query = "INSERT INTO produtos (nome, preco, quantidade_estoque, vendedor_id, loja_id) VALUES (%s, %s, %s, %s, %s)"
			cursor.execute(query, (nome, preco, quantidade_estoque, vendedor_id, loja_id))
			conn.commit()
			return redirect(url_for('loja_data'))
		finally:
			cursor.close()
			conn.close()
	return render_template('adicionar_produto.html')


@app.route('/deletar_produto', methods=['GET', 'POST'])
def deletar_produto():
	if request.method == 'POST':
		nome = request.form['nome']
		vendedor_id = session['id']
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		query = "DELETE FROM produtos WHERE nome = %s AND vendedor_id = %s"
		cursor.execute(query, (nome, vendedor_id))
		conn.commit()
		cursor.close()
		conn.close()
		return redirect(url_for('loja_data'))
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	vendedor_id = session['id']
	query = "SELECT nome FROM produtos WHERE vendedor_id = %s"
	cursor.execute(query, (vendedor_id,))
	produtos = cursor.fetchall()
	cursor.close()
	conn.close()
	return render_template('deletar_produto.html', produtos=produtos)


@app.route('/editar_produto', methods=['GET', 'POST'])
def editar_produto():
	if request.method == 'POST':
		nome_produto = request.form['nome_produto']
		novo_nome = request.form['novo_nome']
		novo_preco = request.form['novo_preco']
		nova_quantidade = request.form['nova_quantidade']
		vendedor_id = session['id']
		conn = mysql.connector.connect(**db_config)
		cursor  = conn.cursor()
		cursor.execute("SELECT id FROM produtos WHERE nome = %s AND vendedor_id = %s", (nome_produto, vendedor_id))
		result = cursor.fetchone()
		if result:
			id_produto = result[0]
			query = """ UPDATE produtos SET nome = %s, preco = %s, quantidade_estoque = %s WHERE id = %s AND vendedor_id = %s """
			cursor.execute(query, (novo_nome, novo_preco, nova_quantidade, id_produto, vendedor_id))
			conn.commit()
		cursor.close()
		conn.close()
		return redirect(url_for('loja_data'))
	conn = mysql.connector.connect(**db_config)
	cursor = conn.cursor()
	vendedor_id = session['id']
	query = "SELECT id, nome, preco, quantidade_estoque FROM produtos WHERE vendedor_id = %s"
	cursor.execute(query, (vendedor_id,))
	produtos = cursor.fetchall()
	cursor.close()
	conn.close()
	return render_template('editar_produto.html', produtos=produtos)

@app.route('/historico_vendas', methods=['GET'])
def historico_vendas():
	vendedor_id = session['id']
	if not vendedor_id:
		return jsonify({"error": "Vendedor ID é necessário"}), 400
	try:
		conn = get_db_connection()
		cursor = conn.cursor(dictionary=True)
		query = """SELECT id, produto_id, quantidade, preco_unitario, total, estado, data FROM vendas WHERE vendedor_id = %s ORDER BY data DESC"""
		cursor.execute(query, (vendedor_id, ))
		vendas = cursor.fetchall()
		cursor.close()
		conn.close()
		if vendas:
			return jsonify(vendas)
		else:
			return ("Error")
	except mysql.connector.Error as err:
		return jsonify({"error": f"Erro ao acessar o banco de dados: {err}"}), 500

@app.route('/analise_de_vendas', methods=['GET'])
def analise_de_vendas():
	vendedor_id = session['id']
	if not vendedor_id:
		return jsonify({"error": "Vendedor ID é necessário"}), 400
	try:
		conn = get_db_connection()
		cursor = conn.cursor(dictionary=True)
		query = """SELECT id, produto_id, quantidade, preco_unitario, total, estado, data 
			FROM vendas WHERE vendedor_id = %s ORDER BY data DESC"""
		cursor.execute(query, (vendedor_id,))
		vendas = cursor.fetchall()
		cursor.close()
		conn.close()
		if vendas:
			return render_template('analise_de_vendas.html', vendas=vendas)
		else:
			return render_template('analise_de_vendas.html', vendas=[])
	except mysql.connector.Error as err:
		return jsonify({"error": f"Erro ao acessar o banco de dados: {err}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5005)
		
