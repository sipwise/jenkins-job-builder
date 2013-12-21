- wrappers:
    name: timeout-wrapper
    wrappers:
        - timeout:
            fail: true
            elastic-percentage: 150
            elastic-default-timeout: 90
            type: elastic

- wrappers:
    name: pre-scm-shell-ant
    wrappers:
        - pre-scm-buildstep:
            - shell: |
                #!/bin/bash
                echo "Doing somethiung cool"
            - shell: |
                #!/bin/zsh
                echo "Doing somethin cool with zsh"
            - ant: "target1 target2"
            ant-name: "Standard Ant"
            - inject:
                properties-file: example.prop
                properties-content: EXAMPLE=foo-bar

- wrappers:
    name: copy-files
    wrappers:
        - copy-to-slave:
            includes:
            - file1
            - file2*.txt
            excludes:
            - file2bad.txt
