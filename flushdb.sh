find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/__pycache__" -delete
find . -path "*/migrations/*.pyc"  -delete
rm db.sqlite3
