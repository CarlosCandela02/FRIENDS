import requests
import pandas as pd
import time

API_KEY = "eadf9d83715cdebdaf48bbd2e448a9d7"
TV_ID = 1668  # ID oficial de Friends en TMDB

print("Descargando episodios de Friends en español desde TMDB...")
episodios = []

for temporada in range(1, 11):
    # El parámetro language=es-ES nos da los textos en español de España
    # Usa es-MX si prefieres español latino
    url = f"https://api.themoviedb.org/3/tv/{TV_ID}/season/{temporada}?api_key={API_KEY}&language=es-ES"
    
    respuesta = requests.get(url)
    
    if respuesta.status_code == 200:
        datos = respuesta.json()
        for ep in datos.get('episodes', []):
            episodios.append({
                "temporada": ep['season_number'],
                "episodio": ep['episode_number'],
                "titulo": ep['name'],
                "descripcion": ep['overview']
            })
        print(f"✅ Temporada {temporada} descargada.")
    else:
        print(f"❌ Error en temporada {temporada}. Código: {respuesta.status_code}")
        
    time.sleep(0.25) # Pausa para respetar los límites de la API

# Guardar en local
df = pd.DataFrame(episodios)
df.to_csv('friends_espanol.csv', index=False, encoding='utf-8')
print("\n¡Listo! Archivo 'friends_espanol.csv' generado con éxito.")