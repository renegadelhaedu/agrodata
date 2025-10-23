from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/dados', methods=['GET'])
def receber_dados():
    dados = request.values.get('percentual')

    print(dados)
    return 'ok',200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
