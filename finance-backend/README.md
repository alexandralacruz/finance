poetry add --group dev ipykernel

# crea el kernel
poetry run python -m ipykernel install --user --name finance-backend --display-name "Poetry finance-backend"

poetry run uvicorn app.main:app --reload

# borrar los kernels
Remove-Item -Recurse -Force "$env:APPDATA\Code\User\globalStorage\ms-toolsai.jupyter\kernels"
