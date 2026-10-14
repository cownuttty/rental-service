pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        COMPOSE_PROJECT_NAME = 'rental-service'
        GATEWAY_PORT = '8081'
    }

    stages {

        stage('Info') {
            steps {
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Build: ${env.BUILD_NUMBER}"
                bat 'docker --version'
                bat 'docker compose version'
            }
        }

        stage('Lint: rental-api') {
            steps {
                dir('rental-api') {
                    bat '''
                        python -m venv venv
                        call venv\\Scripts\\activate
                        pip install -r requirements-dev.txt
                        flake8 app run.py --select=E9,F63,F7,F82,F401,F841
                        flake8 app run.py --exit-zero --max-complexity=10
                    '''
                }
            }
        }

        stage('Lint: cleaning-service') {
            steps {
                dir('cleaning-service') {
                    bat '''
                        python -m venv venv
                        call venv\\Scripts\\activate
                        pip install -r requirements-dev.txt
                        flake8 app run.py --select=E9,F63,F7,F82,F401,F841
                        flake8 app run.py --exit-zero --max-complexity=10
                    '''
                }
            }
        }

        stage('Test: rental-api') {
            steps {
                dir('rental-api') {
                    bat '''
                        call venv\\Scripts\\activate
                        set PYTHONPATH=.
                        pytest tests -v
                    '''
                }
            }
        }

        stage('Test: cleaning-service') {
            steps {
                dir('cleaning-service') {
                    bat '''
                        call venv\\Scripts\\activate
                        set PYTHONPATH=.
                        pytest tests -v
                    '''
                }
            }
        }

        stage('Build images') {
            when { branch 'main' }
            steps {
                // Собираем образы для обоих сервисов. nginx используется
                // как есть (готовый образ nginx:1.27-alpine), поэтому
                // пересобирать его не нужно - только подтягивается при up.
                bat 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                // Останавливаем и удаляем контейнеры предыдущего запуска,
                // чтобы избежать конфликта имён. Флаг || true нужен, чтобы
                // шаг не падал, если контейнеров нет (первый запуск).
                bat 'docker compose down --remove-orphans || exit 0'
                bat 'docker rm -f rental-api cleaning-service nginx-gateway || exit 0'

                // Теперь поднимаем заново
                bat 'docker compose up -d --build --remove-orphans'
            }
        }
    }

    post {
        always {
            echo "Build ${env.BUILD_NUMBER} on ${env.BRANCH_NAME} finished with status: ${currentBuild.currentResult}"
        }
    }
}
