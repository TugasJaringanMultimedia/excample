# models.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class RekamanSiaran(db.Model):
    __tablename__ = 'rekaman_siaran'

    id = db.Column(db.Integer, primary_key=True)
    judul = db.Column(db.String(100), nullable=False)
    tanggal = db.Column(db.String(20), nullable=False)
    waktu_mulai = db.Column(db.String(20), nullable=False)
    waktu_berakhir = db.Column(db.String(20), nullable=False)
    nama_file = db.Column(db.String(150), nullable=False)

    def __repr__(self):
        return f'<Rekaman {self.judul} - {self.tanggal}>'
