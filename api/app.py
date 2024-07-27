
from flask import Flask, request , jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(app)
CORS(app)
login_manager.init_app(app)
login_manager.login_view = 'login'



"""
MODELAGEM DO USER---
{
id , 
username 
password
}
"""

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=True)
    cart = db.relationship('CartItem', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['POST'])
def login():
    data = request.json

    user = User.query.filter_by(username=data.get("username")).first()

    if user:
        if data.get('password') == user.password:
             login_user(user)
             return jsonify({"message": "login feito com sucesso"})
    return jsonify({'message': 'Usuario ou senha invalido'}), 401

@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": " Sua conta foi desconectada com sucesso"})

@app.route('/api/products/add', methods=["POST"])   
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data["name"], price=data["price"], description=data.get("description", ""))
        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Produto cadastrado com sucesso!"})
    return jsonify({"message": "Produto inválido"}), 400

@app.route('/api/products/delete/<int:product_id>', methods=["DELETE"])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Produto deletado com sucesso"})
    return jsonify({"message": "Não foi possivel deletar o produto. Por favor, adicione um produto ou verifique o seu login"}), 404


@app.route('/api/products/<int:product_id>', methods=["GET"])

def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name, 
            'price': product.price, 
            'description': product.description
        })
    return jsonify({'messege': 'Produto não encontrado'}), 404


@app.route('/api/products/update/<int:product_id>', methods=["PUT"])
@login_required
def update_product(product_id):

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Não foi possivel atualizar o produto"}), 404

    data = request.json
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']

    if 'description' in data:
        product.description = data['description']

    db.session.commit()
    return jsonify({'message': 'Produto atualizado com sucesso'})


@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        product_list.append(product_data)

    return jsonify(product_list)

#checkout
@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_card(product_id):

  user = User.query.get(int(current_user.id))
  product = Product.query.get(product_id)

  if user and product:
      cart_item = CartItem(user_id=user.id, product_id=product.id)
      db.session.add(cart_item)
      db.session.commit()
      return jsonify({'message': 'Produto adicionado ao carrinho com sucesso'})
  return jsonify({'message': 'Não foi possivel adicionar o produto ao carrinho'}), 400

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    # Produto, Usuario = Item no carrinho
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item removido com sucesso'})
    return jsonify({'message': 'Não foi possivel remover o item do carrinho'}), 400



@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(current_user.id)
    cart_items = user.cart
    cart_content = []
    for carts in cart_items:
        product = Product.query.get(carts.product_id)
        cart_content.append({

            "id": carts.id,
            "user_id": carts.user_id,
            "product_id": carts.product_id, 
            "product_name": product.name, 
            "product_price": product.price
        })

    return (cart_content)

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user= User.query.get(current_user.id)
    items_cart = user.cart
    for carts in items_cart:
        db.session.delete(carts)
    db.session.commit()
    
    return jsonify({'message': 'Checkout feito com sucesso'})

if __name__ == '__main__':
   
   app.run(debug=True)


