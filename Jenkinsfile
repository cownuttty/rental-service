pipeline {
    agent any

    options {
        timestamps() //вывод времени
        timeout(time: 30, unit: 'MINUTES') //если долго собирается -обрываем
        disableConcurrentBuilds() //запрет на две сборки одновременно
        buildDiscarder(logRotator(numToKeepStr: '10')) //история из 10 сборок
    }

    environment {
    COMPOSE_PROJECT_NAME = 'rental-service'  //префикс докер compose
    GATEWAY_PORT = '8081' //порт шлюза
    DOCKERHUB_USER = 'cownuttty' 
    IMAGE_TAG = "${env.BUILD_NUMBER}" // тег - номер сборки
}

    stages {

        stage('Info') { //сбор контекста сборки в лог(фиксация условий)
            steps {
                echo "Branch: ${env.BRANCH_NAME}"
                echo "Build: ${env.BUILD_NUMBER}" //какая ветка и номер сборки
                bat 'docker --version' //версия docker engine
                bat 'docker compose version' //версия docker compose
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

        stage('Build images') {
            when { branch 'main' }
            steps {
                bat 'docker compose build' //сбор образов для докер compose
                withCredentials([usernamePassword(credentialsId: 'dockerhub-token', usernameVariable: 'DH_USER', passwordVariable: 'DH_TOKEN')]) {
                    bat 'echo %DH_TOKEN%| docker login -u %DH_USER% --password-stdin' //аутентификация в докерхаб
                    bat 'docker compose push' //пушит
                }
            }
        }

        stage('Deploy') {
            steps {
                bat 'docker compose down --remove-orphans || exit 0' //остановить и удалить все контейнеры текущего compose проекта 
                bat 'docker rm -f rental-api cleaning-service nginx-gateway || exit 0' //удалить все контейнеры по фикс именам

                bat 'docker compose up -d --build --remove-orphans' //сервисы поднимаются в фоне, образы пересобираются
            }
        }
    }

    post {
        always {
            echo "Build ${env.BUILD_NUMBER} on ${env.BRANCH_NAME} finished with status: ${currentBuild.currentResult}"
        }
    }
}
