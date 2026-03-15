# Exata-Falada

##### Refatoração completa do repositório original: https://github.com/Felipe-Loureiro/Exata-Falada

## Sobre o Projeto
O **Exata-Falada** é um conversor de material didático em PDF para HTML. 

A demanda por essa ferramenta surgiu a partir da dificuldade que alunos com deficiência visual encontram para conseguir realmente acessar e compreender o material didático que recebem. O formato HTML apresenta grandes vantagens em relação ao PDF para esse tipo de estudante: por ser uma linguagem semântica e estruturada, ele permite que os leitores de tela naveguem com muito mais facilidade pelos conteúdos, cabeçalhos e elementos da página. Além disso, o HTML facilita a aplicação de personalizações visuais essenciais para pessoas com baixa visão, como ajustes de alto contraste, ampliação do tamanho da fonte e alteração de cores, o que no PDF costuma ser muito limitado ou inacessível.

O nome **Exata Falada** vem da enorme barreira que leitores de tela enfrentam ao tentar ler equações matemáticas. Por isso, uma das principais *features* da nossa conversão é conseguir identificar e transcrever essas equações de maneira correta, garantindo que elas sejam lidas e compreendidas de forma adequada.

## Requirements / Instalação

Siga os passos abaixo para preparar o ambiente e rodar o projeto localmente:

1. **Crie e ative um ambiente virtual**:
   ```bash
   python -m venv venv
   
   # No Windows:
   venv\Scripts\activate
   
   # No Linux/Mac:
   source venv/bin/activate
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure as variáveis de ambiente**:
   Crie um arquivo `.env` na raiz do projeto contendo as varíaveis necessárias (veja o arquivo `config.py`).

4. **Inicie o servidor API local**:
   Execute o projeto utilizando:
   ```bash
   python main.py
   ```
   A API estará disponível de forma local nos endereços:
   - `http://127.0.0.1:8000` (Endpoints do Projeto)
   - `http://127.0.0.1:8000/docs` (Swagger UI / Documentação interativa)

5. **Inicie o servidor Frontend local**:
   Navegue até a basta frontend-example:
   ```bash
   cd frontend-example
   ```
   Execute o servidor http:
   ```bash
   python -m http.server 3000 --bind 127.0.0.1
   ```
   O site estará disponível de forma local no endereços:
   - `http://127.0.0.1:3000` 

## Testes
Execute todos os testes com:

```bash
pytest tests/ -v
```

Para verificar a cobertura de código:
```bash
coverage run -m pytest
coverage report
```

## Alembic
* ### Gerar o SQL automáticamente e atualizar o banco de dados
  * Importar os novos modelos no models/_\_init__.py e executar:
  *  ```bash
     alembic revision --autogenerate -m "Descrição da migração"
     ```