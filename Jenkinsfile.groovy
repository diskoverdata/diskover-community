pipeline {
  agent {
    label "streamotion-maven"
  }

  // parameters {
  //       string(name: 'BUILD_BRANCH', defaultValue: 'master', description: 'The target branch')
  // }

  environment {
    ORG = 'fsa-streamotion' 
    APP_NAME = 'diskover'
    DOCKER_REGISTRY='kayosportsau'
    TARGET_GIT_REPO='https://github.com/fsa-streamotion/diskover.git'
  }

        stages {
        stage('PR Build + PREVIEW') {
            when {
                branch 'PR-*'
            }
            environment {
                PREVIEW_VERSION = "0.0.0-SNAPSHOT-$BRANCH_NAME-$BUILD_NUMBER"
                PREVIEW_NAMESPACE = "$APP_NAME-$BRANCH_NAME".toLowerCase()
                HELM_RELEASE = "$PREVIEW_NAMESPACE".toLowerCase()
            }
            steps {
                container('maven') {
                    sh "echo **************** PREVIEW_VERSION: $PREVIEW_VERSION , PREVIEW_NAMESPACE: $PREVIEW_NAMESPACE, HELM_RELEASE: $HELM_RELEASE"
                    sh "echo $PREVIEW_VERSION > PREVIEW_VERSION"
                    sh "skaffold version"
                    sh "export VERSION=$PREVIEW_VERSION && skaffold build -f skaffold.yaml"
                    // sh "jx step post build --image $DOCKER_REGISTRY/$ORG/$APP_NAME:$PREVIEW_VERSION"

                    script {
                        def buildVersion = readFile "${env.WORKSPACE}/PREVIEW_VERSION"
                        currentBuild.description = "$APP_NAME.$PREVIEW_NAMESPACE"
                    }


                    dir('charts/preview') {
                      sh "make preview"
                      sh "jx preview --app $APP_NAME --namespace=$PREVIEW_NAMESPACE --dir ../.."
                      sh "sleep 20"
                      sh "kubectl describe pods -n=$PREVIEW_NAMESPACE"
                      sh "make print"
                    }
                }
            }
        }

        stage('Build Release') {
            when {
                branch 'master'
            }
            steps {
                container('maven') {

                    // ensure we're not on a detached head
                    sh "git checkout master"
                    sh "git config --global credential.helper store"
                    sh "jx step git credentials"

                    // so we can retrieve the version in later steps
                    sh "echo \$(jx-release-version) > VERSION"
                    sh "jx step tag --version \$(cat VERSION)"
                    sh "skaffold version"
                    sh "export VERSION=`cat VERSION` && skaffold build -f skaffold.yaml"

                    script {
                        def buildVersion = readFile "${env.WORKSPACE}/VERSION"
                        currentBuild.description = "$buildVersion"
                        currentBuild.displayName = "$buildVersion"
                    }

//            sh "jx step post build --image $DOCKER_REGISTRY/$ORG/$APP_NAME:\$(cat VERSION)"
                }

            }
        }

      stage('Promote to Environments') {
        when {
          branch 'master'
        }
        steps {
          container('maven') {
            dir("charts/diskover") {
              sh "jx step changelog --generate-yaml=false --version v\$(cat ../../VERSION)"

              // release the helm chart
              // sh "jx step helm release"
              // sh "ls -la"
              sh "make release"
              // promote through all 'Auto' promotion Environments
              // sh "jx promote -b --no-poll=true  --helm-repo-url=$CHART_REPOSITORY --no-poll=true --no-merge=true --no-wait=true --env=staging --version \$(cat ../../VERSION)"

              // sh "jx promote -b --no-poll=true --helm-repo-url=$CHART_REPOSITORY --no-poll=true --no-merge=true --no-wait=true --env=production --version \$(cat ../../VERSION)"

            }
          }
        }
    }

    }

    post {
      always {
      cleanWs()
    }
  }
}
