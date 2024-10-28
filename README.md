# Jornadas - TracBOT

## Como rodar localmente?

### Back-end

1. Clone o repositório se ainda não clonou e navegue até a pasta do projeto:
```
git clone https://github.com/ryanviana/tractian-hackathon.git>
cd chatbot-backend
```

### Front-end

Siga os passos abaixo para rodar o front-end do projeto usando Streamlit:

1. Navegue até a pasta do projeto:

```
cd chatbot-frontend
```

2. Crie um ambiente virtual (venv) no diretório do projeto:

```
python3 -m venv venv
```

3. Ative o ambiente virtual:

- No Windows:

```
venv\Scripts\activate
```

- No macOS/Linux:
```
source venv/bin/activate
```

4. Instale as dependências listadas no arquivo requirements.txt:

```
pip install -r requirements.txt
```

5. Execute o front-end com o Streamlit:

```
streamlit run frontend.py
```

6. Acesse o front-end no navegador através do link fornecido no terminal, geralmente http://localhost:8501.
