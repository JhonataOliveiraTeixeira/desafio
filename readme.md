# 📊 Sistema de Monitoramento de Atos Normativos (Receita Federal)

Solução completa de **RPA + API** para captura, processamento e análise de dados do portal **SIJUT**.

---

## 🚀 Tecnologias e Ferramentas

| Área | Tecnologia |
|------|------------|
| Backend | FastAPI |
| Banco de Dados | PostgreSQL |
| Automação | Selenium |
| Container | Docker / Docker Compose |

---

## 🛠️ Funcionalidades Principais

- **RPA Inteligente:** Automação com Selenium que contorna limitações de interface via JavaScript e extrai dados históricos.
- **API RESTful:** Endpoints para CRUD completo com persistência em PostgreSQL.
- **Segurança:** Autenticação via JWT (JSON Web Tokens) e proteção de rotas.
- **Dashboard:** Endpoints de agregação para métricas por **Órgão/Unidade**, **Tipo de Ato** e **período**.
- **Exclusão Lógica:** Registros removidos permanecem no banco com a flag `deleted`, garantindo integridade.
- **Logs do RPA:** Armazena tempo de execução, volume de dados capturados e erros.

---

## ⚙️ Instalação e Execução

### 1) Configuração do Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/desafio_python
ADMIN_USER=admin
ADMIN_PASSWORD=suasenha
SECRET_KEY=suachavejwt
2) Subindo os Containers (Banco e API)
bash
Copiar código
docker-compose up -d --build
3) Populando o Banco (Seeds)
Para criar o usuário administrador e dados iniciais:

bash
Copiar código
cd api
python -m database.seed
4) Iniciando a API
bash
Copiar código
cd api
uvicorn main:app --reload
5) Executando o Bot RPA
Em um novo terminal (na raiz do projeto):

bash
Copiar código
# Instale as dependências caso ainda não tenha feito
pip install -r requirements.txt

# Rode o bot
python rpa/bot.py
6) Executando os testes E2E (Selenium)
Requer a API rodando e o banco disponível.

bash
Copiar código
# (Opcional) Instale dependências caso necessário
pip install -r requirements.txt

# Execute os testes E2E
pytest -m e2e -v
Caso seus testes E2E estejam em um arquivo específico, você também pode rodar assim:

bash
Copiar código
pytest tests/e2e -v
🔗 Documentação da API
Com o servidor rodando, acesse a documentação interativa:

Swagger UI: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

📂 Estrutura de Pastas
plaintext
Copiar código
├── api/                # Código fonte da API FastAPI
│   ├── database/       # Conexão, models e seeds
│   ├── router/         # Rotas e Endpoints
│   └── services/       # Lógica de negócio
├── rpa/                # Scripts de automação (Selenium)
├── tests/              # Testes (unit/integration/e2e)
│   └── e2e/            # Testes end-to-end (Selenium)
├── .env                # Variáveis sensíveis (não incluído no git)
├── .gitignore          # Arquivos ignorados
├── docker-compose.yml  # Configuração Docker
└── requirements.txt    # Dependências do projeto
✅ Requisitos Atendidos (Tarefa 2)
 CRUD completo com suporte a filtros e busca (search).

 Dashboard com dados tratados e agregados.

 Logs do RPA com tempo de execução e volume de dados.

 Autenticação JWT protegendo os endpoints.

 Exclusão lógica implementada com sucesso.

Desenvolvido para o Desafio Técnico de Backend/RPA.
