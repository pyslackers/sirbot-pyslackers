#!/usr/bin/env bash

echo "Preparing for deploy"
cd ansible
pip install ansible

openssl aes-256-cbc -K $encrypted_113807954c8a_key -iv $encrypted_113807954c8a_iv -in sirbot_travis_rsa.enc -out id_rsa -d
chmod 600 id_rsa

echo -n "$ANSIBLE_PASSWORD" > .pass

ansible-playbook playbook.yml --private-key=id_rsa --tags="deploy"
