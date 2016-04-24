#!/bin/bash -e
#
# Copyright 2016 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

rm -fr .test
mkdir -p .test/run-conf/config

CONFIGS_DIR=$(dirname ${0})/configs
CONFIGS=$(ls -1 ${CONFIGS_DIR}/*.conf 2>/dev/null)

cd .test
if [ -e /usr/zuul-env/bin/zuul-cloner ];
then
    /usr/zuul-env/bin/zuul-cloner -m ../tools/run-compare-clonemap.yaml --cache-dir /opt/git git://git.openstack.org openstack-infra/project-config
else
    git clone --depth=1 git://git.openstack.org/openstack-infra/project-config
fi
cp project-config/jenkins/jobs/* run-conf/config
cd ..

for config in ${CONFIGS}
do
    rm -fr .test/run-conf/out
    mkdir -p .test/run-conf/out
    tox -e venv -- jenkins-jobs --conf ${config} -l debug test -o .test/run-conf/out/ .test/run-conf/config
done

exit 0
