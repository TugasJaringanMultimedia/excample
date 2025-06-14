# app.py
from flask import Flask
from models import db
from routes.penyiar_routes import penyiar_bp
from routes.client_routes import client_bp

app = Flask(__name__)
app.secret_key = "secret-key-radio"

# Koneksi ke MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/suara_radio_mahasiswa'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inisialisasi DB
db.init_app(app)

# Register blueprint
app.register_blueprint(penyiar_bp)
app.register_blueprint(client_bp)

# Buat tabel jika belum ada
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
