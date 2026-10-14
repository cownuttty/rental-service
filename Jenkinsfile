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
            when { branch 'main' }
            steps {
                // --remove-orphans на случай если раньше остались
                // контейнеры со старым (не-docker) способом развёртывания.
                bat 'docker compose up -d --remove-orphans'

                // Ждём, пока nginx и оба сервиса за ним поднимутся,
                // и проверяем health через шлюз, а не напрямую в контейнеры -
                // это и есть проверка того, что весь путь (nginx -> сервис) жив.
                powershell '''
                    $maxAttempts = 15
                    $ok = $false
                    for ($i = 1; $i -le $maxAttempts; $i++) {
                        try {
                            $r1 = Invoke-WebRequest -UseBasicParsing "http://localhost:$env:GATEWAY_PORT/api/health" -TimeoutSec 3
                            $r2 = Invoke-WebRequest -UseBasicParsing "http://localhost:$env:GATEWAY_PORT/cleaning/health" -TimeoutSec 3
                            if ($r1.StatusCode -eq 200 -and $r2.StatusCode -eq 200) {
                                $ok = $true
                                break
                            }
                        } catch {
                            Start-Sleep -Seconds 2
                        }
                    }
                    if (-not $ok) {
                        Write-Error "Сервисы не ответили через nginx за отведённое время"
                        exit 1
                    }
                    Write-Host "Deploy OK: оба сервиса отвечают через nginx-gateway"
                '''
            }
        }
    }

    post {
        always {
            echo "Build ${env.BUILD_NUMBER} on ${env.BRANCH_NAME} finished with status: ${currentBuild.currentResult}"
        }
    }
}
