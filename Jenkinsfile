pipeline {
    agent any
    environment {
        REGISTRY = 'registry.amer-br.tech'
        IMAGE_NAME = 'lumat'
        VERSION = "v${BUILD_NUMBER}"
        USER_PROD = 'admin'
        SERVER_PROD = 'ec2-18-222-223-70.us-east-2.compute.amazonaws.com'
    }
    stages {
        stage('Inicializando...') {
            steps {
                echo 'Asignando workspace y validando entorno.'
            }
        }

        stage('Construir imagen') {
            steps {
                echo 'Copia archivo de entorno'
                sh 'cp env-example .env'

                echo 'Limpiando contenedores antiguos o conflictivos...'
                sh 'docker compose down'

                echo 'Construyendo imagen e inicia contenedores'
                sh 'docker compose up -d --build'
            }
        }

        stage('Revisa estándar de código') {
            steps {
                echo 'Ejecuta flake8...'
                // Ruta corregida: /app/lumat_tutorias (donde está manage.py y lumat_app)
                sh 'docker compose exec -T -w /app/lumat_tutorias app flake8 --max-complexity=10 --exclude "*settings.py,*migrations*" --ignore F811 .'
            }
        }

        stage('Preparar base de datos de pruebas') {
            steps {
                sleep time: 20, unit: 'SECONDS'
                // sh """
                //     DB_ROOT_PASSWORD=\$(grep '^DB_ROOT_PASSWORD=' .env | cut -d '=' -f2)
                //     docker compose exec -T db mariadb -u root -p\${DB_ROOT_PASSWORD} -e "GRANT ALL PRIVILEGES ON \\\`test_lumat_tutorias_db\\\`.* TO 'lumatuser'@'%'; FLUSH PRIVILEGES;"
                // """
                // sh 'docker compose exec -T db mariadb -u root -e "GRANT ALL PRIVILEGES ON \`test_lumat_tutorias_db\`.* TO \'lumatuser\'@\'%\'; FLUSH PRIVILEGES;"'
                // sh 'docker compose exec -T db mariadb -u root -padmin1234 -e "GRANT ALL PRIVILEGES ON \`test_lumat_tutorias_db\`.* TO \'lumatuser\'@\'%\'; FLUSH PRIVILEGES;"'
                sh "docker compose exec -T db mariadb -u root -padmin1234 -e \"GRANT ALL PRIVILEGES ON \\\`test_lumat_tutorias_db\\\`.* TO 'lumatuser'@'%'; FLUSH PRIVILEGES;\""
            }
        }

        stage('Pruebas unitarias y de cobertura') {
            steps {
                timeout(time: 2, unit: 'MINUTES') {
                    sleep time: 20, unit: 'SECONDS'

                    echo 'Ejecuta pruebas unitarias...'
                    // Ruta corregida: /app/lumat_tutorias
                    sh 'docker compose exec -T -w /app/lumat_tutorias app python manage.py test'

                    echo 'Ejecutando pruebas con reporte de cobertura...'

                    // sh """
                    //     docker compose exec -T -w ${PROJECT_DIR} app coverage run \
                    //     --branch --source=. \
                    //     --omit=*test*,*migrations*,*__init*,*settings*,*apps*,*wsgi*,*admin.py,*asgi.py,manage.py,*urls.py \
                    //     manage.py test
                    // """

                    sh """docker compose exec -T -w /app/lumat_tutorias app coverage run --branch --source='.' --omit=*test*,*migrations*,*__init*,*settings*,*apps*,*wsgi*,*admin.py,*asgi.py,manage.py,*urls.py manage.py test"""
                    // PARA WINDOWS  --> docker compose exec -T -w /app/lumat_tutorias app coverage run --branch --source=. --omit="*test*,*migrations*,*__init*,*settings*,*apps*,*wsgi*,*admin*,*asgi*,manage.py,*urls*" manage.py test
                    
                    // 2. Generamos el reporte HTML dentro del contenedor

                    sh 'docker compose exec -T -w /app/lumat_tutorias app coverage html'

                    // Nombre del contenedor corregido: lumat-app
                    sh 'docker cp lumat-app:/app/lumat_tutorias/htmlcov .'

                    publishHTML target:[
                        allowMissing: false,
                        alwaysLinkToLastBuild: false,
                        keepAll: true,
                        reportDir: './htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Reporte de cobertura Lumat',
                        reportTitles: 'Cobertura de código'
                    ]
                }
            }
        }

        stage('Pruebas de aceptacion') {
            steps {
                // Ruta corregida: /app/lumat_tutorias
                sh 'docker compose exec -T -w /app/lumat_tutorias app python manage.py migrate'

                sh 'docker compose exec -T -w /app/lumat_tutorias app python create_superuser.py'

                sh 'docker compose exec -T -w /app/lumat_tutorias app bash -c "python manage.py runserver 0:8000 &"'
                sleep time: 5, unit: 'SECONDS'

                // pruebas_aceptacion está montado en /pruebas_aceptacion (sin cambio)
                // sh 'docker compose exec -T -w /pruebas_aceptacion app behave features/iniciar_sesion.feature'
            }
        }

        stage('Construir imagen producción') {
            steps {
                sh "docker build --build-arg SECRET_KEY=dummy-secret-key-for-build -t ${REGISTRY}/${IMAGE_NAME}:${VERSION} -f Dockerfile-prod ."
                sh "docker tag ${REGISTRY}/${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:latest"
            }
        }

        stage('Push de imagen a registry') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh """
                        echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin ${REGISTRY}
                        docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}
                        docker push ${REGISTRY}/${IMAGE_NAME}:latest
                    """
                }
            }
        }

//         stage('Desplegar en staging') {
//             steps {
//                 sshagent(['prod-ssh-key']) {
//                     sh """
//                         ssh -o StrictHostKeyChecking=no ${USER_PROD}@${SERVER_PROD} << 'EOF'
//                         cd /home/admin/lumat

//                         # Respaldar versión anterior
//                         if grep -q '^IMAGE_VERSION=' .env; then
//                             OLD_VERSION=\$(grep '^IMAGE_VERSION=' .env | cut -d '=' -f2)
//                             sed -i '/^IMAGE_VERSION_OLD=/d' .env
//                             echo "IMAGE_VERSION_OLD=\$OLD_VERSION" >> .env
//                         fi

//                         # Actualizar versión actual
//                         sed -i '/^IMAGE_VERSION=/d' .env
//                         echo "IMAGE_VERSION=${VERSION}" >> .env

//                         echo "Contenido actualizado de .env:"
//                         cat .env

//                         docker compose pull app
//                         docker compose up -d

//                         # Migraciones post-despliegue
//                         docker compose exec -T -w /app/lumat_tutorias app python manage.py migrate
// EOF
//                     """
//                 }
//             }
//         }

        stage('Revisión por QA') {
            steps {
                input "Desplegar en producción?"
            }
        }

//         stage('Despliegue producción') {
//             steps {
//                 sshagent(['prod-ssh-key']) {
//                     sh """
//                         ssh -o StrictHostKeyChecking=no ${USER_PROD}@${SERVER_PROD} << 'EOF'
//                         cd /home/admin/lumat

//                         sed -i '/^IMAGE_VERSION=/d' .env
//                         echo "IMAGE_VERSION=${VERSION}" >> .env

//                         docker compose pull app
//                         docker compose up -d

//                         docker compose exec -T -w /app/lumat_tutorias app python manage.py migrate
// EOF
//                     """
//                 }
//             }
//         }
    }

    post {
        always {
            sh 'docker compose down -v'
        }
        success {
            echo "Despliegue completado exitosamente con versión ${VERSION}"
        }
        failure {
            echo "El pipeline falló en algún paso."
        }
    }
}