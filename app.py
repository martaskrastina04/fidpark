from flask import Flask, render_template, request, redirect, url_for
import requests
from requests.auth import HTTPBasicAuth
from waitress import serve

app = Flask(__name__)

#FIDPARK API autentifikācija
API_LOGIN_URL = "https://demo1.fidpark.com/api/v1/Account/login"
API_URL = "https://demo1.fidpark.com/api/v1/Clients"
USERNAME = "demo"
PASSWORD = "Demo12345"

#Funkcija autentifikācijai un token iegūšanai
def get_bearer_token():
    login_data = {
        "Username": USERNAME,
        "Password": PASSWORD
    }

    response = requests.post(API_LOGIN_URL, json=login_data, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    
    #Pārbaudei
    print(f"Atbilde no servera: {response.status_code}")
    print(f"Atbildes teksts: {response.text}")
    
    if response.status_code == 200:
        bearer_token = response.json().get('Token')
        if bearer_token:
            print("Token saņemts veiksmīgi!")
            return bearer_token
        else:
            print("Token nav atgriezts!")
            return None
    else:
        print(f"Kļūda autentifikācijā: {response.status_code}, {response.text}")
        return None

#Funkcija klientu datu iegūšanai no API
def get_clients(bearer_token):
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(API_URL, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"Kļūda saņemot klientus: {response.status_code}, {response.text}")
        return []

#Funkcija, lai iegūtu klienta detalizēto informāciju
def get_client_details(bearer_token, client_id):
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(f"{API_URL}/{client_id}", headers=headers)
    
    if response.status_code == 200:
        return response.json() 
    else:
        print(f"Kļūda saņemot klienta datus: {response.status_code}, {response.text}")
        return {}
    
#Sākuma lapa
@app.route('/')
@app.route('/index')
def index():
    bearer_token = get_bearer_token()
    if not bearer_token:
        return "Autentifikācija neizdevās!", 500

    clients = get_clients(bearer_token) 
    
    search_by = request.args.get('search_by')
    query = request.args.get('query')

    if search_by and query:
        query = query.lower()
        clients = [
            client for client in clients
            if query in str(client.get(search_by, '')).lower()
        ]

    return render_template('index.html', clients=clients)


#Konkrētā klienta lapa
@app.route('/client/<int:client_id>')
def client_details(client_id):
    bearer_token = get_bearer_token()
    
    if not bearer_token:
        return "Autentifikācija neizdevās!", 500
    
    client = get_client_details(bearer_token, client_id)
    
    if not client:
        return "Klienta dati nav pieejami!", 404
    
    return render_template('client_details.html', client=client)

#Klientu meklēšanas lapa
@app.route('/search')
def search_clients():
    token = get_bearer_token()
    clients = get_clients(token)

    filter_by = request.args.get('filter_by')
    query = request.args.get('query', '').strip().lower()

    if not filter_by or not query:
        return redirect(url_for('index'))

    filtered_clients = [
        client for client in clients 
        if query in str(client.get(filter_by, '')).lower()
    ]

    return render_template('index.html', clients=filtered_clients)

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)

