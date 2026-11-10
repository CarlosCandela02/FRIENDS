import random
import re
import difflib
import time
import pandas as pd

def cargar_dataset_local():
    print("⏳ Cargando la base de datos de episodios...")
    try:
        df = pd.read_csv('friends_espanol.csv')
        df = df.dropna(subset=['descripcion', 'titulo'])
        
        db = df.to_dict('records')
        print(f"✅ ¡Éxito! {len(db)} episodios cargados y listos para jugar.")
        return db
    except FileNotFoundError:
        print("❌ Error: No se encuentra 'friends_espanol.csv'. Ejecuta primero el script de descarga de TMDB.")
        return []

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    
    # Limpiamos los prefijos clásicos de los títulos en español
    prefijos = [
        "aquel en el que ", "el en el que ", "el de las ", 
        "el de los ", "el de la ", "el del ", "el de "
    ]
    
    for prefijo in prefijos:
        if texto.startswith(prefijo):
            texto = texto[len(prefijo):]
            break 
            
    texto_limpio = re.sub(r'[^\w\s]', '', texto).strip()
    return texto_limpio

def evaluar_similitud(respuesta_usuario, titulo_real):
    resp_norm = limpiar_texto(respuesta_usuario)
    tit_norm = limpiar_texto(titulo_real)
    
    if not tit_norm:
        return False
        
    ratio = difflib.SequenceMatcher(None, resp_norm, tit_norm).ratio()
    return ratio >= 0.80

def generar_pista_titulo(titulo):
    """Genera una pista del título (ej: E_ d_ l__ E________)"""
    palabras = str(titulo).split()
    pista = []
    for p in palabras:
        p_limpia = re.sub(r'[^\w\s]', '', p)
        if len(p_limpia) > 1:
            pista.append(p_limpia[0].upper() + "_" * (len(p_limpia)-1))
        elif len(p_limpia) == 1:
            pista.append(p_limpia.upper())
    return " ".join(pista)

def jugar_ronda(episodio, num_pregunta):
    print("\n" + "="*60)
    print(f"🎬 PREGUNTA {num_pregunta}/5 - SINOPSIS:")
    print(f'"{episodio["descripcion"]}"')
    print("="*60 + "\n")
    
    acierto_temp = False
    acierto_ep = False
    acierto_tit = False
    
    pts_temp = 0.0
    pts_ep = 0.0
    pts_tit = 0.0
    
    temp_user = 0
    ep_user = 0
    
    for intento in range(1, 3):
        if intento == 2:
            print("\n" + "-"*30)
            print("💡 SEGUNDO INTENTO (Mitad de puntos por acierto)")
            if not acierto_temp:
                pista_t = "mayor" if episodio["temporada"] > temp_user else "menor"
                print(f"  Pista Temporada: Es {pista_t} que {temp_user}.")
            if not acierto_ep:
                pista_e = "mayor" if episodio["episodio"] > ep_user else "menor"
                print(f"  Pista Episodio: Es {pista_e} que {ep_user}.")
            if not acierto_tit:
                print(f"  Pista Título: {generar_pista_titulo(episodio['titulo'])}")
            print("-" * 30 + "\n")

        # Temporada
        if not acierto_temp:
            while True:
                t_input = input("➤ Temporada (número): ").strip()
                if t_input.lower() == 'salir': return 0.0, False
                try:
                    temp_user = int(t_input)
                    break
                except ValueError:
                    print("  ❌ Introduce solo el número.")
            if temp_user == episodio["temporada"]:
                acierto_temp = True
                pts_temp = 0.5 if intento == 1 else 0.25

        # Episodio
        if not acierto_ep:
            while True:
                e_input = input("➤ Episodio (número): ").strip()
                if e_input.lower() == 'salir': return 0.0, False
                try:
                    ep_user = int(e_input)
                    break
                except ValueError:
                    print("  ❌ Introduce solo el número.")
            if ep_user == episodio["episodio"]:
                acierto_ep = True
                pts_ep = 0.5 if intento == 1 else 0.25

        # Título
        if not acierto_tit:
            tit_user = input("➤ Título del episodio: ").strip()
            if tit_user.lower() == 'salir': return 0.0, False
            if evaluar_similitud(tit_user, episodio["titulo"]):
                acierto_tit = True
                pts_tit = 1.0 if intento == 1 else 0.5
                
        if acierto_temp and acierto_ep and acierto_tit:
            break
            
        if intento == 1 and not (acierto_temp and acierto_ep and acierto_tit):
            print("\n⚠️ Casi... ¡Te daré pistas para lo que has fallado!")
            time.sleep(1)
            
    puntos_ronda = pts_temp + pts_ep + pts_tit
    
    print("\n--- RESULTADOS DE LA RONDA ---")
    time.sleep(0.5)
    
    if puntos_ronda == 2.0:
        print("✅ ¡PERFECTO A LA PRIMERA! Has conseguido los 2.0 puntos.")
    else:
        print(f"Puntuación obtenida: {puntos_ronda} ptos.")
        print(f"Temporada: {'✅' if acierto_temp else '❌'} (+{pts_temp} pts) | Era la {episodio['temporada']}")
        print(f"Episodio:  {'✅' if acierto_ep else '❌'} (+{pts_ep} pts) | Era el {episodio['episodio']}")
        print(f"Título:    {'✅' if acierto_tit else '❌'} (+{pts_tit} pts) | Era '{episodio['titulo']}'")
    
    return puntos_ronda, True

def iniciar_juego():
    friends_db = cargar_dataset_local()
    if not friends_db: return
        
    print("\n☕ BIENVENIDO AL TRIVIA DE FRIENDS ☕")
    print("Mecánica: Baterías de 5 preguntas con 2 intentos por pregunta.")
    print("Truco: No escribas 'El de...', ve directo a la palabra clave (ej: 'embriones').")
    print("Puntuación máx por ronda: Temp (0.5) + Ep (0.5) + Título (1.0) = 2.0 ptos.")
    print("Escribe 'salir' en cualquier momento para terminar.\n")
    
    random.shuffle(friends_db)
    total_episodios = len(friends_db)
    idx_episodio = 0
    jugando = True
    
    while jugando and idx_episodio < total_episodios:
        puntos_bateria = 0.0
        preguntas_jugadas = 0
        
        print("\n" + "🌟"*15)
        print("   NUEVA BATERÍA DE 5 PREGUNTAS")
        print("🌟"*15)
        
        for i in range(1, 6):
            if idx_episodio >= total_episodios:
                print("\n¡Te has pasado el juego! No quedan más episodios.")
                break
                
            ep = friends_db[idx_episodio]
            idx_episodio += 1
            
            puntos, continuar = jugar_ronda(ep, i)
            
            if not continuar:
                jugando = False
                break
                
            puntos_bateria += puntos
            preguntas_jugadas += 1
            
        if preguntas_jugadas > 0:
            puntos_maximos = preguntas_jugadas * 2.0
            print("\n" + "="*60)
            print(f"📊 RESULTADO DE LA BATERÍA: {puntos_bateria} / {puntos_maximos} puntos")
            print("="*60)
            
        if jugando and idx_episodio < total_episodios:
            seguir = input("\n¿Empezar otra batería de 5? (s/n): ").strip().lower()
            if seguir != 's':
                jugando = False
                
    print("\n¡Gracias por jugar! Has demostrado ser un buen fan.")

if __name__ == "__main__":
    iniciar_juego()