# Checklist de Publicação do Site LADEUSA

- [x] 1. Coletar detalhes do site e ajustes necessários (Recebido LADEUSA.zip).
- [x] 2. Analisar requisitos para publicação online (Identificado como Flask, sem requirements.txt).
- [x] 3. Aplicar ajustes técnicos:
    - [x] 3.1. Reestruturar pastas para padrão de deploy Flask (`/home/ubuntu/ladeusa_deploy/src`).
    - [x] 3.2. Renomear `app.py` para `main.py`.
    - [x] 3.3. Criar `requirements.txt` (inicialmente com Flask).
    - [x] 3.4. Adicionar `sys.path.insert` no `main.py`.
- [ ] 4. Preparar e testar versão final:
    - [x] 4.1. Criar ambiente virtual (venv).
    - [x] 4.2. Instalar dependências (`pip install -r requirements.txt`).
    - [x] 4.3. Executar `main.py` localmente (`python src/main.py`).
    - [x] 4.4. Testar acesso local via browser (verificar rotas principais: login, cadastro, painel, admin).
    - [x] 4.5. Atualizar `requirements.txt` se necessário (`pip freeze > requirements.txt`).
- [ ] 5. Publicar site e validar acesso online:
    - [ ] 5.1. Confirmar com usuário se deseja publicação permanente.
    - [ ] 5.2. Realizar deploy usando `deploy_apply_deployment`.
    - [ ] 5.3. Validar acesso público ao URL fornecido.
- [ ] 6. Reportar resultados ao usuário (Enviar URL público).

