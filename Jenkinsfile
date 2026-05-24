pipeline {
    agent any

    stages {
        stage('Construir imagen') {
            steps {
                echo 'Copia archivo de entorno'
                sh 'cp env-example .env'

                echo 'Limpiando contenedores antiguos o conflictivos...'
                // Esto detiene y elimina contenedores huérfanos del mismo proyecto antes de iniciar
                sh 'docker compose down'
                
                echo 'Construyendo imagen e inicia contenedores'
                sh 'docker compose up -d --build'
            }
        }
        stage('Revisa estándar de código') {
            steps {
                echo 'Ejecuta flake8 ...'
                // Envolvemos el comando en sh y ponemos comillas al path de --exclude para evitar problemas con los asteriscos
                sh 'docker compose exec -T -w /app/lumat_tutorias app flake8 --exclude=lumat_app/migrations/,*settings.py --ignore F811'
            }
        }
        stage('Pruebas unitarias') {
            steps {
                echo 'Ejecuta pruebas unitarias ...'
                // Agregamos un pequeño sleep para dar tiempo a la base de datos de iniciar en frío antes del test
                sh 'sleep 5'
                sh 'docker compose exec -T -w /app/lumat_tutorias app python manage.py test'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying....'
            }
        }
    }
}