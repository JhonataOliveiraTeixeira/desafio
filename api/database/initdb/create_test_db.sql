-- Cria o banco de dados usado pelos testes e2e
-- Este arquivo será executado automaticamente pelo container oficial do Postgres
-- quando um volume de dados novo for inicializado.

CREATE DATABASE desafio_python_teste;

\connect desafio_python_teste;
GRANT ALL PRIVILEGES ON DATABASE desafio_python_teste TO "user";
