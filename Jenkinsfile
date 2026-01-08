pipeline{
  agent{
    docker{
      image 'python:3.10-slim'
    }
  }

  stages{
    stage('Setup venv & install deps') {
      steps {
        sh '''
          set -e
          python -V
          python -m venv .venv
          . .venv/bin/activate
          pip install -U pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
        '''
      }
    }

    stage('Run tests') {
      steps {
        sh '''
          set -e
          . .venv/bin/activate
          pytest -q
        '''
      }
    }
}

    post {
      success {
        echo 'CI passed: tests are green'
      }
      failure {
        echo 'CI failed: check test or dependency errors'
      }
  }
}