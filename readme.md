📊 Desafio Técnico: Monitoramento de Atos Normativos
Este projeto implementa uma solução automatizada para captura, armazenamento e análise de atos normativos da Receita Federal. A solução é composta por um robô de automação (RPA), uma API RESTful para persistência e um dashboard para análise de dados.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.10+

Framework Web: FastAPI

Banco de Dados: PostgreSQL

ORM: SQLModel (SQLAlchemy)

Automação (RPA): Selenium WebDriver

Autenticação: JWT (JSON Web Token) e Passlib (Bcrypt)

Containerização: Docker e Docker Compose

📋 Requisitos do Sistema
Docker e Docker Compose instalados.

Google Chrome instalado (para o modo não-headless do RPA).

Python 3.10 ou superior (caso deseje rodar fora do Docker).

🚀 Instruções de Execução (Passo a Passo)
1. Clonar o Repositório e Configurar Ambiente
Bash

git clone <url-do-seu-repositorio>
cd desafio-python-rpa
2. Configurar Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto seguindo o modelo abaixo:

Snippet de código

DATABASE_URL=postgresql://user:password@db:5432/desafio_python
ADMIN_USER=admin
ADMIN_PASSWORD=admin_password_escolhida
SECRET_KEY=uma_chave_secreta_para_jwt
3. Rodar com Docker Compose
Este comando sobe a API e o Banco de Dados automaticamente:

Bash

docker-compose up -d --build
4. Instalação de Dependências (Local)
Para rodar o bot RPA, é necessário instalar as dependências no seu ambiente local ou venv:

Bash

python -m venv venv
source venv/bin/scripts/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
5. Popular Banco e Criar Usuário Admin
Execute o script de seed para garantir que o banco tenha as tabelas e o usuário administrador:

Bash

python -m database.seed
6. Executar o Robô RPA
Bash

python rpa/bot.py
🔌 Documentação da API
A API segue os padrões RESTful e possui documentação automática:

Swagger UI: http://localhost:8000/docs

Redoc: http://localhost:8000/redoc

Endpoints Principais
POST /token: Autenticação e obtenção do token de acesso.

GET /atos/: Listagem de atos com filtros de data e busca por texto.

GET /dashboard/: Dados tratados para visualização (totalizadores por órgão/tipo).

DELETE /atos/{id}: Exclusão lógica do registro.

📁 Estrutura do Projeto
Plaintext

├── database/           # Modelos SQLModel, conexão e seeds
├── router/             # Definição das rotas da API
├── services/           # Lógica de negócio e integração com banco
├── rpa/                # Script bot.py e utilitários de scraping
├── .env                # Variáveis de ambiente
├── docker-compose.yml  # Orquestração de containers
└── main.py             # Ponto de entrada da aplicação FastAPI
📌 Diferenciais Implementados
Exclusão Lógica: Registros deletados não são removidos fisicamente, apenas marcados como deleted.

Resiliência no RPA: Uso de seletores robustos e execução de scripts via JavaScript para contornar limitações de renderização do portal SIJUT.

Logs Detalhados: Registro automático de tempo de execução e performance de cada ciclo do robô.