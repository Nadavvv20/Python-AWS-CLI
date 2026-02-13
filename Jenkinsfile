pipeline {
    agent any

    triggers {
        // Runs every day in 17:00 O'clock.
        cron('0 17 * * *')
    }

    environment {
        // Pull Telegram token.
        TELEGRAM_TOKEN = credentials('my-telegram-token')
        TELEGRAM_CHAT_ID = credentials('telegram-chat-id')
        AWS_ACCESS_KEY_ID = credentials('aws-access-key')
        AWS_SECRET_ACCESS_KEY = credentials('aws-secret-key')
    }

    stages {
        stage('Initialize Environment') {
            steps {
                sh 'python3 -m venv .venv'
                './.venv/bin/pip install .'
            }
        }
        stage('Run AWS check and notify') {
            steps {
                // Run the python status script (with the venv python)
                sh './.venv/bin/python instance_status_check.py'
            }
        }
    }

    post {
        failure {
            echo "The pipeline failed! Check the logs."
        }
    }
}