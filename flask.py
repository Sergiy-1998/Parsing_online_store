from flask import Flask, request, render_template, Response
from parser import get_product_items, filling_tables_product_data

app = Flask(__name__)


@app.route('/')
def my_form():
    return render_template('file.html')


@app.route('/', methods=['post'])
def my_form_post():
    user = request.form['text']  # отримання тексту з форми
    print(user)

    # parse site with user_input
    products_items = get_product_items(user)
    filling_tables_product_data(products_items)
    return Response(status=200)


if __name__ == '__main__':
    app.run(debug=True)
