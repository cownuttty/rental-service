pipeline {
    agent any

    options {
        timestamps() //вывод времени
        timeout(time: 30, unit: 'MINUTES') //если долго собирается -обрываем
        disableConcurrentBuilds() //запрет на две сборки одновременно
        buildDiscarder(logRotator(numToKeepStr: '10')) //история из 10 сборок
    }

    environment {
    COMPOSE_PROJECT_NAME = 'rental-service'
    GATEWAY_PORT = '8081'
    DOCKERHUB_USER = 'cownuttty'
    IMAGE_TAG = "${env.BUILD_NUMBER}"
}

    stages {

        stage('Info') {
            steps {
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Build: ${env.BUILD_NUMBER}" //какая ветка и номер сборки
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
    

        stage('Deploy') {
            steps {
                bat 'docker compose down --remove-orphans || exit 0'
                bat 'docker rm -f rental-api cleaning-service nginx-gateway || exit 0'

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
