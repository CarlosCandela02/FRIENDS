import streamlit as st
import pandas as pd
import random
import re
import difflib

# Configuración de la página
st.set_page_config(page_title="Friends Trivia", page_icon="☕", layout="centered")

# --- LÓGICA DE DATOS Y LIMPIEZA ---
@st.cache_data 
def cargar_datos():
    try:
        df = pd.read_csv('friends_espanol.csv')
        df = df.dropna(subset=['descripcion', 'titulo'])
        db = df.to_dict('records')
        random.shuffle(db)
        return db
    except FileNotFoundError:
        return None

def limpiar_texto(texto):
    texto = str(texto).lower().strip()
    prefijos = ["aquel en el que ", "el en el que ", "el de las ", "el de los ", "el de la ", "el del ", "el de "]
    for p in prefijos:
        if texto.startswith(p):
            texto = texto[len(p):]
            break 
    return re.sub(r'[^\w\s]', '', texto).strip()

def evaluar_similitud(resp, real):
    if not limpiar_texto(real): return False
    return difflib.SequenceMatcher(None, limpiar_texto(resp), limpiar_texto(real)).ratio() >= 0.80

def generar_pista(titulo):
    palabras = str(titulo).split()
    pista = []
    for p in palabras:
        p_limpia = re.sub(r'[^\w\s]', '', p)
        if len(p_limpia) > 1: pista.append(p_limpia[0].upper() + "_" * (len(p_limpia)-1))
        elif len(p_limpia) == 1: pista.append(p_limpia.upper())
    return " ".join(pista)

# --- ESTADO DE LA SESIÓN (Memoria del juego) ---
if 'db' not in st.session_state:
    st.session_state.db = cargar_datos()
    st.session_state.idx = 0
    st.session_state.puntuacion = 0.0
    st.session_state.pregunta_actual = 1
    st.session_state.intento = 1
    st.session_state.aciertos = {'temp': False, 'ep': False, 'tit': False}
    # Nueva memoria para guardar los fallos del primer intento
    st.session_state.last_guesses = {'temp': None, 'ep': None} 
    st.session_state.feedback = ""

# --- INTERFAZ DE USUARIO ---
st.title("☕ Trivia de Friends")

if st.session_state.db is None:
    st.error("No se encuentra 'friends_espanol.csv'.")
    st.stop()

if st.session_state.pregunta_actual > 5:
    st.success(f"🎉 ¡Batería terminada! Puntuación final: {st.session_state.puntuacion} / 10.0")
    if st.button("Jugar otra batería"):
        st.session_state.pregunta_actual = 1
        st.session_state.puntuacion = 0.0
        st.session_state.intento = 1
        st.session_state.aciertos = {'temp': False, 'ep': False, 'tit': False}
        st.session_state.last_guesses = {'temp': None, 'ep': None}
        st.session_state.feedback = ""
        st.rerun()
    st.stop()

ep = st.session_state.db[st.session_state.idx]

# Marcador y progreso
col1, col2 = st.columns(2)
col1.metric("Pregunta", f"{st.session_state.pregunta_actual} / 5")
col2.metric("Puntuación", f"{st.session_state.puntuacion} pts")

st.markdown("---")
st.subheader("🎬 Sinopsis del episodio:")
st.info(f'"{ep["descripcion"]}"')

# Mostrar pistas en el segundo intento
if st.session_state.intento == 2:
    st.warning("💡 Segundo intento (mitad de puntos). Aquí tienes algunas pistas:")
    
    if not st.session_state.aciertos['temp'] and st.session_state.last_guesses['temp'] is not None:
        pista_t = "mayor" if ep["temporada"] > st.session_state.last_guesses['temp'] else "menor"
        st.write(f"**Pista Temporada:** Es {pista_t} que {st.session_state.last_guesses['temp']}.")
        
    if not st.session_state.aciertos['ep'] and st.session_state.last_guesses['ep'] is not None:
        pista_e = "mayor" if ep["episodio"] > st.session_state.last_guesses['ep'] else "menor"
        st.write(f"**Pista Episodio:** Es {pista_e} que {st.session_state.last_guesses['ep']}.")
        
    if not st.session_state.aciertos['tit']:
        st.write(f"**Pista Título:** {generar_pista(ep['titulo'])}")

# Formulario de entrada
with st.form("respuesta_form"):
    col_t, col_e = st.columns(2)
    
    with col_t:
        temp_input = st.text_input("Temporada (número):", disabled=st.session_state.aciertos['temp'])
    with col_e:
        ep_input = st.text_input("Episodio (número):", disabled=st.session_state.aciertos['ep'])
        
    tit_input = st.text_input("Título del episodio (omite 'El de...'):", disabled=st.session_state.aciertos['tit'])
    
    submit = st.form_submit_button("Comprobar Respuesta")

# Lógica al enviar el formulario
if submit:
    # Validar temporada
    if not st.session_state.aciertos['temp'] and temp_input.isdigit():
        if int(temp_input) == ep['temporada']:
            st.session_state.aciertos['temp'] = True
            st.session_state.puntuacion += 0.5 if st.session_state.intento == 1 else 0.25
        else:
            st.session_state.last_guesses['temp'] = int(temp_input)
            
    # Validar episodio
    if not st.session_state.aciertos['ep'] and ep_input.isdigit():
        if int(ep_input) == ep['episodio']:
            st.session_state.aciertos['ep'] = True
            st.session_state.puntuacion += 0.5 if st.session_state.intento == 1 else 0.25
        else:
            st.session_state.last_guesses['ep'] = int(ep_input)
            
    # Validar título
    if not st.session_state.aciertos['tit'] and tit_input:
        if evaluar_similitud(tit_input, ep['titulo']):
            st.session_state.aciertos['tit'] = True
            st.session_state.puntuacion += 1.0 if st.session_state.intento == 1 else 0.5

    # Comprobar estado de la ronda
    todas_acertadas = all(st.session_state.aciertos.values())
    
    if todas_acertadas or st.session_state.intento == 2:
        st.session_state.feedback = f"✅ Era: Temporada {ep['temporada']}, Episodio {ep['episodio']} - '{ep['titulo']}'"
        st.session_state.idx += 1
        st.session_state.pregunta_actual += 1
        st.session_state.intento = 1
        st.session_state.aciertos = {'temp': False, 'ep': False, 'tit': False}
        st.session_state.last_guesses = {'temp': None, 'ep': None}
    else:
        st.session_state.intento = 2
        st.session_state.feedback = "⚠️ Algunos datos no son correctos. Revisa las pistas para el segundo intento."
        
    st.rerun()

# Mostrar feedback de la jugada anterior
if st.session_state.feedback:
    if "✅" in st.session_state.feedback:
        st.success(st.session_state.feedback)
    else:
        st.warning(st.session_state.feedback)