// Jenkinsfile — Declarative Pipeline (Pipeline as Code).
// Ветки dev и feature/* проходят CI (проверка + тесты), ветка main — CI + CD (упаковка и деплой).

// Небольшой помощник: запускает Python из виртуального окружения и на Windows, и на Linux
def py(String args) {
    if (isUnix()) {
        sh "venv/bin/python ${args}"
    } else {
        bat "venv\\Scripts\\python ${args}"
    }
}

pipeline {
    agent any

    options {
        timestamps()                                   // время в каждой строке лога
        timeout(time: 20, unit: 'MINUTES')             // сборка не должна висеть вечно
        disableConcurrentBuilds()                      // не запускать две сборки одной ветки одновременно
        buildDiscarder(logRotator(numToKeepStr: '10')) // хранить только 10 последних сборок
    }

    environment {
        DEPLOY_DIR = 'deploy'   // куда разворачивать релиз (путь относительно workspace или абсолютный)
        APP_PORT   = '5000'     // порт, на котором будет работать развёрнутое приложение
    }

    stages {
        stage('Info') {
            steps {
                echo "Branch: ${env.BRANCH_NAME} | Build: #${env.BUILD_NUMBER}"
            }
        }

        stage('Setup') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'python3 -m venv venv'
                    } else {
                        bat 'python -m venv venv'
                    }
                    py '-m pip install --disable-pip-version-check -r requirements-dev.txt'
                }
            }
        }

        stage('Lint') {
            steps {
                script {
                    // 1) критичные ошибки (синтаксис, неопределённые имена, лишние импорты) — сборка падает
                    py '-m flake8 app tests scripts --count --select=E9,F63,F7,F82,F401,F841 --show-source --statistics'
                    // 2) замечания по стилю — только показываем, сборку не роняют
                    py '-m flake8 app tests scripts --exit-zero --max-complexity=10 --statistics'
                }
            }
        }

        stage('Test') {
            steps {
                script {
                    py '-m pytest --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml --cov-report=term'
                }
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                    archiveArtifacts artifacts: 'reports/coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Package') {
            when { branch 'main' }   // только для основной ветки
            steps {
                script {
                    py "scripts/package.py --version ${env.BUILD_NUMBER}"
                }
                archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
            }
        }

        stage('Deploy') {
            when { branch 'main' }
            steps {
                script {
                    py "scripts/deploy.py --archive dist/rental-service-${env.BUILD_NUMBER}.zip --target ${env.DEPLOY_DIR} --port ${env.APP_PORT}"
                }
            }
        }
    }

    post {
        success { echo "Pipeline for ${env.BRANCH_NAME} finished successfully" }
        failure { echo "Pipeline for ${env.BRANCH_NAME} FAILED - see the log above" }
    }
}
