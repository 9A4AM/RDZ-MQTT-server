import paho.mqtt.client as mqtt
import json
from flask import Flask, render_template, jsonify
from flask import current_app as app  
from models import db, Radiosonda
from datetime import datetime

DATABASE = "sqlite:///radiosonde.db"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
db.init_app(app)

# Kreiranje baze podataka ako ne postoji
with app.app_context():
    db.create_all()  # Stvori sve tablice definirane u SQLAlchemy modelima

# Callback funkcija za povezivanje na broker
def on_connect(client, userdata, flags, rc):
    print("Connected to Mosquitto!")
    client.subscribe("rdz_sonde_server/packet")  # Pretplata na packet temu

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())  # Dekodiraj MQTT poruku
        # print(f"Received data: {data}")  # Ispis podataka

        # Provjeri postoji li 'vframe' i koristi ga za provjeru duplikata
        vframe_value = int(data.get("vframe"))
        ser_value = data.get('ser')  # Dohvati serijski broj

        if vframe_value is None or ser_value is None:
            print("No vframe or serial number found, skipping message")
            return  # Preskoči unos ako nema vframe ili ser

        with app.app_context():  # Postavi aplikacijski kontekst
            # Provjeri postoji li već zapis s istim vframe brojem i serijskim brojem
            existing_entry = Radiosonda.query.filter(Radiosonda.vframe == vframe_value, Radiosonda.ser == ser_value).first()

            if existing_entry:
                print(f"Duplicate vframe={vframe_value} and serial={ser_value} detected!")
                return  # Preskoči unos ako već postoji isti vframe i ser

            # Ako vframe ne postoji, dodaj novi unos u bazu
            new_entry = Radiosonda(
                lat=data.get('lat'),
                lon=data.get('lon'),
                alt=data.get('alt'),
                speed=data.get('speed'),
                dir=data.get('dir'),
                type=data.get('type'),
                ser=ser_value,
                time=datetime.fromtimestamp(data.get('time')) if "time" in data else None,  # Pretvori u datetime
                sats=data.get('sats'),
                freq=data.get('freq'),
                rssi=data.get('rssi'),
                vs=data.get('vs'),
                hs=data.get('hs'),
                climb=data.get('climb'),
                temp=data.get('temp'),
                humidity=data.get('humidity'),
                frame=data.get('frame'),
                vframe=vframe_value,  
                launchsite=data.get('launchsite'),
                batt=data.get('batt')
            )

            db.session.add(new_entry)
            db.session.commit()

            print(f"Saved: {data}")

    except Exception as e:
        print(f"Error processing message: {e}")




# Kreiranje MQTT klijenta
client = mqtt.Client()
client.on_connect = on_connect  # Postavljanje callback funkcije za povezivanje
client.on_message = on_message  # Postavljanje callback funkcije za poruke

# Povezivanje na Mosquitto broker (lokalni ili remote)
client.connect("localhost", 1883, 60)

# Pokretanje MQTT klijenta u pozadini
client.loop_start()

@app.route("/")
def index():
    return render_template("index.html")  # Provjerite da imate ovu HTML datoteku

@app.route("/data")
def get_data():
    subquery = db.session.query(
        Radiosonda.ser, db.func.max(Radiosonda.vframe).label("max_frame")
    ).group_by(Radiosonda.ser).subquery()

    data = db.session.query(Radiosonda).filter(
        db.and_(
            Radiosonda.ser == subquery.c.ser,
            Radiosonda.vframe == subquery.c.max_frame,
            Radiosonda.lat.isnot(None),  # Filtriraj NULL lat
            Radiosonda.lon.isnot(None),  # Filtriraj NULL lon
            Radiosonda.ser.isnot(None),  # Filtriraj NULL ser
            Radiosonda.alt.isnot(None),  # Filtriraj NULL alt
            Radiosonda.speed.isnot(None),  # Filtriraj NULL speed
            Radiosonda.climb.isnot(None)   # Filtriraj NULL climb
        )
    ).all()

    return jsonify([{
        "lat": r.lat, "lon": r.lon, "alt": r.alt, "speed": r.speed, "dir": r.dir,
        "type": r.type, "ser": r.ser, "time": r.time, "sats": r.sats,
        "freq": r.freq, "rssi": r.rssi, "vs": r.vs, "hs": r.hs, "climb": r.climb,
        "temp": r.temp, "humidity": r.humidity, "frame": r.frame, "vframe": r.vframe,
        "launchsite": r.launchsite, "batt": r.batt
    } for r in data])




if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=1111)
