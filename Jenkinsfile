pipeline{
  agent{
    docker{
      image 'python:3.10-slim'
      args '-u root:root'
    }
  }

  stages{
    stage('Install dependencies') {
      steps {
        sh '''
          python -V
          pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
        '''
      }
    }

    stage('Run tests') {
      steps {
        sh 'pytest -q'
      }
    }
  }
}