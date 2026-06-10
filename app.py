import streamlit as st
from openai import OpenAI
import json
import os
import time

# Configuração da Página (Tema adaptável)
st.set_page_config(page_title="Lumina AI - Relé Chat", page_icon="⚡", layout="centered")

# Injeção de Estilos e Classes da Lumina AI adaptados para Light e Dark Mode
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet">
    
    <style>
    /* CORREÇÃO DO IFRAME: Força o Streamlit a manter-se contido sem forçar redesenho da página pai */
    html, body, .stApp {
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        background-color: transparent !important;
        height: 100vh !important;
        width: 100% !important;
    }
    
    /* Evita que blocos de foco do Streamlit propaguem eventos de clique/redimensionamento para fora */
    .stChatInputContainer {
        padding-bottom: 20px !important;
    }
    
    /* ... O resto do teu CSS original da Lumina AI (como .ai-gradient, .glass-panel, etc) ... */
    
    .ai-gradient {
        background: linear-gradient(135deg, #3525cd 0%, #571ac0 50%, #39b8fd 100%);
    }
    
    .glass-panel {
        background: var(--background-color);
        opacity: 0.95;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--secondary-background-color);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    .lumina-title {
        font-size: 2.5rem;
        font-weight: 600;
        letter-spacing: -0.02em;
        color: var(--text-color);
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .lumina-subtitle {
        font-size: 1rem;
        color: var(--text-color);
        opacity: 0.8;
        text-align: center;
        margin-bottom: 2rem;
    }
    .text-primary-lumina {
        color: #3525cd;
        font-weight: 800;
    }
    
    .user-container {
        background: var(--secondary-background-color);
        border-radius: 1rem;
        padding: 1rem 1.5rem;
        margin-top: 1rem;
        color: var(--text-color);
        border-left: 4px solid var(--text-color);
        opacity: 0.9;
    }
    
    .response-container {
        background: var(--background-color);
        border: 1px solid rgba(53, 37, 205, 0.2);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        color: var(--text-color);
        line-height: 1.6;
        box-shadow: 0 10px 25px -5px rgba(53, 37, 205, 0.05);
    }
    .response-container strong {
        color: #3525cd;
    }
    
    div[data-testid="stChatInput"] {
        border-radius: 9999px !important;
        box-shadow: 0 4px 14px rgba(53, 37, 205, 0.1) !important;
        background-color: var(--background-color) !important;
    }

    .suggestion-btn button {
        border-radius: 1rem !important;
        padding: 1.2rem !important;
        border: 1px solid var(--secondary-background-color) !important;
        background-color: var(--background-color) !important;
        transition: all 0.2s ease-in-out !important;
        text-align: left !important;
        height: auto !important;
    }
    .suggestion-btn button:hover {
        border-color: #3525cd !important;
        box-shadow: 0 4px 12px rgba(53, 37, 205, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- GERENCIAMENTO DE ARQUIVOS JSON ---
DATA_DIR = "chat_history"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_chat(chat_id, messages):
    if not messages:
        return
    filename = os.path.join(DATA_DIR, f"{chat_id}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)

def load_chat(chat_id):
    filename = os.path.join(DATA_DIR, f"{chat_id}.json")
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def delete_single_chat(chat_id):
    filename = os.path.join(DATA_DIR, f"{chat_id}.json")
    if os.path.exists(filename):
        os.remove(filename)

def clear_all_history():
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            os.remove(os.path.join(DATA_DIR, file))

def get_all_chats():
    chats = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".json"):
            chat_id = file.replace(".json", "")
            filename = os.path.join(DATA_DIR, file)
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    messages = json.load(f)
                title = "Conversa sem título"
                for msg in messages:
                    if msg["role"] == "user":
                        title = msg["content"]
                        break
                if len(title) > 22:
                    title = title[:19] + "..."
                
                chats.append({
                    "id": chat_id,
                    "title": title,
                    "timestamp": os.path.getmtime(filename)
                })
            except Exception:
                pass
    return sorted(chats, key=lambda x: x["timestamp"], reverse=True)

# --- INICIALIZAÇÃO DOS ESTADOS DA SESSÃO ---
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(int(time.time()))

if "messages" not in st.session_state:
    st.session_state.messages = load_chat(st.session_state.current_chat_id)

if "clicked_suggestion" not in st.session_state:
    st.session_state.clicked_suggestion = None

# --- MENU LATERAL (BARRA LATERAL DE CONFIGURAÇÕES) ---
with st.sidebar:
    st.markdown("<h2>Menu & Histórico</h2>", unsafe_allow_html=True)
    
    if st.button("➕ Nova conversa", use_container_width=True):
        if st.session_state.messages:
            save_chat(st.session_state.current_chat_id, st.session_state.messages)
        st.session_state.current_chat_id = str(int(time.time()))
        st.session_state.messages = []
        st.session_state.clicked_suggestion = None
        st.rerun()
        
    st.markdown("---")
    
    saved_chats = get_all_chats()
    if saved_chats:
        st.markdown("<p style='font-size: 13px; opacity: 0.8;'>Conversas recentes:</p>", unsafe_allow_html=True)
        
        for chat in saved_chats:
            is_current = chat["id"] == st.session_state.current_chat_id
            label = f"💬 {chat['title']}" if not is_current else f"⚡ {chat['title']}"
            
            col_chat, col_del = st.columns([0.85, 0.15])
            
            with col_chat:
                if st.button(label, key=f"sel_{chat['id']}", use_container_width=True, disabled=is_current):
                    if st.session_state.messages:
                        save_chat(st.session_state.current_chat_id, st.session_state.messages)
                    st.session_state.current_chat_id = chat["id"]
                    st.session_state.messages = load_chat(chat["id"])
                    st.session_state.clicked_suggestion = None
                    st.rerun()
                    
            with col_del:
                if st.button("🗑️", key=f"del_{chat['id']}", help="Apagar esta conversa"):
                    delete_single_chat(chat["id"])
                    if is_current:
                        st.session_state.current_chat_id = str(int(time.time()))
                        st.session_state.messages = []
                    st.rerun()
    else:
        st.info("Nenhuma conversa salva ainda.")
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<p style='font-size: 13px; color: #ba1a1a; font-weight: bold;'>Zona de Perigo</p>", unsafe_allow_html=True)
    
    confirm_clear = st.checkbox("Confirmar exclusão em massa", key="confirm_clear_all")
    
    if st.button("🚨 Apagar todo o histórico", use_container_width=True, type="primary", disabled=not confirm_clear):
        clear_all_history()
        st.session_state.current_chat_id = str(int(time.time()))
        st.session_state.messages = []
        st.session_state.clicked_suggestion = None
        st.success("Histórico totalmente limpo!")
        time.sleep(1)
        st.rerun()

# --- ELEMENTOS VISUAIS DA INTERFACE PRINCIPAL ---
st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; margin-top: 2rem;">
        <div class="ai-gradient" style="width: 4rem; height: 4rem; border-radius: 1.5rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; box-shadow: 0 10px 20px rgba(53, 37, 205, 0.2);">
            <span class="material-symbols-outlined" style="color: white; font-size: 2.2rem;">auto_awesome</span>
        </div>
        <h1 class="lumina-title">Olá, eu sou o <span class="text-primary-lumina">Lumina</span></h1>
        <p class="lumina-subtitle">Seu copiloto de engenharia elétrica e automação, pronto para decifrar relés e circuitos.</p>
    </div>
""", unsafe_allow_html=True)

# --- BOTÕES DINÂMICOS E ADAPTÁVEIS ---
col1, col2, col3 = st.columns(3)

# Se NÃO houver mensagens na conversa, mostra as perguntas padrão de boas-vindas
if not st.session_state.messages:
    with col1:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button("📝\nAnálise Teórica\nConceitos da literatura clássica.", key="sug_teoria", use_container_width=True):
            st.session_state.clicked_suggestion = "Explique a teoria de funcionamento de um relé de proteção térmica de acordo com os conceitos clássicos da literatura."
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button("🧠\nBrainstorming\nSoluções para automação.", key="sug_brain", use_container_width=True):
            st.session_state.clicked_suggestion = "Preciso de ideias de diagnóstico para um sistema onde o relé de sobrecorrente está atuando de forma intermitente."
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button("💻\nDimensionamento\nCálculos de relés.", key="sug_calc", use_container_width=True):
            st.session_state.clicked_suggestion = "Como faço o dimensionamento e ajuste de partida de um relé bimetálico para proteção de um motor trifásico?"
        st.markdown('</div>', unsafe_allow_html=True)

# Se JÁ HOUVER mensagens na conversa, transforma os botões em desdobramentos da ÚLTIMA pergunta do usuário
else:
    # Captura a última pergunta feita pelo usuário no histórico
    user_questions = [m["content"] for m in st.session_state.messages if m["role"] == "user"]
    last_question = user_questions[-1] if user_questions else ""
    
    # Cria variações inteligentes baseadas na própria dúvida do usuário
    with col1:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button(f"🔍\nIr mais Fundo\nAprofundar análise técnica.", key="dyn_deep", use_container_width=True):
            st.session_state.clicked_suggestion = f"Gostei da resposta. Pode se aprofundar nos detalhes matemáticos ou normativos sobre: '{last_question}'?"
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button(f"📚\nVer Literatura\nAutores sugeridos.", key="dyn_lit", use_container_width=True):
            st.session_state.clicked_suggestion = f"Quais capítulos ou livros de autores clássicos (como Kindermann ou Boylestad) detalham melhor o que discutimos sobre '{last_question}'?"
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="suggestion-btn">', unsafe_allow_html=True)
        if st.button(f"🛠️\nAplicação Prática\nExemplo no mundo real.", key="dyn_prac", use_container_width=True):
            st.session_state.clicked_suggestion = f"Pode me dar um exemplo prático de aplicação em chão de fábrica ou simulação real envolvendo '{last_question}'?"
        st.markdown('</div>', unsafe_allow_html=True)

# Diretriz do sistema injetada
system_instruction = (
    "[INSTRUÇÃO DO SISTEMA: Você agirá como o Lumina AI, um chatbot especialista em engenharia elétrica e automação. "
    "Responda às dúvidas do usuário utilizando conceitos técnicos fundamentados e contextualizados com a literatura clássica, "
    "como Boylestad, Sadiku, Malvino ou Kindermann. Mantenha as respostas claras e profissionais.]\n\n"
)

# Inicialização do Cliente NVIDIA
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

# Renderizar mensagens anteriores salvas no histórico carregado
for message in st.session_state.messages:
    if message["role"] == "user":
        st.markdown(f'<div class="user-container"><b>Você:</b> {message["content"]}</div>', unsafe_allow_html=True)
    elif message["role"] == "assistant":
        st.markdown(f'<div class="response-container">{message["content"]}</div>', unsafe_allow_html=True)

# Área de Entrada do Usuário fixa no Rodapé
user_prompt = st.chat_input("Como posso te ajudar hoje?")

# Se o usuário clicou em uma sugestão dinamicamente criada
if st.session_state.clicked_suggestion:
    user_prompt = st.session_state.clicked_suggestion
    st.session_state.clicked_suggestion = None

# Processamento de novas requisições
if user_prompt:
    st.markdown(f'<div class="user-container"><b>Você:</b> {user_prompt}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    response_placeholder = st.empty()
    full_response = ""

    try:
        api_messages = []
        for i, msg in enumerate(st.session_state.messages):
            if i == 0 and msg["role"] == "user":
                api_messages.append({"role": "user", "content": system_instruction + msg["content"]})
            else:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

        completion = client.chat.completions.create(
            model="google/gemma-2-2b-it",
            messages=api_messages,
            temperature=0.2,
            top_p=0.7,
            max_tokens=1024,
            stream=True
        )

        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
                response_placeholder.markdown(
                    f'<div class="response-container">{full_response}</div>', 
                    unsafe_allow_html=True
                )
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
        st.rerun()
                    
    except Exception as e:
        st.error(f"Erro de comunicação com Lumina: {e}")

st.markdown("<br><br><br>", unsafe_allow_html=True)